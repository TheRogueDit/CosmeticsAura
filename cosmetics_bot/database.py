import aiosqlite
import json
from datetime import datetime

# Для проверки подписки
bot = None  # Будет установлен в bot.py

DB_NAME = "cosmetics.db"

# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================

async def init_db():
    """Создать все таблицы при первом запуске"""
    async with aiosqlite.connect(DB_NAME) as db:
        
        # === ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT,
                bonus_balance INTEGER DEFAULT 0,
                total_purchases INTEGER DEFAULT 0,
                referral_code TEXT,
                referred_by INTEGER,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА ТОВАРОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                category TEXT,
                photo_id TEXT,
                stock INTEGER DEFAULT 100,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА КОРЗИНЫ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        
        # === ТАБЛИЦА ЗАКАЗОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount INTEGER,
                bonus_used INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                payment_method TEXT,
                address TEXT,
                phone TEXT,
                admin_group_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # === ТАБЛИЦА ПЛАТЕЖЕЙ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,
                amount INTEGER NOT NULL,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                payment_id TEXT,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
        
        # === ТАБЛИЦА ИСТОРИИ БОНУСОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bonus_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # === ТАБЛИЦА ПРОМОКОДОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount_percent INTEGER,
                min_order INTEGER DEFAULT 0,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА КОНКУРСОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                prize TEXT NOT NULL,
                contest_type TEXT DEFAULT 'giveaway',
                end_date TIMESTAMP NOT NULL,
                channel_required TEXT,
                min_purchases INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                winner_id INTEGER,
                ended_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА УЧАСТНИКОВ КОНКУРСОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contest_participants (
                user_id INTEGER,
                contest_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, contest_id),
                FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE
            )
        """)
        
        # === ТАБЛИЦА ОТЗЫВОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id INTEGER,
                product_id INTEGER,
                rating INTEGER NOT NULL,
                comment TEXT,
                photos TEXT,
                is_approved INTEGER DEFAULT 0,
                is_verified_purchase INTEGER DEFAULT 0,
                admin_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # === ТАБЛИЦА ЗАПРОСОВ НА ОТЗЫВЫ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS review_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id INTEGER,
                product_id INTEGER,
                is_sent INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА АНАЛИТИКИ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА ЛОГОВ АДМИНОВ ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА РАССЫЛОК ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                photo_id TEXT,
                total_users INTEGER,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # === ТАБЛИЦА НАСТРОЕК БОТА ===
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === НАСТРОЙКИ ПО УМОЛЧАНИЮ ===
        await db.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('is_maintenance', '0')")
        await db.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bonus_percent', '10')")
        await db.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('free_shipping_threshold', '5000')")
        
        # === ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ===
        await db.execute("CREATE INDEX IF NOT EXISTS idx_users_bonus ON users(bonus_balance)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_payment ON orders(payment_status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews(is_approved)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON analytics_events(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_admin ON admin_logs(admin_id)")
        
        await db.commit()

# ============================================
# ПОЛЬЗОВАТЕЛИ
# ============================================

async def add_user(user_id: int, username: str, first_name: str, phone: str = None):
    """Добавить или обновить пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, phone) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, phone)
        )
        await db.commit()

async def get_user(user_id: int):
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def update_user_phone(user_id: int, phone: str):
    """Обновить телефон пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
        await db.commit()

async def get_all_users(limit: int = 100, offset: int = 0):
    """Получить всех пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM users ORDER BY registered_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return await cursor.fetchall()

async def search_users(query: str, limit: int = 20):
    """Поиск пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE first_name LIKE ? OR username LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        return await cursor.fetchall()

async def ban_user(user_id: int, reason: str = None):
    """Заблокировать пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?",
            (reason, user_id)
        )
        await db.commit()

async def unban_user(user_id: int):
    """Разблокировать пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

# ============================================
# БОНУСНАЯ СИСТЕМА
# ============================================

async def get_bonus_balance(user_id: int) -> int:
    """Получить баланс бонусов"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT bonus_balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0

async def add_bonus(user_id: int, amount: int, reason: str = "purchase"):
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

async def spend_bonus(user_id: int, amount: int) -> bool:
    """Списать бонусы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT bonus_balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        
        if result and result[0] >= amount:
            await db.execute(
                "UPDATE users SET bonus_balance = bonus_balance - ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.execute(
                "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
                (user_id, -amount, "order_payment")
            )
            await db.commit()
            return True
        return False

async def get_bonus_history(user_id: int, limit: int = 10):
    """Получить историю бонусов"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT amount, reason, created_at FROM bonus_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        return await cursor.fetchall()

