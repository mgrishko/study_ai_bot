"""Тести для Admin обробників."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext
from datetime import datetime

from handlers.admin import (
    command_admin_handler,
    admin_main_callback,
    admin_stats_callback,
    admin_orders_callback,
    admin_products_callback,
    admin_users_callback,
    admin_add_product_start,
    process_product_name,
    process_product_description,
    process_product_price,
    process_product_category,
    process_product_stock,
    process_product_image,
    admin_confirm_order,
    admin_ship_order,
    admin_deliver_order,
    admin_cancel_order,
    AddProductStates,
)


class TestCommandAdminHandler:
    """Тести для команди /admin."""
    
    @pytest.mark.asyncio
    async def test_admin_command_sends_main_menu(self):
        """Тест що команда /admin показує головне меню."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(id=12345)
        message.answer = AsyncMock()
        
        with patch('handlers.admin.get_admin_main_keyboard') as mock_keyboard:
            mock_keyboard.return_value = MagicMock()
            await command_admin_handler(message)
        
        # Має відправити повідомлення з клавіатурою
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "Панель" in call_args[0][0]


class TestAdminMainCallback:
    """Тести для повернення до головного меню."""
    
    @pytest.mark.asyncio
    async def test_admin_main_callback_returns_menu(self):
        """Тест що callback повертає до головного меню."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_main"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.get_admin_main_keyboard') as mock_keyboard:
            mock_keyboard.return_value = MagicMock()
            await admin_main_callback(callback)
        
        # Текст редагується з клавіатурою
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args
        assert "Панель" in call_args[0][0]


class TestAdminStatsCallback:
    """Тести для статистики."""
    
    @pytest.mark.asyncio
    async def test_admin_stats_displays_stats(self):
        """Тест що статистика показує дані."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_stats"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        # Мокуємо БД
        mock_conn = MagicMock()
        mock_conn.fetchval = AsyncMock(side_effect=[100, 25, 50, 5, 5000.0])
        
        # Правильно мокуємо async context manager
        mock_pool_context = MagicMock()
        mock_pool_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('handlers.admin.db.pool') as mock_pool:
            mock_pool.acquire = MagicMock(return_value=mock_pool_context)
            with patch('handlers.admin.get_admin_main_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_stats_callback(callback)
        
        # Текст має містити статистику
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args
        text = call_args[0][0]
        assert "👥" in text  # Користувачі
        assert "📦" in text  # Замовлення
        assert "💰" in text  # Дохід


class TestAdminOrdersCallback:
    """Тести для управління замовленнями."""
    
    @pytest.mark.asyncio
    async def test_admin_orders_shows_menu(self):
        """Тест що показує меню замовлень."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_orders"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.get_admin_orders_keyboard') as mock_keyboard:
            mock_keyboard.return_value = MagicMock()
            await admin_orders_callback(callback)
        
        # Показує меню
        callback.message.edit_text.assert_called_once()


class TestAdminProductsCallback:
    """Тести для управління товарами."""
    
    @pytest.mark.asyncio
    async def test_admin_products_shows_menu(self):
        """Тест що показує меню товарів."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_products"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.get_admin_products_keyboard') as mock_keyboard:
            mock_keyboard.return_value = MagicMock()
            await admin_products_callback(callback)
        
        callback.message.edit_text.assert_called_once()


class TestAdminUsersCallback:
    """Тести для перегляду користувачів."""
    
    @pytest.mark.asyncio
    async def test_admin_users_displays_users(self):
        """Тест що показує список користувачів."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_users"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        mock_users = [
            {
                'id': 123,
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'created_at': '2025-01-01'
            }
        ]
        
        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=mock_users)
        
        # Правильно мокуємо async context manager
        mock_pool_context = MagicMock()
        mock_pool_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool_context.__aexit__ = AsyncMock(return_value=None)
        
        with patch('handlers.admin.db.pool') as mock_pool:
            mock_pool.acquire = MagicMock(return_value=mock_pool_context)
            with patch('handlers.admin.get_admin_main_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_users_callback(callback)
        
        # Текст має містити користувачів
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args
        text = call_args[0][0]
        assert "👥" in text


class TestAdminAddProductStart:
    """Тести для початку додавання товара."""
    
    @pytest.mark.asyncio
    async def test_add_product_sets_state(self):
        """Тест що встановлює FSM стан."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "admin_add_product"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        
        await admin_add_product_start(query, state)
        
        state.set_state.assert_called_once_with(AddProductStates.waiting_for_name)
        query.message.edit_text.assert_called_once()


class TestProcessProductName:
    """Тести для вводу назви товара."""
    
    @pytest.mark.asyncio
    async def test_product_name_valid(self):
        """Тест з валідною назвою."""
        message = MagicMock(spec=Message)
        message.text = "iPhone 14"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        await process_product_name(message, state)
        
        state.update_data.assert_called_once_with(name="iPhone 14")
        state.set_state.assert_called_once_with(AddProductStates.waiting_for_description)
    
    @pytest.mark.asyncio
    async def test_product_name_too_long(self):
        """Тест з назвою довше 255 символів."""
        message = MagicMock(spec=Message)
        message.text = "a" * 256
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        await process_product_name(message, state)
        
        # Не має оновлювати дані
        state.update_data.assert_not_called()
        # Має сказати про помилку
        message.answer.assert_called_once()


class TestProcessProductDescription:
    """Тести для вводу опису товара."""
    
    @pytest.mark.asyncio
    async def test_description_valid(self):
        """Тест з валідним описом."""
        message = MagicMock(spec=Message)
        message.text = "High quality smartphone"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        await process_product_description(message, state)
        
        state.update_data.assert_called_once_with(description="High quality smartphone")
        state.set_state.assert_called_once_with(AddProductStates.waiting_for_price)
    
    @pytest.mark.asyncio
    async def test_description_too_long(self):
        """Тест з описом довше 1000 символів."""
        message = MagicMock(spec=Message)
        message.text = "a" * 1001
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        await process_product_description(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()


class TestProcessProductPrice:
    """Тести для вводу ціни товара."""
    
    @pytest.mark.asyncio
    async def test_price_valid(self):
        """Тест з валідною ціною."""
        message = MagicMock(spec=Message)
        message.text = "2500.50"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        mock_categories = ['Electronics', 'Smartphones']
        
        async def mock_get_categories():
            return mock_categories
        
        with patch('handlers.admin.db.get_categories', side_effect=mock_get_categories):
            with patch('handlers.admin.InlineKeyboardBuilder'):
                await process_product_price(message, state)
        
        state.update_data.assert_called_once_with(price=2500.50)
    
    @pytest.mark.asyncio
    async def test_price_zero_or_negative(self):
        """Тест що ціна не може бути <= 0."""
        message = MagicMock(spec=Message)
        message.text = "0"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        async def mock_get_categories():
            return ['Electronics']
        
        with patch('handlers.admin.db.get_categories', side_effect=mock_get_categories):
            await process_product_price(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_price_too_high(self):
        """Тест що ціна не може бути > 999999."""
        message = MagicMock(spec=Message)
        message.text = "1000000"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        async def mock_get_categories():
            return ['Electronics']
        
        with patch('handlers.admin.db.get_categories', side_effect=mock_get_categories):
            await process_product_price(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_price_invalid_format(self):
        """Тест з невалідним форматом ціни."""
        message = MagicMock(spec=Message)
        message.text = "not a number"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        async def mock_get_categories():
            return ['Electronics']
        
        with patch('handlers.admin.db.get_categories', side_effect=mock_get_categories):
            await process_product_price(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()


class TestProcessProductStock:
    """Тести для вводу кількості товара."""
    
    @pytest.mark.asyncio
    async def test_stock_valid(self):
        """Тест з валідною кількістю."""
        message = MagicMock(spec=Message)
        message.text = "50"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        await process_product_stock(message, state)
        
        state.update_data.assert_called_once_with(stock=50)
        state.set_state.assert_called_once_with(AddProductStates.waiting_for_image_url)
    
    @pytest.mark.asyncio
    async def test_stock_negative(self):
        """Тест що кількість не може бути негативною."""
        message = MagicMock(spec=Message)
        message.text = "-5"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        await process_product_stock(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stock_too_large(self):
        """Тест що кількість не може бути > 100000."""
        message = MagicMock(spec=Message)
        message.text = "100001"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        await process_product_stock(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()


class TestProcessProductImage:
    """Тести для вводу URL зображення."""
    
    @pytest.mark.asyncio
    async def test_image_url_valid(self):
        """Тест з валідним URL."""
        message = MagicMock(spec=Message)
        message.text = "https://example.com/image.png"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={
            'name': 'Product',
            'description': 'Desc',
            'price': 100,
            'category': 'Cat',
            'stock': 10,
            'image_url': 'https://example.com/image.png'
        })
        
        with patch('handlers.admin.InlineKeyboardBuilder'):
            await process_product_image(message, state)
        
        state.update_data.assert_called_once_with(image_url="https://example.com/image.png")
    
    @pytest.mark.asyncio
    async def test_image_url_skip(self):
        """Тест пропуску зображення."""
        message = MagicMock(spec=Message)
        message.text = "skip"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={
            'name': 'Product',
            'description': 'Desc',
            'price': 100,
            'category': 'Cat',
            'stock': 10,
            'image_url': None
        })
        
        with patch('handlers.admin.InlineKeyboardBuilder'):
            await process_product_image(message, state)
        
        state.update_data.assert_called_once_with(image_url=None)
    
    @pytest.mark.asyncio
    async def test_image_url_invalid_protocol(self):
        """Тест з невалідним протоколом."""
        message = MagicMock(spec=Message)
        message.text = "ftp://example.com/image.png"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        
        await process_product_image(message, state)
        
        state.update_data.assert_not_called()
        message.answer.assert_called_once()


class TestOrderStatusUpdates:
    """Тести для оновлення статусу замовлення."""
    
    @pytest.mark.asyncio
    async def test_confirm_order(self):
        """Тест підтвердження замовлення."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_confirm_order:123"
        callback.message = MagicMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.db.update_order_status', return_value=AsyncMock()):
            with patch('handlers.admin.get_order_status_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_confirm_order(callback)
        
        callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ship_order(self):
        """Тест відправки замовлення."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_ship_order:456"
        callback.message = MagicMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.db.update_order_status', return_value=AsyncMock()):
            with patch('handlers.admin.get_order_status_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_ship_order(callback)
        
        callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deliver_order(self):
        """Тест доставки замовлення."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_deliver_order:789"
        callback.message = MagicMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.db.update_order_status', return_value=AsyncMock()):
            with patch('handlers.admin.get_order_status_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_deliver_order(callback)
        
        callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Тест скасування замовлення."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "admin_cancel_order:999"
        callback.message = MagicMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        
        with patch('handlers.admin.db.update_order_status', return_value=AsyncMock()):
            with patch('handlers.admin.get_order_status_keyboard') as mock_keyboard:
                mock_keyboard.return_value = MagicMock()
                await admin_cancel_order(callback)
        
        callback.answer.assert_called_once()
