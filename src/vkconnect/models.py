import uuid
from enum import StrEnum
from typing import Self

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TEXT, UUID, VARCHAR, INTEGER

from src.db.connection import db_session
from src.models import BaseDatetimeModel, BaseModel


class VKData(BaseModel):
    __tablename__ = "vk_data"

    user_id = sa.Column(
        "user_id", INTEGER, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = sa.Column("vk_token", TEXT, nullable=True)

    @classmethod
    async def create(cls, user_id: uuid.UUID, token: str) -> uuid.UUID:
        query = (
            sa.Insert(VKData)
            .values(
                user_id=user_id,
                token=token,
            )
            .returning(VKData.id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @classmethod
    async def get_by_user_id(cls, user_id: uuid.UUID) -> Self:
        query = (
            sa.Select(VKData)
            .where(cls.user_id == user_id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()






