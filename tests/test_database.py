import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from database import Database


class TestDatabase:
    """Тести для класу Database."""
    
    @pytest.mark.asyncio
    async def test_get_all_products(self, db):
        """Тест отримання всіх товарів."""
        products = await db.get_all_products()
        assert isinstance(products, list)
        if products:
            assert 'id' in products[0]
            assert 'name' in products[0]
            assert 'price' in products[0]
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(self, db):
        """Тест отримання товару за ID."""
        # Отримуємо всі товари
        products = await db.get_all_products()
        
        if products:
            product_id = products[0]['id']
            product = await db.get_product_by_id(product_id)
            
            assert product is not None
            assert product['id'] == product_id
            assert 'name' in product
            assert 'price' in product
    
    @pytest.mark.asyncio
    async def test_get_product_by_invalid_id(self, db):
        """Тест отримання товару з невірним ID."""
        product = await db.get_product_by_id(99999)
        assert product is None
    
    @pytest.mark.asyncio
    async def test_get_categories(self, db):
        """Тест отримання категорій."""
        categories = await db.get_categories()
        assert isinstance(categories, list)
        if categories:
            assert all(isinstance(cat, str) for cat in categories)
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(self, db):
        """Тест отримання товарів за категорією."""
        categories = await db.get_categories()
        
        if categories:
            category = categories[0]
            products = await db.get_products_by_category(category)
            
            assert isinstance(products, list)
            if products:
                assert all(p['category'] == category for p in products)
    
    @pytest.mark.asyncio
    async def test_add_user(self, db):
        """Тест додавання користувача."""
        import time
        user_id = int(time.time() * 1000) % 999999999  # Унікальний ID
        username = f"testuser_{user_id}"
        first_name = "Тестовий"
        last_name = "Користувач"
        
        await db.add_user(user_id, username, first_name, last_name)
        
        # Перевіряємо, що користувач доданий
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            assert user is not None
            assert user['username'] == username
            assert user['first_name'] == first_name
            assert user['last_name'] == last_name
    
    @pytest.mark.asyncio
    async def test_create_order(self, db):
        """Тест створення замовлення."""
        # Додаємо користувача
        user_id = 12346
        await db.add_user(user_id, "testuser2", "Test", "User")
        
        # Отримуємо товар
        products = await db.get_all_products()
        
        if products:
            product = products[0]
            initial_stock = product['stock']
            
            # Створюємо замовлення
            order_id = await db.create_order(
                user_id=user_id,
                user_name="Test User",
                product_id=product['id'],
                quantity=1
            )
            
            assert order_id is not None
            assert isinstance(order_id, int)
            
            # Перевіряємо, що залишок зменшився
            updated_product = await db.get_product_by_id(product['id'])
            assert updated_product['stock'] == initial_stock - 1
    
    @pytest.mark.asyncio
    async def test_get_user_orders(self, db):
        """Тест отримання замовлень користувача."""
        user_id = 12347
        await db.add_user(user_id, "testuser3", "Test", "User")
        
        products = await db.get_all_products()
        
        if products:
            product = products[0]
            
            # Створюємо замовлення
            await db.create_order(
                user_id=user_id,
                user_name="Test User",
                product_id=product['id'],
                quantity=1
            )
            
            # Отримуємо замовлення користувача
            orders = await db.get_user_orders(user_id)
            
            assert isinstance(orders, list)
            assert len(orders) > 0
            assert orders[0]['user_id'] == user_id
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, db):
        """Тест оновлення статусу замовлення."""
        user_id = 12348
        await db.add_user(user_id, "testuser4", "Test", "User")
        
        products = await db.get_all_products()
        
        if products:
            product = products[0]
            
            # Створюємо замовлення
            order_id = await db.create_order(
                user_id=user_id,
                user_name="Test User",
                product_id=product['id'],
                quantity=1
            )
            
            # Оновлюємо статус
            result = await db.update_order_status(order_id, "confirmed")
            assert result is True
            
            # Перевіряємо, що статус оновлено
            async with db.pool.acquire() as conn:
                order = await conn.fetchrow(
                    "SELECT * FROM orders WHERE id = $1", order_id
                )
                assert order['status'] == "confirmed"
