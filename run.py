import uvicorn
import asyncio
from server import app
from server.database import client
from server.logging import logger
import os

async def main():
    try:
        config = uvicorn.Config("server:app", port=int(os.getenv("PORT")), host="0.0.0.0")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.critical(f"error: {e}")
    finally:
        client.close()
        logger.info("Connection to database closed.")

if __name__ == "__main__":
    asyncio.run(main())