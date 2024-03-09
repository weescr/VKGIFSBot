from fastapi import APIRouter, Body, Depends, status, Path
from fastapi.responses import FileResponse
from src.vkconnect.models import VKData


from src.db.connection import Transaction
from src.exceptions import (
    UserAlreadyRegistered,
    UserNotFoundError,
    UserAlreadyHasToken
)
from .views import VKDataView, VKDataRequestView

auth_router = APIRouter(tags=["VKData"])


@auth_router.get("/vkdata/")
async def get_token(body: VKDataRequestView = Body(...)) -> VKDataView:

    async with Transaction():

        vk_data = await VKData.get_by_telegram_id(body.user_id)

        if vk_data:
            raise UserNotFoundError

    return VKDataView(user_id=vk_data.user_id, token=vk_data.token)


@auth_router.get("/vkdata/{user_id}/catch", response_class=FileResponse)
async def get_token(user_id=Path(...)):

    async with Transaction():

        vk_data = await VKData.get_by_telegram_id(user_id=user_id)

        if vk_data:
            raise UserAlreadyHasToken

    return "static/CatchVKToken.html"

