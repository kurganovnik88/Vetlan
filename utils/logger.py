import logging
import os
from colorama import Fore, Style, init

init(autoreset=True)

def setup_logger():
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    # чтобы не дублировались хэндлеры
    if logger.handlers:
        return logger

    # === форматы ===
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    # === консоль ===
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # === файл ===
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, "bot.log"), encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
 