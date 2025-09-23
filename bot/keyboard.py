from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_images_controls():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev"),
            InlineKeyboardButton("➡️ Следующее", callback_data="next")
        ],
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def publish_placeholder():
    keyboard = [
        [InlineKeyboardButton("Публикую… ⏳", callback_data="noop")]
    ]
    return InlineKeyboardMarkup(keyboard)


def publishing_ended():
    keyboard = [
        [InlineKeyboardButton("Фотографии закончились", callback_data="noop")]
    ]
    return InlineKeyboardMarkup(keyboard)
