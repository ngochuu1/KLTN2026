"""Targeted Phase 2B API smoke checks, not the Phase 2C test suite.

Run from backend: python -m scripts.verify_workspace_api
Uses kltn_test and rolls back all fixtures and API writes.
"""
import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from dotenv import dotenv_values
from sqlalchemy import select, func
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool


async def main():
    values = dotenv_values(Path(__file__).resolve().parents[1] / '.env')
    url = os.environ.get('TEST_DATABASE_URL') or values.get('TEST_DATABASE_URL') or ''
    development = os.environ.get('DATABASE_URL') or values.get('DATABASE_URL') or ''
    if make_url(url).database != 'kltn_test' or make_url(url).drivername != 'postgresql+asyncpg' or make_url(url).database == make_url(development).database:
        raise RuntimeError('Requires separate PostgreSQL kltn_test')
    os.environ['DATABASE_URL'] = url
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.db.session import get_db
    from app.core.security import create_access_token
    from app.models import User, AuthSession, Workspace, WorkspaceMember, WorkspaceInvitation
    from app.repositories.workspace_member_repository import WorkspaceMemberRepository
    from app.repositories.workspace_invitation_repository import WorkspaceInvitationRepository

    engine = create_async_engine(url, poolclass=NullPool)
    checks = 0
    async with engine.connect() as connection:
        outer = await connection.begin()
        async def db_override():
            async with AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as session:
                yield session
        app.dependency_overrides[get_db] = db_override
        try:
            async with AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as session:
                async with session.begin():
                    users = [User(full_name=f'Smoke {n}', email=f'{uuid4()}@example.com', password_hash='unused') for n in range(4)]
                    session.add_all(users)
                    await session.flush()
                    sessions = [AuthSession(user_id=u.id, refresh_token_hash=hashlib.sha256(uuid4().bytes).hexdigest(), expires_at=datetime.now(UTC)+timedelta(hours=1)) for u in users]
                    session.add_all(sessions)
                    await session.flush()
                    tokens = [create_access_token(u.id, s.id) for u, s in zip(users, sessions)]
                    ids = [str(u.id) for u in users]
            async with app.router.lifespan_context(app):
                async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url='http://test') as client:
                    async def request(actor, method, path, status=200, code=None, **kwargs):
                        nonlocal checks
                        headers = {'Authorization': f'Bearer {tokens[actor]}'} if actor is not None else {}
                        response = await client.request(method, '/api/v1'+path, headers=headers, **kwargs)
                        assert response.status_code == status, (method, path.split('/workspace-invitations/')[0], response.status_code, response.text)
                        if code:
                            assert response.json()['error']['code'] == code, response.text
                        checks += 1
                        return response.json().get('data') if response.content and status < 300 else None
                    await request(None, 'GET', '/workspaces', 401)
                    await request(0, 'POST', '/workspaces', 422, json={'name':'Bad', 'role':'OWNER'})
                    workspace = await request(0, 'POST', '/workspaces', 201, json={'name':' Smoke ', 'description':'initial'})
                    assert workspace['role'] == 'OWNER' and workspace['name'] == 'Smoke'
                    wid = workspace['id']; base = '/workspaces/'+wid
                    assert any(w['id'] == wid for w in await request(0, 'GET', '/workspaces'))
                    assert not any(w['id'] == wid for w in await request(1, 'GET', '/workspaces'))
                    await request(1, 'GET', base, 403, 'WORKSPACE_ACCESS_DENIED')
                    direct = await request(0, 'POST', base+'/invitations', 201, json={'invitee_user_id':ids[1]})
                    assert 'token_hash' not in direct and direct['expires_at'] is None
                    invite = '/workspace-invitations/'+direct['token']
                    await request(2, 'GET', invite, 403, 'INVITATION_NOT_FOR_USER')
                    await request(1, 'GET', invite)
                    accepted = await request(1, 'POST', invite+'/accept')
                    assert accepted['role'] == 'MEMBER'
                    await request(1, 'POST', invite+'/accept', 409, 'INVITATION_ALREADY_USED')
                    await request(0, 'POST', base+'/invitations', 409, 'WORKSPACE_ALREADY_MEMBER', json={'invitee_user_id':ids[1]})
                    await request(1, 'PATCH', base, 403, 'WORKSPACE_PERMISSION_DENIED', json={'name':'Denied'})
                    await request(1, 'POST', base+'/invitations', 403, 'WORKSPACE_PERMISSION_DENIED', json={})
                    role_path = base+'/members/'+ids[1]+'/role'
                    assert (await request(0, 'PATCH', role_path, json={'role':'ADMIN'}))['role'] == 'ADMIN'
                    await request(1, 'PATCH', base, json={'description':None})
                    await request(1, 'PATCH', role_path, 403, 'WORKSPACE_PERMISSION_DENIED', json={'role':'MEMBER'})
                    generic = await request(1, 'POST', base+'/invitations', 201, json={})
                    gi = '/workspace-invitations/'+generic['token']
                    await request(2, 'POST', gi+'/accept')
                    await request(1, 'DELETE', base, 403, 'WORKSPACE_PERMISSION_DENIED')
                    await request(2, 'DELETE', base, 403, 'WORKSPACE_PERMISSION_DENIED')
                    await request(1, 'DELETE', base+'/members/'+ids[0], 403, 'WORKSPACE_OWNER_CANNOT_BE_REMOVED')
                    await request(0, 'POST', base+'/leave', 403, 'WORKSPACE_OWNER_CANNOT_LEAVE')
                    await request(0, 'PATCH', role_path, json={'role':'MEMBER'})
                    await request(1, 'PATCH', base, 403, 'WORKSPACE_PERMISSION_DENIED', json={'name':'Denied immediately'})
                    await request(0, 'PATCH', role_path, 422, 'INVALID_WORKSPACE_ROLE', json={'role':'OWNER'})
                    await request(0, 'PATCH', base+'/members/'+ids[0]+'/role', 403, 'INVALID_WORKSPACE_ROLE', json={'role':'ADMIN'})
                    members = await request(2, 'GET', base+'/members')
                    assert len(members)==3 and all(set(m)=={'user_id','full_name','email','role','joined_at'} for m in members)
                    await request(0, 'PATCH', role_path, json={'role':'ADMIN'})
                    await request(1, 'POST', base+'/leave', 204)
                    await request(1, 'GET', base, 403)
                    await request(2, 'POST', base+'/leave', 204)
                    await request(2, 'GET', base, 403)
                    declined = await request(0, 'POST', base+'/invitations', 201, json={})
                    assert (await request(3, 'POST', '/workspace-invitations/'+declined['token']+'/decline'))['status']=='DECLINED'
                    expired = await request(0, 'POST', base+'/invitations', 201, json={'expires_at':(datetime.now(UTC)-timedelta(seconds=1)).isoformat()})
                    await request(3, 'GET', '/workspace-invitations/'+expired['token'], 410, 'INVITATION_EXPIRED')
                    remaining = await request(0, 'POST', base+'/invitations', 201, json={})
                    ri = '/workspace-invitations/'+remaining['token']
                    # Inject failures only to verify rollback of the two multi-write flows.
                    before = await connection.scalar(select(func.count()).select_from(Workspace))
                    async def fail(*args, **kwargs):
                        raise RuntimeError('Controlled rollback verification')
                    with patch.object(WorkspaceMemberRepository, 'create', fail):
                        await request(0, 'POST', '/workspaces', 500, 'INTERNAL_SERVER_ERROR', json={'name':'Rollback'})
                    assert await connection.scalar(select(func.count()).select_from(Workspace)) == before
                    with patch.object(WorkspaceInvitationRepository, 'update_status', fail):
                        await request(3, 'POST', ri+'/accept', 500, 'INTERNAL_SERVER_ERROR')
                    assert await connection.scalar(select(WorkspaceMember.id).where(WorkspaceMember.workspace_id==workspace['id'], WorkspaceMember.user_id==ids[3])) is None
                    await request(3, 'GET', ri)
                    await request(3, 'POST', ri+'/accept')
                    await request(0, 'DELETE', base+'/members/'+ids[3], 204)
                    await request(0, 'DELETE', base+'/members/'+ids[3], 404, 'WORKSPACE_MEMBER_NOT_FOUND')
                    pending = await request(0, 'POST', base+'/invitations', 201, json={})
                    await request(0, 'DELETE', base, 204)
                    assert not any(w['id']==wid for w in await request(0, 'GET', '/workspaces'))
                    for method, suffix, kwargs in [('GET','',{}), ('PATCH','',{'json':{'name':'Deleted'}}), ('POST','/invitations',{'json':{}}), ('GET','/members',{}), ('POST','/leave',{}), ('DELETE','/members/'+ids[0],{}), ('PATCH','/members/'+ids[0]+'/role',{'json':{'role':'ADMIN'}})]:
                        await request(0, method, base+suffix, 404, 'WORKSPACE_NOT_FOUND', **kwargs)
                    await request(3, 'POST', '/workspace-invitations/'+pending['token']+'/accept', 404, 'WORKSPACE_NOT_FOUND')
                    assert await connection.scalar(select(Workspace.deleted_at).where(Workspace.id==wid)) is not None
                    assert await connection.scalar(select(func.count()).select_from(WorkspaceMember).where(WorkspaceMember.workspace_id==wid))==1
                    assert await connection.scalar(select(func.count()).select_from(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id==wid))>0
                    stored = await connection.scalar(select(WorkspaceInvitation.token_hash).where(WorkspaceInvitation.id==direct['id']))
                    assert stored == hashlib.sha256(direct['token'].encode()).hexdigest()
                    assert len([op for path, item in app.openapi()['paths'].items() if '/workspace' in path for op in item if op in {'get','post','patch','delete'}])==13
            print(f'PASS: {checks} targeted API requests; startup, rollback and persistence checks PASS')
        finally:
            app.dependency_overrides.pop(get_db, None)
            await outer.rollback()
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
