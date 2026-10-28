import pytest

from bot import get_users_list_cmd, photos_cmd, purge_cmd, start_cmd, update_cmd
from main import build_application
from utils import UI

PANEL = [
    ("/start", start_cmd),
    (UI.admin_refresh_photo_btn, update_cmd),
    (UI.admin_finish_session_btn, purge_cmd),
    (UI.admin_control_photo_btn, start_cmd),
    (UI.admin_get_users_list, get_users_list_cmd),
]


def command_for(update):
    handlers = build_application("123456:TEST").handlers[0]
    return next(h.callback for h in handlers if h.check_update(update))


@pytest.mark.parametrize("text, command", PANEL)
def test_guide_panel_buttons_reach_their_commands(guide, text, command):
    assert command_for(guide.says(text)) is command


def test_gallery_buttons_reach_the_gallery(guide):
    assert command_for(guide.presses("next")) is photos_cmd
