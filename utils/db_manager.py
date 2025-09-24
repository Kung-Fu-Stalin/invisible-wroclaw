from peewee import (
    SQL,
    Model,
    CharField,
    IntegerField,
    DateTimeField,
    ForeignKeyField,
    SqliteDatabase,
)
from pathlib import Path

from utils.config import settings


db = SqliteDatabase(settings.DATABASE_PATH)


class Users(Model):
    telegram_user_id = CharField(unique=True)
    telegram_user_name = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = db
        table_name = "users"


class PublishedMessages(Model):
    user = ForeignKeyField(Users, backref="messages", on_delete="CASCADE")
    message_id = IntegerField()
    chat_id = IntegerField()
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = db
        table_name = "published_messages"


class DBConnectionContext:
    def __init__(self, database):
        self.db = database

    def __enter__(self):
        if self.db.is_closed():
            self.db.connect()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.db.is_closed():
            self.db.close()


class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.db = db
        self._ensure_database()
        self._ensure_tables()
        self._ensure_columns()

    def _ensure_database(self):
        if not Path(self.db_file):
            self.db.connect()
            self.db.close()

    def _ensure_tables(self):
        with DBConnectionContext(self.db):
            self.db.create_tables([Users, PublishedMessages], safe=True)

    def _ensure_columns(self):
        with DBConnectionContext(self.db):
            columns = [c.name for c in self.db.get_columns("users")]

            required_columns = {"telegram_user_name": "TEXT"}

            for col, col_type in required_columns.items():
                if col not in columns:
                    self.db.execute_sql(
                        f"ALTER TABLE users ADD COLUMN {col} {col_type};"
                    )

    def _get_user(self, telegram_user_id):
        try:
            return Users.get(Users.telegram_user_id == telegram_user_id)
        except Users.DoesNotExist:
            return None

    def transaction(self):
        return self.db.atomic()

    def get_all_users(self):
        users = Users.select()
        users_list = [(u.telegram_user_id, u.telegram_user_name) for u in users]
        return users_list

    def user_exists(self, telegram_user_id):
        return self._get_user(telegram_user_id) is not None

    def add_user(self, telegram_user_id, telegram_user_name=None):
        with self.transaction():
            if self.user_exists(telegram_user_id):
                return None
            return Users.create(
                telegram_user_id=telegram_user_id, telegram_user_name=telegram_user_name
            )

    def delete_user(self, telegram_user_id):
        with self.transaction():
            user = self._get_user(telegram_user_id)
            if not user:
                return 0
            return user.delete_instance(recursive=True)

    def clear_all(self):
        with self.transaction():
            Users.delete().execute()

    def add_published_message(self, telegram_user_id, message_id, chat_id):
        user = self._get_user(telegram_user_id)
        if not user:
            return None
        with self.transaction():
            return PublishedMessages.create(
                user=user, message_id=message_id, chat_id=chat_id
            )

    def get_all_published_messages(self):
        return PublishedMessages.select()

    def clear_all_published_messages(self):
        with self.transaction():
            PublishedMessages.delete().execute()


DBManager = DatabaseManager(settings.DATABASE_PATH)
