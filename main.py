from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from utils import settings, get_logger
from bot import start, update, button


logger = get_logger(__name__)

def main():
    logger.info("Starting bot...")
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", update))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == '__main__':
    main()
