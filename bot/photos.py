from pathlib import Path

from telegram import CallbackQuery, InputMediaPhoto, Message
from telegram.ext import ContextTypes

from bot.keyboard import get_photo_selector_control
from utils import UI, IMGManager, DBManager, get_logger


logger = get_logger(__name__)

STEPS = {"prev": -1, "next": 1}


def neighbour(photos: list[str], current: str | None, step: int) -> str:
    """The photo `step` places away from `current`; the first one if it is gone."""
    if current not in photos:
        return photos[0]
    return photos[(photos.index(current) + step) % len(photos)]


def shown_photo(context: ContextTypes.DEFAULT_TYPE, gallery_id: int) -> str | None:
    return _galleries(context).get(gallery_id)


def _galleries(context: ContextTypes.DEFAULT_TYPE) -> dict[int, str]:
    """The photo each of the guide's gallery messages is showing."""
    return context.user_data.setdefault("galleries", {})


async def ask_to_refresh(message: Message):
    logger.info(f"No photos found in {IMGManager.path}")
    await message.reply_text(
        UI.photos_not_found_msg_template.format(button=UI.admin_refresh_photo_btn)
    )


async def open_gallery(message: Message, context: ContextTypes.DEFAULT_TYPE):
    photos = IMGManager.get_files_paths()
    if not photos:
        await ask_to_refresh(message)
        return
    sent = await message.reply_photo(
        photo=Path(photos[0]),
        reply_markup=get_photo_selector_control(),
    )
    _galleries(context)[sent.message_id] = photos[0]


async def show_photo(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, photo: str
):
    await query.edit_message_media(
        media=InputMediaPhoto(Path(photo)),
        reply_markup=get_photo_selector_control(),
    )
    _galleries(context)[query.message.message_id] = photo


async def publish_photo_to_all(context, users, photo_path, query):
    photo = Path(photo_path)
    for uid, uname in users:
        try:
            msg = await context.bot.send_photo(chat_id=uid, photo=photo)
            photo = msg.photo[-1].file_id  # uploaded once, reused for the others

            DBManager.add_published_message(
                telegram_user_id=uid, message_id=msg.message_id, chat_id=msg.chat_id
            )

            logger.info(f"Image {photo_path} has been published to {uname}")

        except Exception as e:
            logger.error(f"Error publishing to {uid} (@{uname}): {e}")

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=get_photo_selector_control(),
    )
