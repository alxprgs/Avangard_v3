# server/logging.py
import logging
import os
from datetime import datetime
import colorlog

console_log_format = (
    "%(log_color)s%(asctime)s - %(levelname)s:%(reset)s %(message)s"
)
file_log_format = "%(asctime)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

current_date = datetime.now().strftime("%d-%m-%y")
start_time = datetime.now().strftime("%H-%M-%S")

log_directory = f"./logs/{current_date}"
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, f"{start_time}.log")

file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(file_log_format, datefmt=date_format))

console_handler = colorlog.StreamHandler()
console_handler.setFormatter(
    colorlog.ColoredFormatter(
        console_log_format,
        datefmt=date_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        }
    )
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers.clear()
uvicorn_logger.setLevel(logging.INFO)
uvicorn_logger.addHandler(file_handler)
uvicorn_logger.addHandler(console_handler)

logger.info(f"Директория логов: {log_directory}")
logger.info(f"Файл логов: {log_file_path}")