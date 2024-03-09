import uuid
from enum import StrEnum
from typing import Self

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TEXT, UUID, VARCHAR, INTEGER
from pydantic import AnyUrl
from src.db.connection import db_session
from src.models import BaseDatetimeModel, BaseModel


class User(BaseModel):
    __tablename__ = "users"

    class UserStatus(StrEnum):
        GOT_TOKEN = "got_token"
        PRESSED_START = "pressed_start"

    telegram_id = sa.Column("telegram_id", INTEGER, nullable=False)
    status = sa.Column("user_status", VARCHAR(15), nullable=False, default=UserStatus.PRESSED_START)
    username = sa.Column("telegram_username", VARCHAR(33), nullable=True)
    picture_url = sa.Column("telegram_picture_url",TEXT, nullable=True)

    @classmethod
    async def create(cls, telegram_id: int, username: str, picture_url: AnyUrl) -> uuid.UUID:
        query = (
            sa.Insert(User)
            .values(
                telegram_id=telegram_id,
                username=username,
                picture_url=picture_url,
                status=User.UserStatus.PRESSED_START
            )
            .returning(User.id)
        )
        result = await db_session.get().execute(query)
        return result.scalars().first()

    @classmethod
    async def update(cls, user_id: uuid.UUID, status: UserStatus):
        query = (
            sa.Update(User)
            .where(cls.id == user_id)
            .values(status=status)
        )
        await db_session.get().execute(query)
