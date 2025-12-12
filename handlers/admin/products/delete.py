"""Handlers для видалення товарів (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import CallbackQuery

from database import db
from filters import IsAdminFilter
from keyboards import get_admin_products_keyboard
from logger_config import get_logger
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = get_logger("aiogram.handlers")

router = Router()


@router.callback_query(F.data == "admin_delete_products", IsAdminFilter())
async def admin_delete_products_menu(query: CallbackQuery) -> None:
    """Показує список товарів для видалення."""
    logger.info(f"Admin {query.from_user.id} opened product deletion menu")
    
    products = await db.get_all_products()
    
    if not products:
        await query.message.edit_text(
            "❌ Товарів немає.",
            reply_markup=get_admin_products_keyboard()
        )
        await query.answer()
        return
    
    # Показуємо товари для видалення (максимум 15 товарів у одному повідомленні)
    text = f"❌ {html.bold('Виберіть товар для видалення:')}\n\n"
    
    builder = InlineKeyboardBuilder()
    for product in products[:15]:
        builder.button(
            text=f"❌ {product['name']} ({product['stock']} шт) - {float(product['price']):.0f} грн",
            callback_data=f"delete_product:{product['id']}"
        )
    
    builder.button(text="◀️ Назад", callback_data="admin_products")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(F.data.startswith("delete_product:"), IsAdminFilter())
async def confirm_delete_product(query: CallbackQuery) -> None:
    """Подтверждение удаления товара."""
    try:
        product_id = int(query.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await query.message.edit_text(
                "❌ Товар не знайдено.",
                reply_markup=get_admin_products_keyboard()
            )
            await query.answer()
            return
        
        confirmation_text = (
            f"⚠️ {html.bold('ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ')}\n\n"
            f"Товар: {product['name']}\n"
            f"Ціна: {float(product['price']):.2f} грн\n"
            f"Кількість: {product['stock']} шт\n\n"
            f"{html.italic('Ви впевнені що хочете видалити цей товар?')}\n"
            f"{html.italic('Це дійство не можна скасувати!')}"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Так, видалити", callback_data=f"confirm_delete_product:{product_id}")
        builder.button(text="❌ Ні, скасувати", callback_data="admin_delete_products")
        builder.adjust(2)
        
        await query.message.edit_text(confirmation_text, reply_markup=builder.as_markup())
        await query.answer()
    except Exception as e:
        logger.exception(f"Error in delete confirmation: {e}")
        await query.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.callback_query(F.data.startswith("confirm_delete_product:"), IsAdminFilter())
async def execute_delete_product(query: CallbackQuery) -> None:
    """Удаляет товар из БД."""
    try:
        product_id = int(query.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        success = await db.delete_product(product_id)
        
        if success:
            logger.info(f"Admin {query.from_user.id} deleted product: {product['name']} (ID: {product_id})")
            await query.message.edit_text(
                f"✅ Товар '{product['name']}' успішно видалено!",
                reply_markup=get_admin_products_keyboard()
            )
        else:
            await query.message.edit_text(
                "❌ Помилка при видаленні товару.",
                reply_markup=get_admin_products_keyboard()
            )
        
        await query.answer()
    except Exception as e:
        logger.exception(f"Error deleting product: {e}")
        await query.message.edit_text(
            f"❌ Помилка: {str(e)}",
            reply_markup=get_admin_products_keyboard()
        )
        await query.answer()
