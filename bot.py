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
AUTH_URL = "https://oauth.vk.com/authorize?client_id=7894722&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=docs&response_type=token&v=5.52"

TOKEN = os.getenv("TELEGRAM_API_TOKEN")

bot = Bot(token = TOKEN)
dp = Dispatcher(bot)

APIS = {}
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

def check_if_deeplink(text: str):
	args = text.split(" ")
	try:
		deeplink = args[1]
	except:
		return False
	else:
		return deeplink

def return_gifs_with_offset(user_id):
	global ALL_GIFS, sector

	user_gifs = ALL_GIFS[str(user_id)]
	user_sector = db.get_sector_by_telegram_id(user_id)
	offset2 = user_sector * 49
	offset1 = offset2 - 49

	return user_gifs[offset1:offset2]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	user_id = message.from_user.id

	deeplk = check_if_deeplink(message.text)
	if deeplk == "next":
		db.update_sector_by_telegram_id(user_id, "+")
		await message.answer("Следующие 50 гифок")
	elif deeplk == "prev":
		db.update_sector_by_telegram_id(user_id, "-")
		await message.answer("Предыдущие 50 гифок")
	elif not db.get_vk_token_by_telegram_id(user_id):	
		keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
		keyboard_markup.add(
			types.InlineKeyboardButton('Авторизоваться через ВКонтакте', url = AUTH_URL),
		)
		await message.reply(GREATING,  reply_markup=keyboard_markup)
	else:
		await message.reply("Ну старт и старт, что бубнить то...")

@dp.message_handler()
async def await_vk_token(message: types.Message):
	global APIS
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
			db.add(message.from_user.id, vk_token[0])
			APIS.setdefault(f"{message.from_user.id}", api)

@dp.inline_handler()
async def show_gifs(inline_query: types.InlineQuery):
	global APIS, ALL_GIFS

	user_id = inline_query.from_user.id
	if not APIS.get(str(user_id)):
		has_token = db.get_vk_token_by_telegram_id(user_id)
		if has_token:
			APIS.setdefault(str(user_id), get_vk_api(has_token))
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
	vk_api_result = await APIS.get(str(user_id)).docs.get()
	too_much = False
	for file in vk_api_result.response.items:
		if it_is_gif(file.title):
			item = create_item(
				result_id = hashlib.md5(str(file.id).encode()).hexdigest(),
				gif_url = file.url,
			)
			ALL_GIFS[str(user_id)].append(item)

	if len(return_gifs_with_offset(user_id)) >= 49:
		await bot.answer_inline_query(
			inline_query.id, 
			switch_pm_text = 'Следующие 50 GIF',
			switch_pm_parameter = "next",
			results=return_gifs_with_offset(user_id), 
			cache_time=1
		)
	else:
		if db.get_sector_by_telegram_id(user_id) > 1:
			await bot.answer_inline_query(
				inline_query.id, 
				switch_pm_text = 'Предыдущие 50 GIF', 
				switch_pm_parameter = "prev",
				results = return_gifs_with_offset(user_id), 
				cache_time=1
			)
		else:
			await bot.answer_inline_query(
				inline_query.id, 
				results = return_gifs_with_offset(user_id), 
				cache_time=1
			)

if __name__ == "__main__":
	executor.start_polling(dp)