from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev"),
            InlineKeyboardButton("➡️ Следующее", callback_data="next")
        ],
        [InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]
    ]
    return InlineKeyboardMarkup(keyboard)