async def get_user_level(user_id: int) -> dict:
    """Получить уровень пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT total_purchases FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        total = result[0] if result else 0
        
        if total >= 50000:
            return {"level": "Platinum", "percent": 15, "color": "💎"}
        elif total >= 15000:
            return {"level": "Gold", "percent": 12, "color": "🥇"}
        elif total >= 5000:
            return {"level": "Silver", "percent": 10, "color": "🥈"}
        else:
            return {"level": "Bronze", "percent": 5, "color": "🥉"}

async def update_user_purchases(user_id: int, amount: int):
    """Обновить сумму покупок"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET total_purchases = total_purchases + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()

async def get_referral_code(user_id: int) -> str:
    """Получить реферальный код"""
    import random
    import string
    
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT referral_code FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        
        code = 'REF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        await db.execute(
            "UPDATE users SET referral_code = ? WHERE user_id = ?",
            (code, user_id)
        )
        await db.commit()
        return code

async def apply_referral(new_user_id: int, referrer_code: str):
    """Применить реферальный код"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE referral_code = ?",
            (referrer_code,)
        )
        result = await cursor.fetchone()
        
        if result and result[0] != new_user_id:
            referrer_id = result[0]
            await db.execute(
                "UPDATE users SET bonus_balance = bonus_balance + 500 WHERE user_id IN (?, ?)",
                (referrer_id, new_user_id)
            )
            await db.execute(
                "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
                (referrer_id, 500, "referral_bonus")
            )
            await db.execute(
                "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
                (new_user_id, 500, "referral_welcome")
            )
            await db.execute(
                "UPDATE users SET referred_by = ? WHERE user_id = ?",
                (referrer_id, new_user_id)
            )
            await db.commit()
            return True
        return False

async def get_referrals_count(user_id: int) -> int:
    """Получить количество приглашённых"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0
    
async def get_bonus_stats():
    """Статистика по бонусам"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Всего начислено/списано
        cursor = await db.execute("""
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as issued,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as spent
            FROM bonus_history
        """)
        issued, spent = await cursor.fetchone()
        
        # Топ пользователей по бонусам
        cursor = await db.execute("""
            SELECT u.first_name, u.bonus_balance, u.total_purchases
            FROM users u
            WHERE u.bonus_balance > 0
            ORDER BY u.bonus_balance DESC
            LIMIT 5
        """)
        top_users = await cursor.fetchall()
        
        return {
            "issued": issued or 0,
            "spent": spent or 0,
            "top_users": top_users
        }

# ============================================
# ТОВАРЫ
# ============================================

async def add_product(name: str, description: str, price: int, category: str, 
                      photo_id: str, stock: int = 100) -> int:
    """Добавить товар"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, description, price, category, photo_id, stock) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, category, photo_id, stock)
        )
        product_id = cursor.lastrowid
        await db.commit()
        return product_id

async def get_product_by_id(product_id: int):
    """Получить товар по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return await cursor.fetchone()

async def get_all_products(limit: int = 100, offset: int = 0):
    """Получить все товары"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return await cursor.fetchall()

async def get_products_by_category(category: str):
    """Получить товары по категории"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY created_at DESC",
            (category,)
        )
        return await cursor.fetchall()

async def update_product(product_id: int, **kwargs):
    """Обновить товар"""
    allowed_fields = ['name', 'description', 'price', 'category', 'photo_id', 'stock', 'is_active']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if updates:
        values.append(product_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                f"UPDATE products SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            await db.commit()

async def delete_product(product_id: int):
    """Удалить товар"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()

async def get_low_stock_products(threshold: int = 10):
    """Получить товары с низким запасом"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE stock < ? AND is_active = 1 ORDER BY stock ASC",
            (threshold,)
        )
        return await cursor.fetchall()

async def get_product_stats():
    """Статистика по товарам"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 
                p.name,
                p.category,
                p.price,
                p.stock,
                COALESCE(SUM(c.quantity), 0) as sold,
                COALESCE(SUM(c.quantity * p.price), 0) as revenue
            FROM products p
            LEFT JOIN cart c ON p.id = c.product_id
            GROUP BY p.id
            ORDER BY revenue DESC
        """)
        return await cursor.fetchall()
    
# ============================================
# КОРЗИНА
# ============================================

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Добавить в корзину"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?
            """,
            (user_id, product_id, quantity, quantity)
        )
        await db.commit()

