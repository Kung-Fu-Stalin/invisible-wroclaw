from dataclasses import dataclass
from functools import wraps

from telegram import Update, User
from telegram.ext import ContextTypes

from utils import settings, get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class Admins:
    """Guides allowed to run the tour, listed by Telegram id or username."""

    ids: frozenset[int]
    usernames: frozenset[str]

    @classmethod
    def parse(cls, entries) -> "Admins":
        names = [str(entry).strip().lstrip("@") for entry in entries]
        return cls(
            ids=frozenset(int(name) for name in names if name.isdigit()),
            usernames=frozenset(
                name.lower() for name in names if name and not name.isdigit()
            ),
        )

    def __contains__(self, user: User) -> bool:
        username = (user.username or "").lower()
        return user.id in self.ids or username in self.usernames


ADMINS = Admins.parse(settings.ADMINS)


def admin_only(handler):
    @wraps(handler)
    async def guarded(upd: Update, context: ContextTypes.DEFAULT_TYPE):
        if upd.effective_user in ADMINS:
            return await handler(upd, context)
        logger.warning(
            f"Ignored {handler.__name__} from non-admin #{upd.effective_user.id}"
        )

    return guarded
