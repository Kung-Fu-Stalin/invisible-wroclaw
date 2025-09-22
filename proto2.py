import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, \
    ContextTypes

TOKEN = "8456946544:AAGn_QxHd9QV0uasnRq94ybRH-d33kqxlYA"
ADMINS = [39892599]
PHOTOS_DIR = Path("./imgs")
USERS_FILE = Path("users.json")

def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users), f)

USERS = load_users()

# ---------------- Индекс текущего фото для админов ----------------
current_index = {}

# ---------------- Кнопки ----------------
def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev"),
            InlineKeyboardButton("➡️ Следующее", callback_data="next")
        ],
        [InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------------- /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # сохраняем пользователя (только если не админ)
    if user_id not in USERS and user_id not in ADMINS:
        USERS.add(user_id)
        save_users(USERS)

    if user_id in ADMINS:
        current_index[user_id] = 0
        await send_current_photo(update, context)
    else:
        await update.message.reply_text("Привет! Ты подписан на публикации.")

# ---------------- Отправка текущего фото ----------------
async def send_current_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photos = list(PHOTOS_DIR.glob("*.jpg"))
    if not photos:
        await update.message.reply_text("Нет доступных фото")
        return

    idx = current_index[user_id]
    if idx >= len(photos):
        # Все фото показаны
        if update.message:
            await update.message.reply_text("Все фото опубликованы!")
        else:
            await update.callback_query.edit_message_caption(caption="Все фото опубликованы!")
        return

    photo_path = photos[idx]

    # проверяем, что вызов из /start или из callback
    if update.message:
        await update.message.reply_photo(
            photo=open(photo_path, "rb"),
            caption=f"{idx+1}/{len(photos)}: {photo_path.name}",
            reply_markup=get_keyboard()
        )
    else:
        query = update.callback_query
        await context.bot.edit_message_media(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            media=InputMediaPhoto(open(photo_path, "rb"), caption=f"{idx+1}/{len(photos)}: {photo_path.name}"),
            reply_markup=get_keyboard()
        )

# ---------------- Обработка кнопок ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    photos = list(PHOTOS_DIR.glob("*.jpg"))
    if not photos:
        await query.edit_message_caption(caption="Нет доступных фото")
        return

    idx = current_index.get(user_id, 0)

    if query.data == "next":
        idx = (idx + 1) % len(photos)
        current_index[user_id] = idx
        await send_current_photo(update, context)

    elif query.data == "prev":
        idx = (idx - 1) % len(photos)
        current_index[user_id] = idx
        await send_current_photo(update, context)

    elif query.data == "publish":
        photo_path = photos[idx]
        sent = 0
        failed = 0
        for uid in USERS:
            try:
                with open(photo_path, "rb") as img:
                    await context.bot.send_photo(chat_id=uid, photo=img, caption=f"Публикация: {photo_path.name}")
                sent += 1
            except Exception:
                failed += 1
        # увеличиваем индекс на 1 и показываем следующее фото
        current_index[user_id] = idx + 1
        await send_current_photo(update, context)

# ---------------- Запуск ----------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
