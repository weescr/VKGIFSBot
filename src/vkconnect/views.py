from enum import StrEnum
from typing import List
from uuid import UUID, uuid4

from pydantic import AnyUrl, EmailStr, field_validator

from src.protocol import BaseModel, BaseRequestModel


class VKDataRequestView(BaseRequestModel):
    user_id: UUID


class VKDataView(BaseModel):
    user_id: UUID
    token: UUID
