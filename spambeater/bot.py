# -*- coding: utf-8 -*-
from pyrogram.types import CallbackQuery, Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.client import Client
from pyrogram import filters
import uvloop

from collections import Counter
import numpy as np
import traceback
import asyncio

from normalization.image import normalize_image
from db.manager import Category, SaveManager
from antispam.image import ImagePredictModel
from antispam.text import TextPredictModel
from logger import logger
from bot_types import *
from keyboards import *
from config import *
import tasks


uvloop.install()
bot = Client(
    name=BOT_NAME, 
    api_id=BOT_TELEGRAM_API_ID, 
    api_hash=BOT_TELEGRAM_API_HASH,
    bot_token=BOT_TELEGRAM_BOT_TOKEN,
)
text_predict_model = TextPredictModel()
image_predict_model = ImagePredictModel()


def get_top_class_name(spam:list[Spam]) -> str | None:
    if not(spam): return None
    class_counts = Counter(s.cls for s in spam)
    spam_counts = Counter(s.cls for s in spam if s.status)
    class_top = class_counts.most_common(1)
    spam_top = spam_counts.most_common(1)
    top = spam_top if spam_top else class_top
    return top[0][0]

def is_command(message: Message) -> bool:
    text = message.text
    if not(text): return False
    return text.startswith('/')

async def is_chat_admin(user_id:int, chat_id:int) -> bool:
    _admins = (
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    )
    try:
        chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        status = chat_member.status in _admins
        return status
    except:
        return False

async def _admins_only(_, __, message: Message) -> bool: #pyright: ignore
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.id
    admin = await is_chat_admin(user_id=user_id,chat_id=chat_id)
    if admin: return True
    # delete message for not admins
    await bot.delete_messages(
        chat_id=chat_id,
        message_ids=[message_id,],
    )
    return False
admins_only = filters.create(_admins_only, 'AdminsOnly')

async def save_message_data(message: Message, category: Category) -> None:
    logger.debug(f'Processing save message data, category: {category}')
    text = get_effective_normalized_text(message=message)
    media_file = get_media_file(message=message)
    # save text and media
    if text: await SaveManager.save_text(text=text, category=category)
    if not(media_file): return
    filename = f'{media_file.fid}.{media_file.ext}'
    file_bytes = await get_file_bytes(file_id=media_file.fid)
    if not(file_bytes): return
    await SaveManager.save_media(
        file_bytes=file_bytes, 
        filename=filename, 
        category=category,
    )

def predict_images_spam(images: list[np.ndarray]) -> list[Spam]:
    spam = image_predict_model.predict_spam(images=images)
    return spam

def is_chat_for_processing(chat_id:int) -> bool:
    chats = list(BOT_ADMIN_CHATS.keys())
    return chat_id in chats

async def admin_mark_message_as_spam(message: Message, delete: bool = False) -> None:
    chat_id = message.chat.id
    message_ids = [message.id,]
    await save_message_data(message=message, category='spam')
    # delete message after processing
    if not(delete): return
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)

async def admin_mark_message_as_ham(message: Message, delete: bool = False) -> None:
    chat_id = message.chat.id
    message_ids = [message.id,]
    await save_message_data(message=message, category='ham')
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
    chat_id = get_admin_chat(chat_id=from_chat_id)
    if not(chat_id): return
    await bot.copy_message(
        chat_id=chat_id,
        message_id=message_id,
        from_chat_id=from_chat_id,
        **kwargs,
    )

async def get_main_frames_from_video(video: bytes, num_frames=32) -> list[np.ndarray]:
    job = tasks.get_frames_count.delay(video=video)
    while not job.ready(): await asyncio.sleep(1)
    total_frames = job.get()
    if total_frames < num_frames: total_frames = num_frames
    if not(total_frames): return []
    step = total_frames // num_frames
    job = tasks.get_frames_from_video.delay(video=video, stop=total_frames, step=step)
    while not job.ready(): await asyncio.sleep(1)
    frames = job.get()
    return frames[0:num_frames]

async def get_file_bytes(file_id:str) -> bytes | None:
    try:
        file = await bot.download_media(file_id, in_memory=True)
        return bytes(file.getbuffer()) #pyright: ignore
    except:
        return None

def get_media_file(message: Message) -> MediaFile | None:
    photo = message.photo
    video = message.video
    document = (
        message.document or 
        message.animation or 
        message.sticker
    )
    if photo:
        media = MediaFile(
            fclass=FileClass.PHOTO, 
            fid=photo.file_id,
            ext='jpg',
        )
        return media
    elif video: 
        media = MediaFile(
            fclass=FileClass.VIDEO, 
            fid=video.file_id,
            ext='mp4',
        )
        return media
    if not(document): return
    mime_head, ext = document.mime_type.split('/')[0:2]
    if mime_head == 'image':
        media = MediaFile(
            fclass=FileClass.PHOTO, 
            fid=document.file_id,
            ext=ext,
        )
        return media
    elif mime_head == 'video': 
        media = MediaFile(
            fclass=FileClass.VIDEO, 
            fid=document.file_id,
            ext=ext,
        )
        return media

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
    try:
        messages = await bot.get_media_group(chat_id=chat_id, message_id=message_id)
        message_ids = [m.id for m in messages]
    except:
        message_ids = [message_id,]
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)


