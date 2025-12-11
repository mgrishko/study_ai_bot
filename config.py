import sys
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = getenv("BOT_TOKEN")

# OpenAI API Token
OPEN_AI_TOKEN = getenv("OPEN_AI_TOKEN", "")

# Налаштування бази даних (розробка)
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = int(getenv("DB_PORT", "5432"))
DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "")
DB_NAME = getenv("DB_NAME", "shop_bot")

# Налаштування тестової бази даних
TEST_DB_HOST = getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = int(getenv("TEST_DB_PORT", "5432"))
TEST_DB_USER = getenv("TEST_DB_USER", "test_shop_bot_user")
TEST_DB_PASSWORD = getenv("TEST_DB_PASSWORD", "")
TEST_DB_NAME = getenv("TEST_DB_NAME", "test_shop_bot")

# ID адміністраторів (додайте свій Telegram ID)
ADMIN_IDS = [int(id) for id in getenv("ADMIN_IDS", "").split(",") if id]

# Перевірка, чи запускаються тести
IS_TESTING = "pytest" in sys.modules or "test" in sys.argv[0] or "conftest" in sys.argv[0]


def get_db_config():
    """Повертає конфігурацію БД залежно від середовища"""
    if IS_TESTING:
        return {
            "host": TEST_DB_HOST,
            "port": TEST_DB_PORT,
            "user": TEST_DB_USER,
            "password": TEST_DB_PASSWORD,
            "database": TEST_DB_NAME,
        }
    else:
        return {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME,
        }
