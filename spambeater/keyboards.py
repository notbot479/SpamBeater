from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_ask4spam_keyboard(spam_class:str | None) -> InlineKeyboardMarkup:
    if not(spam_class): spam_class = 'none'
    _a = InlineKeyboardButton("❌ Spam", callback_data=f"query-spam-{spam_class}")
    _b = InlineKeyboardButton("✅ Ham", callback_data=f"query-ham-{spam_class}")
    _c = InlineKeyboardButton(f"🗑 Ignore - {spam_class}", callback_data="ignore")
    _buttons = [[_a,_b],[_c,]]
    return InlineKeyboardMarkup(_buttons)
