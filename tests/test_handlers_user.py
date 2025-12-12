"""Comprehensive tests for handlers/user.py - menu buttons, commands, and callbacks."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram import html

from handlers.user import (
    handle_catalog_button,
    handle_my_orders_button,
    handle_categories_button,
    handle_help_button,
    handle_about_button,
    handle_ai_button,
    handle_admin_button,
    command_catalog_handler,
    command_order_handler,
    command_categories_handler,
    command_my_orders_handler,
    product_details_callback,
    listen_product_callback,
    back_to_catalog_callback,
    my_orders_callback,
)
from config import ADMIN_IDS


def create_mock_message(text="Test", user_id=123, full_name="Test User"):
    """Допоміжна функція для створення mock повідомлення."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.full_name = full_name
    
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = user
    message.answer = AsyncMock()
    
    return message


def create_mock_callback(data="test:1", user_id=123, full_name="Test User"):
    """Допоміжна функція для створення mock callback query."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.full_name = full_name
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.from_user = user
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.message.answer_voice = AsyncMock()
    callback.answer = AsyncMock()
    
    return callback


# ═════════════════════════════════════════════════════════════════════════════
# MENU BUTTON HANDLERS TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestCatalogButtonHandler:
    """Тести для обробника кнопки каталогу."""
    
    @pytest.mark.asyncio
    async def test_catalog_button_with_products(self):
        """Тест кнопки каталогу коли товари є."""
        message = create_mock_message("🛍️ Каталог")
        
        mock_products = [
            {'id': 1, 'name': 'Product 1', 'price': 100},
            {'id': 2, 'name': 'Product 2', 'price': 200}
        ]
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_products_keyboard') as mock_keyboard:
                mock_get.return_value = mock_products
                mock_keyboard.return_value = MagicMock()
                
                await handle_catalog_button(message)
                
                # Перевіряємо що БД була запитана
                mock_get.assert_called_once()
                
                # Перевіряємо що повідомлення відправлено
                message.answer.assert_called_once()
                
                # Перевіряємо що клавіатура передана
                call_kwargs = message.answer.call_args[1]
                assert 'reply_markup' in call_kwargs
                mock_keyboard.assert_called_once_with(mock_products)
    
    @pytest.mark.asyncio
    async def test_catalog_button_no_products(self):
        """Тест кнопки каталогу коли товарів немає."""
        message = create_mock_message("🛍️ Каталог")
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await handle_catalog_button(message)
            
            # Перевіряємо що помилка повідомлена
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "На жаль" in call_args or "немає" in call_args


class TestMyOrdersButtonHandler:
    """Тести для обробника кнопки мої замовлення."""
    
    @pytest.mark.asyncio
    async def test_my_orders_button_with_orders(self):
        """Тест кнопки мої замовлення коли замовлення є."""
        message = create_mock_message("📦 Мои заказы", user_id=123)
        
        mock_orders = [
            {
                'id': 1,
                'product_name': 'Product 1',
                'quantity': 2,
                'total_price': 200.0,
                'status': 'confirmed',
                'created_at': '2025-12-12'
            }
        ]
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_my_orders_keyboard') as mock_keyboard:
                mock_get.return_value = mock_orders
                mock_keyboard.return_value = MagicMock()
                
                await handle_my_orders_button(message)
                
                # Перевіряємо що БД була запитана з правильним user_id
                mock_get.assert_called_once_with(123)
                
                # Перевіряємо що повідомлення відправлено
                message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_my_orders_button_no_orders(self):
        """Тест кнопки мої замовлення коли замовлень немає."""
        message = create_mock_message("📦 Мои заказы", user_id=123)
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await handle_my_orders_button(message)
            
            # Перевіряємо що порожне повідомлення
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "ещё нет" in call_args or "нема" in call_args


class TestCategoriesButtonHandler:
    """Тести для обробника кнопки категорій."""
    
    @pytest.mark.asyncio
    async def test_categories_button_with_categories(self):
        """Тест кнопки категорій коли категорії є."""
        message = create_mock_message("📚 Категории")
        
        with patch('handlers.user.db.get_categories', new_callable=AsyncMock) as mock_get_cat:
            mock_get_cat.return_value = ['Category 1', 'Category 2']
            
            await handle_categories_button(message)
            
            # Перевіряємо що категорії були отримані
            mock_get_cat.assert_called_once()
            
            # Перевіряємо повідомлення
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert 'Category 1' in call_args
            assert 'Category 2' in call_args
    
    @pytest.mark.asyncio
    async def test_categories_button_no_categories(self):
        """Тест кнопки категорій коли категорій немає."""
        message = create_mock_message("📚 Категории")
        
        with patch('handlers.user.db.get_categories', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await handle_categories_button(message)
            
            # Перевіряємо помилку
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "не найдены" in call_args or "немає" in call_args


class TestHelpButtonHandler:
    """Тести для обробника кнопки допомога."""
    
    @pytest.mark.asyncio
    async def test_help_button_displays_all_commands(self):
        """Тест кнопки допомога виводить всі команди."""
        message = create_mock_message("❓ Помощь")
        
        await handle_help_button(message)
        
        # Перевіряємо що повідомлення відправлено
        message.answer.assert_called_once()
        
        # Перевіряємо що всі команди присутні
        call_args = message.answer.call_args[0][0]
        assert "/start" in call_args
        assert "/help" in call_args
        assert "/info" in call_args
        assert "/catalog" in call_args
        assert "/order" in call_args
        assert "/myorders" in call_args
        assert "/generate" in call_args


class TestAboutButtonHandler:
    """Тести для обробника кнопки про магазин."""
    
    @pytest.mark.asyncio
    async def test_about_button_displays_info(self):
        """Тест кнопки про магазин виводить інформацію."""
        message = create_mock_message("ℹ️ О магазине")
        
        await handle_about_button(message)
        
        # Перевіряємо що повідомлення відправлено
        message.answer.assert_called_once()
        
        # Перевіряємо що інформація присутня
        call_args = message.answer.call_args[0][0]
        assert "Магазин" in call_args or "магазин" in call_args
        assert "Email" in call_args or "email" in call_args
        assert "Телефон" in call_args or "Телефон" in call_args


class TestAIButtonHandler:
    """Тести для обробника кнопки AI."""
    
    @pytest.mark.asyncio
    async def test_ai_button_redirects_to_generate(self):
        """Тест кнопки AI перенаправляє на /generate."""
        message = create_mock_message("🎨 AI")
        
        await handle_ai_button(message)
        
        # Перевіряємо що повідомлення відправлено
        message.answer.assert_called_once()
        
        # Перевіряємо що згадується команда /generate
        call_args = message.answer.call_args[0][0]
        assert "/generate" in call_args


class TestAdminButtonHandler:
    """Тести для обробника кнопки адміністратор."""
    
    @pytest.mark.asyncio
    async def test_admin_button_for_admin_user(self):
        """Тест кнопки адміністратор для адміна."""
        admin_id = ADMIN_IDS[0] if ADMIN_IDS else 999
        message = create_mock_message("⚙️ Администратор", user_id=admin_id)
        
        with patch('handlers.user.ADMIN_IDS', [admin_id]):
            await handle_admin_button(message)
            
            # Перевіряємо що команда /admin згадується
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "/admin" in call_args
    
    @pytest.mark.asyncio
    async def test_admin_button_for_non_admin_user(self):
        """Тест кнопки адміністратор для звичайного користувача."""
        message = create_mock_message("⚙️ Администратор", user_id=999)
        
        with patch('handlers.user.ADMIN_IDS', [111]):  # Інший ID
            await handle_admin_button(message)
            
            # Перевіряємо що доступ заборонено
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "❌" in call_args or "доступа" in call_args


# ═════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestCommandCatalogHandler:
    """Тести для команди /catalog."""
    
    @pytest.mark.asyncio
    async def test_command_catalog_with_products(self):
        """Тест команди /catalog з товарами."""
        message = create_mock_message("/catalog")
        
        mock_products = [
            {'id': 1, 'name': 'Product 1', 'price': 100},
            {'id': 2, 'name': 'Product 2', 'price': 200}
        ]
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_products_keyboard') as mock_keyboard:
                mock_get.return_value = mock_products
                mock_keyboard.return_value = MagicMock()
                
                await command_catalog_handler(message)
                
                mock_get.assert_called_once()
                message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_command_catalog_no_products(self):
        """Тест команди /catalog без товарів."""
        message = create_mock_message("/catalog")
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await command_catalog_handler(message)
            
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "На жаль" in call_args


class TestCommandOrderHandler:
    """Тести для команди /order."""
    
    @pytest.mark.asyncio
    async def test_command_order_with_products(self):
        """Тест команди /order з товарами."""
        message = create_mock_message("/order")
        
        mock_products = [{'id': 1, 'name': 'Product 1', 'price': 100}]
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_order_keyboard') as mock_keyboard:
                mock_get.return_value = mock_products
                mock_keyboard.return_value = MagicMock()
                
                await command_order_handler(message)
                
                mock_get.assert_called_once()
                message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_command_order_no_products(self):
        """Тест команди /order без товарів."""
        message = create_mock_message("/order")
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await command_order_handler(message)
            
            message.answer.assert_called_once()


class TestCommandCategoriesHandler:
    """Тести для команди /categories."""
    
    @pytest.mark.asyncio
    async def test_command_categories_with_categories(self):
        """Тест команди /categories з категоріями."""
        message = create_mock_message("/categories")
        
        with patch('handlers.user.db.get_categories', new_callable=AsyncMock) as mock_get_cat:
            with patch('handlers.user.db.get_products_by_category', new_callable=AsyncMock) as mock_get_prod:
                mock_get_cat.return_value = ['Category 1', 'Category 2']
                mock_get_prod.side_effect = [[{'id': 1}], [{'id': 2}, {'id': 3}]]
                
                await command_categories_handler(message)
                
                message.answer.assert_called_once()
                call_args = message.answer.call_args[0][0]
                assert "Category 1" in call_args
                assert "Category 2" in call_args
                assert "(1 товарів)" in call_args
                assert "(2 товарів)" in call_args
    
    @pytest.mark.asyncio
    async def test_command_categories_no_categories(self):
        """Тест команди /categories без категорій."""
        message = create_mock_message("/categories")
        
        with patch('handlers.user.db.get_categories', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await command_categories_handler(message)
            
            message.answer.assert_called_once()


class TestCommandMyOrdersHandler:
    """Тести для команди /myorders."""
    
    @pytest.mark.asyncio
    async def test_command_myorders_with_orders(self):
        """Тест команди /myorders з замовленнями."""
        message = create_mock_message("/myorders", user_id=123)
        
        mock_orders = [
            {
                'id': 1,
                'product_name': 'Product 1',
                'quantity': 2,
                'total_price': 200.0,
                'status': 'confirmed',
                'created_at': '2025-12-12'
            }
        ]
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_orders
            
            await command_my_orders_handler(message)
            
            mock_get.assert_called_once_with(123)
            message.answer.assert_called_once()
            
            # Перевіряємо що замовлення деталі присутні
            call_args = message.answer.call_args[0][0]
            assert "Product 1" in call_args
            assert "200" in call_args
    
    @pytest.mark.asyncio
    async def test_command_myorders_no_orders(self):
        """Тест команди /myorders без замовлень."""
        message = create_mock_message("/myorders", user_id=123)
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await command_my_orders_handler(message)
            
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "ещё нет" in call_args or "нема" in call_args
    
    @pytest.mark.asyncio
    async def test_command_myorders_status_emoji_mapping(self):
        """Тест відображення статусів замовлень з емодзі."""
        message = create_mock_message("/myorders", user_id=123)
        
        mock_orders = [
            {
                'id': 1,
                'product_name': 'Product',
                'quantity': 1,
                'total_price': 100.0,
                'status': 'pending',
                'created_at': '2025-12-12'
            },
            {
                'id': 2,
                'product_name': 'Product 2',
                'quantity': 1,
                'total_price': 200.0,
                'status': 'delivered',
                'created_at': '2025-12-12'
            }
        ]
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_orders
            
            await command_my_orders_handler(message)
            
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            
            # Перевіряємо що емодзі присутні
            assert "🕐" in call_args  # pending
            assert "📬" in call_args  # delivered


# ═════════════════════════════════════════════════════════════════════════════
# CALLBACK QUERY HANDLERS TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestProductDetailsCallback:
    """Тести для callback обробника деталей товару."""
    
    @pytest.mark.asyncio
    async def test_product_details_callback_success(self):
        """Тест успішного отримання деталей товару."""
        callback = create_mock_callback("product:1")
        
        mock_product = {
            'id': 1,
            'name': 'Test Product',
            'description': 'Test Description',
            'category': 'Test Category',
            'price': 100.0,
            'stock': 10
        }
        
        with patch('handlers.user.db.get_product_by_id', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_product_details_keyboard') as mock_keyboard:
                mock_get.return_value = mock_product
                mock_keyboard.return_value = MagicMock()
                
                await product_details_callback(callback)
                
                mock_get.assert_called_once_with(1)
                callback.message.edit_text.assert_called_once()
                
                # Перевіряємо що деталі товару присутні
                call_args = callback.message.edit_text.call_args[0][0]
                assert "Test Product" in call_args
                assert "100" in call_args
    
    @pytest.mark.asyncio
    async def test_product_details_callback_product_not_found(self):
        """Тест отримання деталей неіснуючого товару."""
        callback = create_mock_callback("product:999")
        
        with patch('handlers.user.db.get_product_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            await product_details_callback(callback)
            
            # Перевіряємо помилку
            callback.answer.assert_called_once()
            assert "не знайдено" in callback.answer.call_args[0][0]


class TestListenProductCallback:
    """Тести для callback обробника озвучування товару."""
    
    @pytest.mark.asyncio
    async def test_listen_product_callback_success(self):
        """Тест успішного озвучування товару."""
        callback = create_mock_callback("listen_product:1")
        
        mock_product = {
            'id': 1,
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 100.0,
            'stock': 10,
            'category': 'Category'
        }
        
        with patch('handlers.user.db.get_product_by_id', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.text_to_speech', new_callable=AsyncMock) as mock_tts:
                with patch('handlers.user.get_product_description_for_tts') as mock_desc:
                    mock_get.return_value = mock_product
                    mock_tts.return_value = b'audio_data'
                    mock_desc.return_value = "Test Product Description"
                    
                    await listen_product_callback(callback)
                    
                    mock_get.assert_called_once_with(1)
                    mock_tts.assert_called_once()
                    callback.message.answer_voice.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_listen_product_callback_product_not_found(self):
        """Тест озвучування неіснуючого товару."""
        callback = create_mock_callback("listen_product:999")
        
        with patch('handlers.user.db.get_product_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            await listen_product_callback(callback)
            
            callback.answer.assert_called_once()
            assert "не найден" in callback.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_listen_product_callback_tts_failure(self):
        """Тест озвучування при помилці TTS."""
        callback = create_mock_callback("listen_product:1")
        
        mock_product = {
            'id': 1,
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 100.0,
            'stock': 10,
            'category': 'Category'
        }
        
        with patch('handlers.user.db.get_product_by_id', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.text_to_speech', new_callable=AsyncMock) as mock_tts:
                with patch('handlers.user.get_product_description_for_tts') as mock_desc:
                    mock_get.return_value = mock_product
                    mock_tts.return_value = None  # TTS failure
                    mock_desc.return_value = "Test"
                    
                    await listen_product_callback(callback)
                    
                    # Перевіряємо помилку
                    callback.message.answer.assert_called_once()
                    assert "Ошибка" in callback.message.answer.call_args[0][0]


class TestBackToCatalogCallback:
    """Тести для callback обробника повернення до каталогу."""
    
    @pytest.mark.asyncio
    async def test_back_to_catalog_callback_with_products(self):
        """Тест повернення до каталогу з товарами."""
        callback = create_mock_callback("back_to_catalog")
        
        mock_products = [
            {'id': 1, 'name': 'Product 1', 'price': 100},
            {'id': 2, 'name': 'Product 2', 'price': 200}
        ]
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_products_keyboard') as mock_keyboard:
                mock_get.return_value = mock_products
                mock_keyboard.return_value = MagicMock()
                
                await back_to_catalog_callback(callback)
                
                callback.message.edit_text.assert_called_once()
                mock_keyboard.assert_called_once_with(mock_products)
    
    @pytest.mark.asyncio
    async def test_back_to_catalog_callback_no_products(self):
        """Тест повернення до каталогу без товарів."""
        callback = create_mock_callback("back_to_catalog")
        
        with patch('handlers.user.db.get_all_products', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await back_to_catalog_callback(callback)
            
            callback.message.edit_text.assert_called_once()
            assert "На жаль" in callback.message.edit_text.call_args[0][0]


class TestMyOrdersCallback:
    """Тести для callback обробника мої замовлення."""
    
    @pytest.mark.asyncio
    async def test_my_orders_callback_with_orders(self):
        """Тест мої замовлення callback з замовленнями."""
        callback = create_mock_callback("my_orders", user_id=123)
        
        mock_orders = [
            {
                'id': 1,
                'product_name': 'Product 1',
                'quantity': 2,
                'total_price': 200.0,
                'status': 'confirmed',
                'created_at': '2025-12-12'
            }
        ]
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_my_orders_keyboard') as mock_keyboard:
                mock_get.return_value = mock_orders
                mock_keyboard.return_value = MagicMock()
                
                await my_orders_callback(callback)
                
                mock_get.assert_called_once_with(123)
                callback.message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_my_orders_callback_no_orders(self):
        """Тест мої замовлення callback без замовлень."""
        callback = create_mock_callback("my_orders", user_id=123)
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            await my_orders_callback(callback)
            
            callback.message.edit_text.assert_called_once()
            assert "немає" in callback.message.edit_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_my_orders_callback_status_display(self):
        """Тест відображення статусів у замовленнях callback."""
        callback = create_mock_callback("my_orders", user_id=123)
        
        mock_orders = [
            {
                'id': 1,
                'product_name': 'Product',
                'quantity': 1,
                'total_price': 100.0,
                'status': 'shipped',
                'created_at': '2025-12-12'
            }
        ]
        
        with patch('handlers.user.db.get_user_orders', new_callable=AsyncMock) as mock_get:
            with patch('handlers.user.get_my_orders_keyboard') as mock_keyboard:
                mock_get.return_value = mock_orders
                mock_keyboard.return_value = MagicMock()
                
                await my_orders_callback(callback)
                
                call_args = callback.message.edit_text.call_args[0][0]
                assert "🚚" in call_args  # shipped emoji
