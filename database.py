import asyncpg
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import get_db_config
from logger_config import get_logger

logger = get_logger("aiogram.database")


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
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'unpaid',
                    payment_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Таблиця платежів
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL UNIQUE,
                    user_id BIGINT NOT NULL,
                    amount NUMERIC(10, 2) NOT NULL,
                    currency TEXT DEFAULT 'UAH',
                    payment_method TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    liqpay_payment_id TEXT,
                    liqpay_order_id TEXT,
                    telegram_payment_id TEXT,
                    telegram_provider_payment_id TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Таблиця користувачів
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Додаємо колонки телефону та email якщо вони не існують
            await self._migrate_contact_columns(conn)
            
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
    
    async def _migrate_contact_columns(self, conn: asyncpg.Connection):
        """Додає колонки телефону та email якщо вони не існують (для міграції існуючих БД)."""
        try:
            # Перевіряємо чи існує колона phone в таблиці orders
            has_phone = await conn.fetchval(
                """SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='orders' AND column_name='phone'
                )"""
            )
            
            if not has_phone:
                await conn.execute("ALTER TABLE orders ADD COLUMN phone TEXT")
                logger.info("Added phone column to orders table")
            
            # Перевіряємо чи існує колона email в таблиці orders
            has_email = await conn.fetchval(
                """SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='orders' AND column_name='email'
                )"""
            )
            
            if not has_email:
                await conn.execute("ALTER TABLE orders ADD COLUMN email TEXT")
                logger.info("Added email column to orders table")
            
            # Перевіряємо колонки в таблиці users
            has_user_phone = await conn.fetchval(
                """SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='phone'
                )"""
            )
            
            if not has_user_phone:
                await conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                logger.info("Added phone column to users table")
            
            has_user_email = await conn.fetchval(
                """SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='email'
                )"""
            )
            
            if not has_user_email:
                await conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
                logger.info("Added email column to users table")
        
        except Exception as e:
            logger.warning(f"Migration error (may be normal for new DB): {e}")
    
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
    
    async def create_order(self, user_id: int, user_name: str, product_id: int, quantity: int = 1, 
                          phone: str = None, email: str = None) -> Optional[int]:
        """
        Створити нове замовлення.
        
        Args:
            user_id: ID користувача
            user_name: Ім'я користувача
            product_id: ID товару
            quantity: Кількість (за замовчуванням 1)
            phone: Телефон користувача (опціонально)
            email: Email користувача (опціонально)
            
        Returns:
            ID замовлення або None якщо помилка
        """
        async with self.pool.acquire() as conn:
            # Перевіряємо наявність товару
            product = await self.get_product_by_id(product_id)
            if not product or product['stock'] < quantity:
                return None
            
            total_price = float(product['price']) * quantity
            
            # Використовуємо транзакцію для атомарності операцій
            async with conn.transaction():
                # Створюємо замовлення з контактною інформацією
                order_id = await conn.fetchval(
                    """INSERT INTO orders (user_id, user_name, product_id, quantity, total_price, phone, email, status) 
                       VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending') RETURNING id""",
                    user_id, user_name, product_id, quantity, total_price, phone, email
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
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLEANUP METHODS FOR TESTING (Rails-style)
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def truncate_test_tables(self):
        """Очищає всі таблиці БД для тестування (Rails-style cleanup).
        
        Видаляє дані з таблиць у правильному порядку з врахуванням зовнішніх ключів.
        Зберігає структуру БД та початкові товари.
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Видаляємо замовлення першими (вони мають FK на products)
                    await conn.execute("DELETE FROM orders")
                    
                    # Видаляємо користувачів
                    await conn.execute("DELETE FROM users")
                    
                    # Видаляємо тестові товари, але зберігаємо початкові (id 1-8)
                    await conn.execute("DELETE FROM products WHERE id > 8")
                    
                    # Скидаємо sequences (auto-increment counters) на початкові значення
                    await conn.execute("ALTER SEQUENCE orders_id_seq RESTART WITH 1")
                    await conn.execute("ALTER SEQUENCE products_id_seq RESTART WITH 9")
            
            logger.debug("Test tables truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating test tables: {e}", exc_info=True)
            raise
    
    async def clear_specific_table(self, table_name: str, condition: str = ""):
        """Очищає конкретну таблицю з опціональною умовою.
        
        Args:
            table_name: Назва таблиці для очищення
            condition: SQL умова (без WHERE) для вибіркового видалення
        
        Example:
            await db.clear_specific_table("orders", "status = 'pending'")
        """
        try:
            async with self.pool.acquire() as conn:
                if condition:
                    await conn.execute(f"DELETE FROM {table_name} WHERE {condition}")
                else:
                    await conn.execute(f"DELETE FROM {table_name}")
            
            logger.debug(f"Table {table_name} cleared" + (f" with condition: {condition}" if condition else ""))
        except Exception as e:
            logger.error(f"Error clearing {table_name}: {e}", exc_info=True)
            raise
    
    async def reset_sequences(self):
        """Скидає всі автоінкремент sequences для таблиць.
        
        Користується для відновлення порядку ID після очищення таблиць.
        """
        try:
            async with self.pool.acquire() as conn:
                # Скидаємо sequences відповідно до бізнес-логіки
                await conn.execute("ALTER SEQUENCE orders_id_seq RESTART WITH 1")
                await conn.execute("ALTER SEQUENCE products_id_seq RESTART WITH 9")  # Після початкових товарів
            
            logger.debug("Sequences reset successfully")
        except Exception as e:
            logger.error(f"Error resetting sequences: {e}", exc_info=True)
            raise
    
    # ═════════════════════════════════════════════════════════════════════════════
    # PAYMENT METHODS
    # ═════════════════════════════════════════════════════════════════════════════
    
    async def create_payment_record(self, order_id: int, user_id: int, amount: float,
                                   payment_method: str, currency: str = "UAH") -> Optional[int]:
        """
        Create a payment record in the database.
        
        Args:
            order_id: Order ID
            user_id: Telegram user ID
            amount: Payment amount
            payment_method: Payment method ('liqpay' or 'telegram')
            currency: Currency code (default 'UAH')
        
        Returns:
            Payment ID or None if error
        """
        try:
            async with self.pool.acquire() as conn:
                payment_id = await conn.fetchval(
                    """INSERT INTO payments (order_id, user_id, amount, currency, payment_method, status)
                       VALUES ($1, $2, $3, $4, $5, 'pending') RETURNING id""",
                    order_id, user_id, amount, currency, payment_method
                )
                return payment_id
        except Exception as e:
            logger.error(f"Error creating payment record: {e}", exc_info=True)
            return None
    
    async def update_payment_status(self, payment_id: int, status: str,
                                   liqpay_payment_id: str = None,
                                   error_message: str = None) -> bool:
        """
        Update payment status.
        
        Args:
            payment_id: Payment ID
            status: New status ('pending', 'processing', 'completed', 'failed', 'cancelled')
            liqpay_payment_id: LiqPay transaction ID (optional)
            error_message: Error details if payment failed (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE payments 
                       SET status = $1, liqpay_payment_id = $2, error_message = $3, updated_at = CURRENT_TIMESTAMP
                       WHERE id = $4""",
                    status, liqpay_payment_id, error_message, payment_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating payment status: {e}", exc_info=True)
            return False
    
    async def get_payment_by_order(self, order_id: int) -> Optional[Dict]:
        """
        Get payment record by order ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Payment record or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM payments WHERE order_id = $1",
                    order_id
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting payment by order: {e}", exc_info=True)
            return None
    
    async def get_payment_by_id(self, payment_id: int) -> Optional[Dict]:
        """
        Get payment record by payment ID.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Payment record or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM payments WHERE id = $1",
                    payment_id
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting payment by ID: {e}", exc_info=True)
            return None
    
    async def update_order_payment_info(self, order_id: int, payment_status: str,
                                       payment_method: str) -> bool:
        """
        Update order payment information.
        
        Args:
            order_id: Order ID
            payment_status: Payment status ('paid' or 'unpaid')
            payment_method: Payment method used
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """UPDATE orders 
                       SET payment_status = $1, payment_method = $2
                       WHERE id = $3""",
                    payment_status, payment_method, order_id
                )
                return True
        except Exception as e:
            logger.error(f"Error updating order payment info: {e}", exc_info=True)
            return False


# Глобальний екземпляр бази даних
db = Database()