import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from bot.photos import photo_selector, publish_photo_to_all
from bot.keyboard import publish_placeholder, admin_control
from utils import (
    UI,
    GDrive,
    settings,
    get_logger,
    DBManager,
    IMGManager,
    TelegramImageResizer,
)


logger = get_logger(__name__)


async def update_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text(UI.google_drive_download_msg)
    IMGManager.clear_dir()
    logger.info("[!!!] Called update command...")

    gdrive_control = GDrive(settings.IMAGES_ARCHIVE)
    archive_path = gdrive_control.download_archive(settings.IMAGES_DIR)

    await upd.message.reply_text(UI.google_drive_archive_msg)
    IMGManager.extract_archive(archive_path)

    await upd.message.reply_text(UI.google_drive_start_check_images)

    resizer = TelegramImageResizer(settings.IMAGES_DIR)
    resizer.process_all()

    await upd.message.reply_text(UI.google_drive_finish_check_images)

    files = IMGManager.get_files_paths()
    await upd.message.reply_text(
        UI.google_drive_update_msg_template.replace("{files}", str(len(files))).replace(
            "{button}", UI.admin_control_photo_btn
        )
    )


async def get_users_list_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    users = DBManager.get_all_users()
    if not users:
        await upd.message.reply_text(UI.admin_users_list_no_users)
        return

    message = str()
    for uid, uname in users:
        message += UI.admin_users_list_item_template.replace(
            "{user_name}", uname
        ).replace("{user_id}", uid)
    message += UI.admin_users_list_stats_template.replace("{count}", str(len(users)))
    await upd.message.reply_text(message)


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

        await upd.message.reply_text(UI.user_welcome_msg)

    else:
        await upd.message.reply_text(
            UI.admin_welcome_msg_template.replace("{user_name}", user_name),
            reply_markup=admin_control(),
        )
        if IMGManager.is_dir_empty():
            logger.info(f"No files found in {settings.IMAGES_DIR}")
            await upd.message.reply_text(
                UI.photos_not_found_msg_template.replace(
                    "{button}", UI.admin_refresh_photo_btn
                )
            )
            return

        context.user_data["idx"] = 0
        context.user_data["first_message"] = True
        files = IMGManager.get_files_paths()
        await photo_selector(upd, context, file_paths=files)


async def photos_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    query = upd.callback_query
    await query.answer()

    users = DBManager.get_all_users()
    files = IMGManager.get_files_paths()
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


async def purge_cmd(update, context):
    users = DBManager.get_all_users()
    for uid, uname in users:
        try:
            await context.bot.send_message(chat_id=uid, text=UI.user_goodbye_msg)
            logger.info(f"User {uname} ({uid}) notified about unsubscribe")
        except Exception as e:
            logger.error(f"Failed to notify user {uid} (@{uname}): {e}")

    messages = DBManager.get_all_published_messages()
    for msg_record in messages:
        try:
            await context.bot.delete_message(
                chat_id=msg_record.chat_id, message_id=msg_record.message_id
            )
        except Exception as e:
            logger.error(f"Failed to delete message {msg_record.message_id}: {e}")

    DBManager.clear_all_published_messages()

    DBManager.clear_all()
    await update.message.reply_text(UI.admin_all_users_purged_msg)
