from telegram import InputMediaPhoto

from bot.keyboard import get_photo_selector_control
from utils import IMGManager, get_logger


logger = get_logger(__name__)


async def publish_photo_to_all(context, users, photo_path, query):
    for uid, uname in users:
        try:
            await context.bot.send_photo(
                chat_id=uid,
                photo=IMGManager.read_image_file(photo_path)
            )
            logger.info(f"Image {photo_path} has been published to {uname}")
        except Exception as e:
            logger.error(f"Error publishing to {uid} (@{uname}): {e}")

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=get_photo_selector_control()
    )


async def photo_selector(update, context, file_paths):
    idx = context.user_data.get("idx", 0)
    path = file_paths[idx]

    first_message = context.user_data.get("first_message", True)

    if first_message:
        if update.message:
            await update.message.reply_photo(
                photo=IMGManager.read_image_file(path),
                reply_markup=get_photo_selector_control()
            )
        context.user_data["first_message"] = False
    else:
        query = update.callback_query
        if query:
            await context.bot.edit_message_media(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                media=InputMediaPhoto(
                    IMGManager.read_image_file(path)
                ),
                reply_markup=get_photo_selector_control()
            )

