"""Handlers для каталогу та категорій (користувач)."""
from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from keyboards import (
    get_products_keyboard,
    get_order_keyboard
)
from keyboards.inline import (
    get_categories_keyboard,
    get_products_by_category_keyboard
)
from filters import IsUserFilter, IsUserCallbackFilter
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.message(Command("catalog"), IsUserFilter())
async def command_catalog_handler(message: Message) -> None:
    """Обробник команди /catalog."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    # Показуємо меню вибору: всі товари або по категоріях
    catalog_menu_text = (
        f"🛍 {html.bold('Каталог товарів')}\n\n"
        f"Як ви хочете переглядати товари?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 За категоріями", callback_data="choose_categories")
    builder.button(text="📦 Всі товари", callback_data="all_products")
    builder.adjust(1)
    
    await message.answer(catalog_menu_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "choose_categories", IsUserCallbackFilter())
async def choose_categories_callback(callback: CallbackQuery) -> None:
    """Обробник для вибору перегляду за категоріями."""
    categories = await db.get_categories()
    
    if not categories:
        await callback.answer("😔 Наразі немає доступних категорій", show_alert=True)
        return
    
    # Отримуємо кількість товарів для кожної категорії
    categories_with_counts = []
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_with_counts.append((category, products_count))
    
    # Сортуємо за кількістю товарів (спадаючи)
    categories_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    await callback.message.edit_text(
        "📂 Виберіть категорію:",
        reply_markup=get_categories_keyboard(categories_with_counts)
    )
    await callback.answer()


@router.message(Command("categories"), IsUserFilter())
async def command_categories_handler(message: Message) -> None:
    """Обробник команди /categories."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Наразі немає доступних категорій.")
        return
    
    # Отримуємо кількість товарів для кожної категорії
    categories_with_counts = []
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_with_counts.append((category, products_count))
    
    # Сортуємо за кількістю товарів (спадаючи)
    categories_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    await message.answer(
        "📂 Виберіть категорію:",
        reply_markup=get_categories_keyboard(categories_with_counts)
    )


@router.message(Command("order"), IsUserFilter())
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


@router.callback_query(F.data.startswith("category:"), IsUserCallbackFilter())
async def category_selected_callback(callback: CallbackQuery) -> None:
    """Обробник для вибору категорії."""
    category_name = callback.data.split(":", 1)[1]
    
    products = await db.get_products_by_category(category_name)
    
    if not products:
        await callback.answer("😔 У цій категорії немає товарів", show_alert=True)
        return
    
    category_text = (
        f"📂 {html.bold(category_name)}\n\n"
        f"Доступно товарів: {len(products)}\n\n"
        f"Виберіть товар:"
    )
    
    await callback.message.edit_text(
        category_text,
        reply_markup=get_products_by_category_keyboard(products, category_name)
    )
    await callback.answer()


@router.callback_query(F.data == "all_products", IsUserCallbackFilter())
async def all_products_callback(callback: CallbackQuery) -> None:
    """Обробник для показу всіх товарів."""
    products = await db.get_all_products()
    
    if not products:
        await callback.answer("😔 На жаль, немає товарів", show_alert=True)
        return
    
    catalog_text = (
        f"🛍 {html.bold('Всі товари')}\n\n"
        f"Доступно товарів: {len(products)}\n\n"
        f"Виберіть товар:"
    )
    
    await callback.message.edit_text(
        catalog_text,
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_catalog", IsUserCallbackFilter())
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


@router.callback_query(F.data == "back_to_categories", IsUserCallbackFilter())
async def back_to_categories_callback(callback: CallbackQuery) -> None:
    """Обробник для повернення до списку категорій."""
    categories = await db.get_categories()
    
    if not categories:
        await callback.message.edit_text("😔 Наразі немає доступних категорій.")
        return
    
    # Отримуємо кількість товарів для кожної категорії
    categories_with_counts = []
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_with_counts.append((category, products_count))
    
    # Сортуємо за кількістю товарів (спадаючи)
    categories_with_counts.sort(key=lambda x: x[1], reverse=True)
    
    await callback.message.edit_text(
        "📂 Виберіть категорію:",
        reply_markup=get_categories_keyboard(categories_with_counts)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_category:"), IsUserCallbackFilter())
async def back_to_category_callback(callback: CallbackQuery) -> None:
    """Обробник для повернення до товарів категорії."""
    category_name = callback.data.split(":", 1)[1]
    
    products = await db.get_products_by_category(category_name)
    
    if not products:
        await callback.answer("😔 У цій категорії немає товарів", show_alert=True)
        return
    
    category_text = (
        f"📂 {html.bold(category_name)}\n\n"
        f"Доступно товарів: {len(products)}\n\n"
        f"Виберіть товар:"
    )
    
    await callback.message.edit_text(
        category_text,
        reply_markup=get_products_by_category_keyboard(products, category_name)
    )
    await callback.answer()
