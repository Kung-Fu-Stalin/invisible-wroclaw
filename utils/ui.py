import json
from dataclasses import dataclass
from pathlib import Path

from utils.config import settings


@dataclass(frozen=True)
class UIStrings:
    """Every text the bot shows; resources/ui.json must define exactly these."""

    admin_refresh_photo_btn: str
    admin_refresh_photo_placeholder_btn: str
    admin_refresh_photo_exception_msg: str
    admin_finish_session_btn: str
    admin_control_photo_btn: str
    admin_get_users_list: str
    google_drive_start_event: str
    google_drive_download_msg: str
    google_drive_archive_msg: str
    google_drive_start_check_images: str
    google_drive_finish_check_images: str
    google_drive_update_msg_template: str
    user_welcome_msg: str
    user_goodbye_msg: str
    admin_all_users_purged_msg: str
    admin_next_photo_btn: str
    admin_prev_photo_btn: str
    admin_publish_photo_btn: str
    admin_publishing_photo: str
    admin_users_list_no_users: str
    admin_users_list_item_template: str
    admin_users_list_stats_template: str
    admin_welcome_msg_template: str
    photos_not_found_msg_template: str


def load_ui(filepath: Path | str) -> UIStrings:
    with open(filepath, "r", encoding="utf-8") as file:
        return UIStrings(**json.load(file))


UI = load_ui(settings.UI)
