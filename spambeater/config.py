# -*- coding: utf-8 -*-
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import os


load_dotenv()


@dataclass
class LoggerMode:
    active: bool = True
    level: int = logging.INFO

# basic settings
BOT_NAME = "SpamBeater"
BOT_DEBUG_MODE = True

# dotenv
BOT_TELEGRAM_BOT_TOKEN: str = os.getenv("BOT_TELEGRAM_BOT_TOKEN","")
BOT_TELEGRAM_API_ID: str = os.getenv("BOT_TELEGRAM_API_ID","")
BOT_TELEGRAM_API_HASH: str = os.getenv("BOT_TELEGRAM_API_HASH","")

# logger settings
BOTLOGS_LOG_FILE_NAME: str = F'{BOT_NAME}.logs'
BOTLOGS_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
BOTLOGS_WRITE_TO_CONSOLE: LoggerMode = LoggerMode(level=logging.DEBUG)
BOTLOGS_WRITE_TO_FILE: LoggerMode = LoggerMode(active=False)