async def processing_text(text:str, spam_proba:float=0.5) -> Spam:
    if not(text): return Spam(False)
    proba = text_predict_model.predict_spam_proba(text=text)
    logger.debug(f"Text({text}) predicted spam proba: {proba}")
    status = proba > spam_proba
    return Spam(status)

async def processing_photo(file_bytes: bytes) -> Spam:
    logger.debug(f'Start processing photo')
    image = normalize_image(file_bytes)
    spam = predict_images_spam(images=[image,])
    spam = spam[0] if spam else Spam(False)
    logger.info(f'Image shape: {image.shape}, {spam}') 
    return spam

async def processing_video(file_bytes: bytes, spam_proba:float=0.2) -> Spam:
    logger.debug(f'Start processing video')
    images = [normalize_image(i) for i in await get_main_frames_from_video(video=file_bytes)]
    if not(images): return Spam(False)
    predict = predict_images_spam(images)
    if not(predict): return Spam(False)
    spam_images = [image for i,image in zip(predict,images) if i]
    spam_images_count = len(spam_images)
    status = spam_images_count >= int(len(images) * spam_proba)
    cls = get_top_class_name(predict)
    spam = Spam(status=status, cls=cls)
    msg = f'Video frames: {len(images)}, spam_count: {spam_images_count}, {spam}'
    logger.info(msg=msg)
    return spam

async def processing_spam_message(message: Message) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.id
    await bot_ask4spam_in_admin_chat(message=message)
    await bot_delete_post_message(chat_id=chat_id, message_id=message_id)
    msg = f"[Bot] Delete Message({message_id}) from User({user_id}) in Chat({chat_id})"
    logger.info(msg=msg)

async def send_no_target_warn_message(message: Message) -> None:
    text = "Please select target by reply user message"
    await message.reply_text(text=text)

def get_target_message(message: Message) -> Message | None:
    target_message = message.reply_to_message
    if not(target_message): return None
    is_reply = message.from_user != target_message.from_user
    return target_message if is_reply else None


@bot.on_message(filters.command("spam") & admins_only)
async def spam_command_handler(
    _: Client, 
    message: Message, 
    ban_user:bool = False,
    *,
    delete_message: bool = True,
) -> None:
    target_message = get_target_message(message=message)
    if not(target_message): 
        await send_no_target_warn_message(message=message)
        return
    await admin_mark_message_as_spam(target_message, delete=delete_message)
    # delete admin command
    await bot.delete_messages(
        chat_id=message.chat.id,
        message_ids=[message.id,],
    )
    if not(ban_user): return
    await bot.ban_chat_member(
        chat_id=target_message.chat.id,
        user_id=target_message.from_user.id,
    )

@bot.on_message(filters.command("ham") & admins_only)
async def ham_command_handler(
    _: Client, 
    message: Message, 
    delete_message:bool=False,
) -> None:
    target_message = get_target_message(message=message)
    if not(target_message): 
        await send_no_target_warn_message(message=message)
        return
    await admin_mark_message_as_ham(target_message, delete=delete_message)
    # delete admin command
    await bot.delete_messages(
        chat_id=message.chat.id,
        message_ids=[message.id,],
    )

@bot.on_message(filters.command("start"))
async def start_command_handler(_: Client, message: Message) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = message.from_user.first_name
    await message.reply_text(f"Hi, {user}!")
    logger.debug(f'Processing start command for User({user_id}) in Chat({chat_id})')

@bot.on_callback_query()
async def callback_query(_: Client, query: CallbackQuery) -> None:
    message = query.message
    if query.data == "spam":
        await admin_mark_message_as_spam(message=message, delete=True)
    elif query.data == "ham":
        await admin_mark_message_as_ham(message=message, delete=True)
    elif query.data == "ignore":
        await bot.delete_messages(
            chat_id = message.chat.id,
            message_ids=[message.id,],
        )

@bot.on_message()
@bot.on_edited_message()
async def antispam_handler(_: Client, message: Message) -> None:
    user_id, chat_id = message.from_user.id, message.chat.id
    # skip processing
    if is_command(message=message): return
    if not(is_chat_for_processing(chat_id)): return
    #if is_chat_admin(user_id=user_id, chat_id=chat_id): return
    # processing message
    logger.debug(f'Start processing message: User({user_id}) in Chat({chat_id})')
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
