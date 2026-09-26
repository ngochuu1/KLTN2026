"""Phase 1C integration tests: unittest + HTTPX + dedicated PostgreSQL.

Run from backend: python -m unittest tests.test_account_api -v
Install requirements-test.txt first. TEST_DATABASE_URL (environment or .env)
 must point to empty kltn_test, distinct from the application database.
Each test uses an outer transaction; real request sessions commit savepoints.
"""
import asyncio
import os
import unittest
from contextlib import AsyncExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect, select, func, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import decode_access_token, hash_refresh_token, verify_password
from app.models import AuthSession, User

BACKEND = Path(__file__).resolve().parents[1]
PASSWORD = 'Account-test-123'
NEW_PASSWORD = 'Changed-test-456'
EMAIL = 'user@test.com'
_test_url = ''


async def check_database():
    engine = create_async_engine(_test_url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            tables = await connection.run_sync(lambda c: inspect(c).get_table_names())
            if set(tables) - {'users', 'auth_sessions', 'alembic_version'}:
                raise RuntimeError('Refusing test database containing unrelated tables')
            for model in (User, AuthSession):
                if model.__tablename__ in tables:
                    if await connection.scalar(select(func.count()).select_from(model)):
                        raise RuntimeError('Refusing test database containing account data')
    finally:
        await engine.dispose()


def restore_settings(previous):
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    get_settings.cache_clear()


def setUpModule():
    global _test_url, app, get_db
    _test_url = os.environ.get('TEST_DATABASE_URL') or dotenv_values(BACKEND / '.env').get('TEST_DATABASE_URL') or ''
    if not _test_url:
        raise RuntimeError('TEST_DATABASE_URL is required; no development database fallback')
    url = make_url(_test_url)
    dev = make_url(str(get_settings().database_url))
    if url.drivername != 'postgresql+asyncpg' or url.database != 'kltn_test' or url.database == dev.database:
        raise RuntimeError('Tests require a separate PostgreSQL database named kltn_test')
    asyncio.run(check_database())
    overrides = {'DATABASE_URL': _test_url, 'APP_ENV': 'test', 'JWT_SECRET_KEY': 'phase-1c-test-key-only-' * 3}
    unittest.addModuleCleanup(restore_settings, {k: os.environ.get(k) for k in overrides})
    os.environ.update(overrides)
    get_settings.cache_clear()
    command.upgrade(Config(str(BACKEND / 'alembic.ini')), 'head')
    from app.main import app
    from app.db.session import get_db
    # Refuse any already-imported application engine targeting another database.
    from app.main import engine
    if engine.url != make_url(_test_url):
        raise RuntimeError('Application was imported with another database; run this suite separately')
    unittest.addModuleCleanup(lambda: asyncio.run(check_database()))


class AccountApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.stack = AsyncExitStack()
        self.addAsyncCleanup(self.stack.aclose)
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.stack.push_async_callback(self.engine.dispose)
        self.connection = await self.stack.enter_async_context(self.engine.connect())
        transaction = await self.connection.begin()
        self.stack.push_async_callback(transaction.rollback)

        async def test_db():
            async with AsyncSession(bind=self.connection, expire_on_commit=False,
                                    join_transaction_mode='create_savepoint') as session:
                yield session

        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = test_db
        self.stack.callback(lambda: (app.dependency_overrides.clear(), app.dependency_overrides.update(previous)))
        self.client = await self.stack.enter_async_context(httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url='https://testserver'))
        self.cookie_name = get_settings().refresh_cookie_name

    def error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text)
        body = response.json()
        self.assertEqual(set(body), {'error'})
        self.assertEqual(set(body['error']), {'code', 'message', 'fields'})
        self.assertEqual(body['error']['code'], code)
        self.assertIsInstance(body['error']['message'], str)
        self.assertTrue(body['error']['message'])
        if code == 'VALIDATION_ERROR':
            self.assertIsInstance(body['error']['fields'], dict)
            self.assertTrue(body['error']['fields'])
        else:
            self.assertIsNone(body['error']['fields'])
        self.assertNotIn(PASSWORD, response.text)
        return body

    def public(self, value):
        if isinstance(value, dict):
            self.assertFalse(set(value) & {'password', 'password_hash', 'refresh_token', 'refresh_token_hash'})
            for item in value.values():
                self.public(item)
        elif isinstance(value, list):
            for item in value:
                self.public(item)

    async def register(self, **changes):
        payload = dict(full_name='Account Test', email=EMAIL, password=PASSWORD, confirm_password=PASSWORD)
        payload.update(changes)
        response = await self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        self.public(response.json())
        return response.json()['data']

    async def login(self, password=PASSWORD, email=EMAIL):
        response = await self.client.post('/api/v1/auth/login', json=dict(email=email, password=password))
        self.assertEqual(response.status_code, 200, response.text)
        self.public(response.json())
        return response

    async def authenticated(self):
        await self.register()
        response = await self.login()
        token = response.json()['data']['access_token']
        self.headers = {'Authorization': f'Bearer {token}'}
        return decode_access_token(token)

    async def user(self):
        return (await self.connection.execute(select(User.__table__))).mappings().one()

    async def sessions(self):
        return (await self.connection.execute(select(AuthSession.__table__).order_by(AuthSession.created_at))).mappings().all()

    async def refresh(self, token=None):
        headers = {} if token is None else {'Cookie': f'{self.cookie_name}={token}'}
        return await self.client.post('/api/v1/auth/refresh', headers=headers)

    async def change(self, **changes):
        payload = dict(current_password=PASSWORD, new_password=NEW_PASSWORD, confirm_new_password=NEW_PASSWORD)
        payload.update(changes)
        return await self.client.post('/api/v1/users/me/change-password', json=payload, headers=self.headers)

    async def test_r1_register(self):
        data = await self.register()
        user = await self.user()
        self.assertEqual(str(user['id']), data['id'])
        for key, expected in {'email': EMAIL, 'full_name': 'Account Test', 'status': 'ACTIVE', 'system_role': 'USER'}.items():
            self.assertEqual(user[key], expected)
            self.assertEqual(data[key], expected)
        self.assertTrue(user['password_hash'].startswith('$argon2id$'))
        self.assertNotIn(PASSWORD, str(dict(user)))
        self.assertTrue(await verify_password(PASSWORD, user['password_hash']))
        self.assertEqual(await self.sessions(), [])
        self.assertFalse(self.client.cookies)

    async def test_r2_missing_fields(self):
        for field in ('full_name', 'email', 'password', 'confirm_password'):
            with self.subTest(field=field):
                payload = dict(full_name='Test', email=EMAIL, password=PASSWORD, confirm_password=PASSWORD)
                del payload[field]
                self.error(await self.client.post('/api/v1/auth/register', json=payload), 422, 'VALIDATION_ERROR')
        self.assertEqual(await self.connection.scalar(select(func.count()).select_from(User)), 0)

    async def test_r3_r4_r5_validation(self):
        for changes in ({'email': 'invalid'}, {'password': 'a'*7, 'confirm_password': 'a'*7},
                        {'password': 'a'*129, 'confirm_password': 'a'*129}, {'confirm_password': 'different-password'}):
            with self.subTest(changes=changes):
                payload = dict(full_name='Test', email=EMAIL, password=PASSWORD, confirm_password=PASSWORD)
                payload.update(changes)
                self.error(await self.client.post('/api/v1/auth/register', json=payload), 422, 'VALIDATION_ERROR')

    async def test_r4_password_boundaries(self):
        for length in (8, 128):
            with self.subTest(length=length):
                password = 'a' * length
                await self.register(email=f'length{length}@test.com', password=password, confirm_password=password)
                await self.login(password=password, email=f'length{length}@test.com')

    async def test_r6_r7_duplicate_normalized_email(self):
        await self.register(email='User@Test.COM')
        payload = dict(full_name='Duplicate', email=EMAIL, password=PASSWORD, confirm_password=PASSWORD)
        self.error(await self.client.post('/api/v1/auth/register', json=payload), 409, 'EMAIL_ALREADY_EXISTS')
        self.assertEqual(await self.connection.scalar(select(func.count()).select_from(User)), 1)
        self.assertEqual((await self.user())['email'], EMAIL)
        await self.login()

    async def test_l1_l5_login_and_hash(self):
        registered = await self.register()
        response = await self.login()
        data = response.json()['data']
        self.assertEqual(data['user'], {k: registered[k] for k in ('id', 'full_name', 'email', 'status', 'system_role')})
        self.assertEqual(data['token_type'], 'bearer')
        self.assertEqual(data['expires_in'], get_settings().access_token_expire_minutes * 60)
        claims = decode_access_token(data['access_token'])
        self.assertEqual(claims.exp - claims.iat, data['expires_in'])
        session, = await self.sessions()
        self.assertEqual(session['id'], claims.sid)
        self.assertEqual(session['user_id'], claims.sub)
        cookie = self.client.cookies.get(self.cookie_name)
        self.assertTrue(cookie)
        self.assertEqual(session['refresh_token_hash'], hash_refresh_token(cookie))
        self.assertNotIn(cookie, str(dict(session)))
        self.assertIsNone(session['revoked_at'])
        self.assertGreater(session['expires_at'], datetime.now(UTC))
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertIn('SameSite=lax', response.headers['set-cookie'])
        self.assertIn('Path=/api/v1/auth', response.headers['set-cookie'])
        self.assertEqual('Secure' in response.headers['set-cookie'], get_settings().cookie_secure)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertTrue(await verify_password(PASSWORD, (await self.user())['password_hash']))
        self.error(await self.client.post('/api/v1/auth/login', json=dict(email=EMAIL, password='wrong-password')), 401, 'INVALID_CREDENTIALS')
        self.assertEqual(len(await self.sessions()), 1)

    async def test_l2_l3_indistinguishable_credentials(self):
        await self.register()
        errors = []
        for email, password in (('absent@test.com', PASSWORD), (EMAIL, 'wrong-password')):
            errors.append(self.error(await self.client.post('/api/v1/auth/login', json=dict(email=email, password=password)), 401, 'INVALID_CREDENTIALS'))
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(await self.sessions(), [])

    async def test_l4_locked(self):
        await self.register()
        await self.connection.execute(update(User).values(status='LOCKED'))
        self.error(await self.client.post('/api/v1/auth/login', json=dict(email=EMAIL, password=PASSWORD)), 403, 'ACCOUNT_LOCKED')
        self.assertEqual(await self.sessions(), [])

    async def test_f1_f2_f3_refresh_rotation_reuse(self):
        claims = await self.authenticated()
        old_cookie = self.client.cookies.get(self.cookie_name)
        # JWT has second precision and no jti: cross the next second to assert new issuance.
        await asyncio.sleep(max(0, claims.iat + 1.05 - datetime.now(UTC).timestamp()))
        response = await self.refresh()
        self.assertEqual(response.status_code, 200, response.text)
        self.public(response.json())
        data = response.json()['data']
        new_claims = decode_access_token(data['access_token'])
        self.assertGreater(new_claims.iat, claims.iat)
        self.assertEqual(new_claims.sid, claims.sid)
        self.assertEqual(data['token_type'], 'bearer')
        self.assertEqual(data['expires_in'], get_settings().access_token_expire_minutes * 60)
        new_cookie = self.client.cookies.get(self.cookie_name)
        self.assertNotEqual(old_cookie, new_cookie)
        self.assertIn(self.cookie_name, response.headers['set-cookie'])
        session, = await self.sessions()
        self.assertEqual(session['refresh_token_hash'], hash_refresh_token(new_cookie))
        self.assertNotIn(new_cookie, str(dict(session)))
        self.error(await self.refresh(old_cookie), 401, 'SESSION_INVALID')
        self.assertEqual((await self.refresh(new_cookie)).status_code, 200)

    async def test_f4_revoked(self):
        await self.authenticated()
        await self.connection.execute(update(AuthSession).values(revoked_at=datetime.now(UTC)))
        self.error(await self.refresh(), 401, 'SESSION_INVALID')

    async def test_f5_expired(self):
        await self.authenticated()
        await self.connection.execute(update(AuthSession).values(expires_at=datetime.now(UTC)-timedelta(seconds=1)))
        self.error(await self.refresh(), 401, 'SESSION_EXPIRED')

    async def test_f6_locked(self):
        await self.authenticated()
        await self.connection.execute(update(User).values(status='LOCKED'))
        self.error(await self.refresh(), 403, 'ACCOUNT_LOCKED')

    async def test_f7_invalid_missing(self):
        self.error(await self.refresh(), 401, 'SESSION_INVALID')
        await self.authenticated()
        self.error(await self.refresh('unknown-token'), 401, 'SESSION_INVALID')
        token = self.client.cookies.get(self.cookie_name)
        self.error(await self.refresh(token + 'tampered'), 401, 'SESSION_INVALID')

    async def test_o1_o2_o3_logout_current_only(self):
        claims = await self.authenticated()
        old_cookie = self.client.cookies.get(self.cookie_name)
        other = await self.login()
        other_cookie = self.client.cookies.get(self.cookie_name)
        response = await self.client.post('/api/v1/auth/logout', headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertIn('Max-Age=0', response.headers['set-cookie'])
        self.assertIn('Path=/api/v1/auth', response.headers['set-cookie'])
        self.assertIsNone(self.client.cookies.get(self.cookie_name))
        sessions = {s['id']: s for s in await self.sessions()}
        self.assertIsNotNone(sessions[claims.sid]['revoked_at'])
        other_id = decode_access_token(other.json()['data']['access_token']).sid
        self.assertIsNone(sessions[other_id]['revoked_at'])
        self.error(await self.refresh(old_cookie), 401, 'SESSION_INVALID')
        self.error(await self.client.get('/api/v1/users/me', headers=self.headers), 401, 'SESSION_INVALID')
        self.assertEqual((await self.refresh(other_cookie)).status_code, 200)

    async def test_p1_profile(self):
        await self.authenticated()
        response = await self.client.get('/api/v1/users/me', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(set(data), {'id', 'full_name', 'email', 'status', 'system_role', 'created_at', 'updated_at'})
        user = await self.user()
        for key in data:
            if key.endswith('_at'):
                self.assertEqual(datetime.fromisoformat(data[key]), user[key])
            else:
                self.assertEqual(data[key], str(user[key]))
        self.public(response.json())

    async def test_p2_unauthenticated(self):
        self.error(await self.client.get('/api/v1/users/me'), 401, 'AUTHENTICATION_REQUIRED')

    async def test_p3_update_name(self):
        await self.authenticated()
        response = await self.client.patch('/api/v1/users/me', json={'full_name': 'Updated Name'}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['full_name'], 'Updated Name')
        self.assertEqual((await self.user())['full_name'], 'Updated Name')
        response = await self.client.get('/api/v1/users/me', headers=self.headers)
        self.assertEqual(response.json()['data']['full_name'], 'Updated Name')
        self.public(response.json())

    async def test_p4_invalid_name(self):
        await self.authenticated()
        for name in ('', '   ', 'a'*101):
            with self.subTest(name=name):
                self.error(await self.client.patch('/api/v1/users/me', json={'full_name': name}, headers=self.headers), 422, 'VALIDATION_ERROR')
        self.assertEqual((await self.user())['full_name'], 'Account Test')

    async def test_p5_email_rejected(self):
        await self.authenticated()
        self.error(await self.client.patch('/api/v1/users/me', json={'full_name': 'Changed', 'email': 'changed@test.com'}, headers=self.headers), 422, 'VALIDATION_ERROR')
        self.assertEqual((await self.user())['email'], EMAIL)
        self.assertEqual((await self.user())['full_name'], 'Account Test')

    async def test_c1_password_changed(self):
        await self.authenticated()
        old_hash = (await self.user())['password_hash']
        response = await self.change()
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(response.content, b'')
        new_hash = (await self.user())['password_hash']
        self.assertNotEqual(old_hash, new_hash)
        self.assertNotEqual(new_hash, NEW_PASSWORD)
        self.assertTrue(await verify_password(NEW_PASSWORD, new_hash))
        self.error(await self.client.post('/api/v1/auth/login', json=dict(email=EMAIL, password=PASSWORD)), 401, 'INVALID_CREDENTIALS')
        await self.login(password=NEW_PASSWORD)

    async def test_c2_incorrect_current(self):
        await self.authenticated()
        before = (await self.user())['password_hash']
        self.error(await self.change(current_password='wrong-password'), 400, 'CURRENT_PASSWORD_INCORRECT')
        self.assertEqual((await self.user())['password_hash'], before)

    async def test_c3_invalid_new_password(self):
        await self.authenticated()
        before = (await self.user())['password_hash']
        for length in (7, 129):
            with self.subTest(length=length):
                self.error(await self.change(new_password='a'*length, confirm_new_password='a'*length), 422, 'VALIDATION_ERROR')
        self.assertEqual((await self.user())['password_hash'], before)

    async def test_c4_confirmation(self):
        await self.authenticated()
        before = (await self.user())['password_hash']
        response = await self.change(confirm_new_password='different-password')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error']['code'], 'PASSWORD_CONFIRMATION_MISMATCH')
        self.assertEqual((await self.user())['password_hash'], before)

    async def test_c5_same_password(self):
        await self.authenticated()
        before = (await self.user())['password_hash']
        self.error(await self.change(new_password=PASSWORD, confirm_new_password=PASSWORD), 400, 'NEW_PASSWORD_SAME_AS_CURRENT')
        self.assertEqual((await self.user())['password_hash'], before)

    async def test_c6_other_sessions_revoked(self):
        claims = await self.authenticated()
        current_cookie = self.client.cookies.get(self.cookie_name)
        other = await self.login()
        other_cookie = self.client.cookies.get(self.cookie_name)
        other_token = other.json()['data']['access_token']
        response = await self.change()
        self.assertEqual(response.status_code, 204)
        sessions = {s['id']: s for s in await self.sessions()}
        self.assertIsNone(sessions[claims.sid]['revoked_at'])
        self.assertIsNotNone(sessions[decode_access_token(other_token).sid]['revoked_at'])
        self.assertEqual((await self.client.get('/api/v1/users/me', headers=self.headers)).status_code, 200)
        self.error(await self.client.get('/api/v1/users/me', headers={'Authorization': f'Bearer {other_token}'}), 401, 'SESSION_INVALID')
        self.error(await self.refresh(other_cookie), 401, 'SESSION_INVALID')
        self.assertEqual((await self.refresh(current_cookie)).status_code, 200)

    async def test_startup_and_health(self):
        # Exercise real lifespan and PostgreSQL connectivity, not an HTTP-only smoke test.
        async with app.router.lifespan_context(app):
            response = await self.client.get('/api/v1/health')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'status': 'ok'})
