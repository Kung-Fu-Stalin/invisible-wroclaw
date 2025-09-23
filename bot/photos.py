from telegram import InputMediaPhoto

from bot.keyboard import get_images_controls
from utils import IMGManager


async def create_admin_message(update, file_path):
    await update.message.reply_photo(
        photo=IMGManager.read_image_file(file_path),
        reply_markup=get_images_controls()
    )


async def publish_photo(update, context, chat_id, file_path, msg=None):
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=IMGManager.read_image_file(file_path),
        caption=msg
    )


async def photo_selector(update, context, file_path):
    query = update.callback_query
    await context.bot.edit_message_media(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        media=InputMediaPhoto(
            IMGManager.read_image_file(file_path)
        ),
        reply_markup=get_images_controls()
    )
