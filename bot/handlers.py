import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from bot.photos import (
    photo_selector,
    publish_photo_to_all
)
from bot.keyboard import (
    publish_placeholder,
    admin_control
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
    await upd.message.reply_text("Начат процесс скачивания фотографий из Google Drive")
    logger.info("[!] Called update command")
    gdrive_control = GDrive(settings.IMAGES_ARCHIVE)
    archive_path = gdrive_control.download_archive(settings.IMAGES_DIR)
    await upd.message.reply_text("Архив скачан, начинаю распаковку...")
    IMGManager.extract_archive(archive_path)
    files = IMGManager.get_files_paths()
    await upd.message.reply_text(f"Обновление завершено. Всего: {len(files)} изображений. Нажмите 'Контроль изображений'")


async def start_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = upd.effective_user.id
    user_name = upd.effective_user.username

    is_user = user_id not in settings.ADMINS and user_name not in settings.ADMINS

    if is_user:
        if user_name:
            DBManager.add_user(telegram_user_id=user_id, telegram_user_name=user_name)
            logger.info(f"User: @{user_name} has been added to the subscription list")
        else:
            DBManager.add_user(telegram_user_id=user_id)
            logger.info(f"User: #{user_id} has been added to the subscription list")

        await upd.message.reply_text("Вы подписаны на рассылку.")

    else:
        await upd.message.reply_text(
            f"Админ @{user_name} вход выполнен", reply_markup=admin_control()
        )
        if IMGManager.is_dir_empty():
            logger.info(f"No files found in {settings.IMAGES_DIR}")
            await upd.message.reply_text(
                "ВНИМАНИЕ! Локально не найдено ни одной фотографии! Нажмите 'Обновить фотографии'"
            )
            return

        context.user_data["idx"] = 0
        context.user_data["first_message"] = True
        files = IMGManager.get_files_paths()
        await photo_selector(upd, context, file_paths=files)



async def button(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    query = upd.callback_query
    await query.answer()

    users = DBManager.get_all_users()
    files = IMGManager.get_files_paths()

    if not files:
        await query.edit_message_text("Нет доступных фотографий.")
        return

    idx = context.user_data.get("idx", 0)

    if query.data in ["next", "prev"]:
        if query.data == "next":
            idx = (idx + 1) % len(files)
        else:
            idx = (idx - 1) % len(files)
        context.user_data["idx"] = idx
        logger.info(f"Current idx: {idx} preview photo: {files[idx]}")
        await photo_selector(upd, context, file_paths=files)
        return

    elif query.data == "publish":
        await query.edit_message_reply_markup(reply_markup=publish_placeholder())
        photo_path = files[idx]

        asyncio.create_task(publish_photo_to_all(context, users, photo_path, query))


async def purge_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("PURGING TIME")
    await upd.message.reply_text("Not implemented yet")
