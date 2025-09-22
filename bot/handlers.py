from telegram import (
    Update
)
from telegram.ext import (
    CallbackContext,
    ContextTypes
)
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
photos = IMGManager.get_files_paths()
idx = 1


async def update(update: Update, context: CallbackContext):
    logger.info("[!] Called update command")
    gdrive_control = GDrive(settings.IMAGES_ARCHIVE)
    archive_path = gdrive_control.download_archive(settings.IMAGES_DIR)
    IMGManager.extract_archive(archive_path)
    await update.message.reply_text("Обновление завершено")


async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.username
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
        await update.message.reply_text("Вы подписаны на рассылку.")

    else:
        await update.message.reply_text(f"Админ @{user_name} добро пожаловать!")

        if IMGManager.is_dir_empty():
            await update.message.reply_text("ВНИМАНИЕ! Локально не найдено ни одной фотографии! Запустите /update")
            return

        await create_admin_message(update, file_path=photos[0])


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = DBManager.get_all_users()
    photos = IMGManager.get_files_paths()
    query = update.callback_query
    await query.answer()

    if query.data == "next":
        print(photos[idx], idx)
        idx += 1
        await photo_selector(update, context, photos[idx])

    elif query.data == "prev":
        print(photos[idx], idx)
        idx -= 1
        await photo_selector(update, context, photos[idx])

    elif query.data == "publish":
        photo_path = photos[idx]
        for uid, uname in users:
            try:
                await publish_photo(update, context, uid, photo_path)
            except Exception as e:
                logger.error(f"Error: {e}")
        print(photos[idx])
        idx += 1
        await photo_selector(update, context, photos[idx])
