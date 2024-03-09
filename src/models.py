import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base
from src.db.connection import db_session

from src.exceptions import ObjectNotFoundError


class BaseModel(Base):
    __abstract__ = True

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @classmethod
    async def get(cls, value: Any):
        query = sa.select(cls).where(cls.id == value)
        try:
            result = (await db_session.get().execute(query)).scalar_one()
            return result
        except Exception as e:
            raise ObjectNotFoundError from e

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BaseDatetimeModel(BaseModel):
    __abstract__ = True

    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, onupdate=sa.func.now())
    deleted_at = sa.Column(sa.DateTime, nullable=True)