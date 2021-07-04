import sqlite3

connection = sqlite3.connect("configs.db")
cursor = connection.cursor()

def add(tg_id: int, vk_token: str):
	cursor.execute("INSERT INTO data VALUES({}, '{token}' ,1)".format(tg_id, token = vk_token))
	connection.commit()

def get_sector_by_telegram_id(tg_id: int):
	sector = cursor.execute(f"SELECT sector FROM data WHERE telegram_user_id = {tg_id}").fetchall()
	if sector:
		return sector[0][0]
	return False

def get_vk_token_by_telegram_id(tg_id: int):
	vk_token = cursor.execute(f"SELECT vk_docs_token FROM data WHERE telegram_user_id = {tg_id}").fetchall()
	if vk_token:
		return vk_token[0][0]
	return False

def update_sector_by_telegram_id(tg_id: int, math_prikol: int):
	sect = get_sector_by_telegram_id(tg_id)
	if math_prikol == "+":
		sect += 1
	else:
		sect -= 1
	cursor.execute(f"Update data set sector = {sect} where telegram_user_id = {tg_id}")
	connection.commit()