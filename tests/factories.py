"""Фабрики для створення тестових даних."""
import time
from typing import Optional, Dict, List


class UserFactory:
    """Фабрика для створення тестових користувачів з можливістю кастомізації."""
    
    def __init__(self, db):
        self.db = db
        self._counter = int(time.time() * 1000000) % 1000000000
    
    async def create(self, **kwargs) -> Dict:
        """Створює користувача з поданими параметрами або значеннями за замовчуванням."""
        self._counter += 1
        
        defaults = {
            'user_id': self._counter,
            'username': f'testuser_{self._counter}',
            'first_name': 'Test',
            'last_name': 'User'
        }
        defaults.update(kwargs)
        
        user_id = defaults.pop('user_id')
        
        await self.db.add_user(user_id, **defaults)
        
        # Повертаємо дані користувача
        return {
            'id': user_id,
            **defaults
        }
    
    async def create_batch(self, count: int, **kwargs) -> List[Dict]:
        """Створює кілька користувачів з автоматичним індексуванням."""
        users = []
        for i in range(count):
            user_kwargs = kwargs.copy()
            if 'username' not in kwargs or kwargs['username'].startswith('testuser_'):
                # Автогенерована назва користувача
                pass  # Використовуємо default з create()
            if 'first_name' not in kwargs:
                user_kwargs['first_name'] = f"Test{i+1}"
            if 'last_name' not in kwargs:
                user_kwargs['last_name'] = f"User{i+1}"
            
            user = await self.create(**user_kwargs)
            users.append(user)
        
        return users


class ProductFactory:
    """Фабрика для створення тестових товарів з можливістю кастомізації."""
    
    def __init__(self, db):
        self.db = db
    
    async def create(self, **kwargs) -> Dict:
        """Створює товар з поданими параметрами або значеннями за замовчуванням."""
        defaults = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 100.00,
            'category': 'Test Category',
            'stock': 10
        }
        defaults.update(kwargs)
        
        product_id = await self.db.add_product(**defaults)
        return await self.db.get_product_by_id(product_id)
    
    async def create_batch(self, count: int, **kwargs) -> List[Dict]:
        """Створює кілька товарів з автоматичним індексуванням."""
        products = []
        for i in range(count):
            product_kwargs = kwargs.copy()
            if 'name' not in kwargs or kwargs['name'] == 'Test Product':
                product_kwargs['name'] = f"Product {i+1}"
            if 'price' not in kwargs:
                product_kwargs['price'] = 100.00 + (i * 50)
            if 'stock' not in kwargs:
                product_kwargs['stock'] = 10 + i
            
            product = await self.create(**product_kwargs)
            products.append(product)
        
        return products


class OrderFactory:
    """Фабрика для створення тестових замовлень з можливістю кастомізації."""
    
    def __init__(self, db):
        self.db = db
    
    async def create(self, user_id: Optional[int] = None, product_id: Optional[int] = None, **kwargs) -> Dict:
        """Створює замовлення з реальними даними."""
        if product_id is None:
            products = await self.db.get_all_products()
            if not products:
                raise RuntimeError("No products available")
            product_id = products[0]['id']
        
        if user_id is None:
            user_id = int(time.time() * 1000000) % 1000000000
        
        defaults = {
            'user_id': user_id,
            'user_name': 'Test User',
            'product_id': product_id,
            'quantity': 1,
            'phone': '+380501234567',
            'email': 'test@example.com'
        }
        defaults.update(kwargs)
        
        order_id = await self.db.create_order(**defaults)
        
        # Отримуємо створене замовлення
        async with self.db.pool.acquire() as conn:
            order = await conn.fetchrow(
                "SELECT * FROM orders WHERE id = $1",
                order_id
            )
        
        return dict(order) if order else None
    
    async def create_batch(self, count: int, user_id: Optional[int] = None, **kwargs) -> List[Dict]:
        """Створює кілька замовлень для одного користувача."""
        if user_id is None:
            user_id = int(time.time() * 1000000) % 1000000000
        
        orders = []
        for i in range(count):
            order_kwargs = kwargs.copy()
            if 'quantity' not in kwargs:
                order_kwargs['quantity'] = 1 + i
            if 'phone' not in kwargs:
                # Генеруємо різні номери телефонів
                order_kwargs['phone'] = f"+3805012345{67+i:02d}"
            
            order = await self.create(user_id=user_id, **order_kwargs)
            orders.append(order)
        
        return orders
