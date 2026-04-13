from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import ADMIN_IDS, ADMIN_GROUP_ID
from database import get_cart, clear_cart, create_order, get_user_orders, update_user_purchases
from keyboards import back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

# Простое хранилище шагов оформления (вместо FSM)
checkout_steps = {}

# =============================================================================
# КНОПКА "ОФОРМИТЬ ЗАКАЗ"
# =============================================================================
@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    logger.info(f"🛒 Checkout start: user {user_id}")
    
    cart = await get_cart(user_id)
    if not cart:
        await callback.answer("🛒 Корзина пуста!", show_alert=True)
        return
    
    # Считаем сумму (кортеж: product_id, quantity, name, price)
    total = sum(item[3] * item[1] for item in cart)
    items = "\n".join(f"• {item[2]} x{item[1]} - {item[3]*item[1]} ₽" for item in cart)
    
    # Сохраняем в хранилище
    checkout_steps[user_id] = {
        "step": "address",
        "total": total,
        "items": items
    }
    
    await callback.message.answer(
        f"📦 **Ваш заказ:**\n\n{items}\n\n💰 **Итого: {total} ₽**\n\n"
        f"⚠️ Оплата 100% предоплатой.\n\n"
        f"📍 **Введите адрес доставки:**",
        parse_mode="Markdown"
    )
    await callback.answer()

# =============================================================================
# ОБРАБОТКА АДРЕСА
# =============================================================================
@router.message(lambda m: m.from_user.id in checkout_steps and checkout_steps[m.from_user.id].get("step") == "address")
async def handle_address(message: Message):
    user_id = message.from_user.id
    address = message.text.strip()
    
    logger.info(f"📍 Address: {address} from user {user_id}")
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    checkout_steps[user_id]["address"] = address
    checkout_steps[user_id]["step"] = "phone"
    
    await message.answer(
        f"✅ Адрес сохранен.\n\n"
        f"📱 **Введите номер телефона:**\n"
        f"Например: +7 (999) 123-45-67",
        parse_mode="Markdown"
    )

# =============================================================================
# ОБРАБОТКА ТЕЛЕФОНА → создание заказа
# =============================================================================
@router.message(lambda m: m.from_user.id in checkout_steps and checkout_steps[m.from_user.id].get("step") == "phone")
async def handle_phone(message: Message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    logger.info(f"📱 Phone: {phone} from user {user_id}")
    
    if len(phone) < 10 or not any(c.isdigit() for c in phone):
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    data = checkout_steps[user_id]
    address = data["address"]
    total = data["total"]
    items = data["items"]
    
    try:
        # Создаём заказ
        order_id = await create_order(
            user_id=user_id,
            total_amount=total,
            bonus_used=0,
            address=f"{address}\n📞 {phone}",
            phone=phone
        )
        logger.info(f"✅ Order #{order_id} created")
        
        await clear_cart(user_id)
        await update_user_purchases(user_id, total)
        
        # === ОТПРАВКА УВЕДОМЛЕНИЙ (используем message.bot) ===
        
        # 1. В админ-группу
        try:
            await message.bot.send_message(  # ✅ Используем message.bot
                chat_id=ADMIN_GROUP_ID,
                text=f"🔔 **НОВЫЙ ЗАКАЗ #{order_id}**\n\n"
                     f"👤 Клиент: @{message.from_user.username or 'нет'}\n"
                     f"📞 Телефон: {phone}\n"
                     f"📦 Товары:\n{items}\n"
                     f"💰 Итого: {total} ₽\n"
                     f"📍 Адрес: {address}",
                parse_mode="Markdown"
            )
            logger.info(f"✅ Sent to group {ADMIN_GROUP_ID}")
        except Exception as e:
            logger.error(f"❌ Group send error: {e}")
        
        # 2. Админам в ЛС
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(  # ✅ Используем message.bot
                    chat_id=admin_id,
                    text=f"🔔 **Заказ #{order_id}**\n\n"
                         f"👤 @{message.from_user.username}\n"
                         f"📞 {phone}\n"
                         f"💰 {total} ₽\n"
                         f"📍 {address}",
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"❌ Admin {admin_id} send error: {e}")
        
        # 3. Подтверждение пользователю
        await message.answer(
            f"✅ **ЗАКАЗ #{order_id} ОФОРМЛЕН!**\n\n"
            f"💰 Сумма: {total} ₽\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n\n"
            f"🔹 Менеджер свяжется с вами для подтверждения оплаты.",
            parse_mode="Markdown"
        )
        
        # Удаляем из хранилища
        del checkout_steps[user_id]
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: {e}")
        await message.answer("❌ Ошибка при оформлении. Попробуйте позже.")
        if user_id in checkout_steps:
            del checkout_steps[user_id]

# =============================================================================
# КНОПКА "МОИ ЗАКАЗЫ"
# =============================================================================
@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    user_id = callback.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await callback.answer("📦 У вас пока нет заказов", show_alert=True)
        return
    
    text = "📦 **Ваши заказы:**\n\n"
    for order in orders[:10]:
        oid = order[0]
        total = order[2]
        pay_status = order[5] if len(order) > 5 else 'pending'
        created = order[10] if len(order) > 10 else 'N/A'
        emoji = {"pending":"⏳","paid":"✅","shipped":"🚚","delivered":"📬","cancelled":"❌"}.get(pay_status,"❓")
        text += f"№{oid} | {total} ₽ | {emoji} {pay_status}\n📅 {created[:16] if created != 'N/A' else 'N/A'}\n\n"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# =============================================================================
# СБРОС ОФОРМЛЕНИЯ
# =============================================================================
@router.callback_query(F.data == "cancel_order")
async def cancel_checkout(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in checkout_steps:
        del checkout_steps[user_id]
    await callback.message.answer("❌ Оформление отменено")
    await callback.answer()