async def get_cart(user_id: int):
    """Получить корзину"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT c.product_id, c.quantity, p.name, p.price 
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = ?
        """, (user_id,))
        return await cursor.fetchall()

async def clear_cart(user_id: int):
    """Очистить корзину"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()

async def remove_from_cart(user_id: int, product_id: int):
    """Удалить из корзины"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        await db.commit()

# ============================================
# ЗАКАЗЫ
# ============================================

async def create_order(user_id: int, total_amount: int, bonus_used: int, 
                       address: str, phone: str = None) -> int:
    """Создать заказ"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders (user_id, total_amount, bonus_used, address, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, total_amount, bonus_used, address, phone)
        )
        order_id = cursor.lastrowid
        await db.commit()
        return order_id

async def get_order_by_id(order_id: int):
    """Получить заказ по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()

async def get_user_orders(user_id: int):
    """Получить заказы пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def get_all_orders(status: str = None, limit: int = 50, offset: int = 0):
    """Получить все заказы"""
    async with aiosqlite.connect(DB_NAME) as db:
        if status:
            cursor = await db.execute(
                """
                SELECT o.*, u.first_name, u.username, u.phone
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                WHERE o.payment_status = ?
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (status, limit, offset)
            )
        else:
            cursor = await db.execute(
                """
                SELECT o.*, u.first_name, u.username, u.phone
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
        return await cursor.fetchall()

async def update_order_status(order_id: int, status: str):
    """Обновить статус заказа"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, order_id)
        )
        await db.commit()

async def update_payment_status(order_id: int, status: str):
    """Обновить статус оплаты"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET payment_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, order_id)
        )
        await db.commit()

async def cancel_order(order_id: int):
    """Отменить заказ с возвратом бонусов"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id, bonus_used FROM orders WHERE id = ?",
            (order_id,)
        )
        result = await cursor.fetchone()
        
        if result:
            user_id, bonus_used = result
            if bonus_used > 0:
                await db.execute(
                    "UPDATE users SET bonus_balance = bonus_balance + ? WHERE user_id = ?",
                    (bonus_used, user_id)
                )
                await db.execute(
                    "INSERT INTO bonus_history (user_id, amount, reason) VALUES (?, ?, ?)",
                    (user_id, bonus_used, f"order_cancel_{order_id}")
                )
            await db.execute(
                "UPDATE orders SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (order_id,)
            )
        await db.commit()

# ============================================
# ПЛАТЕЖИ
# ============================================

async def create_payment(order_id: int, user_id: int, amount: int, 
                         payment_method: str, payment_id: str = None) -> int:
    """Создать платёж"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO payments (order_id, user_id, amount, payment_method, payment_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, user_id, amount, payment_method, payment_id)
        )
        pid = cursor.lastrowid
        await db.commit()
        return pid

async def get_payment_by_order(order_id: int):
    """Получить платёж по заказу"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM payments WHERE order_id = ?",
            (order_id,)
        )
        return await cursor.fetchone()

# ============================================
# ПРОМОКОДЫ
# ============================================

async def create_promo_code(code: str, discount_percent: int, 
                           min_order: int = 0, max_uses: int = None,
                           expires_at: str = None):
    """Создать промокод"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO promo_codes (code, discount_percent, min_order, max_uses, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (code, discount_percent, min_order, max_uses, expires_at)
        )
        await db.commit()

async def check_promo_code(code: str) -> int:
    """Проверить промокод"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT discount_percent FROM promo_codes WHERE code = ? AND is_active = 1",
            (code,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_all_promo_codes():
    """Получить все промокоды"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM promo_codes ORDER BY created_at DESC")
        return await cursor.fetchall()

async def deactivate_promo_code(code: str):
    """Деактивировать промокод"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE promo_codes SET is_active = 0 WHERE code = ?",
            (code,)
        )
        await db.commit()

# ============================================
# КОНКУРСЫ
# ============================================

async def create_contest(title: str, description: str, prize: str, 
                         contest_type: str, end_date: str,
                         channel_required: str = None, min_purchases: int = 0) -> int:
    """Создать конкурс"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO contests (title, description, prize, contest_type, end_date, channel_required, min_purchases)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, prize, contest_type, end_date, channel_required, min_purchases)
        )
        contest_id = cursor.lastrowid
        await db.commit()
        return contest_id

async def get_active_contests():
    """Получить активные конкурсы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM contests WHERE is_active = 1 AND end_date > datetime('now') ORDER BY end_date ASC"
        )
        return await cursor.fetchall()

