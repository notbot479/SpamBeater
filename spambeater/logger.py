# -*- coding: utf-8 -*-
import logging

from config import *


formatter = logging.Formatter(BOTLOGS_LOG_FORMAT)
write_to_console = BOTLOGS_WRITE_TO_CONSOLE
write_to_file = BOTLOGS_WRITE_TO_FILE
log_file_name = BOTLOGS_LOG_FILE_NAME
logger = logging.getLogger(__name__)
logger.setLevel(write_to_console.level)


def setting_up_logs_to_console(level: int = logging.DEBUG):
    global formatter, logger
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def setting_up_logs_to_file(file_name: str, level: int = logging.INFO):
    global formatter, logger
    fh = logging.FileHandler(file_name)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


# setting up logger
if write_to_console.active:
    setting_up_logs_to_console(level=write_to_console.level)
if write_to_file.active and log_file_name:
    setting_up_logs_to_file(
        file_name=log_file_name,
        level=write_to_file.level,
    )
