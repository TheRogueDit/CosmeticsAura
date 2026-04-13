import aiosqlite
from datetime import datetime

DB_NAME = "cosmetics.db"

# =============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# =============================================================================
async def init_db():
    """Создание всех таблиц"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Пользователи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                bonus_balance REAL DEFAULT 0,
                total_purchases REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Товары
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                stock INTEGER DEFAULT 0,
                photo_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Корзина
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Заказы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount REAL,
                items TEXT,
                address TEXT,
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Бонусная история
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bonus_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Отзывы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                rating INTEGER,
                text TEXT,
                is_approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Конкурсы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                prize TEXT,
                end_date TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Участники конкурсов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contest_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contest_id) REFERENCES contests(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        await db.commit()

# =============================================================================
# ПОЛЬЗОВАТЕЛИ
# =============================================================================
async def add_user(user_id: int, username: str, first_name: str):
    """Добавить пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def get_user(user_id: int):
    """Получить пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

# =============================================================================
# ТОВАРЫ
# =============================================================================
async def get_all_products():
    """Получить все товары"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products ORDER BY category, name")
        return await cursor.fetchall()

async def get_product_by_id(product_id: int):
    """Получить товар по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()

async def add_product(name: str, description: str, price: float, category: str, stock: int, photo_id: str):
    """Добавить товар"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, description, price, category, stock, photo_id) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, category, stock, photo_id)
        )
        await db.commit()
        return cursor.lastrowid

# =============================================================================
# КОРЗИНА
# =============================================================================
async def get_cart_items(user_id: int):
    """Получить товары в корзине пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT c.id, p.name, p.price, c.quantity, p.id as product_id
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        rows = await cursor.fetchall()
        
        # Преобразуем в список словарей
        items = []
        for row in rows:
            items.append({
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'quantity': row[3],
                'product_id': row[4]
            })
        return items

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Добавить товар в корзину"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, есть ли уже товар в корзине
        cursor = await db.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Увеличиваем количество
            await db.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?",
                (quantity, user_id, product_id)
            )
        else:
            # Добавляем новый товар
            await db.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity)
            )
        await db.commit()

async def clear_cart(user_id: int):
    """Очистить корзину пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()

async def remove_from_cart(user_id: int, product_id: int):
    """Удалить товар из корзины"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await db.commit()

# =============================================================================
# ЗАКАЗЫ
# =============================================================================
async def create_order(user_id: int, total: float, items: str, address: str, payment_status: str = "pending"):
    """Создать заказ"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders (user_id, total_amount, items, address, payment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, total, items, address, payment_status, datetime.now())
        )
        await db.commit()
        return cursor.lastrowid

async def get_user_orders(user_id: int):
    """Получить заказы пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_order_by_id(order_id: int):
    """Получить заказ по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()

async def update_order_status(order_id: int, status: str):
    """Обновить статус заказа"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET payment_status = ? WHERE id = ?",
            (status, order_id)
        )
        await db.commit()

# =============================================================================
# БОНУСЫ
# =============================================================================
async def add_bonus(user_id: int, amount: float, reason: str):
    """Начислить бонусы"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET bonus_balance = bonus_balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.execute(
            "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
            (user_id, amount, reason)
        )
        await db.commit()

async def get_bonus_balance(user_id: int):
    """Получить баланс бонусов"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT bonus_balance FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

# =============================================================================
# ОТЗЫВЫ
# =============================================================================
async def add_review(user_id: int, product_id: int, rating: int, text: str):
    """Добавить отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO reviews (user_id, product_id, rating, text) VALUES (?, ?, ?, ?)",
            (user_id, product_id, rating, text)
        )
        await db.commit()
        return cursor.lastrowid

async def get_product_reviews(product_id: int):
    """Получить отзывы о товаре"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM reviews WHERE product_id = ? AND is_approved = 1",
            (product_id,)
        )
        return await cursor.fetchall()

# =============================================================================
# КОНКУРСЫ
# =============================================================================
async def get_active_contests():
    """Получить активные конкурсы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM contests WHERE is_active = 1")
        return await cursor.fetchall()

async def join_contest(contest_id: int, user_id: int):
    """Участвовать в конкурсе"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO contest_participants (contest_id, user_id) VALUES (?, ?)",
            (contest_id, user_id)
        )
        await db.commit()

# =============================================================================
# АНАЛИТИКА
# =============================================================================
async def get_sales_stats():
    """Статистика продаж"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order
            FROM orders
            WHERE payment_status IN ('paid', 'delivered')
        """)
        return await cursor.fetchone()

async def get_user_stats():
    """Статистика пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return await cursor.fetchone()
