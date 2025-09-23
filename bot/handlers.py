from telegram import Update
from telegram.ext import ContextTypes
from bot.photos import (
    create_admin_message,
    photo_selector,
    publish_photo
)
from utils import (
    GDrive,
    settings,
    get_logger,
    DBManager,
    IMGManager
)

logger = get_logger(__name__)
idx = 0


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

    users = DBManager.get_all_users()
    photos = IMGManager.get_files_paths()

    if not photos:
        await query.edit_message_text("Нет доступных фотографий.")
        return

    idx = context.user_data.get("idx", 1)
    print(idx)
    if query.data == "next":
        if idx < len(photos) - 1:
            idx += 1
            print(f"IDX: {idx}")
            context.user_data["idx"] = idx
            await photo_selector(upd, context, photos[idx])
        else:
            await query.edit_message_text("Это последняя фотография.")

    elif query.data == "prev":
        if idx > 0:
            idx -= 1
            context.user_data["idx"] = idx
            print(f"IDX: {idx}")
            await photo_selector(upd, context, photos[idx])
        else:
            await query.edit_message_text("Это первая фотография.")

    elif query.data == "publish":
        photo_path = photos[idx]
        for uid, uname in users:
            try:
                await publish_photo(upd, context, uid, photo_path)
            except Exception as e:
                logger.error(f"Error publishing to {uid} (@{uname}): {e}")

        if idx < len(photos) - 1:
            idx += 1
            context.user_data["idx"] = idx
            await photo_selector(upd, context, photos[idx])
        else:
            await query.edit_message_text("Фотографии закончились.")
