from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import ADMIN_IDS, ADMIN_GROUP_ID
from database import get_cart, clear_cart, create_order, get_user_orders, update_user_purchases
from keyboards import back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

# Хранилище шагов оформления
checkout_steps = {}

# =============================================================================
# КНОПКА "ОФОРМИТЬ ЗАКАЗ"
# =============================================================================
@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery):
    logger.info(f"✅ checkout handler called by user {callback.from_user.id}")
    
    user_id = callback.from_user.id
    cart = await get_cart(user_id)
    
    if not cart:
        await callback.answer("🛒 Корзина пуста!", show_alert=True)
        return
    
    total = sum(item[3] * item[1] for item in cart)
    items = "\n".join(f"• {item[2]} x{item[1]} - {item[3]*item[1]} ₽" for item in cart)
    
    checkout_steps[user_id] = {"step": "address", "total": total, "items": items}
    
    await callback.message.answer(
        f"📦 **Ваш заказ:**\n\n{items}\n\n💰 **Итого: {total} ₽**\n\n"
        f"⚠️ Оплата 100% предоплатой.\n\n"
        f"📍 **Введите адрес доставки:**",
        parse_mode="Markdown"
    )
    await callback.answer()

# =============================================================================
# КНОПКА "МОИ ЗАКАЗЫ"
# =============================================================================
@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    logger.info(f"✅ my_orders handler called by user {callback.from_user.id}")
    
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
# КНОПКА "ОТМЕНИТЬ"
# =============================================================================
@router.callback_query(F.data == "cancel_order")
async def cancel_checkout(callback: CallbackQuery):
    logger.info(f"✅ cancel_order handler called by user {callback.from_user.id}")
    
    user_id = callback.from_user.id
    if user_id in checkout_steps:
        del checkout_steps[user_id]
    
    await callback.message.answer("❌ Оформление отменено")
    await callback.answer()

# =============================================================================
# ОБРАБОТКА АДРЕСА
# =============================================================================
@router.message(lambda m: m.from_user.id in checkout_steps and checkout_steps[m.from_user.id].get("step") == "address")
async def handle_address(message: Message):
    user_id = message.from_user.id
    address = message.text.strip()
    
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
    
    if len(phone) < 10 or not any(c.isdigit() for c in phone):
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    data = checkout_steps[user_id]
    address = data["address"]
    total = data["total"]
    items = data["items"]
    
    try:
        order_id = await create_order(
            user_id=user_id,
            total_amount=total,
            bonus_used=0,
            address=f"{address}\n📞 {phone}",
            phone=phone
        )
        
        await clear_cart(user_id)
        await update_user_purchases(user_id, total)
        
        # Уведомления (используем message.bot - НЕ создаём Bot!)
        try:
            await message.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"🔔 **НОВЫЙ ЗАКАЗ #{order_id}**\n\n"
                     f"👤 Клиент: @{message.from_user.username or 'нет'}\n"
                     f"📞 Телефон: {phone}\n"
                     f"📦 Товары:\n{items}\n"
                     f"💰 Итого: {total} ₽\n"
                     f"📍 Адрес: {address}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"❌ Group send error: {e}")
        
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Заказ #{order_id}**\n\n"
                         f"👤 @{message.from_user.username}\n"
                         f"📞 {phone}\n"
                         f"💰 {total} ₽\n"
                         f"📍 {address}",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        await message.answer(
            f"✅ **ЗАКАЗ #{order_id} ОФОРМЛЕН!**\n\n"
            f"💰 Сумма: {total} ₽\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n\n"
            f"🔹 Менеджер свяжется с вами для подтверждения оплаты.",
            parse_mode="Markdown"
        )
        
        del checkout_steps[user_id]
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: {e}")
        await message.answer("❌ Ошибка при оформлении. Попробуйте позже.")
        if user_id in checkout_steps:
            del checkout_steps[user_id]
# =============================================================================
# ТЕКСТОВАЯ КНОПКА "📦 Мои заказы"
# =============================================================================
@router.message(F.text == "📦 Мои заказы")
async def my_orders_from_main_menu(message: Message):
    """Показать заказы при нажатии на текстовую кнопку"""
    user_id = message.from_user.id
    await show_user_orders(message, user_id)

# =============================================================================
# CALLBACK КНОПКА "Мои заказы"
# =============================================================================
@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery):
    """Показать заказы по callback"""
    user_id = callback.from_user.id
    await show_user_orders(callback, user_id)
    await callback.answer()

# =============================================================================
# ПОКАЗАТЬ ЗАКАЗЫ ПОЛЬЗОВАТЕЛЯ
# =============================================================================
async def show_user_orders(target: Message | CallbackQuery, user_id: int):
    """Показать историю заказов"""
    orders = await get_user_orders(user_id)
    
    if not orders:
        text = "📦 **У вас пока нет заказов**\n\nСделайте первый заказ в каталоге!"
    else:
        text = "📦 **Ваши заказы:**\n\n"
        for order in orders[:10]:
            # order: (id, user_id, total_amount, bonus_used, status, payment_status, payment_method, address, phone, admin_group_message_id, created_at, updated_at)
            oid = order[0]
            total = order[2]
            pay_status = order[5] if len(order) > 5 else 'pending'
            created = order[10] if len(order) > 10 else 'N/A'
            emoji = {"pending":"⏳","paid":"✅","shipped":"🚚","delivered":"📬","cancelled":"❌"}.get(pay_status,"❓")
            text += f"№{oid} | {total} ₽ | {emoji} {pay_status}\n"
            text += f"📅 {created[:16] if created != 'N/A' else 'N/A'}\n\n"
    
    kb = back_keyboard("main")
    
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")
