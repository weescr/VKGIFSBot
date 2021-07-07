"""
	VKGIFSBot Inline Telegram bot that receives GIF images from VK
	yepIwt, 2021
"""
import os
import hashlib
from aiogram import Bot, Dispatcher, executor, types
from vkwave.api import API
from vkwave.client import AIOHTTPClient

import db
from urllib.parse import parse_qs

GREATING = "Привет, этот бот поможет тебе отправлять GIF-изображения из ВКонтакте в Телеграме, войди по кнопке ниже и отправь мне то, что получишь в адресной строке."
AUTH_URL = "https://oauth.vk.com/authorize?client_id=7894722&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=docs,offline&response_type=token&v=5.52"
PARANOID_URL = "https://github.com/yepIwt/VKGIFSBot#vk-gifs-bot"

TOKEN = os.getenv("TELEGRAM_API_TOKEN")

class VKGIFSBot(object):

	def __init__(self, tg_token: str):
		self.APIS = {}
		self.OFFSETS = {}
		self.ALL_GIFS = {}

		self.bot = Bot(token = tg_token)

	def is_it_gif(self, filename: str):
		try:
			ext = title[-3:]
		except Exception:
			return False
		else:
			if ext == 'gif':
				return True
			return False

	def create_query_item(result_id: int, gif_url: str):
		new_item = types.InlineQueryResultGif(
			id=result_id,
			gif_url = gif_url,
			thumb_url = gif_url,
			gif_width = 100,
			gif_height = 100,
		)
		return new_item

	async def get_gifs_from_vk(self, telegram_user_id: int):
		vk_api_result = await self.APIS.get(str(telegram_user_id)).docs.get()
		for file in vk_api_result.response.items:
			if self.is_it_gif(file.title):
				item = create_item(
					result_id = hashlib.md5(str(file.id).encode()).hexdigest(),
					gif_url = file.url,
				)
				self.ALL_GIFS[str(telegram_user_id)].append(item)

	def get_vk_api(self, vk_token: str):
		api_session = API(tokens=vk_token, clients=AIOHTTPClient())
		api = api_session.get_context()
		return api

	def return_gifs_with_offset(self, user_id: int, offset: str):
		user_gifs = self.ALL_GIFS[str(user_id)]

		if offset == "":
			self.OFFSETS[str(user_id)] += 1
			return user_gifs[:50]
		else:
			user_offset = self.OFFSETS[f'{user_id}']
			if user_offset == 0:
				return [] #  гифки пользователя кончились
			else:
				max_user_offsets = len(user_gifs) // 50 # питон всегда округляет в меньшую сторону

				gif_offset2 = user_offset * 50
				gif_offset1 = gif_offset2 - 50

				result = user_gifs[gif_offset1:gif_offset2]

				if user_gifs[gif_offset2:]:
					self.OFFSETS[f"{user_id}"] += 1
				else:
					self.OFFSETS[f'{user_id}'] = 0

				return result

	async def await_vk_token(self, message: types.Message):
		user_id = message.from_user.id

		parsed_url = parse_qs(message.text)
		vk_token = parsed_url.get("https://oauth.vk.com/blank.html#access_token")

		if not vk_token:
			await message.answer("Нет, это не сработает")
			return
		else:
			api = self.get_vk_api(vk_token)

		try:
			await api.docs.get()
		except:
			await message.answer("Неправильный токен")
		else:
			await message.answer("Да, это сработает")
			db.add(f"{user_id}", vk_token[0])
			self.APIS.setdefault(f"{user_id}", api)
			self.OFFSETS.setdefault(f"{user_id}", 1)

	async def send_welcome(self, message: types.Message):
		user_id = message.from_user.id

		if not db.get_vk_token_by_telegram_id(user_id):
			keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
			keyboard_markup.add(
				types.InlineKeyboardButton('Авторизоваться через ВКонтакте', url = AUTH_URL),
				types.InlineKeyboardButton('Я боюсь вводить токен', url = PARANOID_URL)
			)
			await message.reply(GREATING,  reply_markup=keyboard_markup)
		else:
			await message.reply("Вы уже авторизованы!")

	async def inline_process(self, inline_query: types.InlineQuery):
		user_id = inline_query.from_user.id

		if inline_query.query != "":
			pass # gifs = self.users_search_gifs()
		else:
			if not self.APIS.get(str(user_id)): # если сервер перезапускался, то апи нет
				player_token = db.get_vk_token_by_telegram_id(user_id)

				if player_token:
					self.APIS.setdefault(str(user_id), self.get_vk_api(player_token))
					self.OFFSETS.setdefault(str(user_id), 1)
				else:
					await self.bot.answer_inline_query(
						inline_query.id,
						switch_pm_text = 'Авторизуйтесь чтобы использовать бота',
						switch_pm_parameter = "need_authorize",
						results=[],
						cache_time=1
					)
					return # не показываем инлайн

			self.ALL_GIFS.setdefault(str(user_id),[])
			self.ALL_GIFS[str(user_id)] = [] # добавить кнопку "обновить gif"

			if inline_query.offset == "": # запуск инлайна
				self.OFFSETS[str(user_id)] = 1

			if not self.ALL_GIFS[str(user_id)]:
				await self.get_gifs_from_vk(user_id)

			await self.bot.answer_inline_query(
				inline_query.id,
				is_personal = True,
				next_offset = "+",
				results = self.return_gifs_with_offset(user_id, inline_query.offset),
				cache_time=1
			)

	def start(self):
		dp = Dispatcher(self.bot)
		dp.register_message_handler(self.send_welcome, commands = ['start'])
		dp.register_message_handler(self.await_vk_token, content_types = ['any'])
		dp.register_inline_handler(self.inline_process)
		executor.start_polling(dp, skip_updates = True)

if __name__ == '__main__':
	b = VKGIFSBot(TOKEN)
	b.start()