import logging
import os
import shutil
from datetime import datetime, timezone


def setup_logging():
    log_dir = "logs/"
    log_file = log_dir + "current.log"

    os.makedirs(log_dir, exist_ok=True)

    if os.path.exists(log_file):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        shutil.move(log_file, log_dir + f"{timestamp}_THPSBot.log")

    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
    )

    file_handler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.getLogger("Discord.py").setLevel(logging.INFO)
