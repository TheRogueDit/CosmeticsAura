from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import OrderForm
from config import BOT_TOKEN, ADMIN_IDS, ADMIN_GROUP_ID
from database import get_cart, clear_cart, create_order, get_user_orders, update_user_purchases
from keyboards import back_keyboard
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)
router = Router()

# Хранилище для временных данных (вместо FSM, если оно не работает)
user_checkout_data = {}

# =============================================================================
# КНОПКА "ОФОРМИТЬ ЗАКАЗ"
# =============================================================================
@router.callback_query(F.data == "checkout")
async def checkout_callback(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа"""
    user_id = callback.from_user.id
    logger.info(f"🛒 Checkout started for user {user_id}")
    
    cart_items = await get_cart(user_id)
    if not cart_items:
        await callback.message.answer("🛒 Ваша корзина пуста!")
        await callback.answer()
        return
    
    # Считаем сумму
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
        items_text + "\n\n⚠️ Оплата 100% предоплатой.",
        reply_markup=back_keyboard("main"),
        parse_mode="Markdown"
    )
    
    # Сохраняем данные во временное хранилище
    user_checkout_data[user_id] = {"step": "address", "total": total, "items": items_text}
    
    await callback.message.answer("📍 **Введите адрес доставки:**")
    await callback.answer()

# =============================================================================
# ОБРАБОТКА АДРЕСА (через текстовый фильтр)
# =============================================================================
@router.message(lambda m: m.from_user.id in user_checkout_data and user_checkout_data[m.from_user.id].get("step") == "address")
async def process_address(message: Message):
    """Сохраняем адрес и запрашиваем телефон"""
    user_id = message.from_user.id
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    # Сохраняем адрес
    user_checkout_data[user_id]["address"] = address
    user_checkout_data[user_id]["step"] = "phone"
    
    await message.answer("📱 **Введите номер телефона:**\nНапример: +7 (999) 123-45-67")

# =============================================================================
# ОБРАБОТКА ТЕЛЕФОНА
# =============================================================================
@router.message(lambda m: m.from_user.id in user_checkout_data and user_checkout_data[m.from_user.id].get("step") == "phone")
async def process_phone(message: Message):
    """Создаём заказ и отправляем уведомления"""
    user_id = message.from_user.id
    phone = message.text.strip()
    
    if len(phone) < 10 or not any(c.isdigit() for c in phone):
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    data = user_checkout_data[user_id]
    address = data.get("address", "Не указан")
    total = data.get("total", 0)
    items_text = data.get("items", "")
    
    try:
        # Создаём заказ
        order_id = await create_order(
            user_id=user_id,
            total_amount=total,
            bonus_used=0,
            address=f"{address}\n📞 {phone}",
            phone=phone
        )
        logger.info(f"✅ Order created: ID={order_id}")
        
        await clear_cart(user_id)
        await update_user_purchases(user_id, total)
        
        # === ОТПРАВКА УВЕДОМЛЕНИЙ ===
        
        # 1. В админ-группу
        try:
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"🔔 **НОВЫЙ ЗАКАЗ №{order_id}**\n\n"
                     f"👤 Клиент: @{message.from_user.username or 'нет'}\n"
                     f"📞 Телефон: {phone}\n"
                     f"📦 Товары:\n{items_text}"
                     f"💰 Итого: {total} ₽\n"
                     f"📍 Адрес: {address}",
                parse_mode="Markdown"
            )
            logger.info(f"✅ Sent to admin group {ADMIN_GROUP_ID}")
        except Exception as e:
            logger.error(f"❌ Failed to send to group: {e}")
            await message.answer(f"⚠️ Не удалось отправить уведомление в группу: {e}")
        
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
                logger.info(f"✅ Sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send to admin {admin_id}: {e}")
        
        # 3. Подтверждение пользователю
        await message.answer(
            f"✅ **ЗАКАЗ №{order_id} ОФОРМЛЕН!**\n\n"
            f"💰 Сумма: {total} ₽\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n\n"
            f"🔹 Менеджер свяжется с вами для подтверждения оплаты.",
            parse_mode="Markdown"
        )
        
        # Очищаем данные
        del user_checkout_data[user_id]
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        await message.answer(f"❌ Ошибка при оформлении. Попробуйте позже.")
        if user_id in user_checkout_data:
            del user_checkout_data[user_id]

# =============================================================================
# КНОПКА "МОИ ЗАКАЗЫ"
# =============================================================================
@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery):
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
            payment_status = order[5] if len(order) > 5 else 'pending'
            created_at = order[10] if len(order) > 10 else 'N/A'
            status_emoji = {"pending": "⏳", "paid": "✅", "shipped": "🚚", "delivered": "📬", "cancelled": "❌"}
            text += f"№{order_id} | {total} ₽\n"
            text += f"📦 Статус: {status_emoji.get(payment_status, '❓')} {payment_status}\n"
            text += f"📅 {created_at[:16] if created_at != 'N/A' else 'N/A'}\n\n"
        await callback.message.answer(text, parse_mode="Markdown")
    
    await callback.answer()

# =============================================================================
# КНОПКА "ОТМЕНИТЬ"
# =============================================================================
@router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery):
    """Отмена оформления заказа"""
    user_id = callback.from_user.id
    if user_id in user_checkout_data:
        del user_checkout_data[user_id]
    await callback.message.answer("❌ Оформление заказа отменено")
    await callback.answer()
