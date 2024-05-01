# -*- coding: utf-8 -*-
from pyrogram.types import CallbackQuery, Message
from pyrogram.client import Client
import uvloop

import numpy as np
import traceback
import imageio

from normalization.image import normalize_image
from normalization.text import normalize_text
from logger import logger
from bot_types import *
from keyboards import *
from config import *


uvloop.install()
bot = Client(
    name=BOT_NAME, 
    api_id=BOT_TELEGRAM_API_ID, 
    api_hash=BOT_TELEGRAM_API_HASH,
    bot_token=BOT_TELEGRAM_BOT_TOKEN,
)


async def admin_mark_message_as_spam(message: Message, delete: bool = False) -> None:
    chat_id = message.chat.id
    message_ids = [message.id,]
    print('Processing spam')
    # delete message after processing
    if not(delete): return
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)

async def admin_mark_message_as_ham(message: Message, delete: bool = False) -> None:
    chat_id = message.chat.id
    message_ids = [message.id,]
    print('Processing ham')
    # delete message after processing
    if not(delete): return
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)

async def bot_ask4spam_in_admin_chat(message: Message) -> None:
    keyboard = ASK_FOR_SPAM_KEYBOARD
    params = {
        'reply_markup': keyboard,
    }
    await bot_copy_message_to_admin_chat(message=message, **params)

def get_admin_chat(chat_id:int) -> int | None:
    admin_chat_id = BOT_ADMIN_CHATS.get(chat_id)
    return admin_chat_id

async def bot_copy_message_to_admin_chat(message: Message, **kwargs) -> None:
    message_id = message.id
    from_chat_id = message.chat.id
    if from_chat_id > 0: return # skip personal chats
    chat_id = get_admin_chat(chat_id=from_chat_id)
    if not(chat_id): return
    await bot.copy_message(
        chat_id=chat_id,
        message_id=message_id,
        from_chat_id=from_chat_id,
        **kwargs,
    )

def get_main_frames_from_video(video: bytes, num_frames=30) -> list[np.ndarray]:
    frames = get_frames_from_video(video=video)
    if not(frames): return []
    total_frames = len(frames)
    if total_frames < num_frames: return frames
    frame_delta = total_frames // num_frames
    main_frames = [frames[i] for i in range(0, total_frames, frame_delta)]
    return main_frames[0:num_frames]

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
    normalized_text = normalize_text(text=text)
    if not(normalized_text): return False
    print(f'Text: {text}')
    print(f'Text normalized: {normalized_text}')
    return False

async def processing_photo(file_bytes: bytes) -> bool:
    image = normalize_image(file_bytes)
    text = f'Image: {image.shape}'
    print(text)
    return False

async def processing_video(file_bytes: bytes) -> bool:
    frames = get_main_frames_from_video(video=file_bytes)
    images = [normalize_image(i) for i in frames]
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


@bot.on_callback_query()
async def callback_query(_: Client, query: CallbackQuery):
    message = query.message
    if query.data == "spam":
        await admin_mark_message_as_spam(message=message, delete=True)
    elif query.data == "notspam":
        await admin_mark_message_as_ham(message=message, delete=True)

@bot.on_message()
@bot.on_edited_message()
async def processing_message(_: Client, message: Message) -> None:
    spam = False
    text = get_effective_normalized_text(message=message)
    media_file = get_media_file(message=message)
    
    # TODO remove test echo to admin chat
    await bot_ask4spam_in_admin_chat(message=message)

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
