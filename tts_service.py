"""Сервис синтеза речи (Text-to-Speech) с использованием GTTS."""

import io
from typing import Optional
from gtts import gTTS
from aiogram.types import BufferedInputFile
from logger_config import get_logger

logger = get_logger("tts.service")

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "uk": "Українська",
    "ru": "Русский",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
}


async def text_to_speech(text: str, language: str = "uk") -> Optional[BufferedInputFile]:
    """
    Конвертирует текст в речь и возвращает аудиофайл.
    
    Args:
        text: Текст для озвучивания
        language: Код языка (uk, ru, en, de, fr, es)
        
    Returns:
        BufferedInputFile объект с аудиофайлом или None при ошибке
    """
    try:
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {language}, using 'uk'")
            language = "uk"
        
        # Ограничиваем длину текста (Google имеет ограничения)
        if len(text) > 500:
            text = text[:500] + "..."
            logger.info(f"Text truncated to 500 characters")
        
        # Создаем объект gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Сохраняем в BytesIO
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Обертываем в BufferedInputFile для Aiogram
        input_file = BufferedInputFile(audio_buffer.getvalue(), filename="product_info.mp3")
        
        logger.info(f"Audio generated for text (lang={language}, length={len(text)})")
        
        return input_file
        
    except Exception as e:
        logger.error(f"Error generating audio: {type(e).__name__}: {str(e)}")
        return None


def get_product_description_for_tts(product: dict) -> str:
    """
    Подготавливает описание товара для озвучивания.
    
    Args:
        product: Словарь с информацией о товаре
        
    Returns:
        Отформатированный текст для озвучивания
    """
    name = product.get("name", "товар")
    description = product.get("description", "")
    price = product.get("price", 0)
    stock = product.get("stock", 0)
    
    text = f"Товар: {name}. "
    
    if description:
        text += f"Описание: {description}. "
    
    text += f"Цена: {price} гривень. "
    text += f"В наличии: {stock} штук."
    
    return text