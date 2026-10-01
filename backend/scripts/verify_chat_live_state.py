"""DB/storage assertions and narrowly scoped cleanup for the Phase 3E browser run.

Called with JSON on stdin by frontend/tests/chat-live.cjs. Never prints credentials,
tokens, storage keys or signed URLs. Uses the configured local development stack.
"""
import asyncio
import hashlib
import json
import re
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import AuthSession, Channel, ChatAttachment, ChatMessage, MessageReaction, User, Workspace, WorkspaceInvitation, WorkspaceMember
from app.services.storage_service import get_storage_service


async def main(data):
    marker = data["marker"]
    assert re.fullmatch(r"phase3e-[0-9a-f-]{36}", marker), "Invalid fixture marker"
    settings = get_settings()
    engine = create_async_engine(str(settings.database_url))
    storage = get_storage_service()
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            users = (await db.scalars(select(User).where(User.email.in_(data["emails"])))).all()
            assert all(user.email.startswith(marker + "-") and user.email.endswith("@example.com") for user in users)
            workspaces = (await db.scalars(select(Workspace).where(Workspace.name == marker))).all()
            assert len(workspaces) <= 1
            workspace = workspaces[0] if workspaces else None
            channels = (await db.scalars(select(Channel).where(Channel.workspace_id == workspace.id))).all() if workspace else []
            messages = (await db.scalars(select(ChatMessage).where(ChatMessage.channel_id.in_([c.id for c in channels])))).all() if channels else []
            attachments = (await db.scalars(select(ChatAttachment).where(ChatAttachment.message_id.in_([m.id for m in messages])))).all() if messages else []
            if data["action"] == "cleanup":
                for attachment in attachments:
                    await storage.delete(attachment.storage_key)
                if workspace:
                    await db.execute(delete(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id == workspace.id))
                    await db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace.id))
                    await db.execute(delete(Workspace).where(Workspace.id == workspace.id, Workspace.name == marker))
                if users:
                    await db.execute(delete(AuthSession).where(AuthSession.user_id.in_([u.id for u in users])))
                    await db.execute(delete(User).where(User.id.in_([u.id for u in users]), User.email.in_(data["emails"])))
                await db.commit()
                print(json.dumps({"cleanup": "PASS", "users": len(users), "workspaces": len(workspaces), "objects": len(attachments)}))
                return
            assert workspace and str(workspace.id) == data["workspace_id"]
            assert any(c.name == "general" and c.is_default for c in channels)
            assert any(c.name == "live-renamed" for c in channels)
            assert not any(str(c.id) == data["deleted_channel_id"] for c in channels)
            edited = next(m for m in messages if str(m.id) == data["edited_message_id"])
            assert edited.content == "Live edited persistent" and edited.edited_at is not None and edited.deleted_at is None
            removed = next(m for m in messages if str(m.id) == data["deleted_message_id"])
            assert removed.deleted_at is not None
            reactions = (await db.scalars(select(MessageReaction).where(MessageReaction.message_id == edited.id))).all()
            assert len(reactions) == 1 and reactions[0].emoji == "👍"
            attachment = next(a for a in attachments if str(a.id) == data["attachment_id"])
            assert attachment.original_filename == "phase3e-live.txt"
            head = await asyncio.to_thread(storage.client.head_object, Bucket=storage.bucket, Key=attachment.storage_key)
            assert head["ContentLength"] == attachment.size_bytes
            obj = await asyncio.to_thread(storage.client.get_object, Bucket=storage.bucket, Key=attachment.storage_key)
            try:
                digest = hashlib.sha256(obj["Body"].read()).hexdigest()
            finally:
                obj["Body"].close()
            assert digest == data["sha256"]
            anonymous = f"{settings.object_storage_endpoint.rstrip('/')}/{quote(storage.bucket)}/{quote(attachment.storage_key)}"
            try:
                with urlopen(anonymous, timeout=10):
                    raise AssertionError("Anonymous object access unexpectedly allowed")
            except HTTPError as exc:
                assert exc.code == 403
            print(json.dumps({
                "postgresql": "PASS", "revision": await db.scalar(text("SELECT version_num FROM alembic_version")),
                "postgres_version": await db.scalar(text("SHOW server_version")),
                "channel_persistence": "PASS", "message_edit_soft_delete": "PASS", "reaction_persistence": "PASS",
                "attachment_metadata": "PASS", "minio_object_and_sha256": "PASS", "anonymous_object_access": 403,
                "attachment_bytes": attachment.size_bytes, "sha256": digest,
            }))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main(json.load(sys.stdin)))
    except Exception as exc:
        # Avoid driver/client exception strings containing connection secrets.
        print(json.dumps({"result": "FAIL", "exception_type": type(exc).__name__}))
        sys.exit(1)
