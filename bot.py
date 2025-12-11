import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import db
from handlers import common_router, user_router, admin_router

# Налаштування логування
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Головна функція для запуску бота."""
    if not BOT_TOKEN:
        logger.error("Помилка: BOT_TOKEN не знайдено в .env файлі!")
        return

    try:
        # Підключення та ініціалізація бази даних
        await db.connect()
        await db.init_db()
        logger.info("База даних ініціалізована успішно!")
    except Exception as e:
        logger.error(f"Помилка при ініціалізації БД: {e}")
        return

    # Ініціалізація бота та диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Реєстрація роутерів
    dp.include_router(common_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # Запуск бота
    logger.info("Бот запущено!")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено")
