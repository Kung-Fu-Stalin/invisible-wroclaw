from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from utils import UI


def get_photo_selector_control():
    keyboard = [
        [
            InlineKeyboardButton(UI.admin_prev_photo_btn, callback_data="prev"),
            InlineKeyboardButton(UI.admin_next_photo_btn, callback_data="next"),
        ],
        [
            InlineKeyboardButton(UI.admin_publish_photo_btn, callback_data="publish"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def publish_placeholder():
    keyboard = [[InlineKeyboardButton(UI.admin_publishing_photo, callback_data="noop")]]
    return InlineKeyboardMarkup(keyboard)


def admin_control():
    keyboard = [
        [UI.admin_refresh_photo_btn, UI.admin_finish_session_btn],
        [UI.admin_control_photo_btn],
        [UI.admin_get_users_list],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
