from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database import db

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обробник команди /start."""
    await db.add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await message.answer(
        f"👋 Вітаємо, {html.bold(message.from_user.full_name)}!\n\n"
        f"🧥 Ласкаво просимо до нашого магазину верхнього одягу!\n\n"
        f"Тут ви знайдете:\n"
        f"• Куртки\n"
        f"• Пальта\n"
        f"• Плащі\n"
        f"• Вітрівки\n"
        f"• Пуховики\n\n"
        f"Використовуйте команду /help для перегляду всіх доступних команд."
    )


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """Обробник команди /help."""
    help_text = (
        f"📋 {html.bold('Доступні команди:')}\n\n"
        f"/start - Почати роботу з ботом\n"
        f"/help - Показати це повідомлення\n"
        f"/info - Інформація про бота\n"
        f"/catalog - Переглянути каталог товарів з інлайн-кнопками\n"
        f"/order - Оформити замовлення\n"
        f"/categories - Переглянути категорії товарів\n"
        f"/myorders - Переглянути мої замовлення\n\n"
        f"💡 Використовуйте /catalog або /order для перегляду та замовлення товарів!"
    )
    await message.answer(help_text)


@router.message(Command("info"))
async def command_info_handler(message: Message) -> None:
    """Обробник команди /info."""
    info_text = (
        f"ℹ️ {html.bold('Інформація про бота')}\n\n"
        f"🤖 Назва: Магазин верхнього одягу\n"
        f"📦 Версія: 1.0\n"
        f"🛠 Технології: Python 3.14, Aiogram 3.0, PostgreSQL\n\n"
        f"📝 {html.bold('Функціонал:')}\n"
        f"• Перегляд каталогу товарів\n"
        f"• Оформлення замовлень через інлайн-кнопки\n"
        f"• Відстеження статусу замовлень\n"
        f"• Пошук за категоріями\n\n"
        f"📞 {html.bold('Контакти:')}\n"
        f"📧 Email: shop@example.com\n"
        f"📱 Телефон: +380 XX XXX XX XX\n"
        f"🕐 Години роботи: 9:00 - 21:00 (щодня)\n\n"
        f"🚚 Безкоштовна доставка від 1000 грн!"
    )
    await message.answer(info_text)
