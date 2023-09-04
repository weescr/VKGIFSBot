import uuid

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import backendtools
import vktools
from config import settings

GIF_MAX_SIZE_MB = 20


class GifSerializer:
    def __init__(self):
        pass

    def get_telegram_answer(self, gifs_from_vk: list) -> list:
        result = []
        for item in gifs_from_vk:
            if (item.size / 1024 / 1024) < GIF_MAX_SIZE_MB:
                result.append(
                    self.create_query_item(result_id=uuid.uuid4().hex, gif_url=item.url)
                )
        return result

    def create_query_item(
        self, result_id: str, gif_url: str
    ) -> types.InlineQueryResultGif:
        new_item = types.InlineQueryResultGif(
            id=result_id,
            gif_url=gif_url,
            thumb_url=gif_url,
            gif_width=100,
            gif_height=100,
        )
        return new_item


class VKGIFSBot:

    bot = None

    def __init__(self, telegram_bot_token: str):
        self.bot = Bot(token=telegram_bot_token)
        self.backend = backendtools.Requester(
            client_token=settings.BACKEND_CLIENT_TOKEN
        )
        self.APIs = {}

    async def start_button(self, message: types.Message):

        user_id = message.from_user.id

        result = await self.backend.command_start(user_id)
        if result:
            await message.answer("Вы уже залогинены")
        else:
            await message.reply(
                "Почему ты ей не сказал?",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        "Вход", url=self.backend.get_auth_url(telegram_id=user_id)
                    ),
                    InlineKeyboardButton("Я вошел", callback_data="check"),
                ),
            )

    async def auth_callback_query(self, callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id

        vk_token = await self.backend.command_login(telegram_id=user_id)
        if not vk_token:
            await callback_query.answer("Не залогинен")
        else:
            await self.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
            )
            await self.bot.send_message(
                chat_id=callback_query.message.chat.id, text="Good!"
            )

    async def inline_process(self, inline_query: types.InlineQuery):
        user_id = inline_query.from_user.id
        current_api: vktools.VkTools = self.APIs.get(str(user_id))

        if not current_api:
            vk_token = await self.backend.command_login(telegram_id=user_id)
            if not vk_token:
                await self.bot.answer_inline_query(
                    inline_query.id,
                    switch_pm_text="Авторизуйтесь чтобы использовать бота",
                    switch_pm_parameter="need_authorize",
                    results=[],
                    cache_time=1,
                )
            else:
                current_api = vktools.VkTools(vk_token=vk_token)
                self.APIs.setdefault(str(user_id), current_api)

        if inline_query.query != "":
            vk_answer = await current_api.search_vk_gifs(
                q=inline_query.query, offset=inline_query.offset
            )
        else:
            vk_answer = await current_api.get_vk_gifs(offset=inline_query.offset)

        offset = int(inline_query.offset) if inline_query.offset else 0

        await self.bot.answer_inline_query(
            inline_query.id,
            is_personal=True,
            next_offset=offset + len(vk_answer),
            results=GifSerializer().get_telegram_answer(gifs_from_vk=vk_answer),
            cache_time=1,
        )

    def start(self):
        dp = Dispatcher(self.bot)
        dp.register_message_handler(self.start_button, commands=["start"])
        dp.register_callback_query_handler(self.auth_callback_query)
        dp.register_inline_handler(self.inline_process)
        executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    b = VKGIFSBot(telegram_bot_token=settings.TELEGRAM_BOT_TOKEN)
    b.start()
