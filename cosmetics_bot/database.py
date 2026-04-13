import aiosqlite
from datetime import datetime

DB_NAME = "cosmetics.db"

# =============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# =============================================================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
        return await cursor.fetchall()

async def get_user_count():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_user_level(user_id: int):
    """Получить уровень пользователя на основе покупок"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT total_purchases FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        
        if not result:
            return 1
        
        purchases = result[0] or 0
        
        # Уровни: 1 (0-1000), 2 (1001-5000), 3 (5001-10000), 4 (10001+)
        if purchases >= 10000:
            return 4
        elif purchases >= 5000:
            return 3
        elif purchases >= 1000:
            return 2
        else:
            return 1

async def update_user_purchases(user_id: int, amount: float):
    """Обновить сумму покупок пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET total_purchases = total_purchases + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()

# =============================================================================
# ТОВАРЫ
# =============================================================================
async def get_all_products():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products ORDER BY category, name")
        return await cursor.fetchall()

async def get_products_by_category(category: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name",
            (category,)
        )
        return await cursor.fetchall()

async def get_all_categories():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_product_by_id(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()

async def add_product(name: str, description: str, price: float, category: str, stock: int, photo_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, description, price, category, stock, photo_id) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, category, stock, photo_id)
        )
        await db.commit()
        return cursor.lastrowid

async def update_product(product_id: int, name: str = None, price: float = None, stock: int = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if name:
            await db.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
        if price:
            await db.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
        if stock:
            await db.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
        await db.commit()

async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()

async def get_product_rating(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ? AND is_approved = 1",
            (product_id,)
        )
        return await cursor.fetchone()

# =============================================================================
# КОРЗИНА
# =============================================================================
async def get_cart(user_id: int):
    return await get_cart_items(user_id)

async def get_cart_items(user_id: int):
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()

async def remove_from_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await db.commit()

async def update_cart_quantity(user_id: int, product_id: int, quantity: int):
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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_order_by_id(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()

async def get_all_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders ORDER BY created_at DESC")
        return await cursor.fetchall()

async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET payment_status = ? WHERE id = ?",
            (status, order_id)
        )
        await db.commit()

async def get_pending_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE payment_status = 'pending' ORDER BY created_at"
        )
        return await cursor.fetchall()

async def get_daily_revenue(days: int = 30):
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

# =============================================================================
# БОНУСЫ
# =============================================================================
async def add_bonus(user_id: int, amount: float, reason: str):
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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT bonus_balance FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

async def use_bonus(user_id: int, amount: float):
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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM bonus_history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_bonus_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as users_with_bonus,
                SUM(bonus_balance) as total_bonus
            FROM users
        """)
        return await cursor.fetchone()

# =============================================================================
# ОТЗЫВЫ
# =============================================================================
async def add_review(user_id: int, product_id: int, rating: int, text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO reviews (user_id, product_id, rating, text) VALUES (?, ?, ?, ?)",
            (user_id, product_id, rating, text)
        )
        await db.commit()
        return cursor.lastrowid

async def get_product_reviews(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM reviews WHERE product_id = ? AND is_approved = 1",
            (product_id,)
        )
        return await cursor.fetchall()

async def get_pending_reviews():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM reviews WHERE is_approved = 0 ORDER BY created_at DESC"
        )
        return await cursor.fetchall()

async def approve_review(review_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE reviews SET is_approved = 1 WHERE id = ?",
            (review_id,)
        )
        await db.commit()

async def reject_review(review_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        await db.commit()

async def get_review_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 1")
        approved = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 0")
        pending = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT AVG(rating) FROM reviews WHERE is_approved = 1")
        avg_rating = (await cursor.fetchone())[0] or 0
        
        return {
            "approved": approved,
            "pending": pending,
            "avg_rating": round(avg_rating, 1)
        }

async def get_pending_review_requests():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM review_requests WHERE is_sent = 0 AND is_completed = 0"
        )
        return await cursor.fetchall()

# =============================================================================
# КОНКУРСЫ
# =============================================================================
async def get_active_contests():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM contests WHERE is_active = 1")
        return await cursor.fetchall()

async def join_contest(contest_id: int, user_id: int):
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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT c.* FROM contests c
            JOIN contest_participants cp ON c.id = cp.contest_id
            WHERE cp.user_id = ?
        """, (user_id,))
        return await cursor.fetchall()

async def get_contest_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                c.title,
                c.prize,
                COUNT(cp.user_id) as participants,
                c.is_active
            FROM contests c
            LEFT JOIN contest_participants cp ON c.id = cp.contest_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        return await cursor.fetchall()

async def add_contest(title: str, description: str, prize: str, end_date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO contests (title, description, prize, end_date) VALUES (?, ?, ?, ?)",
            (title, description, prize, end_date)
        )
        await db.commit()
        return cursor.lastrowid

async def toggle_contest(contest_id: int, is_active: int):
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
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return await cursor.fetchone()

async def get_dashboard_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        total_orders = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        total_products = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT SUM(total_amount) FROM orders WHERE payment_status IN ('paid', 'delivered')")
        total_revenue = (await cursor.fetchone())[0] or 0
        
        return {
            "users": total_users,
            "orders": total_orders,
            "products": total_products,
            "revenue": total_revenue
        }

async def track_event(user_id: int, event_type: str,  str = None):
    pass

# =============================================================================
# АДМИНКА
# =============================================================================
async def get_all_products_with_stock():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products ORDER BY stock")
        return await cursor.fetchall()

async def update_product_stock(product_id: int, stock: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (stock, product_id)
        )
        await db.commit()

async def delete_product_full(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        await db.commit()
