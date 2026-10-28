from peewee import SqliteDatabase

from utils.db_manager import DatabaseManager, PublishedMessages, Users


def test_database_from_before_usernames_gets_the_username_column(tmp_path):
    legacy = SqliteDatabase(tmp_path / "legacy.db")
    legacy.execute_sql(
        "CREATE TABLE users (id INTEGER PRIMARY KEY,"
        " telegram_user_id VARCHAR(255) NOT NULL UNIQUE,"
        " created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    legacy.execute_sql("INSERT INTO users (telegram_user_id) VALUES ('5')")

    with legacy.bind_ctx([Users, PublishedMessages]):
        subscribers = DatabaseManager(legacy)
        subscribers.add_user(telegram_user_id=7, telegram_user_name="anna")

        assert subscribers.get_all_users() == [("5", None), ("7", "anna")]
