from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import (
    get_products_keyboard,
    get_order_keyboard,
    get_product_details_keyboard,
    get_order_confirmation_keyboard,
    get_my_orders_keyboard,
    get_main_menu,
    get_admin_menu
)
from config import ADMIN_IDS

router = Router()


# Обработчики для кнопок меню
@router.message(F.text == "🛍️ Каталог")
async def handle_catalog_button(message: Message) -> None:
    """Обработчик кнопки каталога."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await message.answer(catalog_text, reply_markup=get_products_keyboard(products))


@router.message(F.text == "📦 Мои заказы")
async def handle_my_orders_button(message: Message) -> None:
    """Обработчик кнопки мои заказы."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("У вас ещё нет заказов.")
        return
    
    orders_text = f"📦 {html.bold('Ваши заказы:')}\n\n"
    
    await message.answer(orders_text, reply_markup=get_my_orders_keyboard(orders))


@router.message(F.text == "📚 Категории")
async def handle_categories_button(message: Message) -> None:
    """Обработчик кнопки категории."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Категории не найдены.")
        return
    
    categories_text = f"📚 {html.bold('Категории товаров:')}\n\n"
    categories_list = "\n".join([f"• {cat}" for cat in categories])
    
    await message.answer(f"{categories_text}{categories_list}")


@router.message(F.text == "❓ Помощь")
async def handle_help_button(message: Message) -> None:
    """Обработчик кнопки помощь."""
    help_text = (
        f"📋 {html.bold('Доступные команды:')}\n\n"
        f"/start - Начать заново\n"
        f"/help - Это сообщение\n"
        f"/info - Информация о боте\n"
        f"/catalog - Просмотр каталога\n"
        f"/order - Оформить заказ\n"
        f"/myorders - Мои заказы\n"
        f"/generate - AI генератор изображений\n\n"
        f"💡 Используйте кнопки меню ниже для быстрого доступа!"
    )
    await message.answer(help_text)


@router.message(F.text == "ℹ️ О магазине")
async def handle_info_button(message: Message) -> None:
    """Обработчик кнопки о магазине."""
    info_text = (
        f"ℹ️ {html.bold('Информация о боте')}\n\n"
        f"🤖 Название: Магазин верхнього одягу\n"
        f"📦 Версия: 1.0\n"
        f"🛠 Технологии: Python 3.14, Aiogram 3.0, PostgreSQL\n\n"
        f"📝 {html.bold('Функционал:')}\n"
        f"• Просмотр каталога товаров\n"
        f"• Оформление заказов\n"
        f"• Отслеживание статуса заказов\n"
        f"• Поиск по категориям\n"
        f"• AI генератор изображений\n\n"
        f"📞 {html.bold('Контакты:')}\n"
        f"📧 Email: shop@example.com\n"
        f"📱 Телефон: +380 XX XXX XX XX\n"
        f"🕐 Часы работы: 9:00 - 21:00 (ежедневно)\n\n"
        f"🚚 Бесплатная доставка от 1000 грн!"
    )
    await message.answer(info_text)


@router.message(F.text == "🎨 AI")
async def handle_ai_button(message: Message) -> None:
    """Обработчик кнопки AI генератора."""
    await message.answer(
        "🎨 Для использования AI генератора используйте команду /generate"
    )


@router.message(F.text == "⚙️ Администратор")
async def handle_admin_button(message: Message) -> None:
    """Обработчик кнопки администратор."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к администраторской панели.")
        return
    
    await message.answer(
        "⚙️ Для доступа к администраторской панели используйте команду /admin"
    )


@router.message(Command("catalog"))
async def command_catalog_handler(message: Message) -> None:
    """Обробник команди /catalog."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await message.answer(catalog_text, reply_markup=get_products_keyboard(products))


@router.message(Command("order"))
async def command_order_handler(message: Message) -> None:
    """Обробник команди /order."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    order_text = (
        f"🛒 {html.bold('Оформлення замовлення')}\n\n"
        f"Виберіть товар, який бажаєте замовити:"
    )
    
    await message.answer(order_text, reply_markup=get_order_keyboard(products))


@router.message(Command("categories"))
async def command_categories_handler(message: Message) -> None:
    """Обробник команди /categories."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Наразі немає доступних категорій.")
        return
    
    categories_text = f"📂 {html.bold('Доступні категорії:')}\n\n"
    
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_text += f"🔸 {category} ({products_count} товарів)\n"
    
    await message.answer(categories_text)


@router.message(Command("myorders"))
async def command_my_orders_handler(message: Message) -> None:
    """Обробник команди /myorders."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("📭 У вас ще немає замовлень. Перегляньте /catalog!")
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
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await message.answer(orders_text)


# =============== CALLBACK ОБРОБНИКИ ===============

@router.callback_query(F.data.startswith("product:"))
async def product_details_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду деталей товару."""
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    details_text = (
        f"🔍 {html.bold(product['name'])}\n\n"
        f"📝 Опис: {product['description']}\n"
        f"📂 Категорія: {product['category']}\n"
        f"💰 Ціна: {float(product['price']):.2f} грн\n"
        f"📦 В наявності: {product['stock']} шт.\n"
    )
    
    await callback.message.edit_text(
        details_text, 
        reply_markup=get_product_details_keyboard(product['id'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_product:"))
async def order_product_callback(callback: CallbackQuery) -> None:
    """Обробник callback для оформлення замовлення товару."""
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    if product['stock'] < 1:
        await callback.answer("❌ Товар закінчився на складі", show_alert=True)
        return
    
    order_id = await db.create_order(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        product_id=product_id,
        quantity=1
    )
    
    if order_id:
        confirmation_text = (
            f"✅ {html.bold('Замовлення оформлено!')}\n\n"
            f"📋 Номер замовлення: #{order_id}\n"
            f"🛍 Товар: {product['name']}\n"
            f"💰 Сума: {float(product['price']):.2f} грн\n"
            f"📦 Кількість: 1 шт.\n\n"
            f"Дякуємо за замовлення! Наш менеджер зв'яжеться з вами найближчим часом.\n\n"
            f"Ви можете переглянути свої замовлення командою /myorders"
        )
        
        await callback.message.edit_text(
            confirmation_text, 
            reply_markup=get_order_confirmation_keyboard()
        )
        await callback.answer("🎉 Замовлення успішно оформлено!")
    else:
        await callback.answer("❌ Помилка оформлення замовлення", show_alert=True)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog_callback(callback: CallbackQuery) -> None:
    """Обробник callback для повернення до каталогу."""
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await callback.message.edit_text(
        catalog_text, 
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду замовлень."""
    orders = await db.get_user_orders(callback.from_user.id)
    
    if not orders:
        await callback.message.edit_text("📭 У вас ще немає замовлень. Перегляньте /catalog!")
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
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await callback.message.edit_text(
        orders_text, 
        reply_markup=get_my_orders_keyboard()
    )
    await callback.answer()
