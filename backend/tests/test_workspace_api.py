"""Phase 2C: real auth + HTTPX + PostgreSQL kltn_test.

Run separately from backend: python -m unittest tests.test_workspace_api -v
Ordinary tests roll back an outer transaction; concurrency tests use independent
connections and delete only their own committed UUID fixtures, even on failure.
"""
import asyncio
from contextlib import AsyncExitStack
from datetime import UTC, datetime, timedelta
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import delete, func, inspect, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import AuthSession, User, Workspace, WorkspaceInvitation, WorkspaceMember
from app.models.enums import InvitationStatus, SystemRole, WorkspaceRole
from app.repositories.workspace_invitation_repository import WorkspaceInvitationRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository

BACKEND = Path(__file__).resolve().parents[1]
_test_url = ''
MODELS = (WorkspaceInvitation, WorkspaceMember, Workspace, AuthSession, User)


async def require_empty_database():
    engine = create_async_engine(_test_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            tables = set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
            if tables - {'alembic_version', *(m.__tablename__ for m in MODELS)}:
                raise RuntimeError('Refusing unrelated tables in kltn_test')
            for model in MODELS:
                if model.__tablename__ in tables and await conn.scalar(select(func.count()).select_from(model)):
                    raise RuntimeError('Requires empty kltn_test; refusing existing data')
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
        raise RuntimeError('TEST_DATABASE_URL required; no development fallback')
    url = make_url(_test_url)
    dev = make_url(str(get_settings().database_url))
    if url.drivername != 'postgresql+asyncpg' or url.database != 'kltn_test' or url.database == dev.database:
        raise RuntimeError('Requires separate PostgreSQL kltn_test')
    asyncio.run(require_empty_database())
    overrides = {'DATABASE_URL': _test_url, 'APP_ENV': 'test', 'JWT_SECRET_KEY': 'phase-2c-only-test-key-' * 3}
    unittest.addModuleCleanup(restore_settings, {key: os.environ.get(key) for key in overrides})
    os.environ.update(overrides)
    get_settings.cache_clear()
    command.upgrade(Config(str(BACKEND / 'alembic.ini')), 'head')
    from app.main import app, engine
    from app.db.session import get_db
    if engine.url != url:
        raise RuntimeError('App previously imported against another DB; run suite separately')
    unittest.addModuleCleanup(lambda: asyncio.run(require_empty_database()))


class WorkspaceHarness(unittest.IsolatedAsyncioTestCase):
    committed = False

    async def asyncSetUp(self):
        self.stack = AsyncExitStack()
        self.addAsyncCleanup(self.stack.aclose)
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.stack.push_async_callback(self.engine.dispose)
        self.connection = await self.stack.enter_async_context(self.engine.connect())
        self.user_ids = [uuid4() for _ in range(6)]
        self.wid = uuid4()
        self.base = f'/workspaces/{self.wid}'
        if self.committed:
            self.stack.push_async_callback(self.cleanup_committed)
        else:
            outer = await self.connection.begin()
            self.stack.push_async_callback(outer.rollback)
        async with self.session() as session:
            async with session.begin():
                users = [User(id=uid, full_name=f'Workspace user {i}', email=f'{uid}@example.com', password_hash='unused-test-hash') for i, uid in enumerate(self.user_ids)]
                session.add_all(users)
                await session.flush()
                sessions = [AuthSession(user_id=uid, refresh_token_hash=hashlib.sha256(uuid4().bytes).hexdigest(), expires_at=datetime.now(UTC)+timedelta(hours=1)) for uid in self.user_ids]
                session.add_all(sessions)
                session.add(Workspace(id=self.wid, name='Workspace fixture', description='Initial'))
                await session.flush()
                session.add_all([WorkspaceMember(workspace_id=self.wid, user_id=self.user_ids[i], role=role) for i, role in enumerate((WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER, WorkspaceRole.MEMBER))])
                self.tokens = [create_access_token(uid, auth.id) for uid, auth in zip(self.user_ids, sessions)]
        async def test_db():
            async with self.session() as session:
                yield session
        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = test_db
        self.stack.callback(lambda: (app.dependency_overrides.clear(), app.dependency_overrides.update(previous)))
        self.client = await self.stack.enter_async_context(httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url='https://testserver'))

    def session(self):
        if self.committed:
            return AsyncSession(self.engine, expire_on_commit=False)
        return AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode='create_savepoint')

    async def cleanup_committed(self):
        async with self.engine.begin() as conn:
            await conn.execute(delete(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id == self.wid))
            await conn.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == self.wid))
            await conn.execute(delete(Workspace).where(Workspace.id == self.wid))
            await conn.execute(delete(AuthSession).where(AuthSession.user_id.in_(self.user_ids)))
            await conn.execute(delete(User).where(User.id.in_(self.user_ids)))

    async def scalar(self, statement):
        async with self.session() as session:
            return await session.scalar(statement)

    async def change_db(self, statement):
        async with self.session() as session:
            async with session.begin():
                await session.execute(statement)

    async def call(self, actor, method, path, status=200, code=None, **kwargs):
        headers = {'Authorization': f'Bearer {self.tokens[actor]}'} if actor is not None else {}
        response = await self.client.request(method, '/api/v1'+path, headers=headers, **kwargs)
        self.assertEqual(response.status_code, status, response.text)
        if code:
            body = response.json()
            self.assertEqual(set(body), {'error'})
            self.assertEqual(set(body['error']), {'code', 'message', 'fields'})
            self.assertEqual(body['error']['code'], code)
            self.assertTrue(body['error']['message'])
            if code == 'VALIDATION_ERROR':
                self.assertIsInstance(body['error']['fields'], dict)
            else:
                self.assertIsNone(body['error']['fields'])
        if status < 300 and status != 204:
            self.assertEqual(set(response.json()), {'data'})
            return response.json()['data']
        if status == 204:
            self.assertEqual(response.content, b'')
        return response

    async def invitation(self, actor=0, **payload):
        return await self.call(actor, 'POST', self.base+'/invitations', 201, json=payload)

    @staticmethod
    def invitation_path(invitation):
        return '/workspace-invitations/'+invitation['token']

    async def membership_count(self, actor):
        return await self.scalar(select(func.count()).select_from(WorkspaceMember).where(
            WorkspaceMember.workspace_id == self.wid, WorkspaceMember.user_id == self.user_ids[actor]))

    async def invitation_status(self, invitation):
        return await self.scalar(select(WorkspaceInvitation.status).where(WorkspaceInvitation.id == UUID(invitation['id'])))


