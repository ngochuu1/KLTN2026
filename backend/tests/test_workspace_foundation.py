"""Phase 2A PostgreSQL verification; fixtures always roll back on kltn_test."""
import asyncio
import hashlib
import os
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import User, Workspace, WorkspaceMember, WorkspaceInvitation
from app.models.enums import WorkspaceRole, InvitationStatus
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_invitation_repository import WorkspaceInvitationRepository

BACKEND = Path(__file__).resolve().parents[1]
_original_url = None
_test_url = ''


def setUpModule():
    global _original_url, _test_url
    _test_url = os.environ.get('TEST_DATABASE_URL') or dotenv_values(BACKEND / '.env').get('TEST_DATABASE_URL') or ''
    url = make_url(_test_url)
    if url.database != 'kltn_test' or url.drivername != 'postgresql+asyncpg' or url.database == make_url(str(get_settings().database_url)).database:
        raise RuntimeError('Requires dedicated kltn_test PostgreSQL database')

    async def guard():
        engine = create_async_engine(_test_url, poolclass=NullPool)
        try:
            async with engine.connect() as conn:
                tables = set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
                if tables - {'alembic_version', 'users', 'auth_sessions', 'workspaces', 'workspace_members', 'workspace_invitations'}:
                    raise RuntimeError('Unrelated tables in test database')
                for table in (Workspace.__table__, WorkspaceMember.__table__, WorkspaceInvitation.__table__):
                    if table.name in tables and await conn.scalar(select(text('count(*)')).select_from(table)):
                        raise RuntimeError('Workspace test tables must be empty before migration round trip')
        finally:
            await engine.dispose()
    asyncio.run(guard())
    _original_url = os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL'] = _test_url
    get_settings.cache_clear()
    config = Config(str(BACKEND / 'alembic.ini'))
    command.upgrade(config, 'head')
    command.check(config)
    command.downgrade(config, '20260924_01')
    command.upgrade(config, 'head')
    command.check(config)


def tearDownModule():
    if _original_url is None:
        os.environ.pop('DATABASE_URL', None)
    else:
        os.environ['DATABASE_URL'] = _original_url
    get_settings.cache_clear()


class WorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(_test_url, poolclass=NullPool)
        self.connection = await self.engine.connect()
        self.transaction = await self.connection.begin()
        self.session = AsyncSession(bind=self.connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
        self.workspaces = WorkspaceRepository(self.session)
        self.members = WorkspaceMemberRepository(self.session)
        self.invitations = WorkspaceInvitationRepository(self.session)
        self.users = [User(full_name='Workspace fixture', email=f'{uuid4()}@example.com', password_hash='unused') for _ in range(3)]
        self.session.add_all(self.users)
        await self.session.flush()
        self.workspace = await self.workspaces.create(name='Foundation')
        self.owner = await self.members.create(workspace_id=self.workspace.id, user_id=self.users[0].id, role=WorkspaceRole.OWNER)

    async def asyncTearDown(self):
        await self.session.close()
        await self.transaction.rollback()
        await self.connection.close()
        await self.engine.dispose()

    async def rejected(self, sql, params):
        with self.assertRaises(IntegrityError):
            async with self.session.begin_nested():
                await self.session.execute(text(sql), params)

    async def test_database_constraints(self):
        sql = 'INSERT INTO workspace_members (id, workspace_id, user_id, role) VALUES (:id, :workspace, :user, :role)'
        for workspace, user, role in [
            (self.workspace.id, self.users[0].id, 'MEMBER'),
            (self.workspace.id, self.users[1].id, 'OWNER'),
            (self.workspace.id, self.users[1].id, 'OTHER'),
            (uuid4(), self.users[1].id, 'MEMBER'),
            (self.workspace.id, uuid4(), 'MEMBER'),
        ]:
            await self.rejected(sql, dict(id=uuid4(), workspace=workspace, user=user, role=role))
        invitation = await self.invitations.create(workspace_id=self.workspace.id, created_by_user_id=self.users[0].id, token_hash=hashlib.sha256(b'test-code').hexdigest())
        sql = 'INSERT INTO workspace_invitations (id, workspace_id, created_by_user_id, invitee_user_id, token_hash, status) VALUES (:id, :workspace, :creator, :invitee, :hash, :status)'
        for overrides in [dict(hash=invitation.token_hash), dict(status='OTHER'), dict(workspace=uuid4()), dict(creator=uuid4()), dict(invitee=uuid4())]:
            params = dict(id=uuid4(), workspace=self.workspace.id, creator=self.users[0].id, invitee=None, hash=hashlib.sha256(uuid4().bytes).hexdigest(), status='PENDING')
            params.update(overrides)
            await self.rejected(sql, params)

    async def test_membership_and_owner_protection(self):
        wid, uid = self.workspace.id, self.users[1].id
        member = await self.members.create(workspace_id=wid, user_id=uid)
        self.assertEqual(member.role, WorkspaceRole.MEMBER)
        self.assertTrue(await self.members.check_membership(wid, uid))
        self.assertEqual((await self.members.get_membership(wid, uid, for_update=True)).id, member.id)
        self.assertEqual(len(await self.members.list_members(wid)), 2)
        self.assertEqual((await self.members.update_role(wid, uid, role=WorkspaceRole.ADMIN)).role, WorkspaceRole.ADMIN)
        self.assertEqual((await self.members.update_role(wid, uid, role=WorkspaceRole.MEMBER)).role, WorkspaceRole.MEMBER)
        with self.assertRaises(ValueError):
            await self.members.update_role(wid, uid, role=WorkspaceRole.OWNER)
        self.assertIsNone(await self.members.update_role(wid, self.users[0].id, role=WorkspaceRole.ADMIN))
        self.assertFalse(await self.members.remove(wid, self.users[0].id))
        self.assertTrue(await self.members.remove(wid, uid))
        self.assertFalse(await self.members.check_membership(wid, uid))

    async def test_workspace_soft_delete(self):
        workspace = await self.workspaces.update(self.workspace, name='Updated', description='Description')
        self.assertEqual(workspace.name, 'Updated')
        self.assertEqual(workspace.description, 'Description')
        self.assertEqual((await self.workspaces.get_by_id(workspace.id, for_update=True)).id, workspace.id)
        self.assertIn(workspace, await self.workspaces.list_active())
        await self.workspaces.soft_delete(workspace, now=datetime.now(UTC))
        self.assertIsNone(await self.workspaces.get_by_id(workspace.id))
        self.assertNotIn(workspace, await self.workspaces.list_active())
        self.assertIsNotNone(await self.workspaces.get_by_id(workspace.id, active_only=False))
        self.assertTrue(await self.members.check_membership(workspace.id, self.users[0].id))

    async def test_invitations_and_relationships(self):
        now = datetime.now(UTC)
        direct = await self.invitations.create(workspace_id=self.workspace.id, created_by_user_id=self.users[0].id, invitee_user_id=self.users[1].id, token_hash=hashlib.sha256(b'direct').hexdigest(), expires_at=now)
        link = await self.invitations.create(workspace_id=self.workspace.id, created_by_user_id=self.users[0].id, token_hash=hashlib.sha256(b'link').hexdigest())
        self.assertTrue(direct.is_expired(now))
        self.assertFalse(direct.is_expired(now - timedelta(seconds=1)))
        self.assertFalse(link.is_expired(now))
        self.assertIsNone(link.expires_at)
        self.assertEqual(link.status, InvitationStatus.PENDING)
        self.assertEqual((await self.invitations.get_by_id(direct.id, for_update=True)).id, direct.id)
        self.assertEqual((await self.invitations.get_by_token_hash(link.token_hash, for_update=True)).id, link.id)
        self.assertIsNone(await self.invitations.get_by_token_hash('link'))
        for status in InvitationStatus:
            self.assertEqual((await self.invitations.update_status(direct, status=status)).status, status)
        self.session.expire_all()
        workspace = await self.session.scalar(select(Workspace).options(
            selectinload(Workspace.members).selectinload(WorkspaceMember.user),
            selectinload(Workspace.members).selectinload(WorkspaceMember.workspace),
            selectinload(Workspace.invitations).selectinload(WorkspaceInvitation.created_by),
            selectinload(Workspace.invitations).selectinload(WorkspaceInvitation.invitee),
            selectinload(Workspace.invitations).selectinload(WorkspaceInvitation.workspace),
        ))
        self.assertEqual(workspace.members[0].user.id, self.users[0].id)
        self.assertIs(workspace.members[0].workspace, workspace)
        self.assertEqual(len(workspace.invitations), 2)
        for invitation in workspace.invitations:
            self.assertIs(invitation.workspace, workspace)
            self.assertEqual(invitation.created_by.id, self.users[0].id)
            self.assertEqual(invitation.invitee.id if invitation.invitee else None, invitation.invitee_user_id)

    async def test_schema(self):
        def schema(conn):
            inspector = inspect(conn)
            return {name: (inspector.get_columns(name), inspector.get_pk_constraint(name), inspector.get_foreign_keys(name)) for name in ('workspaces', 'workspace_members', 'workspace_invitations')}
        info = await self.connection.run_sync(schema)
        for name, (columns, pk, fks) in info.items():
            self.assertEqual(pk['constrained_columns'], ['id'])
            for column in columns:
                if column['name'].endswith('_at'):
                    self.assertTrue(column['type'].timezone)
            self.assertEqual(len(fks), {'workspaces': 0, 'workspace_members': 2, 'workspace_invitations': 3}[name])
        self.assertNotIn('token', {c['name'] for c in info['workspace_invitations'][0]})

    async def test_backend_startup(self):
        from app.main import app
        async with app.router.lifespan_context(app):
            self.assertIsNotNone(app.openapi())
