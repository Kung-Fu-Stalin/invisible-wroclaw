from conftest import GUIDE, TOURIST, finish_background_work
from telegram import User

from bot import get_users_list_cmd, photos_cmd, purge_cmd, start_cmd, update_cmd
from bot.keyboard import get_photo_selector_control
from utils import UI, DBManager, IMGManager


async def test_tourist_who_starts_the_bot_is_subscribed(bot, tourist):
    await start_cmd(tourist.says("/start"), tourist.context)

    assert bot.texts_to(TOURIST.id) == [UI.user_welcome_msg]
    assert DBManager.get_all_users() == [("7", "anna")]


async def test_tourist_without_username_is_subscribed_by_id(bot, tourist):
    tourist.user = User(id=8, first_name="Nobody", is_bot=False)

    await start_cmd(tourist.says("/start"), tourist.context)

    assert bot.texts_to(8) == [UI.user_welcome_msg]
    assert DBManager.get_all_users() == [("8", None)]


async def test_starting_twice_keeps_one_subscription(tourist):
    await start_cmd(tourist.says("/start"), tourist.context)
    await start_cmd(tourist.says("/start"), tourist.context)

    assert DBManager.get_all_users() == [("7", "anna")]


async def test_guide_is_welcomed_and_sees_the_first_photo(bot, guide, photos):
    photos("10.jpg", "2.jpg", "1.jpg")

    await start_cmd(guide.says("/start"), guide.context)

    assert bot.texts_to(GUIDE.id) == ["🏠 Админ @guide вход выполнен"]
    assert bot.photos_to(GUIDE.id) == ["1.jpg"]
    assert DBManager.get_all_users() == []


async def test_guide_without_username_is_welcomed_by_name(bot, guide):
    guide.user = User(id=42, first_name="Olga", is_bot=False)

    await start_cmd(guide.says("/start"), guide.context)

    assert bot.texts_to(42)[0] == "🏠 Админ Olga вход выполнен"


async def test_guide_is_told_to_refresh_when_library_is_empty(bot, guide):
    await start_cmd(guide.says("/start"), guide.context)

    assert bot.texts_to(GUIDE.id)[-1] == (
        "⚠️ ВНИМАНИЕ! Локально не найдено ни одной фотографии! "
        "Нажмите '🔄 Обновить фотографии'"
    )
    assert bot.photos_to(GUIDE.id) == []


async def test_gallery_buttons_cycle_through_photos(bot, guide, photos):
    photos("1.jpg", "2.jpg", "3.jpg")
    await start_cmd(guide.says("/start"), guide.context)

    for button in ["prev", "next", "next", "next"]:
        await photos_cmd(guide.presses(button), guide.context)

    assert bot.photos_to(GUIDE.id) == ["1.jpg", "3.jpg", "1.jpg", "2.jpg", "3.jpg"]


async def test_published_photo_reaches_every_subscriber(bot, guide, photos):
    photos("1.jpg", "2.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.presses("next"), guide.context)

    await photos_cmd(guide.presses("publish"), guide.context)
    await finish_background_work()

    assert bot.photos_to(7) == ["2.jpg"]
    assert bot.photos_to(8) == ["2.jpg"]
    assert len(DBManager.get_all_published_messages()) == 2
    restored = bot.to(GUIDE.id, "edit_message_reply_markup")[-1]["markup"]
    assert restored == get_photo_selector_control()


async def test_subscriber_who_blocked_the_bot_does_not_stop_publishing(
    bot, guide, photos
):
    photos("1.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)
    bot.blocked_by.add("7")
    await start_cmd(guide.says("/start"), guide.context)

    await photos_cmd(guide.presses("publish"), guide.context)
    await finish_background_work()

    assert bot.photos_to(8) == ["1.jpg"]


async def test_guide_sees_the_list_of_subscribers(bot, guide):
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)

    await get_users_list_cmd(guide.says(UI.admin_get_users_list), guide.context)

    assert bot.texts_to(GUIDE.id) == [
        "✅ Пользователь: @anna (ID: 7) подписан.\n"
        "✅ Пользователь: NoUsername (ID: 8) подписан.\n"
        "📈 Всего: 2 подписчик(ов)"
    ]


async def test_guide_is_told_when_nobody_is_subscribed(bot, guide):
    await get_users_list_cmd(guide.says(UI.admin_get_users_list), guide.context)

    assert bot.texts_to(GUIDE.id) == [UI.admin_users_list_no_users]


async def test_finishing_the_tour_cleans_up_and_unsubscribes_everyone(
    bot, guide, photos
):
    photos("1.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.presses("publish"), guide.context)
    await finish_background_work()
    to_subscribers = bot.to(7, "send_photo") + bot.to(8, "send_photo")
    published = {(str(m["chat_id"]), m["sent_id"]) for m in to_subscribers}

    await purge_cmd(guide.says(UI.admin_finish_session_btn), guide.context)

    assert bot.texts_to(7) == [UI.user_goodbye_msg]
    assert bot.texts_to(8) == [UI.user_goodbye_msg]
    deleted = {(str(m["chat_id"]), m["message_id"]) for m in bot.all("delete_message")}
    assert deleted == published
    assert DBManager.get_all_users() == []
    assert len(DBManager.get_all_published_messages()) == 0
    assert bot.texts_to(GUIDE.id)[-1] == UI.admin_all_users_purged_msg


async def test_refresh_replaces_the_library_with_the_drive_archive(
    bot, guide, photos, drive
):
    photos("old.jpg")
    drive.photos = ["1.jpg", "2.jpg"]

    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await finish_background_work()

    assert library() == ["1.jpg", "2.jpg"]
    assert bot.texts_to(GUIDE.id) == [
        UI.google_drive_start_event,
        UI.google_drive_download_msg,
        UI.google_drive_archive_msg,
        UI.google_drive_start_check_images,
        UI.google_drive_finish_check_images,
        "🆕 Обновление завершено. Всего: 2 изображений. "
        "Нажмите '🏞️ Выбор изображений'",
    ]


async def test_guide_is_told_when_refresh_fails(bot, guide, drive):
    drive.error = ConnectionAbortedError("drive is down")

    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await finish_background_work()

    assert bot.texts_to(GUIDE.id)[-1] == UI.admin_refresh_photo_exception_msg


def library():
    return [path.rsplit("/", 1)[-1] for path in IMGManager.get_files_paths()]
