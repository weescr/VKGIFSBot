from enum import StrEnum
from typing import List
from uuid import UUID, uuid4

from pydantic import AnyUrl, EmailStr, field_validator

from src.protocol import BaseModel, BaseRequestModel


class TelegramUserRequestView(BaseRequestModel):
    telegram_id: int
    username: str
    picture_url: AnyUrl


class UserView(BaseModel):
    user_id: UUID
