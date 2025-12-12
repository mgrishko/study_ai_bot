"""Обробники команд для роботи з AI (генерація зображень).

ПРИМІТКА: Генерація зображень тепер доступна тільки адміністраторам при додаванні товарів.
Публічний доступ до /generate командиції видалено.
"""

from aiogram import Router

from openai_service import generate_image, get_available_sizes, get_available_styles
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


