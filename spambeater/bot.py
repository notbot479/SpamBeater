# -*- coding: utf-8 -*-
from pyrogram.types import Message
from pyrogram.client import Client
import uvloop

import traceback

from normalization import normalize_text
from logger import logger
from config import *


uvloop.install()
bot = Client(
    name=BOT_NAME, 
    api_id=BOT_TELEGRAM_API_ID, 
    api_hash=BOT_TELEGRAM_API_HASH,
    bot_token=BOT_TELEGRAM_BOT_TOKEN,
)


def get_media_file_id(message: Message) -> str | None:
    photo = message.photo
    video = message.video
    document = message.document
    if photo: return photo.file_id
    elif video: return video.file_id
    elif document: return document.file_id

def get_effective_text(message: Message) -> str | None:
    text = message.text or message.caption
    return text

def get_effective_normalized_text(message: Message) -> str | None:
    text = get_effective_text(message=message)
    if not(text): return None
    text = normalize_text(text=text)
    return text

async def bot_delete_post_message(chat_id:int, message_id: int) -> None:
    '''delete all messages from group by message id'''
    messages = await bot.get_media_group(chat_id=chat_id, message_id=message_id)
    message_ids = [m.id for m in messages]
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
    logger.info(f"[Bot] Delete Message({message_id}) from Chat({chat_id})")


@bot.on_message()
@bot.on_edited_message()
async def processing_message(_: Client, message: Message) -> None:
    text = get_effective_normalized_text(message=message)
    file_id = get_media_file_id(message=message)
    if not(text or file_id): return
    print(text, file_id)
    chat_id = message.chat.id
    message_id = message.id
    if text != 'spam': return 
    await bot_delete_post_message(chat_id, message_id)


def main():
    try:
        mode = 'debug' if BOT_DEBUG_MODE else 'deploy'
        logger.info(f'[Bot] Started in {mode} mode')
        bot.run()
    except KeyboardInterrupt:
        logger.info(f'[Bot] Stopped via keyboard interrupt')
    except Exception as e:
        # don't log critical in debug mode
        if BOT_DEBUG_MODE: raise e 
        logger.critical(f'[Bot] Fatal error was happened, traceback below. Error: {e}')
        logger.critical(traceback.format_exc())
    finally:
        logger.info(f'[Bot] Successfully stopped')


if __name__ == "__main__":
    main()
