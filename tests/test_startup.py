import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from utils.ui import load_ui

PROJECT = Path(__file__).resolve().parent.parent
UI_JSON = PROJECT / "resources" / "ui.json"


def test_ui_texts_with_a_missing_entry_are_rejected_at_startup(tmp_path):
    texts = json.loads(UI_JSON.read_text(encoding="utf-8"))
    del texts["admin_get_users_list"]
    broken = tmp_path / "ui.json"
    broken.write_text(json.dumps(texts), encoding="utf-8")

    with pytest.raises(TypeError, match="admin_get_users_list"):
        load_ui(broken)


def test_bot_without_telegram_token_explains_what_is_missing(tmp_path):
    for item in ["utils", "resources", "settings.yaml"]:
        source = PROJECT / item
        copy = shutil.copytree if source.is_dir() else shutil.copy
        copy(source, tmp_path / item)
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in {"TELEGRAM_TOKEN", "DATABASE", "IMAGES_DIR", "ADMINS"}
    }

    started = subprocess.run(
        [sys.executable, "-c", "import utils"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )

    assert started.returncode != 0
    assert "TELEGRAM_TOKEN is not found" in started.stderr
