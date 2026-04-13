from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_cart, clear_cart, remove_from_cart, get_product_by_id
from keyboards import cart_keyboard, back_keyboard, cart_item_keyboard

router = Router()

# ============================================
# КНОПКА КОРЗИНА
# ============================================

@router.message(F.text == "🛍 Корзина")
async def show_cart(message: Message):
    """Показать содержимое корзины"""
    await view_cart(message)

# ============================================
# ПРОСМОТР КОРЗИНЫ
# ============================================

async def view_cart(message: Message):
    """Отобразить корзину"""
    user_id = message.from_user.id
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await message.answer(
            "🛒 **Ваша корзина пуста**\n\n"
            "Добавьте товары из каталога! 😊\n\n"
            "👉 Нажмите «Каталог» в меню, чтобы выбрать товары.",
            reply_markup=back_keyboard("catalog"),
            parse_mode="Markdown"
        )
        return
    
    total = 0
    text = "🛒 **Ваша корзина:**\n\n"
    
    for item in cart_items:
        product_id, quantity, name, price = item
        item_total = price * quantity
        total += item_total
        
        text += f"▫️ **{name}**\n"
        text += f"   {quantity} шт. × {price} ₽ = **{item_total} ₽**\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💰 **Итого: {total} ₽**\n\n"
    text += "📦 Для оформления нажмите кнопку ниже:"
    
    await message.answer(
        text,
        reply_markup=cart_keyboard(),
        parse_mode="Markdown"
    )

# ============================================
# CALLBACK: ПРОСМОТР КОРЗИНЫ
# ============================================

@router.callback_query(F.data == "view_cart")
async def view_cart_callback(callback: CallbackQuery):
    """Показать корзину (callback)"""
    await view_cart(callback.message)
    await callback.answer()

# ============================================
# УДАЛЕНИЕ ТОВАРА ИЗ КОРЗИНЫ
# ============================================

@router.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart_callback(callback: CallbackQuery):
    """Удалить конкретный товар из корзины"""
    try:
        product_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await remove_from_cart(callback.from_user.id, product_id)
    
    # Получаем название товара для уведомления
    product = await get_product_by_id(product_id)
    product_name = product[1] if product else "Товар"
    
    await callback.answer(f"❌ {product_name} удалён из корзины")
    
    # Обновляем вид корзины
    # Создаём новый объект Message-подобный для совместимости
    class FakeMessage:
        def __init__(self, bot, chat, from_user):
            self.bot = bot
            self.chat = chat
            self.from_user = from_user
    
    fake_msg = FakeMessage(
        callback.bot,
        callback.message.chat,
        callback.from_user
    )
    await view_cart(fake_msg)

# ============================================
# ОЧИСТКА КОРЗИНЫ
# ============================================

@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: CallbackQuery):
    """Очистить всю корзину"""
    await clear_cart(callback.from_user.id)
    
    await callback.message.answer(
        "🗑 **Корзина очищена!**\n\n"
        "Хотите вернуться к покупкам?",
        reply_markup=back_keyboard("catalog"),
        parse_mode="Markdown"
    )
    
    await callback.answer()

# ============================================
# ПЕРЕХОД К ОФОРМЛЕНИЮ
# ============================================

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery):
    """Начать оформление заказа"""
    cart_items = await get_cart(callback.from_user.id)
    
    if not cart_items:
        await callback.answer(
            "🛒 Корзина пуста! Добавьте товары.",
            show_alert=True
        )
        return
    
    # Считаем сумму
    total = sum(item[3] * item[1] for item in cart_items)  # price * quantity
    
    await callback.message.answer(
        f"💳 **Оформление заказа**\n\n"
        f"📦 Товаров в корзине: {len(cart_items)}\n"
        f"💰 Сумма: **{total} ₽**\n\n"
        f"⚠️ **Важно:** Оплата заказа 100% предоплатой.\n"
        f"После оплаты менеджер свяжется с вами.\n\n"
        f"Введите ваш **адрес доставки**:\n"
        f"(Город, улица, дом, квартира)",
        reply_markup=back_keyboard("cart"),
        parse_mode="Markdown"
    )
    
    await callback.answer()
    
    # Здесь будет переход к состоянию OrderState.address_input
    # Это обрабатывается в handlers/order.py
