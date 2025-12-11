"""Конфигурация логирования в стиле Rails."""

import logging
import logging.handlers
import sys
from pathlib import Path

# Создаем директорию для логов если её нет
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Форматирование логов в стиле Rails
CONSOLE_FORMAT = logging.Formatter(
    fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

FILE_FORMAT = logging.Formatter(
    fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def setup_logging(level=logging.INFO):
    """Настраивает логирование для всего приложения."""
    
    # Корневой logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Очищаем существующие handlers
    root_logger.handlers.clear()
    
    # Консольный handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(CONSOLE_FORMAT)
    root_logger.addHandler(console_handler)
    
    # Файловый handler для всех логов
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "bot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(FILE_FORMAT)
    root_logger.addHandler(file_handler)
    
    # Отдельный файл для ошибок
    error_handler = logging.FileHandler(
        LOG_DIR / "errors.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(FILE_FORMAT)
    root_logger.addHandler(error_handler)
    
    # Настройка логеров для конкретных модулей
    setup_module_loggers(level)
    
    return root_logger


def setup_module_loggers(level):
    """Настраивает уровни логирования для конкретных модулей."""
    
    # Loggers для основного приложения
    logging.getLogger("aiogram.requests").setLevel(level)
    logging.getLogger("aiogram.database").setLevel(level)
    logging.getLogger("aiogram.handlers").setLevel(level)
    logging.getLogger("aiogram.middleware").setLevel(level)
    
    # Aiogram library loggers
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiogram.api").setLevel(logging.WARNING)
    
    # Database logger
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    
    # OpenAI logger
    logging.getLogger("openai").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Получить logger для модуля."""
    return logging.getLogger(name)