async def get_contest_by_id(contest_id: int):
    """Получить конкурс по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM contests WHERE id = ?", (contest_id,))
        return await cursor.fetchone()

async def join_contest(user_id: int, contest_id: int):
    """Присоединиться к конкурсу"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO contest_participants (user_id, contest_id) VALUES (?, ?)",
            (user_id, contest_id)
        )
        await db.commit()

async def can_join_contest(user_id: int, contest: tuple):
    """Проверить, может ли пользователь участвовать в конкурсе"""
    from aiogram.exceptions import TelegramBadRequest
    
    # Проверка подписки на канал
    if contest[6]:  # channel_required
        try:
            member = await bot.get_chat_member(contest[6], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False, "❌ Вы не подписаны на канал"
        except:
            return False, "❌ Не удалось проверить подписку"
    
    # Проверка: уже участвует?
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM contest_participants WHERE user_id = ? AND contest_id = ?",
            (user_id, contest[0])
        )
        if await cursor.fetchone():
            return False, "✅ Вы уже участвуете в этом конкурсе!"
    
    return True, "OK"

async def get_contest_participants(contest_id: int):
    """Получить участников конкурса"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT u.user_id, u.username, u.first_name, cp.joined_at 
            FROM contest_participants cp
            JOIN users u ON cp.user_id = u.user_id
            WHERE cp.contest_id = ?
            """,
            (contest_id,)
        )
        return await cursor.fetchall()

async def get_user_contests(user_id: int):
    """Получить конкурсы пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT c.id, c.title, c.prize, c.end_date, c.winner_id
            FROM contests c
            JOIN contest_participants cp ON c.id = cp.contest_id
            WHERE cp.user_id = ?
            ORDER BY c.end_date DESC
            """,
            (user_id,)
        )
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
    
async def pick_winner(contest_id: int):
    """Выбрать победителя"""
    import random
    
    participants = await get_contest_participants(contest_id)
    if not participants:
        return None
    
    winner = random.choice(participants)
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE contests SET winner_id = ?, is_active = 0, ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (winner[0], contest_id)
        )
        await db.commit()
    
    return winner

# ============================================
# ОТЗЫВЫ
# ============================================

async def create_review(user_id: int, order_id: int, product_id: int, 
                        rating: int, comment: str, photos: list = None) -> int:
    """Создать отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO reviews (user_id, order_id, product_id, rating, comment, photos, is_verified_purchase)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (user_id, order_id, product_id, rating, comment, json.dumps(photos) if photos else None)
        )
        review_id = cursor.lastrowid
        await db.commit()
        return review_id

async def get_product_reviews(product_id: int, approved_only: bool = True, limit: int = 20):
    """Получить отзывы о товаре"""
    async with aiosqlite.connect(DB_NAME) as db:
        if approved_only:
            cursor = await db.execute(
                """
                SELECT r.*, u.first_name, u.username
                FROM reviews r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.product_id = ? AND r.is_approved = 1
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (product_id, limit)
            )
        else:
            cursor = await db.execute(
                """
                SELECT r.*, u.first_name, u.username
                FROM reviews r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.product_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (product_id, limit)
            )
        return await cursor.fetchall()
    
async def get_user_reviews(user_id: int, limit: int = 20):
    """Получить отзывы пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT r.*, p.name as product_name
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        return await cursor.fetchall()
    
async def get_pending_reviews(limit: int = 50):
    """Получить отзывы на модерации"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT r.*, u.first_name, u.username, p.name as product_name
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            JOIN products p ON r.product_id = p.id
            WHERE r.is_approved = 0
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        return await cursor.fetchall()

async def get_pending_review_requests():
    """Получить запросы на отзывы"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM review_requests WHERE is_sent = 0 AND is_completed = 0"
        )
        return await cursor.fetchall()
    
async def approve_review(review_id: int, admin_response: str = None):
    """Одобрить отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE reviews SET is_approved = 1, admin_response = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (admin_response, review_id)
        )
        await db.commit()

async def reject_review(review_id: int):
    """Отклонить отзыв"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        await db.commit()

