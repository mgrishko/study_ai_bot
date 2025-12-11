"""Middleware для логирования запросов (по аналогии с Rails)."""

import logging
import time
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update, User, Message, CallbackQuery

logger = logging.getLogger("aiogram.requests")


class MessageLoggerMiddleware(BaseMiddleware):
    """Логирует входящие сообщения в стиле Rails."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        """Обработка сообщения с логированием."""
        start_time = time.time()
        
        user = event.from_user
        action: str = "unknown"
        details: dict[str, Any] = {}

        # Определяем тип сообщения
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
        
        logger.info(log_msg)

        # Выполняем handler
        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            
            logger.info(
                f"[RESPONSE] {action} {user_info} completed in {duration:.3f}s"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[ERROR] {action} {user_info} failed in {duration:.3f}s: {type(e).__name__}"
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
        """Обработка callback с логированием."""
        start_time = time.time()
        
        user = event.from_user
        callback_data = event.data or "unknown"
        action = f"callback:{callback_data.split(':')[0]}"
        details = {"callback_data": callback_data[:50]}

        # Логируем входящий запрос
        user_info = f"user_id={user.id}"
        details_str = " ".join(f"{k}={v}" for k, v in details.items())
        
        log_msg = f"[REQUEST] {action} {user_info} {details_str}"
        logger.info(log_msg)

        # Выполняем handler
        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            
            logger.info(
                f"[RESPONSE] {action} {user_info} completed in {duration:.3f}s"
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[ERROR] {action} {user_info} failed in {duration:.3f}s: {type(e).__name__}"
            )
            raise
