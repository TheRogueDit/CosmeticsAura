from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# ГЛАВНОЕ МЕНЮ (КЛАВИАТУРА ВНИЗУ)
# ============================================

def main_menu(is_admin: bool = False):
    """Главное меню пользователя"""
    kb = [
        [KeyboardButton(text="🛒 Каталог"), KeyboardButton(text="🛍 Корзина")],
        [KeyboardButton(text="🔥 Акции"), KeyboardButton(text="🎁 Бонусы")],
        [KeyboardButton(text="📝 Отзывы"), KeyboardButton(text="🏆 Розыгрыш")],
        [KeyboardButton(text="👩‍⚕️ Менеджер"), KeyboardButton(text="📦 Мои заказы")]
    ]
    
    if is_admin:
        kb.append([KeyboardButton(text="👨‍💼 Админ-панель")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ============================================
# КАТАЛОГ
# ============================================

def catalog_keyboard():
    """Категории товаров"""
    kb = [
        [InlineKeyboardButton(text="💄 Косметика", callback_data="cat_cosmetics")],
        [InlineKeyboardButton(text="💊 БАДы", callback_data="cat_bads")],
        [InlineKeyboardButton(text="🧴 Уход за телом", callback_data="cat_body")],
        [InlineKeyboardButton(text="🎁 Наборы", callback_data="cat_sets")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def product_keyboard(product_id: int):
    """Карточка товара"""
    kb = [
        [InlineKeyboardButton(text="➕ В корзину", callback_data=f"add_cart_{product_id}")],
        [InlineKeyboardButton(text="📝 Отзыв", callback_data=f"review_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_catalog")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# КОРЗИНА
# ============================================

def cart_keyboard():
    """Корзина"""
    kb = [
        [InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cart_item_keyboard(product_id: int):
    """Кнопка удаления товара из корзины"""
    kb = [
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"remove_cart_{product_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# ОПЛАТА И ЗАКАЗ
# ============================================

def payment_method_keyboard():
    """Выбор способа оплаты"""
    kb = [
        [InlineKeyboardButton(text="💳 Банковская карта", callback_data="pay_with_telegram")],
        [InlineKeyboardButton(text="🔗 Ссылка на оплату", callback_data="pay_link")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_checkout")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def bonus_keyboard():
    """Использование бонусов"""
    kb = [
        [InlineKeyboardButton(text="💰 Использовать бонусы", callback_data="pay_with_bonus")],
        [InlineKeyboardButton(text="➖ Пропустить", callback_data="skip_bonus")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def order_confirm_keyboard():
    """Подтверждение заказа"""
    kb = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# БОНУСЫ
# ============================================

def bonus_menu_keyboard():
    """Меню бонусов"""
    kb = [
        [InlineKeyboardButton(text="📜 История бонусов", callback_data="bonus_history")],
        [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="bonus_referral")],
        [InlineKeyboardButton(text="📋 Правила", callback_data="bonus_rules")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# ОТЗЫВЫ
# ============================================

def reviews_keyboard():
    """Меню отзывов"""
    kb = [
        [InlineKeyboardButton(text="📚 Читать отзывы", callback_data="read_reviews")],
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="write_review")],
        [InlineKeyboardButton(text="📊 Моя история отзывов", callback_data="my_reviews")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def rating_keyboard():
    """Выбор рейтинга (звёзды)"""
    kb = [
        [
            InlineKeyboardButton(text="⭐", callback_data="rating_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rating_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rating_3")
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rating_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rating_5")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_reviews")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def review_form_keyboard():
    """Форма отзыва"""
    kb = [
        [InlineKeyboardButton(text="📸 Добавить фото", callback_data="review_add_photo")],
        [InlineKeyboardButton(text="✅ Отправить", callback_data="review_finish")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_reviews")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# КОНКУРСЫ
# ============================================

def contest_list_keyboard():
    """Список конкурсов"""
    kb = [
        [InlineKeyboardButton(text="🎫 Мои участия", callback_data="my_contests")],
        [InlineKeyboardButton(text="📋 Правила конкурсов", callback_data="contest_rules")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def contest_detail_keyboard(contest_id: int, channel_required: str = None):
    """Детали конкурса"""
    kb = [
        [InlineKeyboardButton(text="🎟 Участвовать", callback_data=f"join_contest_{contest_id}")]
    ]
    
    if channel_required:
        kb.append([InlineKeyboardButton(
            text=f"📢 Подписаться на @{channel_required.replace('@', '')}",
            url=f"https://t.me/{channel_required.replace('@', '')}"
        )])
    
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_contests")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# АДМИН-ПАНЕЛЬ
# ============================================

def admin_main_keyboard():
    """Главное меню админа"""
    kb = [
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products"),
         InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
         InlineKeyboardButton(text="📝 Отзывы", callback_data="admin_reviews")],
        [InlineKeyboardButton(text="🏷 Промокоды", callback_data="admin_promo"),
         InlineKeyboardButton(text="📢 Рассылки", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics_main"),
         InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📋 Логи", callback_data="admin_logs"),
         InlineKeyboardButton(text="🔙 В бот", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_products_keyboard():
    """Управление товарами"""
    kb = [
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📦 Список товаров", callback_data="admin_products_list")],
        [InlineKeyboardButton(text="⚠️ Заканчиваются", callback_data="admin_low_stock")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_orders_keyboard():
    """Управление заказами"""
    kb = [
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_orders_all")],
        [InlineKeyboardButton(text="⏳ Ожидают оплаты", callback_data="admin_orders_pending")],
        [InlineKeyboardButton(text="✅ Оплачены", callback_data="admin_orders_paid")],
        [InlineKeyboardButton(text="🚚 В доставке", callback_data="admin_orders_shipped")],
        [InlineKeyboardButton(text="📬 Доставлены", callback_data="admin_orders_delivered")],
        [InlineKeyboardButton(text="❌ Отменены", callback_data="admin_orders_cancelled")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_order_keyboard(order_id: int):
    """Действия с заказом"""
    kb = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_order_confirm_{order_id}"),
            InlineKeyboardButton(text="🚚 Отправить", callback_data=f"admin_order_ship_{order_id}")
        ],
        [
            InlineKeyboardButton(text="📬 Доставлен", callback_data=f"admin_order_deliver_{order_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_order_cancel_{order_id}")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль клиента", callback_data=f"admin_user_profile_{order_id}"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_orders")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_users_keyboard():
    """Управление пользователями"""
    kb = [
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users_list")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_users_search")],
        [InlineKeyboardButton(text="📊 Топ по покупкам", callback_data="admin_users_top")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_promo_keyboard():
    """Управление промокодами"""
    kb = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")],
        [InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin_promo_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_mailing_keyboard():
    """Управление рассылками"""
    kb = [
        [InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_mailing_create")],
        [InlineKeyboardButton(text="📜 История рассылок", callback_data="admin_mailing_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_settings_keyboard():
    """Настройки бота"""
    kb = [
        [InlineKeyboardButton(text="🔧 Режим обслуживания", callback_data="admin_toggle_maintenance")],
        [InlineKeyboardButton(text="🎁 Настройка бонусов", callback_data="admin_settings_bonus")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_reviews_keyboard():
    """Модерация отзывов"""
    kb = [
        [InlineKeyboardButton(text="🔍 На модерации", callback_data="admin_reviews_pending")],
        [InlineKeyboardButton(text="✅ Опубликованные", callback_data="admin_reviews_approved")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_reviews_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# АНАЛИТИКА
# ============================================

def analytics_keyboard():
    """Меню аналитики"""
    kb = [
        [InlineKeyboardButton(text="💰 Продажи", callback_data="analytics_sales"),
         InlineKeyboardButton(text="👥 Пользователи", callback_data="analytics_users")],
        [InlineKeyboardButton(text="📦 Товары", callback_data="analytics_products"),
         InlineKeyboardButton(text="🎁 Бонусы", callback_data="analytics_bonuses")],
        [InlineKeyboardButton(text="🏆 Конкурсы", callback_data="analytics_contests")],
        [InlineKeyboardButton(text="📤 Экспорт CSV", callback_data="analytics_export")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def period_keyboard(report_type: str):
    """Выбор периода для отчёта"""
    kb = [
        [InlineKeyboardButton(text="1 день", callback_data=f"period_{report_type}_1d"),
         InlineKeyboardButton(text="7 дней", callback_data=f"period_{report_type}_7d")],
        [InlineKeyboardButton(text="30 дней", callback_data=f"period_{report_type}_30d"),
         InlineKeyboardButton(text="Все время", callback_data=f"period_{report_type}_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="analytics_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ============================================
# УНИВЕРСАЛЬНЫЕ КНОПКИ
# ============================================

def back_keyboard(back_to: str):
    """Кнопка назад"""
    back_map = {
        "main": "🏠 Главное меню",
        "catalog": "📚 Каталог",
        "cart": "🛍 Корзина",
        "checkout": "💳 Оформление",
        "bonus": "🎁 Бонусы",
        "reviews": "📝 Отзывы",
        "contests": "🏆 Конкурсы",
        "admin": "👨‍💼 Админ-панель",
        "admin_products": "📦 Товары",
        "admin_orders": "📋 Заказы",
        "admin_users": "👥 Пользователи",
        "admin_promo": "🏷 Промокоды",
        "admin_mailing": "📢 Рассылки",
        "admin_reviews": "📝 Отзывы",
        "analytics": "📊 Аналитика"
    }
    
    kb = [[InlineKeyboardButton(
        text=back_map.get(back_to, "🔙 Назад"),
        callback_data=f"back_{back_to}"
    )]]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_keyboard():
    """Кнопка отмены"""
    kb = [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def yes_no_keyboard(yes_callback: str, no_callback: str):
    """Кнопки Да/Нет"""
    kb = [
        [InlineKeyboardButton(text="✅ Да", callback_data=yes_callback)],
        [InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

