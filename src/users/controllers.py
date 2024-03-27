from typing import Union

from fastapi import APIRouter, Body, Depends, status

from src.users.models import User


from src.db.connection import Transaction
from .views import TelegramUserRequestView, UserView, VKToken, VKAuthLink, UsersCounter
from ..config import settings

users_router = APIRouter(tags=["User"])


@users_router.get("/users/{hashed_telegram_id}")
async def get_user(hashed_telegram_id: str) -> Union[VKToken, VKAuthLink]:

    async with Transaction():

        user = await User.get_by_hashed_telegram_id(hashed_telegram_id=hashed_telegram_id)

    if user:
        return VKToken(vktoken=user.vktoken)
    else:
        return VKAuthLink(vk_auth_link=settings.VK_AUTH_LINK(hashed_telegram_id=hashed_telegram_id))


@users_router.get("/users/")
async def get_user() -> UsersCounter:

    async with Transaction():

        counter = await User.get_counter()

    return UsersCounter(users_count=counter)