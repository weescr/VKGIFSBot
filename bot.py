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

bot = Bot(token = TOKEN)
dp = Dispatcher(bot)

APIS = {}
OFFSETS = {}
ALL_GIFS = {}

def get_vk_api(token):
	api_session = API(tokens=token, clients=AIOHTTPClient())
	api = api_session.get_context()
	return api

def create_item(result_id: int, gif_url: str):
	new_item = types.InlineQueryResultGif(
		id=result_id,
		gif_url = gif_url,
		thumb_url = gif_url,
		gif_width = 100,
		gif_height = 100,
	)
	return new_item

def it_is_gif(title: str):
	try:
		ext = title[-3:]
	except Exception:
		return False
	else:
		if ext == 'gif':
			return True
		return False

def return_gifs_with_offset(user_id, offset = None):
	global ALL_GIFS, OFFSETS

	user_gifs = ALL_GIFS[str(user_id)]

	if offset == "":
		OFFSETS[str(user_id)] += 1
		return user_gifs[:50]
	else:
		user_offset = OFFSETS[f'{user_id}']

		if user_offset == 0:
			return [] #  гифки пользователя кончились
		else:
			max_user_offsets = len(user_gifs) // 50 # питон всегда округляет в меньшую сторону

			gif_offset2 = user_offset * 50
			gif_offset1 = gif_offset2 - 50

			result = user_gifs[gif_offset1:gif_offset2]

			if user_gifs[gif_offset2:]:
				OFFSETS[f"{user_id}"] += 1
			else:
				OFFSETS[f'{user_id}'] = 0

			return result

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
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

@dp.message_handler()
async def await_vk_token(message: types.Message):
	global APIS, OFFSETS
	user_id = message.from_user.id
	parsed_url = parse_qs(message.text)
	vk_token = parsed_url.get("https://oauth.vk.com/blank.html#access_token")
	if not vk_token:
		await message.answer("Нет, это не сработает")
	else:
		api = get_vk_api(vk_token)
		try:
			await api.docs.get()
		except:
			await message.answer("Неправильный токен")
		else:
			await message.answer("Да, это сработает")
			db.add(f"{user_id}", vk_token[0])
			APIS.setdefault(f"{user_id}", api)
			OFFSETS.setdefault(f"{user_id}", 1)

@dp.inline_handler()
async def show_gifs(inline_query: types.InlineQuery):
	global APIS, ALL_GIFS

	user_id = inline_query.from_user.id

	if not APIS.get(str(user_id)):
		has_token = db.get_vk_token_by_telegram_id(user_id)
		if has_token:
			APIS.setdefault(str(user_id), get_vk_api(has_token))
			OFFSETS.setdefault(str(user_id), 1)
		else:
			await bot.answer_inline_query(
				inline_query.id,
				switch_pm_text = 'Авторизуйтесь чтобы использовать бота',
				switch_pm_parameter = "need_authorize",
				results=[],
				cache_time=1
			)
			return

	ALL_GIFS.setdefault(str(user_id),[])
	ALL_GIFS[str(user_id)] = [] # добавить кнопку "обновить gif"
	vk_api_result = await APIS.get(str(user_id)).docs.get()

	if inline_query.offset != "+": # первый раз выбор
		OFFSETS[str(user_id)] = 1

	if not ALL_GIFS[str(user_id)]:
		for file in vk_api_result.response.items:
			if it_is_gif(file.title):
				item = create_item(
					result_id = hashlib.md5(str(file.id).encode()).hexdigest(),
					gif_url = file.url,
				)
				ALL_GIFS[str(user_id)].append(item)


	await bot.answer_inline_query(
			inline_query.id,
			is_personal = True,
			next_offset = "+",
			results=return_gifs_with_offset(user_id, inline_query.offset), 
			cache_time=1
		)

if __name__ == "__main__":
	executor.start_polling(dp, skip_updates = True)