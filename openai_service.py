"""Сервіс для роботи з OpenAI API (DALL-E 3)."""

import logging
from typing import Optional

from openai import AsyncOpenAI, APIError, RateLimitError
from config import OPEN_AI_TOKEN

logger = logging.getLogger(__name__)

# Глобальний екземпляр клієнта OpenAI
openai_client: Optional[AsyncOpenAI] = None


def init_openai() -> AsyncOpenAI:
    """Ініціалізує OpenAI клієнт з токеном з конфігурації.
    
    Returns:
        AsyncOpenAI: Ініціалізований клієнт
        
    Raises:
        ValueError: Якщо OPEN_AI_TOKEN не встановлено
    """
    global openai_client
    
    if not OPEN_AI_TOKEN:
        logger.error("OPEN_AI_TOKEN не встановлен в .env файлі")
        raise ValueError("OPEN_AI_TOKEN не встановлен в .env файлі")
    
    openai_client = AsyncOpenAI(api_key=OPEN_AI_TOKEN)
    logger.info("OpenAI клієнт ініціалізований успішно")
    return openai_client


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    style: str = "vivid"
) -> Optional[str]:
    """Генерує зображення через OpenAI DALL-E 3.
    
    Args:
        prompt: Текстовий опис зображення (10-4000 символів)
        size: Розмір зображення (1024x1024, 1792x1024, 1024x1792)
        style: Стиль (vivid або natural)
    
    Returns:
        URL сгенерованого зображення або None при помилці
    """
    global openai_client
    
    if not openai_client:
        try:
            openai_client = init_openai()
        except ValueError:
            logger.error("Не вдалося ініціалізувати OpenAI клієнт")
            return None
    
    try:
        # Валідація довжини промпту
        if len(prompt) < 10:
            logger.warning(f"Промпт занадто короткий ({len(prompt)} символів): {prompt}")
            return None
        
        if len(prompt) > 4000:
            logger.warning(f"Промпт занадто довгий ({len(prompt)} символів), скорочено до 4000")
            prompt = prompt[:4000]
        
        logger.info(f"Запуск генерації зображення: {prompt[:100]}...")
        
        # Виклик OpenAI DALL-E 3 API
        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            style=style,
            n=1
        )
        
        # Отримання URL сгенерованого зображення
        image_url = response.data[0].url
        logger.info(f"Зображення успішно згенеровано: {image_url[:50]}...")
        
        return image_url
        
    except RateLimitError as e:
        logger.warning(f"RateLimitError: Перевищено ліміт запитів. Спробуйте пізніше.")
        return None
        
    except APIError as e:
        logger.exception(f"OpenAI API помилка: {e}")
        return None
        
    except ValueError as e:
        logger.error(f"Помилка валідації: {e}")
        return None
        
    except Exception as e:
        logger.exception(f"Невідома помилка при генерації зображення: {e}")
        return None


async def get_available_sizes() -> list[str]:
    """Повертає доступні розміри для DALL-E 3.
    
    Returns:
        Список доступних розмірів
    """
    return ["1024x1024", "1792x1024", "1024x1792"]


async def get_available_styles() -> list[str]:
    """Повертає доступні стилі для DALL-E 3.
    
    Returns:
        Список доступних стилів
    """
    return ["vivid", "natural"]
