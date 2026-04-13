from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import (
    get_cart, clear_cart, create_order, get_bonus_balance,
    spend_bonus, check_promo_code, add_bonus, update_user_purchases,
    get_user_level, create_payment, update_payment_status, update_order_status,
    get_user, track_event
)
from keyboards import payment_method_keyboard, bonus_keyboard, back_keyboard
from states import OrderState
from config import ADMIN_IDS, ADMIN_GROUP_ID

router = Router()

# ============================================
# ВВОД АДРЕСА
# ============================================

@router.message(OrderState.address_input)
async def process_address(message: Message, state: FSMContext):
    """Обработка ввода адреса"""
    address = message.text
    
    if len(address) < 10:
        await message.answer(
            "❌ Пожалуйста, введите полный адрес\n"
            "(Город, улица, дом, квартира)\n\n"
            "Попробуйте ещё раз:"
        )
        return
    
    await state.update_data(address=address)
    
    await message.answer(
        "📱 Введите ваш **номер телефона**:\n"
        "(например: +79991234567)",
        parse_mode="Markdown"
    )
    
    await OrderState.phone_input.set()

# ============================================
# ВВОД ТЕЛЕФОНА
# ============================================

@router.message(OrderState.phone_input)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text
    
    # Простая валидация телефона
    if not phone.startswith("+") or len(phone) < 11:
        await message.answer(
            "❌ Неверный формат телефона\n"
            "Введите в формате: +79991234567\n\n"
            "Попробуйте ещё раз:"
        )
        return
    
    await state.update_data(phone=phone)
    
    # Проверяем бонусы
    bonus_balance = await get_bonus_balance(message.from_user.id)
    
    if bonus_balance > 0:
        await message.answer(
            f"🎁 У вас есть **{bonus_balance} бонусов**!\n\n"
            f"Хотите использовать их для оплаты?\n"
            f"(1 бонус = 1 рубль, можно оплатить до 50% заказа)",
            reply_markup=bonus_keyboard(),
            parse_mode="Markdown"
        )
        await OrderState.bonus_choice.set()
    else:
        await process_bonus_choice(message, state, False)

# ============================================
# ВЫБОР БОНУСОВ
# ============================================

@router.callback_query(F.data == "pay_with_bonus")
async def use_bonus(callback: CallbackQuery, state: FSMContext):
    """Использовать бонусы"""
    await process_bonus_choice(callback.message, state, True)
    await callback.answer()

@router.callback_query(F.data == "skip_bonus")
async def skip_bonus(callback: CallbackQuery, state: FSMContext):
    """Пропустить бонусы"""
    await process_bonus_choice(callback.message, state, False)
    await callback.answer()

async def process_bonus_choice(message: Message, state: FSMContext, use_bonus: bool):
    """Обработка выбора бонусов"""
    data = await state.get_data()
    cart_items = await get_cart(message.from_user.id)
    total = sum(item[3] * item[1] for item in cart_items)
    
    bonus_used = 0
    
    if use_bonus:
        bonus_balance = await get_bonus_balance(message.from_user.id)
        
        # Можно использовать до 50% от суммы заказа
        max_bonus = total // 2
        bonus_used = min(bonus_balance, max_bonus)
        
        if bonus_used > 0:
            await spend_bonus(message.from_user.id, bonus_used)
            total -= bonus_used
    
    await state.update_data(
        total=total,
        bonus_used=bonus_used
    )
    
    await message.answer(
        "🏷 Есть **промокод**? Введите его сейчас.\n"
        "Если нет — напишите «Пропустить»",
        parse_mode="Markdown"
    )
    
    await OrderState.promo_input.set()

# ============================================
# ВВОД ПРОМОКОДА
# ============================================

@router.message(OrderState.promo_input)
async def process_promo(message: Message, state: FSMContext):
    """Обработка промокода"""
    if message.text.lower() in ["пропустить", "skip", "нет", "-"]:
        await finalize_order(message, state)
        return
    
    promo_code = message.text.strip().upper()
    discount = await check_promo_code(promo_code)
    
    if discount == 0:
        await message.answer(
            "❌ Промокод не найден или истёк\n"
            "Попробуйте другой или напишите «Пропустить»:"
        )
        return
    
    data = await state.get_data()
    total = data.get("total", 0)
    
    # Применяем скидку
    discount_amount = total * discount // 100
    new_total = total - discount_amount
    
    await state.update_data(
        total=new_total,
        promo_code=promo_code,
        discount_percent=discount,
        discount_amount=discount_amount
    )
    
    await message.answer(
        f"✅ **Промокод применён!**\n\n"
        f"Скидка: {discount}% ({discount_amount} ₽)\n"
        f"Новая сумма: **{new_total} ₽**",
        parse_mode="Markdown"
    )
    
    await finalize_order(message, state)

