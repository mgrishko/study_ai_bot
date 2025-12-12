import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import BOT_TOKEN, LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY, LIQPAY_CALLBACK_URL
from database import db
from handlers import common_router, user_router, admin_router, ai_router, payment_router
from handlers.webhook import handle_liqpay_webhook
from openai_service import init_openai
from middleware import MessageLoggerMiddleware, CallbackLoggerMiddleware
from logger_config import get_logger

logger = get_logger("bot")


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

    # Перевірка LiqPay конфігурації
    if LIQPAY_PUBLIC_KEY and LIQPAY_PRIVATE_KEY:
        logger.info("✅ LiqPay платежі активовані")
        logger.info(f"   Callback URL: {LIQPAY_CALLBACK_URL}")
    else:
        logger.warning("❌ LiqPay платежі: відсутні облікові дані (LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY)")

    # Ініціалізація бота та диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Реєстрація middleware для логирования запросів
    dp.message.middleware(MessageLoggerMiddleware())
    dp.callback_query.middleware(CallbackLoggerMiddleware())

    # Реєстрація роутерів
    dp.include_router(common_router)
    dp.include_router(payment_router)  # Payment handlers (before user handlers)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(ai_router)

    # Запуск бота
    logger.info("Бот запущено!")
    try:
        # Create aiohttp app for webhook
        app = web.Application()
        app.router.add_post('/webhook/liqpay', handle_liqpay_webhook)
        
        # Create runner for the app
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("Webhook сервер запущено на порту 8080")
        
        # Start polling
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено")
