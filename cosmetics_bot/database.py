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
        
        # Запросы на отзывы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS review_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id INTEGER,
                is_sent INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

async def get_all_users():
    """Получить всех пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
        return await cursor.fetchall()

async def get_user_count():
    """Получить количество пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        result = await cursor.fetchone()
        return result[0] if result else 0

# =============================================================================
# ТОВАРЫ
# =============================================================================
async def get_all_products():
    """Получить все товары"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products ORDER BY category, name")
        return await cursor.fetchall()

async def get_products_by_category(category: str):
    """Получить товары по категории"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name",
            (category,)
        )
        return await cursor.fetchall()

async def get_all_categories():
    """Получить все категории"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

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

async def update_product(product_id: int, name: str = None, price: float = None, stock: int = None):
    """Обновить товар"""
    async with aiosqlite.connect(DB_NAME) as db:
        if name:
            await db.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
        if price:
            await db.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
        if stock:
            await db.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
        await db.commit()

async def delete_product(product_id: int):
    """Удалить товар"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()

async def get_product_rating(product_id: int):
    """Получить рейтинг товара"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ? AND is_approved = 1",
            (product_id,)
        )
        return await cursor.fetchone()

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
        cursor = await db.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await db.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?",
                (quantity, user_id, product_id)
            )
        else:
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

async def update_cart_quantity(user_id: int, product_id: int, quantity: int):
    """Обновить количество товара в корзине"""
    async with aiosqlite.connect(DB_NAME) as db:
        if quantity <= 0:
            await db.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
        else:
            await db.execute(
                "UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (quantity, user_id, product_id)
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

async def get_all_orders():
    """Получить все заказы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders ORDER BY created_at DESC")
        return await cursor.fetchall()

async def update_order_status(order_id: int, status: str):
    """Обновить статус заказа"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET payment_status = ? WHERE id = ?",
            (status, order_id)
        )
        await db.commit()

async def get_pending_orders():
    """Получить ожидающие заказы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE payment_status = 'pending' ORDER BY created_at"
        )
        return await cursor.fetchall()

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

async def use_bonus(user_id: int, amount: float):
    """Списать бонусы"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET bonus_balance = bonus_balance - ? WHERE user_id = ? AND bonus_balance >= ?",
            (amount, user_id, amount)
        )
        await db.execute(
            "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
            (user_id, -amount, "Списание бонусов")
        )
        await db.commit()

async def get_bonus_history(user_id: int):
    """Получить историю бонусов"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM bonus_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_bonus_stats():
    """Статистика по бонусам"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as users_with_bonus,
                SUM(bonus_balance) as total_bonus,
                SUM(amount) as total_accrued
            FROM users
            LEFT JOIN bonus_history ON users.user_id = bonus_history.user_id
        """)
        return await cursor.fetchone()

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

async def get_pending_reviews():
    """Получить отзывы на модерации"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM reviews WHERE is_approved = 0 ORDER BY created_at DESC"
        )
        return await cursor.fetchall()

async def approve_review(review_id: int):
    """Одобрить отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE reviews SET is_approved = 1 WHERE id = ?",
            (review_id,)
        )
        await db.commit()

async def reject_review(review_id: int):
    """Отклонить отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        await db.commit()

async def get_review_stats():
    """Статистика по отзывам"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 1")
        approved = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 0")
        pending = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT AVG(rating) FROM reviews WHERE is_approved = 1")
        avg_rating = (await cursor.fetchone())[0] or 0
        
        cursor = await db.execute("""
            SELECT p.name, COUNT(r.id) as review_count, AVG(r.rating) as avg_rating
            FROM products p
            JOIN reviews r ON p.id = r.product_id
            WHERE r.is_approved = 1
            GROUP BY p.id
            ORDER BY review_count DESC
            LIMIT 5
        """)
        top_products = await cursor.fetchall()
        
        return {
            "approved": approved,
            "pending": pending,
            "avg_rating": round(avg_rating, 1),
            "top_products": top_products
        }

async def get_pending_review_requests():
    """Получить запросы на отзывы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM review_requests WHERE is_sent = 0 AND is_completed = 0"
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
            "SELECT * FROM contest_participants WHERE contest_id = ? AND user_id = ?",
            (contest_id, user_id)
        )
        existing = await cursor.fetchone()
        
        if not existing:
            await db.execute(
                "INSERT INTO contest_participants (contest_id, user_id) VALUES (?, ?)",
                (contest_id, user_id)
            )
            await db.commit()
            return True
        return False

async def get_user_contests(user_id: int):
    """Получить конкурсы пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT c.* FROM contests c
            JOIN contest_participants cp ON c.id = cp.contest_id
            WHERE cp.user_id = ?
        """, (user_id,))
        return await cursor.fetchall()

async def get_contest_stats():
    """Статистика по конкурсам"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                c.title,
                c.prize,
                COUNT(cp.user_id) as participants,
                c.is_active,
                c.end_date
            FROM contests c
            LEFT JOIN contest_participants cp ON c.id = cp.contest_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        return await cursor.fetchall()

async def add_contest(title: str, description: str, prize: str, end_date: str):
    """Добавить конкурс"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO contests (title, description, prize, end_date) VALUES (?, ?, ?, ?)",
            (title, description, prize, end_date)
        )
        await db.commit()
        return cursor.lastrowid

async def toggle_contest(contest_id: int, is_active: int):
    """Включить/выключить конкурс"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE contests SET is_active = ? WHERE id = ?",
            (is_active, contest_id)
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

async def get_daily_revenue(days: int = 30):
    """Выручка по дням"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                date(created_at) as day,
                SUM(total_amount) as revenue
            FROM orders
            WHERE payment_status IN ('paid', 'delivered')
            AND created_at >= date('now', ?)
            GROUP BY day
            ORDER BY day ASC
        """, (f'-{days} days',))
        return await cursor.fetchall()

async def get_dashboard_stats():
    """Общая статистика для дашборда"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Пользователи
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        # Заказы
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        total_orders = (await cursor.fetchone())[0]
        
        # Товары
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        total_products = (await cursor.fetchone())[0]
        
        # Выручка
        cursor = await db.execute("SELECT SUM(total_amount) FROM orders WHERE payment_status IN ('paid', 'delivered')")
        total_revenue = (await cursor.fetchone())[0] or 0
        
        return {
            "users": total_users,
            "orders": total_orders,
            "products": total_products,
            "revenue": total_revenue
        }

# =============================================================================
# АДМИНКА
# =============================================================================
async def get_all_products_with_stock():
    """Получить все товары с остатками"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products ORDER BY stock")
        return await cursor.fetchall()

async def update_product_stock(product_id: int, stock: int):
    """Обновить остаток товара"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (stock, product_id)
        )
        await db.commit()

async def delete_product_full(product_id: int):
    """Полное удаление товара"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await db.commit()

# =============================================================================
# СОБЫТИЯ (АНАЛИТИКА)
# =============================================================================
async def track_event(user_id: int, event_type: str, data: str = None):
    """Записать событие для аналитики"""
    # Заглушка - таблица events не создана, но функция нужна для импорта
    pass
