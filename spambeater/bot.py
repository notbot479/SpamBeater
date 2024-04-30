# -*- coding: utf-8 -*-
from pyrogram.types import Message
from pyrogram.client import Client
import uvloop

import traceback
import imageio

from logger import logger
from normalization import *
from bot_types import *
from config import *


uvloop.install()
bot = Client(
    name=BOT_NAME, 
    api_id=BOT_TELEGRAM_API_ID, 
    api_hash=BOT_TELEGRAM_API_HASH,
    bot_token=BOT_TELEGRAM_BOT_TOKEN,
)


def get_frames_from_video(video:bytes) -> list[np.ndarray]:
    frames = imageio.get_reader(video, format='mp4') #pyright: ignore
    frames = [np.array(i) for i in frames] # pyright: ignore
    return frames

async def get_file_bytes(file_id:str) -> bytes | None:
    try:
        file = await bot.download_media(file_id, in_memory=True)
        file_bytes = bytes(file.getbuffer()) #pyright: ignore
        return file_bytes
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
    text = text.replace('\n',' ').lower()
    return text

async def bot_delete_post_message(chat_id:int, message_id: int) -> None:
    '''delete all messages from group by message id'''
    messages = await bot.get_media_group(chat_id=chat_id, message_id=message_id)
    message_ids = [m.id for m in messages]
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
    logger.debug(f"[Bot] Delete Message({message_id}) from Chat({chat_id})")


async def processing_text(text:str) -> bool:
    text = f'Text: {text}'
    print(text)
    return False

async def processing_photo(file_bytes: bytes) -> bool:
    image = normalize_image(image_bytes=file_bytes)
    text = f'Image: {image.shape}'
    print(text)
    return False

async def processing_video(file_bytes: bytes) -> bool:
    frames = get_frames_from_video(video=file_bytes)

    text = f'Video frames {len(frames)}'
    print(text)
    return False

async def processing_spam_message(message: Message) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.id
    await bot_delete_post_message(chat_id=chat_id, message_id=message_id)
    msg = f"[Bot] Delete Message({message_id}) from User({user_id}) in Chat({chat_id})"
    logger.info(msg=msg)


@bot.on_message()
@bot.on_edited_message()
async def processing_message(_: Client, message: Message) -> None:
    spam = False
    text = get_effective_normalized_text(message=message)
    media_file = get_media_file(message=message)
    if text: spam = await processing_text(text=text)
    if spam: await processing_spam_message(message=message)
    if not(media_file) or spam: return
    file_bytes = await get_file_bytes(file_id=media_file.fid)
    if not(file_bytes): return
    if media_file.fclass == FileClass.PHOTO:
        spam = await processing_photo(file_bytes=file_bytes)
    elif media_file.fclass == FileClass.VIDEO:
        spam = await processing_video(file_bytes=file_bytes)
    if spam: await processing_spam_message(message=message)


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
