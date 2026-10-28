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


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    panel = {
        UI.admin_refresh_photo_btn: update_cmd,
        UI.admin_finish_session_btn: purge_cmd,
        UI.admin_control_photo_btn: start_cmd,
        UI.admin_get_users_list: get_users_list_cmd,
    }
    for button, command in panel.items():
        app.add_handler(MessageHandler(filters.Text([button]), command))
    app.add_handler(CallbackQueryHandler(photos_cmd))
    return app


def main():
    logger.info("Starting bot...")
    app = build_application(settings.TELEGRAM_TOKEN)
    logger.info("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()
