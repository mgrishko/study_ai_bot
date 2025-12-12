"""Handlers для кнопок меню (користувач)."""
from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import (
    get_main_menu,
    get_admin_menu,
    get_my_orders_keyboard
)
from filters import IsUserFilter, IsUserCallbackFilter
from config import ADMIN_IDS
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.message(F.text == "🛍️ Каталог", IsUserFilter())
async def handle_catalog_button(message: Message) -> None:
    """Обробник кнопки каталога."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    from keyboards import get_products_keyboard
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await message.answer(catalog_text, reply_markup=get_products_keyboard(products))


@router.message(F.text == "📦 Мої замовлення", IsUserFilter())
async def handle_my_orders_button(message: Message) -> None:
    """Обробник кнопки мої замовлення."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("У вас ще немає замовлень.")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}"
            f"\n   Товар: {order['product_name']}"
            f"\n   Кількість: {order['quantity']} шт."
            f"\n   Сума: {float(order['total_price']):.2f} грн"
            f"\n   Статус: {status}"
            f"\n   Дата: {order['created_at']}\n\n"
        )
    
    await message.answer(orders_text, reply_markup=get_my_orders_keyboard())


@router.message(F.text == "📚 Категорії", IsUserFilter())
async def handle_categories_button(message: Message) -> None:
    """Обробник кнопки категорії."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Категорії не знайдені.")
        return
    
    # Отримуємо кількість товарів для кожної категорії
    categories_with_counts = []
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_with_counts.append((category, products_count))
    
    # Сортуємо за кількістю товарів (спадаючи)
    categories_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    from keyboards.inline import get_categories_keyboard
    
    await message.answer(
        "📂 Виберіть категорію:",
        reply_markup=get_categories_keyboard(categories_with_counts)
    )


@router.message(F.text == "❓ Допомога", IsUserFilter())
async def handle_help_button(message: Message) -> None:
    """Обробник кнопки допомога."""
    help_text = (
        f"📋 {html.bold('Доступні команди:')}\n\n"
        f"/start - Почати заново\n"
        f"/help - Це повідомлення\n"
        f"/info - Інформація про бота\n"
        f"/catalog - Перегляд каталогу\n"
        f"/order - Оформити замовлення\n"
        f"/myorders - Мої замовлення\n"
        f"/generate - AI генератор зображень\n\n"
        f"💡 Використовуйте кнопки меню нижче для швидкого доступу!"
    )
    await message.answer(help_text)


@router.message(F.text == "ℹ️ Про магазин", IsUserFilter())
async def handle_about_button(message: Message) -> None:
    """Обробник кнопки про магазин."""
    info_text = (
        f"ℹ️ {html.bold('Інформація про бота')}\n\n"
        f"🤖 Назва: Магазин верхнього одягу\n"
        f"📦 Версія: 1.0\n"
        f"🛠 Технології: Python 3.13, Aiogram 3.0, PostgreSQL\n\n"
        f"📝 {html.bold('Функціонал:')}\n"
        f"• Перегляд каталогу товарів\n"
        f"• Оформлення замовлень\n"
        f"• Відстеження статусу замовлень\n"
        f"• Пошук за категоріями\n"
        f"• AI генератор зображень\n\n"
        f"📞 {html.bold('Контакти:')}\n"
        f"📧 Email: shop@example.com\n"
        f"📱 Телефон: +380 XX XXX XX XX\n"
        f"🕐 Години роботи: 9:00 - 21:00 (щодня)\n\n"
        f"🚚 Безкоштовна доставка від 1000 грн!"
    )
    await message.answer(info_text)


@router.message(F.text == "🎨 AI")
async def handle_ai_button(message: Message) -> None:
    """Обробник кнопки AI генератора."""
    await message.answer(
        "🎨 Для використання AI генератора використовуйте команду /generate"
    )


@router.message(F.text == "⚙️ Адміністратор")
async def handle_admin_button(message: Message) -> None:
    """Обробник кнопки адміністратор."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нема доступу до панелі адміністратора.")
        return
    
    await message.answer(
        "⚙️ Для доступу до панелі адміністратора використовуйте команду /admin"
    )


@router.callback_query(F.data == "back_to_start", IsUserCallbackFilter())
async def back_to_start(callback: CallbackQuery) -> None:
    """Обробник кнопки повернення на початок."""
    is_admin = callback.from_user.id in ADMIN_IDS
    menu = get_admin_menu() if is_admin else get_main_menu()
    
    await callback.message.answer(
        f"👋 Вітаємо, {html.bold(callback.from_user.full_name)}!\n\n"
        f"🧥 Ласкаво просимо до нашого магазину верхнього одягу!",
        reply_markup=menu
    )
    await callback.answer()
