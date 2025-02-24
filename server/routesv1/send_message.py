from . import routerv1
from fastapi import Body

@routerv1.post("/send_message")
async def send_tg_nessage(key: int = Body(...), message: str = Body(...), id: int = Body(...)):
    pass