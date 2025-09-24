from telegram.ext import (
    filters,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler
)

from utils import settings, get_logger
from bot import start_cmd, update_cmd, purge_cmd, button


logger = get_logger(__name__)

def main():
    logger.info("Starting bot...")
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.Text(["🔄 Обновить фотографии"]), update_cmd))
    app.add_handler(MessageHandler(filters.Text(["🚫 Закончить экскурсию"]), purge_cmd))
    app.add_handler(MessageHandler(filters.Text(["🏞️ Контроль изображений"]), start_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == '__main__':
    main()