class WorkspaceApiTests(WorkspaceHarness):
    async def test_create_owner_and_persistence(self):
        data = await self.call(4, 'POST', '/workspaces', 201, json={'name':' New workspace ', 'description':'Description'})
        self.assertEqual((data['name'], data['description'], data['role']), ('New workspace', 'Description', 'OWNER'))
        wid = UUID(data['id'])
        self.assertEqual(await self.scalar(select(Workspace.name).where(Workspace.id == wid)), 'New workspace')
        self.assertEqual(await self.scalar(select(WorkspaceMember.role).where(WorkspaceMember.workspace_id == wid, WorkspaceMember.user_id == self.user_ids[4])), WorkspaceRole.OWNER)
        self.assertEqual(await self.scalar(select(func.count()).select_from(WorkspaceMember).where(WorkspaceMember.workspace_id == wid)), 1)

    async def test_create_invalid_input(self):
        before = await self.scalar(select(func.count()).select_from(Workspace))
        for payload in ({}, {'name':''}, {'name':'  '}, {'name':'a'*121}, {'name':None}, {'name':123},
                        *({'name':'Bad', key:value} for key, value in [('owner_id',str(self.user_ids[0])), ('user_id',str(self.user_ids[0])), ('role','OWNER'), ('deleted_at',None)])):
            with self.subTest(payload=payload):
                await self.call(0, 'POST', '/workspaces', 422, 'VALIDATION_ERROR', json=payload)
        self.assertEqual(await self.scalar(select(func.count()).select_from(Workspace)), before)

    async def test_create_rolls_back_owner_failure(self):
        before = await self.scalar(select(func.count()).select_from(Workspace))
        async def fail(*args, **kwargs):
            raise RuntimeError('Injected membership failure')
        with patch.object(WorkspaceMemberRepository, 'create', fail):
            await self.call(4, 'POST', '/workspaces', 500, 'INTERNAL_SERVER_ERROR', json={'name':'Atomic'})
        self.assertEqual(await self.scalar(select(func.count()).select_from(Workspace)), before)
        orphan = select(func.count()).select_from(Workspace).where(~select(WorkspaceMember.id).where(WorkspaceMember.workspace_id == Workspace.id, WorkspaceMember.role == WorkspaceRole.OWNER).exists())
        self.assertEqual(await self.scalar(orphan), 0)

    async def test_list_only_own_active_workspaces(self):
        other = await self.call(4, 'POST', '/workspaces', 201, json={'name':'Other'})
        for actor, role in [(0,'OWNER'), (1,'ADMIN'), (2,'MEMBER')]:
            data = await self.call(actor, 'GET', '/workspaces')
            self.assertEqual([(w['id'],w['role']) for w in data], [(str(self.wid),role)])
        self.assertEqual([w['id'] for w in await self.call(4, 'GET', '/workspaces')], [other['id']])
        await self.call(0, 'DELETE', self.base, 204)
        self.assertEqual(await self.call(0, 'GET', '/workspaces'), [])

    async def test_view_and_list_members_permissions(self):
        for actor, role in [(0,'OWNER'), (1,'ADMIN'), (2,'MEMBER')]:
            with self.subTest(role=role):
                self.assertEqual((await self.call(actor, 'GET', self.base))['role'], role)
                members = await self.call(actor, 'GET', self.base+'/members')
                self.assertEqual({m['user_id'] for m in members}, {str(u) for u in self.user_ids[:4]})
                self.assertEqual({m['user_id']:m['role'] for m in members}, {str(self.user_ids[i]):r for i,r in enumerate(['OWNER','ADMIN','MEMBER','MEMBER'])})
                for m in members:
                    self.assertEqual(set(m), {'user_id','full_name','email','role','joined_at'})
                    self.assertEqual(m['email'], m['user_id']+'@example.com')
                    self.assertTrue(m['full_name'])
                    self.assertIsNotNone(datetime.fromisoformat(m['joined_at']).tzinfo)
        for suffix in ('','/members'):
            await self.call(4, 'GET', self.base+suffix, 403, 'WORKSPACE_ACCESS_DENIED')

    async def test_update_permission_matrix_and_patch_semantics(self):
        for actor in (0,1):
            data = await self.call(actor, 'PATCH', self.base, json={'name':f'Updated {actor}'})
            self.assertEqual(data['name'], f'Updated {actor}')
            self.assertEqual(data['description'], 'Initial')
        await self.call(2, 'PATCH', self.base, 403, 'WORKSPACE_PERMISSION_DENIED', json={'name':'Denied'})
        self.assertEqual(await self.scalar(select(Workspace.name).where(Workspace.id == self.wid)), 'Updated 1')
        data = await self.call(0, 'PATCH', self.base, json={'description':None})
        self.assertIsNone(data['description'])
        self.assertEqual(data['name'], 'Updated 1')
        for payload in ({}, {'name':None}, {'name':' '}, {'role':'OWNER'}, {'deleted_at':None}):
            await self.call(0, 'PATCH', self.base, 422, 'VALIDATION_ERROR', json=payload)

    async def test_invitation_permission_matrix_and_hash_storage(self):
        tokens = []
        for actor in (0,1):
            invitation = await self.invitation(actor)
            tokens.append(invitation['token'])
            self.assertIsNone(invitation['expires_at'])
            self.assertIsNone(invitation['invitee_user_id'])
            self.assertEqual(invitation['status'], 'PENDING')
            self.assertNotIn('token_hash', invitation)
            token_hash = await self.scalar(select(WorkspaceInvitation.token_hash).where(WorkspaceInvitation.id == UUID(invitation['id'])))
            self.assertEqual(token_hash, hashlib.sha256(invitation['token'].encode()).hexdigest())
            self.assertNotEqual(token_hash, invitation['token'])
        self.assertNotEqual(tokens[0], tokens[1])
        await self.call(2, 'POST', self.base+'/invitations', 403, 'WORKSPACE_PERMISSION_DENIED', json={})
        self.assertEqual(await self.scalar(select(func.count()).select_from(WorkspaceInvitation)), 2)
        columns = await self.connection.run_sync(lambda c: inspect(c).get_columns('workspace_invitations'))
        self.assertFalse({'token','code','invitation_token'} & {c['name'] for c in columns})

    async def test_direct_invitation_validation_and_preview(self):
        invitation = await self.invitation(invitee_user_id=str(self.user_ids[4]))
        data = await self.call(4, 'GET', self.invitation_path(invitation))
        self.assertEqual(set(data), {'workspace_id','name','description','expires_at'})
        self.assertEqual(data['workspace_id'], str(self.wid))
        for method, suffix in [('GET',''), ('POST','/accept'), ('POST','/decline')]:
            await self.call(5, method, self.invitation_path(invitation)+suffix, 403, 'INVITATION_NOT_FOR_USER')
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.PENDING)
        await self.call(0, 'POST', self.base+'/invitations', 404, 'USER_NOT_FOUND', json={'invitee_user_id':str(uuid4())})
        await self.call(0, 'POST', self.base+'/invitations', 409, 'WORKSPACE_ALREADY_MEMBER', json={'invitee_user_id':str(self.user_ids[2])})
        await self.call(0, 'POST', self.base+'/invitations', 422, 'VALIDATION_ERROR', json={'role':'ADMIN'})

    async def test_accept_direct_invitation_atomic_state(self):
        invitation = await self.invitation(invitee_user_id=str(self.user_ids[4]))
        result = await self.call(4, 'POST', self.invitation_path(invitation)+'/accept')
        self.assertEqual(result['role'], 'MEMBER')
        self.assertEqual(await self.membership_count(4), 1)
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.ACCEPTED)
        self.assertEqual((await self.call(4, 'GET', self.base))['role'], 'MEMBER')
        for method, suffix in [('GET',''), ('POST','/accept'), ('POST','/decline')]:
            await self.call(4, method, self.invitation_path(invitation)+suffix, 409, 'INVITATION_ALREADY_USED')
        self.assertEqual(await self.membership_count(4), 1)

    async def test_generic_invitation_accept_no_expiry(self):
        invitation = await self.invitation()
        await self.call(4, 'GET', self.invitation_path(invitation))
        await self.call(4, 'POST', self.invitation_path(invitation)+'/accept')
        await self.call(5, 'POST', self.invitation_path(invitation)+'/accept', 409, 'INVITATION_ALREADY_USED')
        self.assertEqual(await self.membership_count(4), 1)
        self.assertEqual(await self.membership_count(5), 0)

    async def test_decline_creates_no_membership(self):
        for payload in ({}, {'invitee_user_id':str(self.user_ids[4])}):
            invitation = await self.invitation(**payload)
            data = await self.call(4, 'POST', self.invitation_path(invitation)+'/decline')
            self.assertEqual(data['status'], 'DECLINED')
            self.assertEqual(await self.invitation_status(invitation), InvitationStatus.DECLINED)
            self.assertEqual(await self.membership_count(4), 0)
            await self.call(4, 'POST', self.invitation_path(invitation)+'/accept', 409, 'INVITATION_ALREADY_USED')

    async def test_invalid_expired_and_revoked_invitations(self):
        expired = await self.invitation(expires_at=(datetime.now(UTC)-timedelta(seconds=1)).isoformat())
        revoked = await self.invitation()
        await self.change_db(update(WorkspaceInvitation).where(WorkspaceInvitation.id == UUID(revoked['id'])).values(status=InvitationStatus.REVOKED))
        for path, status, code in [('/workspace-invitations/not-a-token',404,'INVITATION_INVALID'), (self.invitation_path(expired),410,'INVITATION_EXPIRED'), (self.invitation_path(revoked),409,'INVITATION_ALREADY_USED')]:
            for method, suffix in [('GET',''), ('POST','/accept'), ('POST','/decline')]:
                with self.subTest(code=code, suffix=suffix):
                    await self.call(4, method, path+suffix, status, code)
        self.assertEqual(await self.membership_count(4), 0)
        self.assertEqual(await self.invitation_status(expired), InvitationStatus.PENDING)
        future = await self.invitation(expires_at=(datetime.now(UTC)+timedelta(hours=1)).isoformat())
        await self.call(4, 'POST', self.invitation_path(future)+'/accept')

    async def test_duplicate_membership_does_not_consume_invitation(self):
        invitation = await self.invitation()
        for method, suffix in [('GET',''), ('POST','/accept'), ('POST','/decline')]:
            await self.call(2, method, self.invitation_path(invitation)+suffix, 409, 'WORKSPACE_ALREADY_MEMBER')
        self.assertEqual(await self.membership_count(2), 1)
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.PENDING)

    async def test_accept_rolls_back_membership_on_status_failure(self):
        invitation = await self.invitation()
        original = WorkspaceInvitationRepository.update_status
        async def fail_after_status(repository, *args, **kwargs):
            await original(repository, *args, **kwargs)
            raise RuntimeError('Injected failure after both writes')
        with patch.object(WorkspaceInvitationRepository, 'update_status', fail_after_status):
            await self.call(4, 'POST', self.invitation_path(invitation)+'/accept', 500, 'INTERNAL_SERVER_ERROR')
        self.assertEqual(await self.membership_count(4), 0)
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.PENDING)
        await self.call(4, 'POST', self.invitation_path(invitation)+'/accept')
        self.assertEqual(await self.membership_count(4), 1)

    async def test_database_unique_membership_and_single_owner(self):
        async with self.session() as session:
            async with session.begin():
                for uid, role, constraint in [(self.user_ids[2],'MEMBER','uq_workspace_members_workspace_user'), (self.user_ids[4],'OWNER','uq_workspace_members_owner')]:
                    with self.subTest(constraint=constraint):
                        with self.assertRaises(IntegrityError) as raised:
                            async with session.begin_nested():
                                await session.execute(text('INSERT INTO workspace_members (id, workspace_id, user_id, role) VALUES (:id, :wid, :uid, :role)'), {'id':uuid4(),'wid':self.wid,'uid':uid,'role':role})
                        self.assertEqual(getattr(raised.exception.orig.__cause__, 'constraint_name', None), constraint)
        self.assertEqual(await self.membership_count(2), 1)
        self.assertEqual(await self.membership_count(4), 0)

    async def test_owner_remove_member_and_admin(self):
        for target in (3,1):
            await self.call(0, 'DELETE', self.base+f'/members/{self.user_ids[target]}', 204)
            self.assertEqual(await self.membership_count(target), 0)
            await self.call(target, 'GET', self.base, 403, 'WORKSPACE_ACCESS_DENIED')

    async def test_remove_permission_matrix_and_missing_target(self):
        path = self.base+f'/members/{self.user_ids[3]}'
        await self.call(2, 'DELETE', path, 403, 'WORKSPACE_PERMISSION_DENIED')
        self.assertEqual(await self.membership_count(3), 1)
        await self.call(1, 'DELETE', path, 204)
        self.assertEqual(await self.membership_count(3), 0)
        await self.call(0, 'DELETE', path, 404, 'WORKSPACE_MEMBER_NOT_FOUND')
        await self.call(0, 'DELETE', self.base+f'/members/{uuid4()}', 404, 'WORKSPACE_MEMBER_NOT_FOUND')

    async def test_owner_cannot_be_removed(self):
        for actor in (0,1):
            await self.call(actor, 'DELETE', self.base+f'/members/{self.user_ids[0]}', 403, 'WORKSPACE_OWNER_CANNOT_BE_REMOVED')
        self.assertEqual(await self.membership_count(0), 1)

    async def test_change_role_owner_and_immediate_permission(self):
        path = self.base+f'/members/{self.user_ids[2]}/role'
        self.assertEqual((await self.call(0, 'PATCH', path, json={'role':'ADMIN'}))['role'], 'ADMIN')
        await self.call(2, 'PATCH', self.base, json={'name':'New admin'})
        self.assertEqual((await self.call(0, 'PATCH', path, json={'role':'MEMBER'}))['role'], 'MEMBER')
        await self.call(2, 'PATCH', self.base, 403, 'WORKSPACE_PERMISSION_DENIED', json={'name':'Denied'})
        self.assertEqual(await self.scalar(select(WorkspaceMember.role).where(WorkspaceMember.workspace_id==self.wid, WorkspaceMember.user_id==self.user_ids[2])), WorkspaceRole.MEMBER)

    async def test_change_role_denied_for_admin_and_member(self):
        for actor in (1,2):
            await self.call(actor, 'PATCH', self.base+f'/members/{self.user_ids[3]}/role', 403, 'WORKSPACE_PERMISSION_DENIED', json={'role':'ADMIN'})
        self.assertEqual(await self.scalar(select(WorkspaceMember.role).where(WorkspaceMember.workspace_id==self.wid, WorkspaceMember.user_id==self.user_ids[3])), WorkspaceRole.MEMBER)

    async def test_role_cannot_assign_owner_or_modify_self_owner(self):
        for role in ('OWNER','OTHER','admin'):
            await self.call(0, 'PATCH', self.base+f'/members/{self.user_ids[2]}/role', 422, 'INVALID_WORKSPACE_ROLE', json={'role':role})
        await self.call(0, 'PATCH', self.base+f'/members/{self.user_ids[0]}/role', 403, 'INVALID_WORKSPACE_ROLE', json={'role':'ADMIN'})
        await self.call(0, 'PATCH', self.base+f'/members/{uuid4()}/role', 404, 'WORKSPACE_MEMBER_NOT_FOUND', json={'role':'ADMIN'})
        self.assertEqual(await self.scalar(select(WorkspaceMember.role).where(WorkspaceMember.workspace_id==self.wid, WorkspaceMember.user_id==self.user_ids[0])), WorkspaceRole.OWNER)

    async def test_leave_permission_matrix_and_loss_of_access(self):
        await self.call(0, 'POST', self.base+'/leave', 403, 'WORKSPACE_OWNER_CANNOT_LEAVE')
        self.assertEqual(await self.membership_count(0), 1)
        for actor in (1,2):
            await self.call(actor, 'POST', self.base+'/leave', 204)
            self.assertEqual(await self.membership_count(actor), 0)
            await self.call(actor, 'GET', self.base, 403, 'WORKSPACE_ACCESS_DENIED')
            self.assertEqual(await self.call(actor, 'GET', '/workspaces'), [])
            await self.call(actor, 'POST', self.base+'/leave', 403, 'WORKSPACE_ACCESS_DENIED')

    async def test_delete_permission_matrix_preserves_rows(self):
        invitation = await self.invitation()
        for actor in (1,2):
            await self.call(actor, 'DELETE', self.base, 403, 'WORKSPACE_PERMISSION_DENIED')
        self.assertIsNone(await self.scalar(select(Workspace.deleted_at).where(Workspace.id==self.wid)))
        await self.call(0, 'DELETE', self.base, 204)
        deleted_at = await self.scalar(select(Workspace.deleted_at).where(Workspace.id==self.wid))
        self.assertIsNotNone(deleted_at)
        self.assertIsNotNone(deleted_at.tzinfo)
        self.assertEqual(await self.scalar(select(func.count()).select_from(Workspace).where(Workspace.id==self.wid)), 1)
        self.assertEqual(await self.scalar(select(func.count()).select_from(WorkspaceMember).where(WorkspaceMember.workspace_id==self.wid)), 4)
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.PENDING)

    async def test_deleted_workspace_blocks_all_business_endpoints(self):
        invitation = await self.invitation()
        await self.call(0, 'DELETE', self.base, 204)
        for method, suffix, kwargs in [('GET','',{}), ('PATCH','',{'json':{'name':'No'}}), ('DELETE','',{}), ('POST','/invitations',{'json':{}}), ('GET','/members',{}), ('DELETE',f'/members/{self.user_ids[2]}',{}), ('PATCH',f'/members/{self.user_ids[2]}/role',{'json':{'role':'ADMIN'}}), ('POST','/leave',{})]:
            with self.subTest(method=method, suffix=suffix):
                await self.call(0, method, self.base+suffix, 404, 'WORKSPACE_NOT_FOUND', **kwargs)
        for method, suffix in [('GET',''), ('POST','/accept'), ('POST','/decline')]:
            await self.call(4, method, self.invitation_path(invitation)+suffix, 404, 'WORKSPACE_NOT_FOUND')
        for actor in (0,1,2):
            self.assertEqual(await self.call(actor, 'GET', '/workspaces'), [])

    async def test_system_admin_has_no_workspace_privileges(self):
        await self.change_db(update(User).where(User.id.in_([self.user_ids[2],self.user_ids[4]])).values(system_role=SystemRole.ADMIN))
        await self.call(4, 'GET', self.base, 403, 'WORKSPACE_ACCESS_DENIED')
        await self.call(2, 'PATCH', self.base, 403, 'WORKSPACE_PERMISSION_DENIED', json={'name':'No'})
        await self.call(2, 'DELETE', self.base, 403, 'WORKSPACE_PERMISSION_DENIED')

    async def test_error_contract_representatives(self):
        await self.call(None, 'GET', '/workspaces', 401, 'AUTHENTICATION_REQUIRED')
        await self.call(4, 'GET', self.base, 403, 'WORKSPACE_ACCESS_DENIED')
        await self.call(0, 'GET', '/workspaces/'+str(uuid4()), 404, 'WORKSPACE_NOT_FOUND')
        await self.call(0, 'POST', self.base+'/invitations', 409, 'WORKSPACE_ALREADY_MEMBER', json={'invitee_user_id':str(self.user_ids[2])})
        await self.call(4, 'GET', '/workspace-invitations/invalid', 404, 'INVITATION_INVALID')

    async def test_backend_startup(self):
        async with app.router.lifespan_context(app):
            response = await self.client.get('/api/v1/health')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'status':'ok'})


