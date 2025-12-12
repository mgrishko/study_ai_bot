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
    """Тести для початку замовлення з контактною інформацією (Real DB)."""
    
    @pytest.mark.asyncio
    async def test_order_product_with_contact_start_success(self, test_products, db_clean):
        """Тест успішного початку замовлення з реальною БД."""
        # Отримуємо перший товар від fixture
        product = test_products[0]
        
        user = MagicMock(spec=User)
        user.id = 123
        user.full_name = "Test User"
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = f"order_product:{product['id']}"
        callback.from_user = user
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.update_data = AsyncMock(return_value={})
        state.set_state = AsyncMock()
        
        # Замінюємо db на реальний від fixture
        with patch('handlers.user.orders.db', db_clean):
            await order_product_with_contact_start(callback, state)
            
            # Перевіряємо що стан встановлено на waiting_for_phone
            state.set_state.assert_called_once_with(OrderStates.waiting_for_phone)
            
            # Перевіряємо що повідомлення редаговано
            callback.message.edit_text.assert_called_once()
            
            # Перевіряємо що дані оновлені з реального товару
            update_call = state.update_data.call_args[1]
            assert update_call['product_id'] == product['id']
            assert update_call['product_name'] == product['name']
    
    @pytest.mark.asyncio
    async def test_order_product_not_found(self, db_clean):
        """Тест замовлення неіснуючого товара."""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "order_product:99999"
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        with patch('handlers.user.orders.db', db_clean):
            await order_product_with_contact_start(callback, state)
            
            # Перевіряємо що показана помилка
            callback.answer.assert_called_once()
            assert "Товар не знайдено" in callback.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_order_product_out_of_stock(self, db_clean, product_factory):
        """Тест замовлення товара що закінчився (реальна БД)."""
        # Використовуємо factory для товару без запасу
        product = await product_factory.create(
            name="Out of Stock Product",
            description="This product is out of stock",
            price=99.99,
            category="Test",
            stock=0
        )
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = f"order_product:{product['id']}"
        callback.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        
        with patch('handlers.user.orders.db', db_clean):
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
    async def test_confirm_order_success(self, test_products, db_clean):
        """Тест успішного підтвердження замовлення."""
        # Отримуємо реальний товар від fixture
        product = test_products[0]
        
        message = MagicMock(spec=Message)
        message.text = "так"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'user_id': 123,
            'user_name': 'Test User',
            'product_id': product['id'],
            'product_name': product['name'],
            'product_price': product['price'],
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'user@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.orders.db', db_clean):
            await confirm_order_with_contact(message, state)
            
            # Перевіряємо що замовлення створено в реальній БД
            orders = await db_clean.get_user_orders(123)
            assert len(orders) > 0
            assert orders[0]['product_id'] == product['id']
            assert orders[0]['phone'] == '+380501234567'
            assert orders[0]['email'] == 'user@example.com'
            
            # Перевіряємо що стан оновлено (не очищено, оскільки переходимо до оплати)
            state.update_data.assert_called_once()
            state.set_state.assert_called_once()
            state.clear.assert_not_called()
            
            # Перевіряємо що показано підтвердження
            message.answer.assert_called_once()
            assert "Замовлення оформлено" in message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_confirm_order_with_yes(self, test_products, db_clean):
        """Тест підтвердження з 'yes'."""
        # Отримуємо реальний товар
        product = test_products[0]
        
        message = MagicMock(spec=Message)
        message.text = "yes"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'user_id': 124,
            'user_name': 'Test User 2',
            'product_id': product['id'],
            'product_name': product['name'],
            'product_price': product['price'],
            'quantity': 2,
            'phone': '+380501234568',
            'email': 'user2@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.orders.db', db_clean):
            await confirm_order_with_contact(message, state)
            
            # Перевіряємо що замовлення створено в реальній БД
            orders = await db_clean.get_user_orders(124)
            assert len(orders) > 0
            assert orders[0]['product_id'] == product['id']
            assert orders[0]['quantity'] == 2
    
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
    async def test_order_creation_fails(self, test_products, db_clean):
        """Тест коли замовлення не може бути створено (недостатньо товару)."""
        # Отримуємо реальний товар з малим запасом
        product = test_products[0]
        
        message = MagicMock(spec=Message)
        message.text = "так"
        message.answer = AsyncMock()
        
        state = AsyncMock(spec=FSMContext)
        # Спробуємо замовити більше ніж є в наявності
        large_quantity = product['stock'] + 100
        state.get_data = AsyncMock(return_value={
            'user_id': 125,
            'user_name': 'Test User 3',
            'product_id': product['id'],
            'product_name': product['name'],
            'product_price': product['price'],
            'quantity': large_quantity,
            'phone': '+380501234569',
            'email': 'user3@example.com'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.user.orders.db', db_clean):
            await confirm_order_with_contact(message, state)
            
            # Замовлення не повинно бути створено через недостатність товару
            # Перевіряємо що показана помилка
            message.answer.assert_called_once()
            call_text = message.answer.call_args[0][0]
            assert "❌" in call_text or "Помилка" in call_text or "Недостатньо" in call_text
