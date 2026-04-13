from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import OrderForm
from config import BOT_TOKEN, ADMIN_IDS, ADMIN_GROUP_ID
from database import get_cart_items, clear_cart, create_order, get_user_orders
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
    
    cart_items = await get_cart_items(user_id)
    
    if not cart_items:
        await callback.message.answer("🛒 Ваша корзина пуста!")
        await callback.answer()
        return
    
    total = 0
    items_text = "📦 **Ваш заказ:**\n\n"
    for item in cart_items:
        if isinstance(item, dict):
            name = item.get('name', 'Товар')
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
        else:
            name = item[1] if len(item) > 1 else 'Товар'
            price = item[2] if len(item) > 2 else 0
            quantity = item[3] if len(item) > 3 else 1
        
        total += price * quantity
        items_text += f"• {name} x{quantity} - {price * quantity} ₽\n"
    
    items_text += f"\n💰 **Итого: {total} ₽**"
    
    await callback.message.answer(items_text, parse_mode="Markdown", reply_markup=back_keyboard())
    await state.set_state(OrderForm.address)
    
    await callback.message.answer(
        "📍 **Введите адрес доставки:**\n\n"
        "Город, улица, дом, квартира",
        parse_mode="Markdown"
    )
    
    await callback.answer()

# =============================================================================
# ОБРАБОТКА АДРЕСА
# =============================================================================
@router.message(OrderForm.address)
async def process_address(message: Message, state: FSMContext):
    """Сохраняем адрес и запрашиваем телефон"""
    address = message.text.strip()
    await state.update_data(address=address)
    
    await message.answer(
        "📱 **Введите номер телефона:**\n\n"
        "Например: +7 (999) 123-45-67",
        parse_mode="Markdown"
    )
    await state.set_state(OrderForm.phone)

# =============================================================================
# ОБРАБОТКА ТЕЛЕФОНА И ЗАВЕРШЕНИЕ ЗАКАЗА
# =============================================================================
@router.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    """Сохраняем телефон, создаём заказ и отправляем уведомления"""
    try:
        phone = message.text.strip()
        user_id = message.from_user.id
        
        data = await state.get_data()
        address = data.get("address", "Не указан")
        
        cart_items = await get_cart_items(user_id)
        
        if not cart_items:
            await message.answer("❌ Корзина пуста!")
            await state.clear()
            return
        
        total = 0
        items_text = ""
        for item in cart_items:
            if isinstance(item, dict):
                name = item.get('name', 'Товар')
                price = item.get('price', 0)
                quantity = item.get('quantity', 1)
            else:
                name = item[1] if len(item) > 1 else 'Товар'
                price = item[2] if len(item) > 2 else 0
                quantity = item[3] if len(item) > 3 else 1
            
            total += price * quantity
            items_text += f"• {name} x{quantity} - {price * quantity} ₽\n"
        
        order_id = await create_order(
            user_id=user_id,
            total=total,
            items=items_text,
            address=f"{address}\n📞 Тел: {phone}",
            payment_status="pending"
        )
        
        await clear_cart(user_id)
        
        try:
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"🔔 **НОВЫЙ ЗАКАЗ №{order_id}**\n\n"
                     f"👤 Клиент: @{message.from_user.username}\n"
                     f"📞 Телефон: {phone}\n"
                     f"📦 Товары:\n{items_text}"
                     f"💰 Итого: {total} ₽\n"
                     f"📍 Адрес: {address}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ Ошибка отправки в группу: {e}")
        
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
        
        await message.answer(
            f"✅ **ЗАКАЗ ОФОРМЛЕН!**\n\n"
            f"📦 Номер: №{order_id}\n"
            f"💰 Сумма: {total} ₽\n"
            f"📞 Телефон: {phone}\n\n"
            f"Менеджер свяжется с вами в ближайшее время!",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")

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
            order_id = order[0]
            total = order[2]
            status = order[5] if len(order) > 5 else 'pending'
            created_at = order[6] if len(order) > 6 else 'N/A'
            
            text += f"№{order_id} | {total} ₽ | {status}\n"
            text += f"📅 {created_at}\n\n"
        
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
