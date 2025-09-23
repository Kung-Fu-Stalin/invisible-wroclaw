from telegram import Update
from telegram.ext import ContextTypes
from bot.photos import (
    create_admin_message,
    photo_selector,
    publish_photo
)
from bot.keyboard import (
    publish_placeholder,
    publishing_ended
)
from utils import (
    GDrive,
    settings,
    get_logger,
    DBManager,
    IMGManager
)

logger = get_logger(__name__)


async def update_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[!] Called update command")
    gdrive_control = GDrive(settings.IMAGES_ARCHIVE)
    archive_path = gdrive_control.download_archive(settings.IMAGES_DIR)
    IMGManager.extract_archive(archive_path)
    await upd.message.reply_text("Обновление завершено")


async def start_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = upd.effective_user.id
    user_name = upd.effective_user.username

    is_user = ((user_id not in settings.ADMINS)
               and (user_name not in settings.ADMINS))

    if is_user:
        if user_name:
            DBManager.add_user(
                telegram_user_id=user_id,
                telegram_user_name=user_name
            )
            logger.info(f"User: @{user_name} has been added to the subscription list")
        else:
            DBManager.add_user(telegram_user_id=user_id)
            logger.info(f"User: {user_id} has been added to the subscription list")

        await upd.message.reply_text("Вы подписаны на рассылку.")

    else:
        await upd.message.reply_text(f"Админ @{user_name} добро пожаловать!")

        if IMGManager.is_dir_empty():
            await upd.message.reply_text(
                "ВНИМАНИЕ! Локально не найдено ни одной фотографии! Запустите /update"
            )
            return

        photos = IMGManager.get_files_paths()
        if photos:
            start_index = 0
            context.user_data["idx"] = start_index
            await create_admin_message(upd, file_path=photos[start_index])


async def button(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    query = upd.callback_query
    await query.answer()
    admin_user = upd.effective_user.username
    users = DBManager.get_all_users()
    photos = IMGManager.get_files_paths()

    if not photos:
        await query.edit_message_text("Нет доступных фотографий.")
        return

    idx = context.user_data.get("idx", 1)

    if query.data == "next":
        idx += 1
        context.user_data["idx"] = idx
        logger.info(
            f"User: {admin_user} pressed (next) button. "
            f"Index: {idx} "
            f"Loaded image: {photos[idx]}"
        )
        await photo_selector(upd, context, photos[idx])

    elif query.data == "prev":
        idx -= 1
        context.user_data["idx"] = idx
        logger.info(
            f"User: {admin_user} pressed (prev) button. "
            f"Index: {idx} "
            f"Loaded image: {photos[idx]}"
        )
        await photo_selector(upd, context, photos[idx])

    elif query.data == "publish":
        logger.info(
            f"User: {admin_user} pressed (publish) button."
            f"Index: {idx} "
            f"Loaded image: {photos[idx]}"
        )
        await query.edit_message_reply_markup(
            reply_markup=publish_placeholder()
        )

        photo_path = photos[idx]
        for uid, uname in users:
            logger.info(
                f"Attempt to send image to user: {uname} with id: {uid}"
            )
            try:
                await publish_photo(upd, context, uid, photo_path)
                logger.info(f"Image {photo_path} has been published")
            except Exception as e:
                logger.error(f"Error publishing to {uid} (@{uname}): {e}")

        if idx < len(photos) - 1:
            idx += 1
            context.user_data["idx"] = idx
            logger.info(f"Calling photo_selector with image: {photos[idx]}")
            await photo_selector(upd, context, photos[idx])
        else:
            await query.edit_message_reply_markup(reply_markup=publishing_ended())
