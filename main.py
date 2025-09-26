from telegram.ext import (
    filters,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
)

from utils import settings, get_logger, UI
from bot import start_cmd, update_cmd, purge_cmd, photos_cmd, get_users_list_cmd


logger = get_logger(__name__)


def main():
    logger.info("Starting bot...")
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(
        MessageHandler(filters.Text([UI.admin_refresh_photo_btn]), update_cmd)
    )
    app.add_handler(
        MessageHandler(filters.Text([UI.admin_finish_session_btn]), purge_cmd)
    )
    app.add_handler(
        MessageHandler(filters.Text([UI.admin_control_photo_btn]), start_cmd)
    )
    app.add_handler(
        MessageHandler(filters.Text([UI.admin_get_users_list]), get_users_list_cmd)
    )
    app.add_handler(CallbackQueryHandler(photos_cmd))
    logger.info("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()
