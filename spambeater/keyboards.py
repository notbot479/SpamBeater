from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


_a = InlineKeyboardButton("❌ Spam", callback_data="spam")
_b = InlineKeyboardButton("✅ Ham", callback_data="ham")
_c = InlineKeyboardButton("🗑 Ignore", callback_data="ignore")
_buttons = [[_a,_b],[_c,]]
ASK_FOR_SPAM_KEYBOARD = InlineKeyboardMarkup(_buttons)
