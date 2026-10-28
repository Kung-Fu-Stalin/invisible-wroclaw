import asyncio
import io
import itertools
import os
import shutil
import tempfile
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

# The application reads its settings at import time, so the sandbox has to be
# in place before anything from bot/ or utils/ is imported.
SANDBOX = Path(tempfile.mkdtemp(prefix="invisible-wroclaw-tests-"))
os.environ["TELEGRAM_TOKEN"] = "123456:TEST"
os.environ["DATABASE"] = str(SANDBOX / "bot.db")
os.environ["IMAGES_DIR"] = str(SANDBOX / "imgs")
os.environ["ADMINS"] = '["guide", 42]'

from PIL import Image  # noqa: E402
from telegram import (  # noqa: E402
    CallbackQuery,
    Chat,
    InputFile,
    InputMediaPhoto,
    Message,
    Update,
    User,
)
from telegram.error import Forbidden  # noqa: E402

from utils import DBManager, GDrive, IMGManager  # noqa: E402

GUIDE = User(id=1, first_name="Guide", is_bot=False, username="guide")
TOURIST = User(id=7, first_name="Anna", is_bot=False, username="anna")


def jpeg_bytes(size=(32, 24), color="red") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "JPEG")
    return buffer.getvalue()


def photo_name(photo) -> str:
    if isinstance(photo, InputMediaPhoto):
        photo = photo.media
    if isinstance(photo, InputFile):
        return photo.filename
    return Path(getattr(photo, "name", photo)).name


class FakeBot:
    """Stands in for the Telegram Bot API and records what the bot sent."""

    defaults = None

    def __init__(self):
        self.calls = []
        self.blocked_by = set()
        self._message_ids = itertools.count(1000)

    def _record(self, method, chat_id, **details):
        if str(chat_id) in self.blocked_by:
            raise Forbidden("Forbidden: bot was blocked by the user")
        sent = SimpleNamespace(message_id=next(self._message_ids), chat_id=chat_id)
        self.calls.append(
            (method, {"chat_id": chat_id, "sent_id": sent.message_id, **details})
        )
        return sent

    async def send_message(self, chat_id, text, reply_markup=None, **_):
        return self._record("send_message", chat_id, text=text, markup=reply_markup)

    async def send_photo(self, chat_id, photo, reply_markup=None, **_):
        return self._record(
            "send_photo", chat_id, photo=photo_name(photo), markup=reply_markup
        )

    async def edit_message_media(
        self, media, chat_id=None, message_id=None, reply_markup=None, **_
    ):
        return self._record(
            "edit_message_media",
            chat_id,
            message_id=message_id,
            photo=photo_name(media),
            markup=reply_markup,
        )

    async def edit_message_reply_markup(
        self, chat_id=None, message_id=None, reply_markup=None, **_
    ):
        return self._record(
            "edit_message_reply_markup",
            chat_id,
            message_id=message_id,
            markup=reply_markup,
        )

    async def delete_message(self, chat_id, message_id, **_):
        return self._record("delete_message", chat_id, message_id=message_id)

    async def answer_callback_query(self, callback_query_id, **_):
        return True

    def all(self, method):
        return [details for name, details in self.calls if name == method]

    def to(self, chat_id, method):
        return [
            details
            for details in self.all(method)
            if str(details["chat_id"]) == str(chat_id)
        ]

    def texts_to(self, chat_id):
        return [details["text"] for details in self.to(chat_id, "send_message")]

    def photos_to(self, chat_id):
        sent = self.to(chat_id, "send_photo") + self.to(chat_id, "edit_message_media")
        return [details["photo"] for details in sent]


class Chatting:
    """Builds the updates Telegram would deliver for one user's actions."""

    def __init__(self, bot: FakeBot, user: User):
        self.bot = bot
        self.user = user
        self.context = SimpleNamespace(
            bot=bot, user_data={}, application=FakeApplication()
        )
        self._ids = itertools.count(1)

    def _message(self, text=None, message_id=None):
        message = Message(
            message_id=message_id or next(self._ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=self.user.id, type=Chat.PRIVATE),
            from_user=self.user,
            text=text,
        )
        message.set_bot(self.bot)
        return message

    def says(self, text) -> Update:
        return Update(update_id=next(self._ids), message=self._message(text))

    def presses(self, button_data, on_message_id=None) -> Update:
        """A button press on the given message, by default the latest photo."""
        if on_message_id is None:
            sent_photos = self.bot.to(self.user.id, "send_photo")
            on_message_id = sent_photos[-1]["sent_id"] if sent_photos else 500
        query = CallbackQuery(
            id=str(next(self._ids)),
            from_user=self.user,
            chat_instance="chat",
            message=self._message(message_id=on_message_id),
            data=button_data,
        )
        query.set_bot(self.bot)
        return Update(update_id=next(self._ids), callback_query=query)


class FakeApplication:
    def create_task(self, coroutine, update=None, name=None):
        return asyncio.create_task(coroutine, name=name)


async def finish_background_work():
    current = asyncio.current_task()
    while pending := [
        task for task in asyncio.all_tasks() if task is not current and not task.done()
    ]:
        await asyncio.gather(*pending)


@pytest.fixture(autouse=True)
def fresh_bot_state():
    DBManager.clear_all_published_messages()
    DBManager.clear_all()
    for item in IMGManager.path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def guide(bot):
    return Chatting(bot, GUIDE)


@pytest.fixture
def tourist(bot):
    return Chatting(bot, TOURIST)


@pytest.fixture
def photos():
    """Puts photos with the given file names into the bot's photo library."""

    def put(*names):
        for name in names:
            Path(IMGManager.path, name).write_bytes(jpeg_bytes())

    return put


@pytest.fixture
def drive(monkeypatch):
    """Google Drive stand-in serving an archive with `drive.photos` in it."""
    state = SimpleNamespace(
        photos=[],
        error=None,
        downloading=threading.Event(),
        release=threading.Event(),
        downloaded=threading.Event(),
    )
    state.release.set()

    def download_archive(self, download_path):
        state.downloading.set()
        state.release.wait(timeout=2)
        if state.error:
            raise state.error
        archive = Path(download_path, "file-archive.zip")
        with zipfile.ZipFile(archive, "w") as zip_file:
            for name in state.photos:
                zip_file.writestr(f"wroclaw-photo/{name}", jpeg_bytes())
        state.downloaded.set()
        return archive

    monkeypatch.setattr(GDrive, "__init__", lambda self, *args, **kwargs: None)
    monkeypatch.setattr(GDrive, "download_archive", download_archive)
    return state
