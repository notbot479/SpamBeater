from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


_a = InlineKeyboardButton("Spam", callback_data="spam")
_b = InlineKeyboardButton("NotSpam", callback_data="notspam")
_buttons = [[_a,_b]]
ASK_FOR_SPAM_KEYBOARD = InlineKeyboardMarkup(_buttons)