async def get_product_rating(product_id: int) -> dict:
    """Получить рейтинг товара"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE product_id = ? AND is_approved = 1",
            (product_id,)
        )
        result = await cursor.fetchone()
        return {
            "avg_rating": round(result[0], 1) if result[0] else 0,
            "count": result[1] or 0
        }

async def get_review_stats():
    """Статистика по отзывам"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Всего отзывов
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 1")
        approved = (await cursor.fetchone())[0]
        
        # На модерации
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 0")
        pending = (await cursor.fetchone())[0]
        
        # Средний рейтинг по магазину
        cursor = await db.execute("SELECT AVG(rating) FROM reviews WHERE is_approved = 1")
        avg_rating = (await cursor.fetchone())[0] or 0
        
        # Топ товаров по отзывам
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
    
# ============================================
# АНАЛИТИКА
# ============================================

async def track_event(user_id: int, event_type: str, event_data: dict = None, value: float = None):
    """Записать событие аналитики"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO analytics_events (user_id, event_type, event_data, value) VALUES (?, ?, ?, ?)",
            (user_id, event_type, json.dumps(event_data) if event_data else None, value)
        )
        await db.commit()

async def get_sales_stats(period: str = "7d") -> dict:
    """Статистика продаж"""
    date_filter = ""
    if period == "1d":
        date_filter = "AND created_at >= datetime('now', '-1 day')"
    elif period == "7d":
        date_filter = "AND created_at >= datetime('now', '-7 days')"
    elif period == "30d":
        date_filter = "AND created_at >= datetime('now', '-30 days')"
    
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0), COUNT(*) 
            FROM orders 
            WHERE status IN ('paid', 'delivered', 'confirmed', 'shipped') {date_filter}
        """)
        revenue, orders_count = await cursor.fetchone()
        
        avg_check = revenue / orders_count if orders_count > 0 else 0
        
        cursor = await db.execute(f"""
            SELECT COUNT(*) FROM users 
            WHERE registered_at >= datetime('now', '-{period.replace("d", " days").replace("all", "10000 days")}')
        """)
        new_users = (await cursor.fetchone())[0]
        
        return {
            "revenue": revenue,
            "orders": orders_count,
            "avg_check": round(avg_check, 2),
            "new_users": new_users
        }

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
    
async def get_dashboard_stats() -> dict:
    """Статистика для дашборда"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending'")
        pending_orders = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'paid'")
        total_revenue = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        total_products = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM products WHERE stock < 10 AND is_active = 1")
        low_stock = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 1")
        approved_reviews = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 0")
        pending_reviews = (await cursor.fetchone())[0]
        
        return {
            "total_users": total_users,
            "pending_orders": pending_orders,
            "total_revenue": total_revenue,
            "total_products": total_products,
            "low_stock": low_stock,
            "approved_reviews": approved_reviews,
            "pending_reviews": pending_reviews
        }

# ============================================
# АДМИН-ЛОГИРОВАНИЕ
# ============================================

async def log_admin_action(admin_id: int, action: str, details: str = None):
    """Записать действие админа"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO admin_logs (admin_id, action, details) VALUES (?, ?, ?)",
            (admin_id, action, details)
        )
        await db.commit()

async def get_admin_logs(admin_id: int = None, limit: int = 50):
    """Получить логи"""
    async with aiosqlite.connect(DB_NAME) as db:
        if admin_id:
            cursor = await db.execute(
                "SELECT * FROM admin_logs WHERE admin_id = ? ORDER BY created_at DESC LIMIT ?",
                (admin_id, limit)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        return await cursor.fetchall()

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

async def get_bot_setting(key: str):
    """Получить настройку"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def update_bot_setting(key: str, value: str):
    """Обновить настройку"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bot_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, value)
        )
        await db.commit()

# ============================================
# РАССЫЛКИ
# ============================================

async def create_mailing(message_text: str, photo_id: str = None) -> int:
    """Создать рассылку"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO mailings (message_text, photo_id, total_users) VALUES (?, ?, (SELECT COUNT(*) FROM users))",
            (message_text, photo_id)
        )
        mailing_id = cursor.lastrowid
        await db.commit()
        return mailing_id

async def update_mailing_status(mailing_id: int, status: str, sent: int = 0, failed: int = 0):
    """Обновить статус рассылки"""
    async with aiosqlite.connect(DB_NAME) as db:
        if status == 'completed':
            await db.execute(
                """
                UPDATE mailings 
                SET status = ?, sent_count = ?, failed_count = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, sent, failed, mailing_id)
            )
        else:
            await db.execute(
                "UPDATE mailings SET status = ?, sent_count = ?, failed_count = ? WHERE id = ?",
                (status, sent, failed, mailing_id)
            )
        await db.commit()

async def get_mailing_history(limit: int = 10):
    """История рассылок"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM mailings ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return await cursor.fetchall()
