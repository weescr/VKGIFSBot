#! /usr/bin/env python
# -*- coding: utf-8 -*-

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

import aiohttp
import moviepy.editor as mp
from loguru import logger

GREATING = "Привет, этот бот поможет тебе отправлять GIF-изображения из ВКонтакте в Телеграме, войди по кнопке ниже и отправь мне то, что получишь в адресной строке."
AUTH_URL = "https://oauth.vk.com/authorize?client_id=7894722&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=docs,offline&response_type=token&v=5.52"
PARANOID_URL = "https://github.com/yepIwt/VKGIFSBot#vk-gifs-bot"

TOKEN = os.getenv("TELEGRAM_API_TOKEN")

class VKGIFSBot(object):

	def __init__(self, tg_token: str):
		self.APIS = {} # Хранение объектов vkwave.api.API пользователей
		self.OFFSETS = {} # Хранение оффсетов пользователей для прокрутки Inline ответа
		self.ALL_GIFS = {} # Хранение Inline ответов для пользователя

		self.bot = Bot(token = tg_token)

	# Функция для создания Inline ответов для телеграмма
	def create_query_item(self, result_id: str, gif_url: str) -> types.InlineQueryResultGif:
		new_item = types.InlineQueryResultGif(
			id=result_id,
			gif_url = gif_url,
			thumb_url = gif_url,
			gif_width = 100,
			gif_height = 100,
		)
		return new_item

	# Функция получения ВСЕХ гифок пользователя по telegram_id
	async def get_gifs_from_vk(self, telegram_user_id: int):
		vk_api_result = await self.APIS \
			.get(str(telegram_user_id)) \
			.docs.get(type = 3)

		for file in vk_api_result.response.items:

			# Создаем ответ
			item = self.create_query_item(
				result_id = hashlib.md5(str(file.id).encode()).hexdigest(),
				gif_url = file.url,
			)
			self.ALL_GIFS[str(telegram_user_id)].append(item) # Добавляем ответ в гифки пользователя

	# Функция поиска по гифкам
	async def search_gifs_from_vk(self, telegram_user_id, text):

		# Я написал в поддержку, как ответят - перепишу
		# UPD9.1.22 Поддержке насрать

		# Получим ID пользователя с помощью первого документа
		vk_api_result = await self.APIS.get(str(telegram_user_id)).docs.get()
		owner_id = vk_api_result.response.items[0].owner_id

		# Ищем в документах пользователя q
		vk_api_result = await self.APIS.get(str(telegram_user_id)).docs.search(
			search_own = 1,
			q = text,
		)
		
		# Переберем все найденные файлы
		for file in vk_api_result.response.items:

			# Получаем только наши гифки по запросу q
			if file.ext == 'gif' and file.owner_id == owner_id:

				# Создаем inline ответ для телеграма
				item = self.create_query_item(
					result_id = hashlib.md5(str(file.id).encode()).hexdigest(),
					gif_url = file.url,
				)
				self.ALL_GIFS[str(telegram_user_id)].append(item)
		
		# Выполним поиск по всем гифкам VK

	# Функция получения VK API
	def get_vk_api(self, vk_token: str):
		api_session = API(tokens=vk_token, clients=AIOHTTPClient())
		api = api_session.get_context()
		return api

	@logger.catch
	# Функция отправки Inline ответа
	def return_gifs_with_offset(self, user_id: int, offset: str):

		# Все полученные гифки от пользователя
		user_gifs = self.ALL_GIFS[str(user_id)]

		# Если не было скролла, то вернуть первые 50 гифок
		if offset == "":
			self.OFFSETS[str(user_id)] += 1 # Обозначаем, что мы вернули первые 50 гифок
			return user_gifs[:50]
		else: # Если уже была прокрутка
			user_offset = self.OFFSETS[f'{user_id}'] # Получаем оффсет пользователя

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

	# Функиця регистрации пользователя в боте
	async def await_vk_token(self, message: types.Message):
		user_id = message.from_user.id # Получаем telegram_id
		logger.debug(f"{user_id}: send {message.text}")

		# Парсим токен
		parsed_url = parse_qs(message.text)
		vk_token = parsed_url.get("https://oauth.vk.com/blank.html#access_token")

		if not vk_token:
			logger.warning(f"{vk_token} not vk token")
			await message.answer("Нет, это не сработает")
			return
		else:
			logger.warning(f"{vk_token} is vk token")
			api = self.get_vk_api(vk_token)

		# Проверяем доступ API
		try:
			await api.docs.get()
		except:
			logger.warning(f"{vk_token} bad vk token")
			await message.answer("Неправильный токен")
		else:
			logger.warning(f"{vk_token} good vk token")
			await message.answer("Да, это сработает")
			
			# Записываем вк токен в базу данных
			db.add(f"{user_id}", vk_token[0])

			logger.info(f"{user_id}: added to base")

			# Создаем место для нового пользователя
			self.APIS.setdefault(f"{user_id}", api)
			self.OFFSETS.setdefault(f"{user_id}", 1)

	# Функция отправки инфо о бэкапе
	async def backup_info(self, msg: types.Message):
		user_id = msg.from_user.id

		self.APIS.setdefault(f"{user_id}", None)

		if not self.APIS[str(user_id)]:
			if not db.get_vk_token_by_telegram_id(user_id):
				await msg.answer("Авторизируйтесь для начала")
				return

		await msg.answer("Для бэкапа гифки в вк просто отправьте ее боту")

	@logger.catch
	# Функция бэкапа гифки в ВК
	async def backup_gif(self, msg: types.Message):
		user_id = msg.from_user.id

		logger.debug(f"{user_id}: tries to backup gifs")

		# Если пользователь не авторизирован
		if not self.APIS[str(user_id)]:
			has_token = db.get_vk_token_by_telegram_id(user_id)
			if has_token:
				self.APIS[str(user_id)] = self.get_vk_api(has_token)
			else:
				await msg.answer("Сначала авторизуйтесь")
				return

		logger.debug("Started downloading gif")

		# Переписать, когда ботом будет пользоваться больше 1 человека
		await self.bot.download_file_by_id(msg.animation.file_id,'animation.mp4')

		logger.debug("Started converting video to gif")
		clip = mp.VideoFileClip('animation.mp4')
		clip.write_gif('animation.gif',logger=None)

		logger.debug("Started uploading GIF to VK")
		vk_api_answer = await self.APIS[str(msg.from_user.id)].docs.get_upload_server()
		url_for_upload = vk_api_answer.response.upload_url
		f = open('animation.gif','rb')

		async with aiohttp.ClientSession() as session:
			async with session.post(url_for_upload, data = {'file':f}) as resp:
				json = await resp.json()
				file_obj = json['file']

		vk_api_answer = await self.APIS[str(msg.from_user.id)].docs.save(
				file = file_obj,
				title = f'{msg.from_user.first_name}_{msg.date}.gif',
				tags = '',
				return_tags = 0
		)

		logger.debug(f"Gif uploaded")

		# Очистим временные файлы
		f.close()
		os.remove('animation.gif')
		os.remove('animation.mp4')
		logger.debug(f"Files cleared")

		await msg.answer('Забэкапленно!')
	
	# Функция подготовки полученных гифок ПОЛЬЗОВАТЕЛЯ для Inline процесса
	async def show_users_gifs(self, user_id, inline_query):
		user_id = str(user_id)
		self.ALL_GIFS.setdefault(user_id,[])
		self.ALL_GIFS[user_id] = [] # TODO: добавить кнопку "обновить gif"

		if inline_query.offset == "": # запуск инлайна
			logger.debug(f"{user_id}: OFFSET now {self.OFFSETS[user_id]} -> 1")
			self.OFFSETS[user_id] = 1 # Сигнал, что показаны первые 50 GIF

		if not self.ALL_GIFS[user_id]:
			logger.warning(f"{user_id}: haven't gifs")
			await self.get_gifs_from_vk(user_id)

		logger.debug(f"{user_id}: have {len(self.ALL_GIFS[user_id])} gifs")

		logger.debug(f"Before sending inline query result {user_id} have Offset {self.OFFSETS[user_id]}")

		return self.return_gifs_with_offset(user_id, inline_query.offset)
	
	# Функция подготовки поиска гифок ВК для Inline процесса
	async def users_search_gifs(self, user_id, inline_query):
		user_id = str(user_id)
		self.ALL_GIFS.setdefault(user_id,[])
		self.ALL_GIFS[user_id] = []
		if inline_query.offset == "": # Инлайн только что показал первые 50 GIF
			logger.debug(f"{user_id}: OFFSET now {self.OFFSETS[user_id]} -> 1")
			self.OFFSETS[user_id] = 1

		if not self.ALL_GIFS[user_id]:
			logger.warning(f"{user_id}: haven't gifs")
			await self.search_gifs_from_vk(user_id, inline_query.query)

		return self.return_gifs_with_offset(user_id, inline_query.offset)

	# Функция /start
	async def send_welcome(self, message: types.Message):
		user_id = message.from_user.id

		if not db.get_vk_token_by_telegram_id(user_id):
			keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
			keyboard_markup.add(
				types.InlineKeyboardButton('Авторизоваться через ВКонтакте', url = AUTH_URL),
				types.InlineKeyboardButton('Я боюсь вводить токен', url = PARANOID_URL)
			)

			logger.info(f"{user_id}: Bot started")

			await message.reply(GREATING,  reply_markup=keyboard_markup)
		else:

			logger.warning(f"{user_id}: sending /start with no reason")

			await message.reply("Вы уже авторизованы!")

	@logger.catch
	# Inline: main
	async def inline_process(self, inline_query: types.InlineQuery):
		user_id = inline_query.from_user.id

		logger.info(f"{user_id}: starting inline process")
		if not self.APIS.get(str(user_id)): # если сервер перезапускался, то апи нет
			player_token = db.get_vk_token_by_telegram_id(user_id)

			if player_token:
				logger.debug(f"{user_id}: registered api object")
				# Создаем место для нового пользователя
				self.APIS.setdefault(str(user_id), self.get_vk_api(player_token))
				self.OFFSETS.setdefault(str(user_id), 1)
			else:
				logger.warning(f"{user_id}: hasn't api object; require auth")
				await self.bot.answer_inline_query(
					inline_query.id,
					switch_pm_text = 'Авторизуйтесь чтобы использовать бота',
					switch_pm_parameter = "need_authorize",
					results=[],
					cache_time=1
				)
				return # не показываем инлайн

		if inline_query.query != "":

			logger.info(f"{user_id}: find gif; value {inline_query.query}")

			gif_results = await self.users_search_gifs(user_id, inline_query)

		else:

			gif_results = await self.show_users_gifs(user_id, inline_query)

		# Отправка инлайн ответа
		await self.bot.answer_inline_query(
			inline_query.id,
			is_personal = True,
			next_offset = "+",
			results = gif_results,
			cache_time=1
		)

	# Counter пользователей бота
	async def now_use(self, message: types.Message):
		n = db.get_counter()
		await message.answer(f"Пользователей: {n}")

	def start(self):
		dp = Dispatcher(self.bot)
		dp.register_message_handler(self.send_welcome, commands = ['start'])
		dp.register_message_handler(self.backup_info, commands = ['backup'])
		dp.register_message_handler(self.export, commands = ['export_db'])
		dp.register_message_handler(self.now_use, commands = ['users'])
		dp.register_message_handler(self.await_vk_token, content_types = ['text'])
		dp.register_message_handler(self.backup_gif, content_types = ['animation']) # странно, что animation - это гиф
		dp.register_inline_handler(self.inline_process)
		executor.start_polling(dp, skip_updates = True)

if __name__ == '__main__':
	b = VKGIFSBot(TOKEN)
	b.start()