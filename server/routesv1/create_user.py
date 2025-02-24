from . import routerv1
from fastapi import Body, Depends
from server.database import database
from server.logging import logger
from fastapi.responses import JSONResponse
from server.functions import get_next_id, create_hash, validate_api_key
import secrets

@routerv1.post("/create_user", dependencies=[Depends(validate_api_key)])
async def create_user(tg_id: int = Body(...), nickname: str = Body(..., max_length=32, min_length=3), chats: list[int] = Body(...)):
    db = database["users"]
    existing_user = await db.find_one({"tg_id": tg_id})
    if existing_user:
        logger.warning(f"Попытка повторной регистрации tg_id: {tg_id}")
        return JSONResponse({"status": False, "message": "Отказано в доступе. Аккаунт уже зарегистрирован."},status_code=409)
    try:
        key = None
        for attempt in range(10):
            new_key = secrets.randbelow(10**10 - 10**9) + 10**9
            key_str = str(new_key)
            if not await db.find_one({"key": create_hash(text=key_str)}):
                key = new_key
                logger.debug(f"Ключ сгенерирован с попытки {attempt + 1}")
                break
        if not key:
            logger.error(f"Не удалось сгенерировать уникальный ключ после 10 попыток, tg_id: {tg_id}")
            return JSONResponse({"status": False, "message": "Не удалось сгенерировать уникальный ключ"},status_code=500)
        key_hash = create_hash(text=str(key))
        user_data = {
            "_id": await get_next_id(collection=db),
            "tg_id": tg_id,
            "nickname": nickname,
            "chats": chats,
            "key": key_hash
        } 
        await db.insert_one(user_data)
        logger.info(f"Успешная регистрация пользователя: tg_id={tg_id}")
        return JSONResponse({"status": True, "message": "Успешная регистрация.", "key": key},status_code=200, headers={"Cache-Control": "no-store"})
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {str(e)}", exc_info=True)
        return JSONResponse({"status": False, "message": f"Внутренняя ошибка сервера."},status_code=500)