from pymongo.collection import Collection
import bcrypt
from .security import api_key_header
from .logging import logger
import os 
from fastapi import Depends, HTTPException, status

def create_hash(text: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(text.encode(), salt).decode()

async def get_next_id(collection: Collection) -> int:
    try:
        result = await collection.find_one(filter={},sort=[("_id", -1)],projection={"_id": 1})
        return (result["_id"] + 1) if result else 1
    except Exception as e:
        logger.error(f"Ошибка генерации ID: {e}")
        raise

async def validate_api_key(api_key: str = Depends(api_key_header)):
    valid_key = os.getenv("API_KEY")
    if not valid_key:
        logger.critical("API_KEY не настроен в .env файле!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Серверная ошибка конфигурации"
        )
    if api_key != valid_key:
        logger.warning(f"Неверный API-ключ: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий API-ключ"
        )
    return True