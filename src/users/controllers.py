from fastapi import APIRouter, Body, Depends, status

from src.users.models import User


from src.db.connection import Transaction
from src.exceptions import (
    UserAlreadyRegistered,
)
from .views import TelegramUserRequestView, UserView

auth_router = APIRouter(tags=["User"])


@auth_router.post("/users/create")
async def new_user(body: TelegramUserRequestView = Body(...)) -> UserView:

    async with Transaction():

        user = await User.get_by_telegram_id(body.telegram_id)

        if user:
            raise UserAlreadyRegistered

        user_id = await User.create(
            telegram_id=body.telegram_id,
            username=body.username,
            picture_url=body.picture_url
        )

    return UserView(user_id=user_id)
