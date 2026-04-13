from aiogram.fsm.state import State, StatesGroup

# =============================================================================
# ФОРМА ОФОРМЛЕНИЯ ЗАКАЗА
# =============================================================================
class OrderForm(StatesGroup):
    address = State()
    phone = State()

# =============================================================================
# ФОРМА ОТЗЫВА
# =============================================================================
class ReviewForm(StatesGroup):
    product_id = State()
    rating = State()
    text = State()
    comment = State()
    photo = State()

# Алиас для совместимости
ReviewState = ReviewForm

# =============================================================================
# ФОРМА ОБРАТНОЙ СВЯЗИ
# =============================================================================
class FeedbackForm(StatesGroup):
    text = State()

# =============================================================================
# АДМИНКА - ТОВАРЫ
# =============================================================================
class AdminProductForm(StatesGroup):
    product_name = State()
    product_desc = State()
    product_price = State()
    product_category = State()
    product_photo = State()
    product_stock = State()

# Алиас для совместимости
AdminProductState = AdminProductForm

# =============================================================================
# АДМИНКА - ПРОМОКОДЫ
# =============================================================================
class AdminPromoForm(StatesGroup):
    promo_code = State()
    promo_discount = State()
    promo_min_order = State()
    promo_max_uses = State()
    promo_expires = State()

# Алиас для совместимости
AdminPromoState = AdminPromoForm

# =============================================================================
# АДМИНКА - РАССЫЛКИ
# =============================================================================
class AdminMailingForm(StatesGroup):
    mailing_text = State()
    mailing_photo = State()
    mailing_confirm = State()
    mailing_button_text = State()
    mailing_button_url = State()

# Алиас для совместимости
AdminMailingState = AdminMailingForm

# =============================================================================
# АДМИНКА - ПОЛЬЗОВАТЕЛИ
# =============================================================================
class AdminUserForm(StatesGroup):
    user_id = State()
    message = State()
    ban_reason = State()
    bonus_amount = State()

# Алиас для совместимости
AdminUserState = AdminUserForm

# =============================================================================
# АДМИНКА - ОТЗЫВЫ
# =============================================================================
class AdminReviewForm(StatesGroup):
    review_id = State()
    response = State()

AdminReviewState = AdminReviewForm

# =============================================================================
# АДМИНКА - КОНКУРСЫ
# =============================================================================
class AdminContestForm(StatesGroup):
    title = State()
    description = State()
    prize = State()
    end_date = State()
    channel = State()

AdminContestState = AdminContestForm

# =============================================================================
# ПОИСК
# =============================================================================
class SearchForm(StatesGroup):
    query = State()

# =============================================================================
# ОПЛАТА
# =============================================================================
class PaymentForm(StatesGroup):
    amount = State()
    method = State()

# =============================================================================
# КОРЗИНА
# =============================================================================
class CartForm(StatesGroup):
    quantity = State()
