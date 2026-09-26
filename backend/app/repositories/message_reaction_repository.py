from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message_reaction import MessageReaction


class MessageReactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, message_id: UUID, user_id: UUID, emoji: str) -> MessageReaction:
        reaction = MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self.session.add(reaction)
        await self.session.flush()
        await self.session.refresh(reaction)
        return reaction

    async def add_if_absent(self, *, message_id: UUID, user_id: UUID, emoji: str) -> bool:
        reaction_id = await self.session.scalar(
            insert(MessageReaction)
            .values(message_id=message_id, user_id=user_id, emoji=emoji)
            .on_conflict_do_nothing(constraint="uq_message_reactions_message_user_emoji")
            .returning(MessageReaction.id)
        )
        return reaction_id is not None

    async def find_exact(self, message_id: UUID, user_id: UUID, emoji: str) -> MessageReaction | None:
        return await self.session.scalar(select(MessageReaction).where(
            MessageReaction.message_id == message_id, MessageReaction.user_id == user_id, MessageReaction.emoji == emoji,
        ))

    async def delete(self, reaction: MessageReaction) -> None:
        await self.session.execute(delete(MessageReaction).where(MessageReaction.id == reaction.id))
        await self.session.flush()

    async def list_by_message(self, message_id: UUID) -> list[MessageReaction]:
        return list(await self.session.scalars(
            select(MessageReaction).where(MessageReaction.message_id == message_id).order_by(MessageReaction.created_at, MessageReaction.id)
        ))

    async def count_by_message(self, message_id: UUID) -> int:
        return int(await self.session.scalar(
            select(func.count()).select_from(MessageReaction).where(MessageReaction.message_id == message_id)
        ) or 0)
