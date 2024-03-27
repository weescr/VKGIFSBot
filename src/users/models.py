import uuid
from enum import StrEnum
from typing import Self

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import TEXT, UUID, VARCHAR, INTEGER
from pydantic import AnyUrl
from src.db.connection import db_session
from src.models import BaseDatetimeModel, BaseModel


class User(BaseModel):
    __tablename__ = "users"  # noqa

    # TODO: Get more data from the user to make the login page more beautiful
    hashed_telegram_id = sa.Column("hashed_tg_id", TEXT, nullable=False)
    vktoken = sa.Column("vktoken", TEXT, nullable=False)

    @classmethod
    async def create(cls, hashed_tg_id: str) -> uuid.UUID:
        query = (
            sa.Insert(User)
            .values(
                hashed_tg_id=hashed_tg_id,
            )
            .returning(User.id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @classmethod
    async def get_by_hashed_telegram_id(cls, hashed_telegram_id: str):
        query = (
            sa.Select(User)
            .where(User.hashed_telegram_id == hashed_telegram_id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @classmethod
    async def set_vk_token(cls, user_id: uuid.UUID, vktoken: str):
        query = (
            sa.Update(User)
            .where(cls.id == user_id)
            .values(vktoken=vktoken)
        )
        await db_session.get().execute(query)

    @classmethod
    async def get_counter(cls):
        query = select(
            sa.func.count()
        ).select_from(User)
        result = await db_session.get().execute(query)
        return result.scalar_one()