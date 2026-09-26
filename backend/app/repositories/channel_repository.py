from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.enums import ChannelType


class ChannelRepository:
    """Query/flush only; authorization and default-channel protection belong to services."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: UUID, name: str, type: ChannelType, description: str | None = None, is_default: bool = False) -> Channel:
        channel = Channel(workspace_id=workspace_id, name=name, description=description, type=type, is_default=is_default)
        self.session.add(channel)
        await self.session.flush()
        await self.session.refresh(channel)
        return channel

    async def get_by_id(self, channel_id: UUID, *, for_update: bool = False) -> Channel | None:
        statement = select(Channel).where(Channel.id == channel_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def list_by_workspace(self, workspace_id: UUID) -> list[Channel]:
        return list(await self.session.scalars(
            select(Channel).where(Channel.workspace_id == workspace_id).order_by(Channel.created_at, Channel.id)
        ))

    async def update(self, channel: Channel, *, name: str, description: str | None, type: ChannelType | None = None) -> Channel:
        channel.name = name
        channel.description = description
        if type is not None:
            channel.type = type
        await self.session.flush()
        await self.session.refresh(channel)
        return channel

    async def delete(self, channel: Channel) -> None:
        await self.session.execute(delete(Channel).where(Channel.id == channel.id))
        await self.session.flush()

    async def get_default(self, workspace_id: UUID) -> Channel | None:
        return await self.session.scalar(select(Channel).where(Channel.workspace_id == workspace_id, Channel.is_default.is_(True)))

    async def name_exists(self, workspace_id: UUID, name: str, *, exclude_channel_id: UUID | None = None) -> bool:
        filters = [Channel.workspace_id == workspace_id, Channel.name == name]
        if exclude_channel_id is not None:
            filters.append(Channel.id != exclude_channel_id)
        return bool(await self.session.scalar(select(exists().where(*filters))))
