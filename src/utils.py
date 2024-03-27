import hashlib
from src.config import settings

def create_hashed_telegram_id(telegram_id: int) -> str:
    telegram_id_str = str(telegram_id)
    hasher = hashlib.sha256()
    hasher.update((telegram_id_str + settings.SALT).encode())
    hashed_telegram_id = hasher.hexdigest()
    return hashed_telegram_id
