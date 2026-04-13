from aiogram.fsm.state import State, StatesGroup

# ============================================
# ОФОРМЛЕНИЕ ЗАКАЗА
# ============================================

class OrderState(StatesGroup):
    """Состояния для оформления заказа"""
    address_input = State()      # Ввод адреса
    phone_input = State()        # Ввод телефона
    bonus_choice = State()       # Выбор использования бонусов
    promo_input = State()        # Ввод промокода
    payment_method = State()     # Выбор способа оплаты
    confirm = State()            # Подтверждение заказа

# ============================================
# ОТЗЫВЫ
# ============================================

class ReviewState(StatesGroup):
    """Состояния для создания отзыва"""
    product_id = State()         # Выбор товара
    rating = State()             # Оценка (звёзды)
    comment = State()            # Текст отзыва
    photo = State()              # Фото к отзыву
    confirm = State()            # Подтверждение отправки

# ============================================
# АДМИН-ПАНЕЛЬ: ТОВАРЫ
# ============================================

class AdminProductState(StatesGroup):
    """Состояния для добавления товара"""
    product_name = State()       # Название товара
    product_desc = State()       # Описание
    product_price = State()      # Цена
    product_category = State()   # Категория
    product_photo = State()      # Фото товара
    product_stock = State()      # Количество на складе

# ============================================
# АДМИН-ПАНЕЛЬ: ПРОМОКОДЫ
# ============================================

class AdminPromoState(StatesGroup):
    """Состояния для создания промокода"""
    promo_code = State()         # Код промокода
    promo_discount = State()     # Процент скидки
    promo_min_order = State()    # Минимальная сумма заказа
    promo_expires = State()      # Срок действия

# ============================================
# АДМИН-ПАНЕЛЬ: РАССЫЛКИ
# ============================================

class AdminMailingState(StatesGroup):
    """Состояния для создания рассылки"""
    mailing_text = State()       # Текст сообщения
    mailing_photo = State()      # Фото к рассылке
    mailing_confirm = State()    # Подтверждение отправки

# ============================================
# АДМИН-ПАНЕЛЬ: ПОЛЬЗОВАТЕЛИ
# ============================================

class AdminUserState(StatesGroup):
    """Состояния для работы с пользователями"""
    bonus_amount = State()       # Сумма бонусов для начисления
    ban_reason = State()         # Причина блокировки

# ============================================
# КОНКУРСЫ (АДМИН)
# ============================================

class AdminContestState(StatesGroup):
    """Состояния для создания конкурса"""
    contest_title = State()      # Название конкурса
    contest_desc = State()       # Описание
    contest_prize = State()      # Приз
    contest_type = State()       # Тип конкурса
    contest_end = State()        # Дата окончания
    contest_channel = State()    # Канал для подписки

# ============================================
# ПОДДЕРЖКА
# ============================================

class SupportState(StatesGroup):
    """Состояния для обращения в поддержку"""
    support_message = State()    # Текст сообщения
    support_photo = State()      # Фото (если нужно)

# ============================================
# ПОИСК
# ============================================

class SearchState(StatesGroup):
    """Состояния для поиска товаров"""
    search_query = State()       # Поисковый запрос

