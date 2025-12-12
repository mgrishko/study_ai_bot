"""Тести для обробки замовлень з контактною інформацією."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext

from handlers.user import (
    order_product_with_contact_start,
    process_order_phone,
    process_order_email,
    confirm_order_with_contact,
)
from handlers.order_states import OrderStates


class TestOrderProductWithContactStart:
    """Тести для початку замовлення з контактною інформацією."""
    
    @pytest.mark.asyncio
    async def test_order_product_with_contact_start_success(self):
        """Тест успішного початку замовлення."""
        user = MagicMock(spec=User)
        user.id = 123
        user.full_name = "Test User"
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "order_product:1"
        callback.from_user = user
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.update_data = AsyncMock(return_value={})
        state.set_state = AsyncMock()
        
        with patch('handlers.user.db.get_product_by_id') as mock_get_product:
            mock_get_product.return_value = {
                'id': 1,
                'name': 'Test Product',
                'price': 100.00,
                'stock': 10
            }
            
            await order_product_with_contact_start(callback, state)
            
            # Перевіряємо що товар було отримано
            mock_get_product.assert_called_once_with(1)
            
            # Перевіряємо що стан встановлено на waiting_for_phone
            state.set_state.assert_called_once_with(OrderStates.waiting_for_phone)
            
            # Перевіряємо що повідомлення редаговано
            callback.message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_order_product_not_found(self):
        """Тест замовлення неіснуючого товара."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "order_product:999"
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        with patch('handlers.user.db.get_product_by_id') as mock_get_product:
            mock_get_product.return_value = None
            
            await order_product_with_contact_start(callback, state)
            
            # Перевіряємо що показана помилка
            callback.answer.assert_called_once()
            assert "Товар не знайдено" in callback.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_order_product_out_of_stock(self):
        """Тест замовлення товара що закінчився."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "order_product:1"
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        with patch('handlers.user.db.get_product_by_id') as mock_get_product:
            mock_get_product.return_value = {
                'id': 1,
                'name': 'Test Product',
                'price': 100.00,
                'stock': 0
            }
            
            await order_product_with_contact_start(callback, state)
            
            # Перевіряємо що показана помилка про закінчення товара
            callback.answer.assert_called_once()
            assert "закінчився" in callback.answer.call_args[0][0]


class TestProcessOrderPhone:
    """Тести для обробки телефонного номера в замовленні."""
    
    @pytest.mark.asyncio
    async def test_valid_phone_plus_format(self):
        """Тест валідного телефону у форматі +380."""
        message = MagicMock(spec=Message)
        message.text = "+380501234567"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.update_data = AsyncMock(return_value={})
        state.set_state = AsyncMock()
        
        await process_order_phone(message, state)
        
        # Перевіряємо що стан змінено на waiting_for_email
        state.set_state.assert_called_once_with(OrderStates.waiting_for_email)
        
        # Перевіряємо що запрошено email
        message.answer.assert_called_once()
        assert "email" in message.answer.call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_valid_phone_zero_format(self):
        """Тест валідного телефону у форматі 0."""
        message = MagicMock(spec=Message)
        message.text = "0501234567"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.update_data = AsyncMock(return_value={})
        state.set_state = AsyncMock()
        
        await process_order_phone(message, state)
        
        # Перевіряємо що стан змінено на waiting_for_email
        state.set_state.assert_called_once_with(OrderStates.waiting_for_email)
    
    @pytest.mark.asyncio
    async def test_invalid_phone_too_short(self):
        """Тест невалідного телефону (занадто короткий)."""
        message = MagicMock(spec=Message)
        message.text = "123"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await process_order_phone(message, state)
        
        # Перевіряємо що показана помилка
        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_invalid_phone_wrong_format(self):
        """Тест невалідного телефону (неправильний формат)."""
        message = MagicMock(spec=Message)
        message.text = "1234567890"  # Починається з 1
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await process_order_phone(message, state)
        
        # Перевіряємо що показана помилка
        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]


class TestProcessOrderEmail:
    """Тести для обробки email в замовленні."""
    
    @pytest.mark.asyncio
    async def test_valid_email(self):
        """Тест валідного email."""
        message = MagicMock(spec=Message)
        message.text = "user@example.com"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.update_data = AsyncMock(return_value={
            'product_name': 'Test Product',
            'product_price': 100.00,
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'user@example.com'
        })
        state.set_state = AsyncMock()
        
        await process_order_email(message, state)
        
        # Перевіряємо що стан змінено на waiting_for_confirmation
        state.set_state.assert_called_once_with(OrderStates.waiting_for_confirmation)
        
        # Перевіряємо що запрошено підтвердження
        message.answer.assert_called_once()
        assert "Підтвердження" in message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_invalid_email_no_at_symbol(self):
        """Тест невалідного email (без @)."""
        message = MagicMock(spec=Message)
        message.text = "userexample.com"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await process_order_email(message, state)
        
        # Перевіряємо що показана помилка
        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_invalid_email_no_domain(self):
        """Тест невалідного email (без домену)."""
        message = MagicMock(spec=Message)
        message.text = "user@"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        await process_order_email(message, state)
        
        # Перевіряємо що показана помилка
        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]


class TestConfirmOrderWithContact:
    """Тести для підтвердження замовлення з контактною інформацією."""
    
    @pytest.mark.asyncio
    async def test_confirm_order_success(self):
        """Тест успішного підтвердження замовлення."""
        message = MagicMock(spec=Message)
        message.text = "так"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'user_id': 123,
            'user_name': 'Test User',
            'product_id': 1,
            'product_name': 'Test Product',
            'product_price': 100.00,
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'user@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.db.create_order') as mock_create_order:
            mock_create_order.return_value = 42  # Замовлення ID
            
            await confirm_order_with_contact(message, state)
            
            # Перевіряємо що замовлення створено з правильними параметрами
            mock_create_order.assert_called_once_with(
                user_id=123,
                user_name='Test User',
                product_id=1,
                quantity=1,
                phone='+380501234567',
                email='user@example.com'
            )
            
            # Перевіряємо що стан очищено
            state.clear.assert_called_once()
            
            # Перевіряємо що показано підтвердження
            message.answer.assert_called_once()
            assert "Замовлення оформлено" in message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_confirm_order_with_yes(self):
        """Тест підтвердження з 'yes'."""
        message = MagicMock(spec=Message)
        message.text = "yes"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'user_id': 123,
            'user_name': 'Test User',
            'product_id': 1,
            'product_name': 'Test Product',
            'product_price': 100.00,
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'user@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.db.create_order') as mock_create_order:
            mock_create_order.return_value = 42
            
            await confirm_order_with_contact(message, state)
            
            # Перевіряємо що замовлення створено
            mock_create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_order_with_no(self):
        """Тест скасування замовлення з 'ні'."""
        message = MagicMock(spec=Message)
        message.text = "ні"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.clear = AsyncMock()
        
        await confirm_order_with_contact(message, state)
        
        # Перевіряємо що замовлення скасовано
        message.answer.assert_called_once()
        assert "скасовано" in message.answer.call_args[0][0].lower()
        
        # Перевіряємо що стан очищено
        state.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_order_creation_fails(self):
        """Тест коли замовлення не може бути створено."""
        message = MagicMock(spec=Message)
        message.text = "так"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'user_id': 123,
            'user_name': 'Test User',
            'product_id': 1,
            'product_name': 'Test Product',
            'product_price': 100.00,
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'user@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.db.create_order') as mock_create_order:
            mock_create_order.return_value = None  # Помилка при створенні
            
            await confirm_order_with_contact(message, state)
            
            # Перевіряємо що показана помилка
            message.answer.assert_called_once()
            assert "❌" in message.answer.call_args[0][0] or "Помилка" in message.answer.call_args[0][0]
            
            # Перевіряємо що стан очищено
            state.clear.assert_called_once()