# ============================================
# ФИНАЛИЗАЦИЯ ЗАКАЗА
# ============================================

async def finalize_order(message: Message, state: FSMContext):
    """Создание заказа"""
    data = await state.get_data()
    cart_items = await get_cart(message.from_user.id)
    
    if not cart_items:
        await message.answer("❌ Корзина пуста!")
        await state.clear()
        return
    
    # Создаём заказ в БД
    order_id = await create_order(
        user_id=message.from_user.id,
        total_amount=data.get("total", 0),
        bonus_used=data.get("bonus_used", 0),
        address=data.get("address", ""),
        phone=data.get("phone", "")
    )
    
    # Получаем уровень пользователя для начисления бонусов
    level_info = await get_user_level(message.from_user.id)
    bonus_percent = level_info["percent"]
    
    # Начисляем бонусы (кэшбэк)
    bonus_earned = data.get("total", 0) * bonus_percent // 100
    await add_bonus(message.from_user.id, bonus_earned, "purchase")
    
    # Обновляем сумму покупок пользователя
    await update_user_purchases(message.from_user.id, data.get("total", 0))
    
    # Трекаем событие (аналитика)
    await track_event(
        message.from_user.id,
        "order_completed",
        {"order_id": order_id, "amount": data.get("total", 0)},
        value=data.get("total", 0)
    )
    
    # Формируем сообщение для клиента
    text = (
        f"✅ **Заказ #{order_id} оформлен!**\n\n"
        f"📦 **Товары:**\n"
    )
    
    for item in cart_items:
        product_id, quantity, name, price = item
        text += f"  ▫️ {name} × {quantity} = {price * quantity} ₽\n"
    
    text += (
        f"\n💰 **Сумма:** {data.get('total', 0)} ₽\n"
    )
    
    if data.get("bonus_used", 0) > 0:
        text += f"🎁 Списано бонусов: {data['bonus_used']} ₽\n"
    
    if data.get("promo_code"):
        text += f"🏷 Промокод: {data['promo_code']} ({data.get('discount_percent', 0)}%)\n"
    
    text += (
        f"\n📍 **Адрес:** {data.get('address', '')}\n"
        f"📱 **Телефон:** {data.get('phone', '')}\n"
        f"\n🎁 Вам начислено **{bonus_earned} бонусов**!\n\n"
        f"⏳ Выберите способ оплаты:"
    )
    
    # Очищаем корзину
    await clear_cart(message.from_user.id)
    
    await message.answer(
        text,
        reply_markup=payment_method_keyboard(),
        parse_mode="Markdown"
    )
    
    # Уведомляем админа (отправляем данные в группу)
    await send_admin_notification(message.bot, order_id, message.from_user.id, data)
    
    await state.clear()

# ============================================
# УВЕДОМЛЕНИЕ АДМИНАМ
# ============================================

