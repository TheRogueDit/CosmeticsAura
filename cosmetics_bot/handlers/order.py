from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from states import OrderForm
from config import BOT_TOKEN, ADMIN_IDS, ADMIN_GROUP_ID
from database import get_cart, clear_cart, create_order, get_user_orders, add_bonus, update_user_purchases
from keyboards import back_keyboard
from aiogram import Bot

bot = Bot(token=BOT_TOKEN)
router = Router()

# =============================================================================
# КНОПКА "ОФОРМИТЬ ЗАКАЗ"
# =============================================================================
@router.callback_query(F.data == "checkout")
async def checkout_callback(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа"""
    user_id = callback.from_user.id
    
    cart_items = await get_cart(user_id)
    
    if not cart_items:
        await callback.message.answer("🛒 Ваша корзина пуста!")
        await callback.answer()
        return
    
    # Считаем сумму (кортеж: product_id, quantity, name, price)
    total = 0
    items_text = "📦 **Ваш заказ:**\n\n"
    for item in cart_items:
        name = item[2] if len(item) > 2 else 'Товар'
        price = item[3] if len(item) > 3 else 0
        quantity = item[1] if len(item) > 1 else 1
        
        total += price * quantity
        items_text += f"• {name} x{quantity} - {price * quantity} ₽\n"
    
    items_text += f"\n💰 **Итого: {total} ₽**"
    
    await callback.message.answer(
        items_text + "\n\n⚠️ Оплата 100% предоплатой. Менеджер свяжется после оплаты.",
        reply_markup=back_keyboard("main"),
        parse_mode="Markdown"
    )
    
    await callback.message.answer(
        "📍 **Введите адрес доставки:**\n"
        "Город, улица, дом, квартира",
        parse_mode="Markdown"
    )
    
    await state.set_state(OrderForm.address)
    await callback.answer()

# =============================================================================
# ОБРАБОТКА АДРЕСА → запрашиваем телефон
# =============================================================================
@router.message(OrderForm.address)
async def process_address(message: Message, state: FSMContext):
    """Сохраняем адрес и запрашиваем телефон"""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    await state.update_data(address=address)
    
    await message.answer(
        "📱 **Введите номер телефона:**\n"
        "Например: +7 (999) 123-45-67",
        parse_mode="Markdown"
    )
    
    await state.set_state(OrderForm.phone)

# =============================================================================
# ОБРАБОТКА ТЕЛЕФОНА → создаём заказ
# =============================================================================
@router.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    """Сохраняем телефон, создаём заказ и отправляем уведомления"""
    try:
        phone = message.text.strip()
        
        # Простая валидация телефона
        if len(phone) < 10 or not any(c.isdigit() for c in phone):
            await message.answer("❌ Введите корректный номер телефона:")
            return
        
        user_id = message.from_user.id
        
        # Получаем данные из state
        data = await state.get_data()
        address = data.get("address", "Не указан")
        
        # Получаем товары из корзины
        cart_items = await get_cart(user_id)
        
        if not cart_items:
            await message.answer("❌ Корзина пуста! Начните заново.")
            await state.clear()
            return
        
        # Считаем сумму (кортеж: product_id, quantity, name, price)
        total = 0
        items_text = ""
        for item in cart_items:
            name = item[2] if len(item) > 2 else 'Товар'
            price = item[3] if len(item) > 3 else 0
            quantity = item[1] if len(item) > 1 else 1
            
            total += price * quantity
            items_text += f"• {name} x{quantity} - {price * quantity} ₽\n"
        
        # === СОЗДАЁМ ЗАКАЗ (правильные параметры!) ===
        order_id = await create_order(
            user_id=user_id,
            total_amount=total,      # ✅ Правильное имя параметра
            bonus_used=0,            # ✅ Обязательный параметр
            address=f"{address}\n📞 {phone}",  # ✅ Адрес + телефон
            phone=phone              # ✅ Телефон отдельно
        )
        
        # Очищаем корзину
        await clear_cart(user_id)
        
        # Обновляем статистику покупок пользователя
        await update_user_purchases(user_id, total)
        
        # === ОТПРАВКА УВЕДОМЛЕНИЙ ===
        
        # 1. В админ-группу
        try:
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"🔔 **НОВЫЙ ЗАКАЗ №{order_id}**\n\n"
                     f"👤 Клиент: @{message.from_user.username or 'нет юзернейма'}\n"
                     f"📞 Телефон: {phone}\n"
                     f"📦 Товары:\n{items_text}"
                     f"💰 Итого: {total} ₽\n"
                     f"📍 Адрес: {address}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ Ошибка отправки в группу: {e}")
        
        # 2. Каждому админу в ЛС
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Новый заказ №{order_id}**\n\n"
                         f"👤 Клиент: @{message.from_user.username}\n"
                         f"📞 Телефон: {phone}\n"
                         f"💰 Сумма: {total} ₽\n"
                         f"📍 Адрес: {address}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"❌ Ошибка отправки админу {admin_id}: {e}")
        
        # 3. Подтверждение пользователю
        await message.answer(
            f"✅ **ЗАКАЗ №{order_id} ОФОРМЛЕН!**\n\n"
            f"💰 Сумма: {total} ₽\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n\n"
            f"🔹 Менеджер свяжется с вами в ближайшее время для подтверждения оплаты.\n"
            f"🔹 После оплаты ваш заказ будет отправлен.",
            parse_mode="Markdown"
        )
        
        # Завершаем машину состояний
        await state.clear()
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в process_phone: {e}")
        await message.answer(f"❌ Произошла ошибка при оформлении заказа. Попробуйте позже.")
        await state.clear()

# =============================================================================
# КНОПКА "МОИ ЗАКАЗЫ"
# =============================================================================
@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery, state: FSMContext):
    """Показать заказы пользователя"""
    user_id = callback.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await callback.message.answer("📦 У вас пока нет заказов")
    else:
        text = "📦 **Ваши заказы:**\n\n"
        for order in orders[:10]:
            # order: (id, user_id, total_amount, bonus_used, status, payment_status, payment_method, address, phone, admin_group_message_id, created_at, updated_at)
            order_id = order[0]
            total = order[2]
            status = order[4] if len(order) > 4 else 'pending'
            payment_status = order[5] if len(order) > 5 else 'pending'
            created_at = order[10] if len(order) > 10 else 'N/A'
            
            status_emoji = {"pending": "⏳", "paid": "✅", "shipped": "🚚", "delivered": "📬", "cancelled": "❌"}
            
            text += f"№{order_id} | {total} ₽\n"
            text += f"📦 Статус: {status_emoji.get(payment_status, '❓')} {status}\n"
            text += f"📅 {created_at[:16] if created_at != 'N/A' else 'N/A'}\n\n"
        
        await callback.message.answer(text, parse_mode="Markdown")
    
    await callback.answer()

# =============================================================================
# КНОПКА "ОТМЕНИТЬ"
# =============================================================================
@router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()
    await callback.message.answer("❌ Оформление заказа отменено")
    await callback.answer()
