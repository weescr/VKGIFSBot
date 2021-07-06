import os
import sqlite3

connection = sqlite3.connect(os.path.join("db", "configs.db"))
cursor = connection.cursor()

def add(tg_id: int, vk_token: str):
	cursor.execute("INSERT INTO data VALUES({}, '{token}')".format(tg_id, token = vk_token))
	connection.commit()

def get_vk_token_by_telegram_id(tg_id: int):
	vk_token = cursor.execute(f"SELECT vk_docs_token FROM data WHERE telegram_user_id = {tg_id}").fetchall()
	if vk_token:
		return vk_token[0][0]
	return False
