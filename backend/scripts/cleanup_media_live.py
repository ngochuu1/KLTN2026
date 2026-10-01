"""Remove only the unique Phase 4C browser fixture supplied on stdin."""
import asyncio
import json
import re
import sys

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import AuthSession, User, Workspace, WorkspaceInvitation, WorkspaceMember


async def main(data):
    marker = data["marker"]
    assert re.fullmatch(r"phase4c-[0-9a-f-]{36}", marker)
    emails = [f"{marker}-{role}@example.com" for role in ("owner", "member")]
    engine = create_async_engine(str(get_settings().database_url))
    try:
        async with async_sessionmaker(engine)() as db, db.begin():
            users = list(await db.scalars(select(User.id).where(User.email.in_(emails))))
            workspaces = list(await db.scalars(select(Workspace.id).where(Workspace.name == marker)))
            assert len(workspaces) <= 1
            await db.execute(delete(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id.in_(workspaces)))
            await db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id.in_(workspaces)))
            await db.execute(delete(Workspace).where(Workspace.id.in_(workspaces), Workspace.name == marker))
            await db.execute(delete(AuthSession).where(AuthSession.user_id.in_(users)))
            await db.execute(delete(User).where(User.id.in_(users), User.email.in_(emails)))
        print("Scoped Phase 4C fixture cleanup PASS")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main(json.load(sys.stdin)))
    except Exception as exc:
        print(type(exc).__name__)
        sys.exit(1)
