"""Middleware для логирования запросов (по аналогии с Rails)."""

import time
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from logger_config import get_logger

logger_requests = get_logger("aiogram.requests")


class MessageLoggerMiddleware(BaseMiddleware):
    """Логирует входящие сообщения в стиле Rails."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        """Обробка повідомлення з логуванням."""
        start_time = time.time()
        
        user = event.from_user
        action: str = "unknown"
        details: dict[str, Any] = {}

        # Визначаємо тип повідомлення
        if event.text:
            if event.text.startswith("/"):
                action = f"command:{event.text.split()[0]}"
            else:
                action = "message"
            details["text"] = event.text[:80]
        elif event.photo:
            action = "photo"
            details["file_id"] = event.photo[-1].file_id[:15]
        elif event.document:
            action = "document"
            details["file_name"] = event.document.file_name
        elif event.contact:
            action = "contact"
        elif event.location:
            action = "location"
        else:
            action = "message"

        # Логируем входящий запрос
        user_info = f"user_id={user.id}"
        details_str = " ".join(f"{k}={v}" for k, v in details.items()) if details else ""
        
        log_msg = f"[REQUEST] {action} {user_info}"
        if details_str:
            log_msg += f" {details_str}"
        
        logger_requests.info(log_msg)

        # Выполняем handler
        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            
            logger_requests.info(
                f"[RESPONSE] {action} {user_info} completed in {duration:.3f}s"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger_requests.error(
                f"[ERROR] {action} {user_info} failed in {duration:.3f}s: {type(e).__name__}",
                exc_info=True
            )
            raise


class CallbackLoggerMiddleware(BaseMiddleware):
    """Логирует callback запросы в стиле Rails."""

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        """Обробка callback з логуванням."""
        start_time = time.time()
        
        user = event.from_user
        callback_data = event.data or "unknown"
        action = f"callback:{callback_data.split(':')[0]}"
        details = {"callback_data": callback_data[:50]}

        # Логируем входящий запрос
        user_info = f"user_id={user.id}"
        details_str = " ".join(f"{k}={v}" for k, v in details.items())
        
        log_msg = f"[REQUEST] {action} {user_info} {details_str}"
        logger_requests.info(log_msg)

        # Выполняем handler
        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            
            logger_requests.info(
                f"[RESPONSE] {action} {user_info} completed in {duration:.3f}s"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger_requests.error(
                f"[ERROR] {action} {user_info} failed in {duration:.3f}s: {type(e).__name__}",
                exc_info=True
            )
            raise
