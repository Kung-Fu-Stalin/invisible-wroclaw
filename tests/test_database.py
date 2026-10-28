from peewee import SqliteDatabase

from utils.db_manager import DatabaseManager, PublishedMessages, Users


def test_database_of_an_earlier_version_keeps_its_data(tmp_path):
    legacy = SqliteDatabase(tmp_path / "legacy.db")
    legacy.execute_sql(
        "CREATE TABLE users (id INTEGER PRIMARY KEY,"
        " telegram_user_id VARCHAR(255) NOT NULL UNIQUE,"
        " created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    legacy.execute_sql("INSERT INTO users (telegram_user_id) VALUES ('5')")
    legacy.execute_sql(
        "CREATE TABLE published_messages (id INTEGER PRIMARY KEY,"
        " user_id INTEGER NOT NULL, message_id INTEGER NOT NULL,"
        " chat_id INTEGER NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    legacy.execute_sql(
        "INSERT INTO published_messages (user_id, message_id, chat_id) VALUES (1, 77, 5)"
    )

    with legacy.bind_ctx([Users, PublishedMessages]):
        subscribers = DatabaseManager(legacy)
        subscribers.add_user(telegram_user_id=7, telegram_user_name="anna")

        assert subscribers.get_all_users() == [("5", None), ("7", "anna")]
        published = subscribers.get_all_published_messages()
        assert [(m.chat_id, m.message_id) for m in published] == [(5, 77)]
