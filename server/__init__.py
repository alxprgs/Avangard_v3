from .logging import logger
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
import os
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

try:
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"), serverSelectionTimeoutMS=5000, socketTimeoutMS=5000)
    database = client["AVANGARD"]
    logger.info("Подключение к MongoDB установлено.")
except Exception as e:
    logger.critical(f"Ошибка подключения к MongoDB: {e}")
    raise

app = FastAPI()

from routesv1 import routerv1

app.include_router(routerv1)
