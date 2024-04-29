# -*- coding: utf-8 -*-
from pyrogram.types import Message
from pyrogram.client import Client
import uvloop

from dataclasses import dataclass
from io import BytesIO
from enum import Enum
import traceback

from normalization import normalize_text
from logger import logger
from config import *


class FileClass(Enum):
    PHOTO = 1
    VIDEO = 2

@dataclass
class MediaFile:
    fclass: FileClass
    fid: str


uvloop.install()
bot = Client(
    name=BOT_NAME, 
    api_id=BOT_TELEGRAM_API_ID, 
    api_hash=BOT_TELEGRAM_API_HASH,
    bot_token=BOT_TELEGRAM_BOT_TOKEN,
)


async def get_file_bytes(file_id:str) ->  BytesIO | None:
    try:
        file_bytes = await bot.download_media(file_id, in_memory=True)
        if isinstance(file_bytes, BytesIO): return file_bytes
    except:
        return None

def get_media_file(message: Message) -> MediaFile | None:
    photo = message.photo
    video = message.video
    document = message.document
    if photo: 
        return MediaFile(fclass=FileClass.PHOTO, fid=photo.file_id)
    elif video: 
        return MediaFile(fclass=FileClass.VIDEO, fid=video.file_id)
    if not(document): return
    mime_head = document.mime_type.split('/')[0]
    if mime_head == 'image':
        return MediaFile(fclass=FileClass.PHOTO, fid=document.file_id)
    elif mime_head == 'video': 
        return MediaFile(fclass=FileClass.VIDEO, fid=document.file_id)

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


async def processing_text(text:str, message: Message) -> None:
    text = f'Text: {text}'
    print(text)
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id,text=text)


async def processing_photo(file: BytesIO, message: Message) -> None:
    text = f'Image: {file}'
    print(text)
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id,text=text)

async def processing_video(file: BytesIO, message: Message) -> None:
    text = f'Video: {file}'
    print(text)
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id,text=text)


@bot.on_message()
@bot.on_edited_message()
async def processing_message(_: Client, message: Message) -> None:
    text = get_effective_normalized_text(message=message)
    media_file = get_media_file(message=message)
    if text: await processing_text(text=text, message=message)
    if not(media_file): return
    file = await get_file_bytes(file_id=media_file.fid)
    if not(file): return
    if media_file.fclass == FileClass.PHOTO:
        await processing_photo(file=file, message=message)
    elif media_file.fclass == FileClass.VIDEO:
        await processing_video(file=file, message=message)


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