class WorkspaceConcurrencyTests(WorkspaceHarness):
    committed = True

    async def race(self, requests):
        # Independent request sessions/connections. A bounded timeout prevents hangs.
        return await asyncio.wait_for(asyncio.gather(*[
            self.client.request(method, '/api/v1'+path, headers={'Authorization':f'Bearer {self.tokens[actor]}'})
            for actor, method, path in requests
        ]), timeout=15)

    async def test_same_invitation_two_users_only_one_accepts(self):
        invitation = await self.invitation()
        path = self.invitation_path(invitation)+'/accept'
        arrived = 0
        ready = asyncio.Event()
        original = WorkspaceRepository.get_by_id
        async def synchronized(repository, *args, **kwargs):
            nonlocal arrived
            arrived += 1
            if arrived == 2:
                ready.set()
            await asyncio.wait_for(ready.wait(), timeout=10)
            return await original(repository, *args, **kwargs)
        with patch.object(WorkspaceRepository, 'get_by_id', synchronized):
            responses = await self.race([(4,'POST',path),(5,'POST',path)])
        self.assertEqual(sorted(r.status_code for r in responses), [200,409], [r.text for r in responses])
        loser = next(r for r in responses if r.status_code == 409)
        self.assertEqual(loser.json()['error']['code'], 'INVITATION_ALREADY_USED')
        self.assertEqual(await self.membership_count(4)+await self.membership_count(5), 1)
        self.assertEqual(await self.invitation_status(invitation), InvitationStatus.ACCEPTED)

    async def test_two_invitations_same_user_no_duplicate(self):
        first, second = await self.invitation(), await self.invitation()
        responses = await self.race([(4,'POST',self.invitation_path(i)+'/accept') for i in (first,second)])
        self.assertEqual(sorted(r.status_code for r in responses), [200,409], [r.text for r in responses])
        self.assertEqual(next(r for r in responses if r.status_code==409).json()['error']['code'], 'WORKSPACE_ALREADY_MEMBER')
        self.assertEqual(await self.membership_count(4), 1)
        self.assertCountEqual([await self.invitation_status(first), await self.invitation_status(second)], [InvitationStatus.ACCEPTED,InvitationStatus.PENDING])

    async def test_accept_versus_decline_consistent_final_state(self):
        invitation = await self.invitation()
        path = self.invitation_path(invitation)
        responses = await self.race([(4,'POST',path+'/accept'),(5,'POST',path+'/decline')])
        self.assertEqual(sorted(r.status_code for r in responses), [200,409], [r.text for r in responses])
        status = await self.invitation_status(invitation)
        self.assertIn(status, (InvitationStatus.ACCEPTED,InvitationStatus.DECLINED))
        self.assertEqual(await self.membership_count(4), int(status==InvitationStatus.ACCEPTED))
        self.assertEqual(await self.membership_count(5), 0)
