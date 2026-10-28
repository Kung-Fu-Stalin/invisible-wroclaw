import asyncio
import gc
import warnings
from pathlib import Path

from conftest import GUIDE, TOURIST, finish_background_work, labels
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

    for button in [
        UI.admin_prev_photo_btn,
        UI.admin_next_photo_btn,
        UI.admin_next_photo_btn,
        UI.admin_next_photo_btn,
    ]:
        await photos_cmd(guide.taps(button), guide.context)

    assert bot.photos_to(GUIDE.id) == ["1.jpg", "3.jpg", "1.jpg", "2.jpg", "3.jpg"]


async def test_published_photo_reaches_every_subscriber(bot, guide, photos):
    photos("1.jpg", "2.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)

    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
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

    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
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
    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
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


NO_PHOTOS = (
    "⚠️ ВНИМАНИЕ! Локально не найдено ни одной фотографии! "
    "Нажмите '🔄 Обновить фотографии'"
)


async def test_guide_is_told_to_refresh_when_library_holds_no_photos(bot, guide):
    Path(IMGManager.path, "notes.txt").write_text("not a photo")

    await start_cmd(guide.says("/start"), guide.context)

    assert bot.texts_to(GUIDE.id)[-1] == NO_PHOTOS


async def test_gallery_button_asks_to_refresh_when_photos_are_gone(bot, guide, photos):
    photos("1.jpg")
    await start_cmd(guide.says("/start"), guide.context)
    Path(IMGManager.path, "1.jpg").unlink()

    await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)

    assert bot.texts_to(GUIDE.id)[-1] == NO_PHOTOS


async def test_photo_removed_from_library_is_not_published(bot, guide, photos):
    photos("1.jpg", "2.jpg", "3.jpg")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_prev_photo_btn), guide.context)
    Path(IMGManager.path, "3.jpg").unlink()

    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
    await finish_background_work()

    assert bot.photos_to(8) == []
    assert bot.photos_to(GUIDE.id)[-1] == "1.jpg"


async def test_each_gallery_publishes_the_photo_it_shows(bot, guide, photos):
    photos("1.jpg", "2.jpg")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    first_gallery = bot.to(GUIDE.id, "send_photo")[-1]["sent_id"]
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)

    await photos_cmd(
        guide.taps(UI.admin_publish_photo_btn, on_message_id=first_gallery),
        guide.context,
    )
    await finish_background_work()

    assert bot.photos_to(8) == ["1.jpg"]


async def test_failed_refresh_keeps_the_current_photos(bot, guide, photos, drive):
    photos("1.jpg", "2.jpg")
    drive.error = ConnectionAbortedError("drive is down")

    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await finish_background_work()

    assert library() == ["1.jpg", "2.jpg"]


async def test_refresh_leaves_only_photos_in_the_library(guide, photos, drive):
    photos("old.jpg")
    drive.photos = ["1.jpg"]

    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await finish_background_work()

    assert [item.name for item in IMGManager.path.iterdir()] == ["1.jpg"]


async def test_tourists_are_served_while_photos_download(bot, guide, tourist, drive):
    drive.photos = ["1.jpg"]
    drive.release.clear()
    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await asyncio.to_thread(drive.downloading.wait, 2)

    await start_cmd(tourist.says("/start"), tourist.context)
    welcomed_during_download = not drive.downloaded.is_set()
    drive.release.set()
    await finish_background_work()

    assert bot.texts_to(TOURIST.id) == [UI.user_welcome_msg]
    assert welcomed_during_download
    assert library() == ["1.jpg"]


async def test_showing_and_publishing_photos_leaves_no_files_open(guide, photos):
    photos("1.jpg", "2.jpg")
    DBManager.add_user(telegram_user_id=8)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        await start_cmd(guide.says("/start"), guide.context)
        await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)
        await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
        await finish_background_work()
        gc.collect()

    assert [str(w.message) for w in caught if w.category is ResourceWarning] == []


GUIDE_PANEL = [
    [UI.admin_refresh_photo_btn, UI.admin_finish_session_btn],
    [UI.admin_control_photo_btn],
    [UI.admin_get_users_list],
]


async def test_guide_gets_the_control_panel_on_start(bot, guide):
    await start_cmd(guide.says("/start"), guide.context)

    assert labels(bot.to(GUIDE.id, "send_message")[0]["markup"]) == GUIDE_PANEL


async def test_panel_is_locked_while_photos_refresh(bot, guide, drive):
    drive.photos = ["1.jpg"]

    await update_cmd(guide.says(UI.admin_refresh_photo_btn), guide.context)
    await finish_background_work()

    keyboards = [m["markup"] for m in bot.to(GUIDE.id, "send_message") if m["markup"]]
    assert labels(keyboards[0]) == [[UI.admin_refresh_photo_placeholder_btn]]
    assert labels(keyboards[-1]) == GUIDE_PANEL


async def test_gallery_restarts_from_the_first_photo_when_its_photo_is_gone(
    bot, guide, photos
):
    photos("1.jpg", "2.jpg", "3.jpg")
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)
    Path(IMGManager.path, "2.jpg").unlink()

    await photos_cmd(guide.taps(UI.admin_next_photo_btn), guide.context)

    assert bot.photos_to(GUIDE.id) == ["1.jpg", "2.jpg", "1.jpg"]


async def test_finishing_the_tour_reaches_everyone_who_did_not_block_the_bot(
    bot, guide, photos
):
    photos("1.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    DBManager.add_user(telegram_user_id=8)
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
    await finish_background_work()
    bot.blocked_by.add("7")

    await purge_cmd(guide.says(UI.admin_finish_session_btn), guide.context)

    assert bot.texts_to(8) == [UI.user_goodbye_msg]
    assert [str(m["chat_id"]) for m in bot.all("delete_message")] == ["8"]
    assert DBManager.get_all_users() == []
    assert bot.texts_to(GUIDE.id)[-1] == UI.admin_all_users_purged_msg


async def test_finishing_a_tour_with_one_tourist_removes_their_photo(
    bot, guide, photos
):
    photos("1.jpg")
    DBManager.add_user(telegram_user_id=7, telegram_user_name="anna")
    await start_cmd(guide.says("/start"), guide.context)
    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
    await finish_background_work()
    published = bot.to(7, "send_photo")[0]["sent_id"]

    await purge_cmd(guide.says(UI.admin_finish_session_btn), guide.context)

    assert [m["message_id"] for m in bot.to(7, "delete_message")] == [published]


async def test_published_photo_is_uploaded_once_for_all_subscribers(bot, guide, photos):
    photos("1.jpg")
    for tourist_id in (7, 8, 9):
        DBManager.add_user(telegram_user_id=tourist_id)
    bot.blocked_by.add("7")
    await start_cmd(guide.says("/start"), guide.context)

    await photos_cmd(guide.taps(UI.admin_publish_photo_btn), guide.context)
    await finish_background_work()

    sent = [bot.to(tourist_id, "send_photo")[0] for tourist_id in (8, 9)]
    assert [s["photo"] for s in sent] == ["1.jpg", "1.jpg"]
    assert [s["uploaded"] for s in sent] == [True, False]
