from peewee import (
    SQL,
    Model,
    CharField,
    IntegerField,
    DateTimeField,
    ForeignKeyField,
    SqliteDatabase,
)

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


class DatabaseManager:
    def __init__(self, database: SqliteDatabase):
        self.db = database
        with self.db.connection_context():
            self.db.create_tables([Users, PublishedMessages], safe=True)
            self._add_username_column()

    def _add_username_column(self):
        """Databases created before usernames were stored lack this column."""
        columns = [column.name for column in self.db.get_columns("users")]
        if "telegram_user_name" not in columns:
            self.db.execute_sql("ALTER TABLE users ADD COLUMN telegram_user_name TEXT;")

    def get_all_users(self):
        users = Users.select().order_by(Users.id)
        return [(u.telegram_user_id, u.telegram_user_name) for u in users]

    def add_user(self, telegram_user_id, telegram_user_name=None):
        Users.insert(
            telegram_user_id=telegram_user_id, telegram_user_name=telegram_user_name
        ).on_conflict_ignore().execute()

    def add_published_message(self, telegram_user_id, message_id, chat_id):
        user = Users.get_or_none(Users.telegram_user_id == telegram_user_id)
        if user:
            PublishedMessages.create(user=user, message_id=message_id, chat_id=chat_id)

    def get_all_published_messages(self):
        return PublishedMessages.select()

    def unsubscribe_all(self):
        with self.db.atomic():
            PublishedMessages.delete().execute()
            Users.delete().execute()


DBManager = DatabaseManager(db)
