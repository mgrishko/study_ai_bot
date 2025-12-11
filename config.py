from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = getenv("BOT_TOKEN")

# Налаштування бази даних
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = int(getenv("DB_PORT", "5432"))
DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "")
DB_NAME = getenv("DB_NAME", "shop_bot")

# ID адміністраторів (додайте свій Telegram ID)
ADMIN_IDS = [int(id) for id in getenv("ADMIN_IDS", "").split(",") if id]
