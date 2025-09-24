from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)


def get_photo_selector_control():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev"),
            InlineKeyboardButton("➡️ Следующее", callback_data="next")
        ],
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def publish_placeholder():
    keyboard = [
        [InlineKeyboardButton("Публикую… ⏳", callback_data="noop")]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_control():
    keyboard = [
        [
            "🔄 Обновить фотографии",
            "🚫 Закончить экскурсию"
        ],
        [
            "🏞️ Контроль изображений"
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
