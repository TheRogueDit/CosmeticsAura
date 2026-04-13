from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_cart, clear_cart, remove_from_cart, get_product_by_id
from keyboards import cart_keyboard, back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

# =============================================================================
# ТЕКСТОВАЯ КНОПКА "🛍 Корзина"
# =============================================================================
@router.message(F.text == "🛍 Корзина")
async def cart_from_main_menu(message: Message):
    """Показать корзину при нажатии на текстовую кнопку"""
    user_id = message.from_user.id
    await show_cart_content(message, user_id)

# =============================================================================
# CALLBACK КНОПКА "Корзина"
# =============================================================================
@router.callback_query(F.data == "cart")
async def cart_callback(callback: CallbackQuery):
    """Показать корзину по callback"""
    user_id = callback.from_user.id
    await show_cart_content(callback, user_id)
    await callback.answer()

# =============================================================================
# ПОКАЗАТЬ СОДЕРЖИМОЕ КОРЗИНЫ
# =============================================================================
async def show_cart_content(target: Message | CallbackQuery, user_id: int):
    """Показать товары в корзине"""
    cart = await get_cart(user_id)
    
    if not cart:
        text = "🛍 **Корзина пуста**\n\nДобавьте товары из каталога!"
    else:
        total = sum(item[3] * item[1] for item in cart)  # price * quantity
        text = "🛍 **Ваша корзина:**\n\n"
        for item in cart:
            # item: (product_id, quantity, name, price)
            name = item[2] if len(item) > 2 else 'Товар'
            price = item[3] if len(item) > 3 else 0
            qty = item[1] if len(item) > 1 else 1
            text += f"• {name} x{qty} — {price * qty} ₽\n"
        text += f"\n💰 **Итого: {total} ₽**"
    
    kb = cart_keyboard() if cart else back_keyboard("main")
    
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")

# =============================================================================
# ОЧИСТИТЬ КОРЗИНУ
# =============================================================================
@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    await clear_cart(user_id)
    await callback.answer("🗑 Корзина очищена!", show_alert=True)
    await show_cart_content(callback, user_id)

# =============================================================================
# УДАЛИТЬ ТОВАР ИЗ КОРЗИНЫ
# =============================================================================
@router.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart_handler(callback: CallbackQuery):
    """Удалить товар из корзины"""
    try:
        product_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        await remove_from_cart(user_id, product_id)
        await callback.answer("❌ Товар удалён", show_alert=True)
        await show_cart_content(callback, user_id)
    except:
        await callback.answer("❌ Ошибка", show_alert=True)

# =============================================================================
# ОФОРМИТЬ ЗАКАЗ
# =============================================================================
@router.callback_query(F.data == "checkout")
async def checkout_handler(callback: CallbackQuery):
    """Начать оформление заказа"""
    user_id = callback.from_user.id
    cart = await get_cart(user_id)
    
    if not cart:
        await callback.answer("🛍 Корзина пуста!", show_alert=True)
        return
    
    total = sum(item[3] * item[1] for item in cart)
    
    await callback.message.answer(
        f"💳 **Оформление заказа**\n\n"
        f"💰 Сумма: {total} ₽\n\n"
        f"⚠️ Оплата 100% предоплатой.\n"
        f"Менеджер свяжется с вами после подтверждения.\n\n"
        f"📍 **Введите адрес доставки:**",
        parse_mode="Markdown"
    )
    await callback.answer()
