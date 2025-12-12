"""Handlers для товарів (користувач)."""
from aiogram import Router, html, F
from aiogram.types import CallbackQuery

from database import db
from keyboards import get_product_details_keyboard
from keyboards.inline import get_product_details_with_category_keyboard
from filters import IsUserCallbackFilter
from tts_service import text_to_speech, get_product_description_for_tts
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.callback_query(F.data.startswith("listen_product:"), IsUserCallbackFilter())
async def listen_product_callback(callback: CallbackQuery) -> None:
    """Обробник для озвучування опису товару."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return
        
        # Показуємо статус обробки
        await callback.answer("🔊 Генерую аудіофайл...")
        
        # Підготовляємо текст для озвучування
        tts_text = get_product_description_for_tts(product)
        
        # Генеруємо аудіофайл
        audio_buffer = await text_to_speech(tts_text, language="uk")
        
        if audio_buffer:
            # Відправляємо аудіофайл
            await callback.message.answer_voice(
                voice=audio_buffer,
                caption=f"🔊 Інформація про товар '{product['name']}'"
            )
            logger.info(f"Product audio sent for product_id={product_id}")
        else:
            await callback.message.answer(
                "❌ Помилка при генерації аудіо. Спробуйте пізніше."
            )
        
    except Exception as e:
        logger.error(f"Error in listen_product_callback: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.callback_query(F.data.startswith("product:"), IsUserCallbackFilter())
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


@router.callback_query(F.data.startswith("product_cat:"), IsUserCallbackFilter())
async def product_details_with_category_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду деталей товару з контекстом категорії."""
    # Парсимо: product_cat:{product_id}:{category}
    parts = callback.data.split(":", 2)
    product_id = int(parts[1])
    category_name = parts[2] if len(parts) > 2 else None
    
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
    
    # Використовуємо спеціальну клавіатуру з контекстом категорії якщо вона є
    if category_name:
        keyboard = get_product_details_with_category_keyboard(product['id'], category_name)
    else:
        keyboard = get_product_details_keyboard(product['id'])
    
    await callback.message.edit_text(
        details_text, 
        reply_markup=keyboard
    )
    await callback.answer()