async def send_admin_notification(bot, order_id: int, user_id: int, data: dict):
    """Отправить уведомление о заказе в админ-группу"""
    from database import get_user, get_cart
    
    user = await get_user(user_id)
    cart_items = await get_cart(user_id)
    
    # Формируем теги
    tags = ["#НОВЫЙ_ЗАКАЗ 📦"]
    if data.get("bonus_used", 0) > 0:
        tags.append("#БОНУСЫ 🎁")
    if data.get("total", 0) > 10000:
        tags.append("#VIP 💎")
    if data.get("promo_code"):
        tags.append("#ПРОМОКОД 🏷")
    
    tags_text = " ".join(tags)
    
    # Формируем сообщение
    text = (
        f"{tags_text}\n\n"
        f"🛒 **ЗАКАЗ #{order_id}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Клиент:**\n"
        f"• ID: `{user_id}`\n"
        f"• Имя: {user[2] if user else 'Неизвестно'}\n"
        f"• Username: @{user[1] if user and user[1] else 'нет'}\n"
        f"• Телефон: {data.get('phone', 'не указан')}\n\n"
        f"💰 **Финансы:**\n"
        f"• Сумма: {data.get('total', 0):,} ₽\n"
        f"• Бонусы списано: {data.get('bonus_used', 0)} ₽\n"
        f"• К оплате: {data.get('total', 0) + data.get('bonus_used', 0):,} ₽\n"
        f"• Оплата: ⏳ Ожидает\n\n"
        f"📍 **Доставка:**\n"
        f"• Адрес: {data.get('address', '')}\n\n"
        f"📦 **Товары:**\n"
    )
    
    if cart_items:
        for item in cart_items:
            product_id, quantity, name, price = item
            text += f"• {name} × {quantity} = {price * quantity:,} ₽\n"
    
    text += (
        f"\n⏰ **Время:** {data.get('created_at', '')[:19] if data.get('created_at') else 'Сейчас'}\n"
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"\n⚠️ **Требуется предоплата 100%!**\n"
        f"Свяжитесь с клиентом для оплаты."
    )
    
    # Отправляем в админ-группу или админам в ЛС
    if ADMIN_GROUP_ID:
        try:
            await bot.send_message(
                ADMIN_GROUP_ID,
                text,
                parse_mode="Markdown"
            )
        except:
            pass
    
    # Дублируем админам в ЛС
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                text,
                parse_mode="Markdown"
            )
        except:
            pass

# ============================================
# ВЫБОР ОПЛАТЫ
# ============================================

@router.callback_query(F.data == "pay_with_telegram")
async def pay_with_telegram(callback: CallbackQuery):
    """Оплата через Telegram (заглушка)"""
    data = await callback.bot.get_state().get_data()
    
    await callback.message.answer(
        "💳 **Оплата через Telegram**\n\n"
        "⚙️ Платёжная система настраивается...\n\n"
        "Для тестирования выберите «Ссылка на оплату» или свяжитесь с менеджером.",
        reply_markup=back_keyboard("checkout")
    )
    await callback.answer()

@router.callback_query(F.data == "pay_link")
async def pay_with_link(callback: CallbackQuery):
    """Оплата по ссылке"""
    await callback.message.answer(
        "🔗 **Ссылка на оплату**\n\n"
        "Менеджер отправит вам ссылку на оплату в течение 5 минут.\n\n"
        "Ожидайте сообщения! ⏳",
        reply_markup=back_keyboard("main")
    )
    await callback.answer()

# ============================================
# ОТМЕНА ЗАКАЗА
# ============================================

@router.callback_query(F.data == "cancel_order")
async def cancel_order_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()
    
    # Возвращаем бонусы если были списаны
    data = await state.get_data()
    if data.get("bonus_used", 0) > 0:
        from database import add_bonus
        await add_bonus(callback.from_user.id, data["bonus_used"], "order_cancel")
    
    await callback.message.answer(
        "❌ **Заказ отменён**\n\n"
        "Бонусы возвращены на ваш счёт.\n\n"
        "Хотите вернуться к покупкам?",
        reply_markup=back_keyboard("catalog"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# НАЗАД
# ============================================

@router.callback_query(F.data == "back_checkout")
async def back_to_checkout(callback: CallbackQuery):
    """Назад к оформлению"""
    await callback.message.answer(
        "💳 **Оформление заказа**\n\n"
        "Выберите способ оплаты:",
        reply_markup=payment_method_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_cart")
async def back_to_cart(callback: CallbackQuery):
    """Назад в корзину"""
    from handlers.cart import view_cart
    
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
    await callback.answer()

# === ОБРАБОТКА КНОПКИ "МОИ ЗАКАЗЫ" ===
@dp.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery, state: FSMContext):
    """Показать заказы пользователя"""
    from database import get_user_orders
    
    user_id = callback.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await callback.message.answer("📦 У вас пока нет заказов")
    else:
        text = "📦 **Ваши заказы:**\n\n"
        for order in orders:
            # order[0] = id, order[4] = total_amount, order[5] = status
            text += f"№{order[0]} | {order[4]} ₽ | Статус: {order[5]}\n"
            text += f"📍 {order[3]}\n\n"
        await callback.message.answer(text, parse_mode="Markdown")
    
    await callback.answer()
# === КОНЕЦ ОБРАБОТКИ ===
