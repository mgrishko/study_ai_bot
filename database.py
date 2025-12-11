import asyncpg
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import get_db_config

logger = logging.getLogger(__name__)


class Database:
    """Клас для роботи з базою даних PostgreSQL."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.config = get_db_config()
    
    async def connect(self):
        """Створення пулу підключень до PostgreSQL."""
        self.pool = await asyncpg.create_pool(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
            min_size=1,
            max_size=10
        )
    
    async def close(self):
        """Закриття пулу підключень."""
        if self.pool:
            await self.pool.close()
    
    async def init_db(self):
        """Ініціалізація бази даних та створення таблиць."""
        # Переконуємось, що є підключення до БД
        if not self.pool:
            await self.connect()
        
        if not self.pool:
            raise RuntimeError("Не вдалося створити пул підключень до БД")
        
        async with self.pool.acquire() as conn:
            # Таблиця товарів
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price NUMERIC(10, 2) NOT NULL,
                    category TEXT NOT NULL,
                    image_url TEXT,
                    stock INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблиця замовлень
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    user_name TEXT,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    total_price NUMERIC(10, 2) NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Таблиця користувачів
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Додаємо початкові товари, якщо база порожня
            await self._add_initial_products(conn)
    
    async def _add_initial_products(self, conn: asyncpg.Connection):
        """Додає початкові товари в базу даних."""
        count = await conn.fetchval("SELECT COUNT(*) FROM products")
        
        if count == 0:
            products = [
                ("Зимова куртка 'Арктика'", "Тепла зимова куртка з хутряним коміром", 3500.00, "Куртки", None, 15),
                ("Пальто класичне", "Елегантне вовняне пальто для офісу", 4200.00, "Пальта", None, 10),
                ("Плащ 'Осінній'", "Водонепроникний плащ для дощової погоди", 2800.00, "Плащі", None, 20),
                ("Вітрівка спортивна", "Легка вітрівка для активного відпочинку", 1500.00, "Вітрівки", None, 25),
                ("Пуховик 'Норд'", "Ультралегкий пуховик з мембраною", 5500.00, "Пуховики", None, 12),
                ("Куртка шкіряна", "Стильна шкіряна куртка", 6000.00, "Куртки", None, 8),
                ("Пальто вовняне довге", "Довге пальто з вовни для холодної погоди", 4800.00, "Пальта", None, 7),
                ("Плащ тренч", "Класичний тренч бежевого кольору", 3200.00, "Плащі", None, 14),
            ]
            
            await conn.executemany(
                "INSERT INTO products (name, description, price, category, image_url, stock) VALUES ($1, $2, $3, $4, $5, $6)",
                products
            )
    
    async def get_all_products(self) -> List[Dict]:
        """Отримати всі товари."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM products WHERE stock > 0 ORDER BY id")
            return [dict(row) for row in rows]
    
    async def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Отримати товар за ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
            return dict(row) if row else None
    
    async def get_products_by_category(self, category: str) -> List[Dict]:
        """Отримати товари за категорією."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM products WHERE category = $1 AND stock > 0 ORDER BY id", 
                category
            )
            return [dict(row) for row in rows]
    
    async def create_order(self, user_id: int, user_name: str, product_id: int, quantity: int = 1) -> Optional[int]:
        """Створити нове замовлення."""
        async with self.pool.acquire() as conn:
            # Перевіряємо наявність товару
            product = await self.get_product_by_id(product_id)
            if not product or product['stock'] < quantity:
                return None
            
            total_price = float(product['price']) * quantity
            
            # Використовуємо транзакцію для атомарності операцій
            async with conn.transaction():
                # Створюємо замовлення
                order_id = await conn.fetchval(
                    """INSERT INTO orders (user_id, user_name, product_id, quantity, total_price, status) 
                       VALUES ($1, $2, $3, $4, $5, 'pending') RETURNING id""",
                    user_id, user_name, product_id, quantity, total_price
                )
                
                # Зменшуємо кількість товару на складі
                await conn.execute(
                    "UPDATE products SET stock = stock - $1 WHERE id = $2",
                    quantity, product_id
                )
                
                return order_id
    
    async def get_user_orders(self, user_id: int) -> List[Dict]:
        """Отримати всі замовлення користувача."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT o.*, p.name as product_name 
                   FROM orders o 
                   JOIN products p ON o.product_id = p.id 
                   WHERE o.user_id = $1 
                   ORDER BY o.created_at DESC""",
                user_id
            )
            return [dict(row) for row in rows]
    
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Оновити статус замовлення."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET status = $1 WHERE id = $2",
                status, order_id
            )
            return True
    
    async def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        """Додати або оновити користувача."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO users (id, username, first_name, last_name) 
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (id) DO UPDATE 
                   SET username = $2, first_name = $3, last_name = $4""",
                user_id, username, first_name, last_name
            )
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Отримати користувача за ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return dict(row) if row else None
    
    async def get_categories(self) -> List[str]:
        """Отримати список всіх категорій."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT category FROM products WHERE stock > 0 ORDER BY category")
            return [row['category'] for row in rows]
    
    async def add_product(
        self, 
        name: str, 
        description: str, 
        price: float, 
        category: str, 
        stock: int,
        image_url: Optional[str] = None
    ) -> Optional[int]:
        """Додає новий товар в каталог.
        
        Args:
            name: Назва товару (макс 255 символів)
            description: Опис товару (макс 1000 символів)
            price: Ціна товару в гривнях
            category: Категорія товару
            stock: Кількість на складі
            image_url: URL зображення товару (опціонально)
        
        Returns:
            ID нового товару або None при помилці
        """
        try:
            query = """
                INSERT INTO products (name, description, price, category, stock, image_url)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            async with self.pool.acquire() as conn:
                product_id = await conn.fetchval(query, name, description, price, category, stock, image_url)
            
            logger.info(f"Product added: {name} (ID: {product_id})")
            return product_id
        except Exception as e:
            logger.exception(f"Error adding product: {e}")
            return None
    
    async def update_product(
        self, 
        product_id: int, 
        **kwargs: Any
    ) -> bool:
        """Оновлює товар (name, description, price, category, stock, image_url).
        
        Args:
            product_id: ID товару для оновлення
            **kwargs: Поля для оновлення (name, description, price, category, stock, image_url)
        
        Returns:
            True якщо успішно оновлено, False інакше
        """
        try:
            allowed_fields = {'name', 'description', 'price', 'category', 'stock', 'image_url'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning(f"No valid fields to update for product {product_id}")
                return False
            
            set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(update_fields.keys()))
            query = f"UPDATE products SET {set_clause} WHERE id = ${len(update_fields)+1}"
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *update_fields.values(), product_id)
            
            if result == "UPDATE 1":
                logger.info(f"Product {product_id} updated: {update_fields}")
                return True
            return False
        except Exception as e:
            logger.exception(f"Error updating product: {e}")
            return False
    
    async def delete_product(self, product_id: int) -> bool:
        """Видаляє товар з каталогу.
        
        Args:
            product_id: ID товару для видалення
        
        Returns:
            True якщо успішно видалено, False інакше
        """
        try:
            # Спочатку отримуємо назву товару для логування
            product = await self.get_product_by_id(product_id)
            if not product:
                logger.warning(f"Product {product_id} not found for deletion")
                return False
            
            async with self.pool.acquire() as conn:
                # Видаляємо товар
                result = await conn.execute("DELETE FROM products WHERE id = $1", product_id)
            
            if result == "DELETE 1":
                logger.info(f"Product deleted: {product['name']} (ID: {product_id})")
                return True
            return False
        except Exception as e:
            logger.exception(f"Error deleting product: {e}")
            return False


# Глобальний екземпляр бази даних
db = Database()