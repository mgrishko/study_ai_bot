import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import db
from handlers import common_router, user_router, admin_router, ai_router
from openai_service import init_openai
from middleware import MessageLoggerMiddleware, CallbackLoggerMiddleware

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

    # Ініціалізація OpenAI
    try:
        init_openai()
        logger.info("OpenAI клієнт ініціалізовано успішно!")
    except Exception as e:
        logger.warning(f"Помилка при ініціалізації OpenAI: {e}")
        logger.warning("Команда /generate буде недоступна")

    # Ініціалізація бота та диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Реєстрація middleware для логирования запросов
    dp.message.middleware(MessageLoggerMiddleware())
    dp.callback_query.middleware(CallbackLoggerMiddleware())

    # Реєстрація роутерів
    dp.include_router(common_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(ai_router)

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
