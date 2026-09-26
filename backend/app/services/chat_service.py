from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import PurePath
from tempfile import SpooledTemporaryFile
from typing import BinaryIO
from uuid import UUID
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models.enums import ChannelType
from app.realtime.connection_manager import ChannelConnectionManager, channel_connections
from app.repositories.channel_repository import ChannelRepository
from app.repositories.chat_attachment_repository import ChatAttachmentRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.message_reaction_repository import MessageReactionRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.chat import (
    AttachmentResponse, MessageRequest, MessageResponse, MessageSenderResponse, ReactionSummaryResponse,
)
from app.services.auth_service import AuthService, Principal
from app.services.storage_service import StorageService, get_storage_service


ALLOWED_ATTACHMENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".txt": {"text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


class ChatService:
    def __init__(
        self, db: AsyncSession, manager: ChannelConnectionManager = channel_connections,
        storage: StorageService | None = None,
    ) -> None:
        self.db = db
        self.manager = manager
        self.channels = ChannelRepository(db)
        self.messages = ChatMessageRepository(db)
        self.attachments = ChatAttachmentRepository(db)
        self.reactions = MessageReactionRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.members = WorkspaceMemberRepository(db)
        self.storage = storage

    @asynccontextmanager
    async def transaction(self, principal: Principal):
        async with self.db.begin():
            await AuthService(self.db).load_principal(principal.user.id, principal.session.id)
            yield

    async def channel_access(self, channel_id: UUID, user_id: UUID, *, for_update: bool = False):
        channel = await self.channels.get_by_id(channel_id, for_update=for_update)
        if channel is None:
            raise AppError(404, "CHANNEL_NOT_FOUND", "Không tìm thấy Channel")
        workspace = await self.workspaces.get_by_id(channel.workspace_id, for_update=True)
        if workspace is None:
            raise AppError(404, "CHANNEL_NOT_FOUND", "Không tìm thấy Channel")
        if await self.members.get_membership(workspace.id, user_id) is None:
            raise AppError(403, "CHANNEL_ACCESS_DENIED", "Bạn không có quyền truy cập Channel")
        if channel.type != ChannelType.TEXT:
            raise AppError(422, "CHANNEL_NOT_TEXT", "Channel này không hỗ trợ Chat")
        return channel

    async def active_message(self, message_id: UUID, user_id: UUID, *, for_update: bool = False):
        candidate = await self.messages.get_by_id(message_id)
        if candidate is None:
            raise AppError(404, "MESSAGE_NOT_FOUND", "Không tìm thấy tin nhắn")
        channel = await self.channel_access(candidate.channel_id, user_id, for_update=for_update)
        message = await self.messages.get_by_id(message_id, for_update=for_update)
        if message is None or message.channel_id != channel.id:
            raise AppError(404, "MESSAGE_NOT_FOUND", "Không tìm thấy tin nhắn")
        if message.deleted_at is not None:
            raise AppError(409, "MESSAGE_ALREADY_DELETED", "Tin nhắn đã bị xóa")
        return channel, message

    @staticmethod
    def message_response(message) -> MessageResponse:
        grouped: dict[str, list] = {}
        for reaction in message.reactions:
            grouped.setdefault(reaction.emoji, []).append(reaction)
        summaries = [
            ReactionSummaryResponse(emoji=emoji, count=len(reactions))
            for emoji, reactions in sorted(grouped.items())
        ]
        attachments = [
            AttachmentResponse(
                id=attachment.id, original_filename=attachment.original_filename,
                content_type=attachment.content_type, size_bytes=attachment.size_bytes,
            )
            for attachment in message.attachments
        ]
        return MessageResponse(
            id=message.id, channel_id=message.channel_id, content=message.content,
            sender=MessageSenderResponse(id=message.sender.id, full_name=message.sender.full_name),
            created_at=message.created_at, edited_at=message.edited_at, reactions=summaries,
            attachments=attachments,
        )

    async def history(self, principal: Principal, channel_id: UUID, *, limit: int, before_message_id: UUID | None):
        async with self.transaction(principal):
            await self.channel_access(channel_id, principal.user.id)
            before = None
            if before_message_id is not None:
                before = await self.messages.get_by_id(before_message_id)
                if before is None or before.channel_id != channel_id or before.deleted_at is not None:
                    raise AppError(404, "MESSAGE_NOT_FOUND", "Không tìm thấy tin nhắn mốc")
            messages = await self.messages.list_history(channel_id, limit=limit, before=before)
            result = [self.message_response(message) for message in messages]
        return result

    async def send(self, principal: Principal, channel_id: UUID, request: MessageRequest):
        content = self.valid_content(request.content)
        async with self.transaction(principal):
            channel = await self.channel_access(channel_id, principal.user.id, for_update=True)
            message = await self.messages.create(
                channel_id=channel.id, sender_user_id=principal.user.id, content=content,
            )
            message = await self.messages.get_with_details(message.id)
            result = self.message_response(message)
        await self.manager.broadcast(channel_id, {"type": "message.created", "data": result.model_dump(mode="json")})
        return result

    async def send_attachment(
        self, principal: Principal, channel_id: UUID, file: UploadFile, content: str | None,
    ) -> MessageResponse:
        storage = self.storage or get_storage_service()
        storage_key = ""
        uploaded = False
        body: BinaryIO | None = None
        try:
            async with self.transaction(principal):
                channel = await self.channel_access(channel_id, principal.user.id, for_update=True)
                content = self.valid_optional_content(content)
                original_filename, extension, content_type = self.valid_attachment_metadata(file)
                body, size = await self.read_limited(file)
                storage_key = f"chat/{uuid4().hex}{extension}"
                try:
                    await storage.upload(storage_key, body, content_type)
                    uploaded = True
                except Exception as exc:
                    raise AppError(503, "ATTACHMENT_UPLOAD_FAILED", "Không thể tải tệp lên") from exc
                message = await self.messages.create(
                    channel_id=channel.id, sender_user_id=principal.user.id, content=content,
                )
                await self.attachments.create(
                    message_id=message.id, storage_key=storage_key,
                    original_filename=original_filename, content_type=content_type, size_bytes=size,
                )
                message = await self.messages.get_with_details(message.id)
                result = self.message_response(message)
        except Exception:
            if uploaded:
                try:
                    await storage.delete(storage_key)
                except Exception:
                    pass
            raise
        finally:
            if body is not None:
                body.close()
            await file.close()
        try:
            await self.manager.broadcast(
                channel_id, {"type": "message.created", "data": result.model_dump(mode="json")},
            )
        except Exception:
            pass
        return result

    async def attachment_download_url(self, principal: Principal, attachment_id: UUID) -> str:
        async with self.transaction(principal):
            attachment = await self.attachments.get_with_message(attachment_id)
            if attachment is None or attachment.message.deleted_at is not None:
                raise AppError(404, "ATTACHMENT_NOT_FOUND", "Không tìm thấy tệp đính kèm")
            try:
                await self.channel_access(attachment.message.channel_id, principal.user.id)
            except AppError as exc:
                if exc.code == "CHANNEL_ACCESS_DENIED":
                    raise AppError(403, "ATTACHMENT_ACCESS_DENIED", "Bạn không có quyền tải tệp") from exc
                raise
            storage_key = attachment.storage_key
            filename = attachment.original_filename
        try:
            return await (self.storage or get_storage_service()).temporary_download_url(storage_key, filename)
        except Exception as exc:
            raise AppError(503, "ATTACHMENT_DOWNLOAD_FAILED", "Không thể tạo liên kết tải tệp") from exc

    async def edit(self, principal: Principal, message_id: UUID, request: MessageRequest):
        content = self.valid_content(request.content)
        async with self.transaction(principal):
            channel, message = await self.active_message(message_id, principal.user.id, for_update=True)
            if message.sender_user_id != principal.user.id:
                raise AppError(403, "MESSAGE_PERMISSION_DENIED", "Bạn không có quyền sửa tin nhắn")
            await self.messages.update_content(message, content=content, edited_at=datetime.now(UTC))
            message = await self.messages.get_with_details(message.id)
            result = self.message_response(message)
            channel_id = channel.id
        await self.manager.broadcast(channel_id, {"type": "message.updated", "data": result.model_dump(mode="json")})
        return result

    async def delete(self, principal: Principal, message_id: UUID):
        async with self.transaction(principal):
            channel, message = await self.active_message(message_id, principal.user.id, for_update=True)
            if message.sender_user_id != principal.user.id:
                raise AppError(403, "MESSAGE_PERMISSION_DENIED", "Bạn không có quyền xóa tin nhắn")
            await self.messages.mark_deleted(message, deleted_at=datetime.now(UTC))
            channel_id = channel.id
        await self.manager.broadcast(channel_id, {"type": "message.deleted", "data": {"message_id": str(message_id)}})

    async def add_reaction(self, principal: Principal, message_id: UUID, emoji: str):
        emoji = self.valid_emoji(emoji)
        async with self.transaction(principal):
            channel, message = await self.active_message(message_id, principal.user.id, for_update=True)
            changed = await self.reactions.add_if_absent(message_id=message.id, user_id=principal.user.id, emoji=emoji)
            message = await self.messages.get_with_details(message.id)
            result = self.message_response(message).reactions
            channel_id = channel.id
        if changed:
            await self.manager.broadcast(channel_id, {
                "type": "reaction.updated",
                "data": {"message_id": str(message_id), "reactions": [item.model_dump(mode="json") for item in result]},
            })
        return result

    async def remove_reaction(self, principal: Principal, message_id: UUID, emoji: str):
        emoji = self.valid_emoji(emoji)
        async with self.transaction(principal):
            channel, message = await self.active_message(message_id, principal.user.id, for_update=True)
            reaction = await self.reactions.find_exact(message.id, principal.user.id, emoji)
            changed = reaction is not None
            if reaction is not None:
                await self.reactions.delete(reaction)
            message = await self.messages.get_with_details(message.id)
            result = self.message_response(message).reactions
            channel_id = channel.id
        if changed:
            await self.manager.broadcast(channel_id, {
                "type": "reaction.updated",
                "data": {"message_id": str(message_id), "reactions": [item.model_dump(mode="json") for item in result]},
            })
        return result

    async def authorize_subscription(self, principal: Principal, channel_id: UUID) -> None:
        async with self.transaction(principal):
            await self.channel_access(channel_id, principal.user.id)

    @staticmethod
    def valid_emoji(emoji: str) -> str:
        value = emoji.strip()
        if not value or len(value) > 32:
            raise AppError(422, "INVALID_REACTION_EMOJI", "Cảm xúc không hợp lệ")
        return value

    @staticmethod
    def valid_content(content: str | None) -> str:
        if content is None or not content.strip():
            raise AppError(422, "INVALID_MESSAGE_CONTENT", "Nội dung tin nhắn không hợp lệ")
        return content.strip()

    @staticmethod
    def valid_optional_content(content: str | None) -> str | None:
        if content is None:
            return None
        if not content.strip():
            raise AppError(422, "INVALID_MESSAGE_CONTENT", "Nội dung tin nhắn không hợp lệ")
        return content.strip()

    @staticmethod
    def valid_attachment_metadata(file: UploadFile) -> tuple[str, str, str]:
        raw_filename = file.filename or ""
        filename = PurePath(raw_filename.replace("\\", "/")).name.strip()
        if (
            not filename or filename in {".", ".."} or len(filename) > 255
            or any(ord(character) < 32 for character in filename)
        ):
            raise AppError(422, "ATTACHMENT_TYPE_NOT_ALLOWED", "Tên tệp không hợp lệ")
        extension = PurePath(filename).suffix.lower()
        content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
        if extension not in ALLOWED_ATTACHMENT_TYPES or content_type not in ALLOWED_ATTACHMENT_TYPES[extension]:
            raise AppError(422, "ATTACHMENT_TYPE_NOT_ALLOWED", "Loại tệp không được hỗ trợ")
        return filename, extension, content_type

    @staticmethod
    async def read_limited(file: UploadFile) -> tuple[BinaryIO, int]:
        maximum = get_settings().attachment_max_size_bytes
        body = SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
        size = 0
        try:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > maximum:
                    raise AppError(413, "ATTACHMENT_TOO_LARGE", "Tệp vượt quá dung lượng cho phép")
                body.write(chunk)
            if size == 0:
                raise AppError(422, "ATTACHMENT_EMPTY", "Tệp không được để trống")
            body.seek(0)
            return body, size
        except Exception:
            body.close()
            await file.close()
            raise
