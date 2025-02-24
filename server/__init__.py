from fastapi import FastAPI
from .telegram_bot import TelegramBot
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot = TelegramBot()
    await bot.start()
    yield
    await bot.stop()

app = FastAPI(lifespan=lifespan)

from .routesv1 import routerv1

app.include_router(routerv1)
