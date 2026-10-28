import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from bot.auth import ADMINS, admin_only
from bot.photos import (
    STEPS,
    neighbour,
    show_photo,
    shown_photo,
    open_gallery,
    ask_to_refresh,
    publish_photo_to_all,
)
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


async def _do_update(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await upd.message.reply_text(UI.google_drive_download_msg)
        logger.info("[!!!] Called update command...")

        with IMGManager.staging() as next_photos:
            gdrive_control = GDrive(settings.IMAGES_ARCHIVE)
            archive_path = await asyncio.to_thread(
                gdrive_control.download_archive, next_photos.path
            )

            await upd.message.reply_text(UI.google_drive_archive_msg)
            await asyncio.to_thread(next_photos.extract_archive, archive_path)

            await upd.message.reply_text(UI.google_drive_start_check_images)
            resizer = TelegramImageResizer(next_photos.path)
            await asyncio.to_thread(resizer.process_all)

            await upd.message.reply_text(UI.google_drive_finish_check_images)
            IMGManager.replace_photos_with(next_photos)

        files = IMGManager.get_files_paths()
        await upd.message.reply_text(
            UI.google_drive_update_msg_template.replace(
                "{files}", str(len(files))
            ).replace("{button}", UI.admin_control_photo_btn),
            reply_markup=admin_control(is_updating=False),
        )
    except Exception:
        logger.exception("Update process failed")
        await upd.message.reply_text(
            UI.admin_refresh_photo_exception_msg,
            reply_markup=admin_control(is_updating=False),
        )


@admin_only
async def update_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text(
        UI.google_drive_start_event,
        reply_markup=admin_control(is_updating=True),
    )

    context.application.create_task(_do_update(upd, context), update=upd)


@admin_only
async def get_users_list_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    users = DBManager.get_all_users()
    if not users:
        await upd.message.reply_text(UI.admin_users_list_no_users)
        return

    message = str()
    for uid, uname in users:
        uname = f"@{uname}" if uname else "NoUsername"
        message += UI.admin_users_list_item_template.replace(
            "{user_name}", uname
        ).replace("{user_id}", uid)
    message += UI.admin_users_list_stats_template.replace("{count}", str(len(users)))
    await upd.message.reply_text(message)


async def start_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = upd.effective_user.id
    user_name = upd.effective_user.username

    if upd.effective_user not in ADMINS:
        if user_name:
            DBManager.add_user(telegram_user_id=user_id, telegram_user_name=user_name)
            logger.info(f"User: @{user_name} has been added to the subscription list")
        else:
            DBManager.add_user(telegram_user_id=user_id)
            logger.info(f"User: #{user_id} has been added to the subscription list")

        await upd.message.reply_text(UI.user_welcome_msg)

    else:
        await upd.message.reply_text(
            UI.admin_welcome_msg_template.replace(
                "{user_name}", upd.effective_user.name
            ),
            reply_markup=admin_control(),
        )
        await open_gallery(upd.message, context)


@admin_only
async def photos_cmd(upd: Update, context: ContextTypes.DEFAULT_TYPE):
    query = upd.callback_query
    await query.answer()

    photos = IMGManager.get_files_paths()
    if not photos:
        await ask_to_refresh(query.message)
        return

    shown = shown_photo(context, query.message.message_id)
    if query.data in STEPS:
        await show_photo(query, context, neighbour(photos, shown, STEPS[query.data]))
    elif query.data == "publish" and shown in photos:
        await query.edit_message_reply_markup(reply_markup=publish_placeholder())
        users = DBManager.get_all_users()
        context.application.create_task(
            publish_photo_to_all(context, users, shown, query), update=upd
        )
    elif query.data == "publish":
        await show_photo(query, context, photos[0])


@admin_only
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

    DBManager.unsubscribe_all()
    await update.message.reply_text(UI.admin_all_users_purged_msg)
