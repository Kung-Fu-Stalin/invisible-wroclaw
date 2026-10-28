import pytest
from conftest import finish_background_work
from telegram import User

from bot import get_users_list_cmd, photos_cmd, purge_cmd, start_cmd, update_cmd
from bot.auth import Admins
from utils import UI, DBManager, IMGManager

GUIDE_BUTTONS = [
    (purge_cmd, UI.admin_finish_session_btn),
    (update_cmd, UI.admin_refresh_photo_btn),
    (get_users_list_cmd, UI.admin_get_users_list),
]


@pytest.mark.parametrize("command, button", GUIDE_BUTTONS)
async def test_tourist_typing_a_guide_button_changes_nothing(
    bot, tourist, photos, drive, command, button
):
    photos("1.jpg")
    drive.photos = ["2.jpg"]
    DBManager.add_user(telegram_user_id=8)

    await command(tourist.says(button), tourist.context)
    await finish_background_work()

    assert bot.calls == []
    assert DBManager.get_all_users() == [("8", None)]
    assert len(IMGManager.get_files_paths()) == 1


@pytest.mark.parametrize("button", ["prev", "next", "publish"])
async def test_tourist_pressing_a_gallery_button_changes_nothing(
    bot, tourist, photos, button
):
    photos("1.jpg", "2.jpg")
    DBManager.add_user(telegram_user_id=8)

    await photos_cmd(tourist.presses(button), tourist.context)
    await finish_background_work()

    assert bot.photos_to(8) == []
    assert bot.photos_to(tourist.user.id) == []


async def test_guide_username_is_matched_regardless_of_case(bot, guide):
    guide.user = User(id=3, first_name="Guide", is_bot=False, username="GUIDE")

    await start_cmd(guide.says("/start"), guide.context)

    assert DBManager.get_all_users() == []


def test_guides_are_listed_by_id_or_username():
    admins = Admins.parse([42, "1001", "@Boss", "guide", ""])

    assert User(id=42, first_name="A", is_bot=False) in admins
    assert User(id=1001, first_name="B", is_bot=False) in admins
    assert User(id=5, first_name="C", is_bot=False, username="boss") in admins
    assert User(id=6, first_name="D", is_bot=False, username="Guide") in admins
    assert User(id=7, first_name="E", is_bot=False) not in admins
    assert User(id=8, first_name="F", is_bot=False, username="tourist") not in admins
