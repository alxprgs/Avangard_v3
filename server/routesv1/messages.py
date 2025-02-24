from . import routerv1
from fastapi import Body

@routerv1.post("/get_messages")
async def get_messagess(key: int = Body(...), id: int = Body(...)):
    pass