from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import (
    get_dashboard_stats, get_all_products, add_product, update_product,
    delete_product, get_all_orders, get_order_by_id, update_order_status,
    update_payment_status, cancel_order, get_all_users, get_user,
    add_bonus, get_pending_reviews, approve_review, reject_review,
    get_all_promo_codes, create_promo_code, deactivate_promo_code,
    create_mailing, get_mailing_history, log_admin_action, get_admin_logs,
    get_bot_setting, update_bot_setting, get_low_stock_products, get_user_orders
)
from keyboards import (
    admin_main_keyboard, admin_products_keyboard, admin_orders_keyboard,
    admin_users_keyboard, admin_reviews_keyboard, admin_promo_keyboard,
    admin_mailing_keyboard, admin_settings_keyboard, back_keyboard,
    admin_order_keyboard
)
from states import AdminProductState, AdminPromoState, AdminMailingState, AdminUserState
from config import ADMIN_IDS, ADMIN_GROUP_ID

router = Router()

# ============================================
# ПРОВЕРКА ПРАВ АДМИНА
# ============================================

async def check_admin(callback: CallbackQuery | Message):
    """Проверить права администратора"""
    user_id = callback.from_user.id if hasattr(callback, 'from_user') else callback.from_user.id
    if user_id not in ADMIN_IDS:
        if isinstance(callback, CallbackQuery):
            await callback.answer("🔒 Доступ запрещён", show_alert=True)
        else:
            await callback.answer("🔒 Доступ только для администраторов")
        return False
    return True

# ============================================
# КНОПКА АДМИН-ПАНЕЛЬ
# ============================================

@router.message(F.text == "👨‍💼 Админ-панель")
@router.callback_query(F.data == "admin_main")
async def admin_main(message: Message | CallbackQuery):
    """Главное меню админ-панели"""
    if not await check_admin(message):
        return
    
    stats = await get_dashboard_stats()
    
    text = (
        f"👨‍💼 **Панель администратора**\n\n"
        f"📊 **Быстрая статистика:**\n\n"
        f"👥 Пользователи: {stats['total_users']}\n"
        f"📋 Заказы в ожидании: {stats['pending_orders']}\n"
        f"💰 Выручка: {stats['total_revenue']:,} ₽\n"
        f"🏷 Товаров: {stats['total_products']} (⚠️ {stats['low_stock']} мало на складе)\n"
        f"📝 Отзывы: {stats['approved_reviews']} опубликованы (🔍 {stats['pending_reviews']} на модерации)\n\n"
        f"Выберите раздел:"
    )
    
    if isinstance(message, CallbackQuery):
        await message.message.answer(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")
        await message.answer()
    else:
        await message.answer(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")
    
    await log_admin_action(message.from_user.id, "admin_panel_opened")

# ============================================
# УПРАВЛЕНИЕ ТОВАРАМИ
# ============================================

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Меню управления товарами"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "📦 **Управление товарами**\n\nВыберите действие:",
        reply_markup=admin_products_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "➕ **Добавление товара**\n\n"
        "Введите **название товара**:",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_name.set()
    await callback.answer()

@router.message(AdminProductState.product_name)
async def admin_product_name_received(message: Message, state: FSMContext):
    """Получение названия товара"""
    await state.update_data(product_name=message.text)
    
    await message.answer(
        "📝 Теперь введите **описание товара**:",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_desc.set()

@router.message(AdminProductState.product_desc)
async def admin_product_desc_received(message: Message, state: FSMContext):
    """Получение описания товара"""
    await state.update_data(product_desc=message.text)
    
    await message.answer(
        "💰 Введите **цену товара** (в рублях, только цифры):",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_price.set()

@router.message(AdminProductState.product_price)
async def admin_product_price_received(message: Message, state: FSMContext):
    """Получение цены товара"""
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError()
    except:
        await message.answer("❌ Введите корректную цену (число больше 0)")
        return
    
    await state.update_data(product_price=price)
    
    await message.answer(
        "📂 Выберите **категорию**:\n"
        "• cosmetics - Косметика\n"
        "• bads - БАДы\n"
        "• body - Уход за телом\n"
        "• sets - Наборы",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_category.set()

@router.message(AdminProductState.product_category)
async def admin_product_category_received(message: Message, state: FSMContext):
    """Получение категории товара"""
    category = message.text.lower().strip()
    valid_categories = ['cosmetics', 'bads', 'body', 'sets']
    
    if category not in valid_categories:
        await message.answer(f"❌ Выберите из: {', '.join(valid_categories)}")
        return
    
    await state.update_data(product_category=category)
    
    await message.answer(
        "📸 Теперь **отправьте фото товара**:",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_photo.set()

@router.message(F.photo, AdminProductState.product_photo)
async def admin_product_photo_received(message: Message, state: FSMContext):
    """Получение фото товара"""
    photo_id = message.photo[-1].file_id
    await state.update_data(product_photo=photo_id)
    
    await message.answer(
        "📦 Введите **количество на складе**:",
        reply_markup=back_keyboard("admin_products")
    )
    
    await AdminProductState.product_stock.set()

@router.message(AdminProductState.product_stock)
async def admin_product_stock_received(message: Message, state: FSMContext):
    """Получение количества товара"""
    try:
        stock = int(message.text)
        if stock < 0:
            raise ValueError()
    except:
        await message.answer("❌ Введите корректное количество")
        return
    
    data = await state.get_data()
    
    # Создаём товар
    product_id = await add_product(
        name=data['product_name'],
        description=data['product_desc'],
        price=data['product_price'],
        category=data['product_category'],
        photo_id=data['product_photo'],
        stock=stock
    )
    
    await log_admin_action(message.from_user.id, "product_added", f"ID: {product_id}")
    
    await message.answer(
        f"✅ **Товар добавлен!**\n\n"
        f"ID: {product_id}\n"
        f"Название: {data['product_name']}\n"
        f"Цена: {data['product_price']} ₽\n"
        f"Склад: {stock} шт.",
        reply_markup=admin_products_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.clear()

@router.callback_query(F.data == "admin_products_list")
async def admin_products_list(callback: CallbackQuery):
    """Список товаров"""
    if not await check_admin(callback):
        return
    
    products = await get_all_products(limit=10)
    
    if not products:
        await callback.answer("📭 Товаров нет", show_alert=True)
        return
    
    text = "📦 **Список товаров (последние 10):**\n\n"
    
    for product in products:
        pid, name, desc, price, category, photo, stock = product[:7]
        status = "✅" if stock > 10 else "⚠️" if stock > 0 else "❌"
        text += f"{status} {name} | {price} ₽ | Склад: {stock}\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_products"))
    await callback.answer()

@router.callback_query(F.data == "admin_low_stock")
async def admin_low_stock(callback: CallbackQuery):
    """Товары с низким запасом"""
    if not await check_admin(callback):
        return
    
    products = await get_low_stock_products()
    
    if not products:
        await callback.answer("✅ Все товары в наличии!", show_alert=True)
        return
    
    text = "⚠️ **Товары заканчиваются:**\n\n"
    
    for product in products:
        pid, name, desc, price, category, photo, stock = product[:7]
        text += f"❗ {name} - осталось {stock} шт.\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_products"))
    await callback.answer()

# ============================================
# УПРАВЛЕНИЕ ЗАКАЗАМИ
# ============================================

@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """Меню управления заказами"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "📦 **Управление заказами**\n\nВыберите статус для просмотра:",
        reply_markup=admin_orders_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_orders_"))
async def admin_orders_by_status(callback: CallbackQuery):
    """Заказы по статусу"""
    if not await check_admin(callback):
        return
    
    status_map = {
        "admin_orders_all": None,
        "admin_orders_pending": "pending",
        "admin_orders_paid": "paid",
        "admin_orders_shipped": "shipped",
        "admin_orders_delivered": "delivered",
        "admin_orders_cancelled": "cancelled"
    }
    
    status = status_map.get(callback.data)
    orders = await get_all_orders(status=status, limit=10)
    
    if not orders:
        await callback.answer("📭 Заказов нет", show_alert=True)
        return
    
    text = f"📦 **Заказы** ({status or 'все'}):\n\n"
    
    for order in orders:
        oid = order[0]
        user_name = order[10] if len(order) > 10 else "Неизвестно"
        total = order[2]
        pay_status = order[6] if len(order) > 6 else "pending"
        
        status_emoji = {"pending": "⏳", "paid": "✅", "shipped": "🚚", "delivered": "📬", "cancelled": "❌"}
        
        text += f"#{oid} | {user_name} | {total} ₽ | {status_emoji.get(pay_status, '❓')}\n"
    
    text += "\nНажмите на номер заказа для деталей:"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_orders"))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_detail_"))
async def admin_order_detail(callback: CallbackQuery):
    """Детали заказа"""
    if not await check_admin(callback):
        return
    
    try:
        order_id = int(callback.data.split("_")[3])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    text = (
        f"📦 **Заказ #{order_id}**\n\n"
        f"👤 Клиент ID: {order[1]}\n"
        f"💰 Сумма: {order[2]:,} ₽\n"
        f"🎁 Бонусы: {order[3]} ₽\n"
        f"📍 Адрес: {order[7]}\n"
        f"📱 Телефон: {order[8]}\n"
        f"💳 Оплата: {order[6]}\n"
        f"📦 Статус: {order[4]}\n"
        f"🕐 Дата: {order[10][:19] if len(order) > 10 else '—'}"
    )
    
    kb = admin_order_keyboard(order_id)
    
    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_"))
async def admin_order_action(callback: CallbackQuery):
    """Действие с заказом"""
    if not await check_admin(callback):
        return
    
    data = callback.data.split("_")
    action = data[3]
    
    try:
        order_id = int(data[4])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    status_map = {
        "confirm": "confirmed",
        "ship": "shipped",
        "deliver": "delivered",
        "cancel": "cancelled"
    }
    
    new_status = status_map.get(action)
    
    if not new_status:
        await callback.answer("❌ Неизвестное действие", show_alert=True)
        return
    
    if action == "cancel":
        await cancel_order(order_id)
    else:
        await update_order_status(order_id, new_status)
    
    await log_admin_action(callback.from_user.id, f"order_{action}", f"Order ID: {order_id}")
    
    # Уведомляем клиента
    order = await get_order_by_id(order_id)
    if order:
        user_id = order[1]
        messages = {
            "confirm": "✅ Ваш заказ подтверждён! Ожидайте отправки.",
            "ship": "🚚 Ваш заказ отправлен! Трек-номер будет отправлен отдельно.",
            "deliver": "📬 Заказ доставлен! Спасибо за покупку! 🎁",
            "cancel": "❌ Ваш заказ был отменён. Бонусы возвращены на счёт."
        }
        
        try:
            await callback.bot.send_message(user_id, messages.get(action, "Статус обновлён"))
        except:
            pass
    
    await callback.answer(f"✅ Статус изменён на {new_status}")
    
    # Обновляем сообщение
    await admin_order_detail(callback)

# ============================================
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# ============================================

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Меню управления пользователями"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "👥 **Управление пользователями**\n\nВыберите действие:",
        reply_markup=admin_users_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_users_list")
async def admin_users_list(callback: CallbackQuery):
    """Список пользователей"""
    if not await check_admin(callback):
        return
    
    users = await get_all_users(limit=20)
    
    text = "👥 **Последние пользователи:**\n\n"
    
    for user in users:
        uid, username, first_name, bonus, purchases = user[:5]
        text += f"• {first_name} (@{username or 'нет'}) | {bonus} б.\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_users"))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_profile_"))
async def admin_user_profile(callback: CallbackQuery):
    """Профиль пользователя"""
    if not await check_admin(callback):
        return
    
    try:
        user_id = int(callback.data.split("_")[3])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    user = await get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    text = (
        f"👤 **Профиль пользователя**\n\n"
        f"ID: `{user_id}`\n"
        f"Имя: {user[2]}\n"
        f"Username: @{user[1] or 'нет'}\n"
        f"🎁 Бонусы: {user[3]}\n"
        f"💰 Всего покупок: {user[4]:,} ₽\n"
        f"📅 Регистрация: {user[9][:19] if len(user) > 9 and user[9] else '—'}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Начислить бонусы", callback_data=f"admin_bonus_add_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_bonus_add_"))
async def admin_bonus_add_start(callback: CallbackQuery, state: FSMContext):
    """Начать начисление бонусов"""
    if not await check_admin(callback):
        return
    
    try:
        user_id = int(callback.data.split("_")[3])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await state.update_data(bonus_user_id=user_id)
    
    await callback.message.answer(
        "💰 Введите **количество бонусов** для начисления:",
        reply_markup=back_keyboard("admin_users")
    )
    
    await AdminUserState.bonus_amount.set()
    await callback.answer()

@router.message(AdminUserState.bonus_amount)
async def admin_bonus_amount_received(message: Message, state: FSMContext):
    """Получение суммы бонусов"""
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число")
        return
    
    data = await state.get_data()
    user_id = data.get('bonus_user_id')
    
    await add_bonus(user_id, amount, f"admin_bonus_{message.from_user.id}")
    await log_admin_action(message.from_user.id, "bonus_added", f"User: {user_id}, Amount: {amount}")
    
    await message.answer(f"✅ Начислено {amount} бонусов пользователю {user_id}")
    await state.clear()

# ============================================
# МОДЕРАЦИЯ ОТЗЫВОВ
# ============================================

@router.callback_query(F.data == "admin_reviews")
async def admin_reviews(callback: CallbackQuery):
    """Меню модерации отзывов"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "📝 **Модерация отзывов**\n\nВыберите действие:",
        reply_markup=admin_reviews_keyboard()
    )
    await callback.answer()

# ============================================
# ПРОМОКОДЫ
# ============================================

@router.callback_query(F.data == "admin_promo")
async def admin_promo(callback: CallbackQuery):
    """Меню управления промокодами"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "🏷 **Управление промокодами**\n\nВыберите действие:",
        reply_markup=admin_promo_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_promo_create")
async def admin_promo_create_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание промокода"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "🏷 **Создание промокода**\n\n"
        "Введите **код промокода** (латиницей, без пробелов):",
        reply_markup=back_keyboard("admin_promo")
    )
    
    await AdminPromoState.promo_code.set()
    await callback.answer()

@router.message(AdminPromoState.promo_code)
async def admin_promo_code_received(message: Message, state: FSMContext):
    """Получение кода промокода"""
    code = message.text.strip().upper()
    
    if not code.isalnum():
        await message.answer("❌ Используйте только буквы и цифры")
        return
    
    await state.update_data(promo_code=code)
    
    await message.answer(
        "💰 Введите **процент скидки** (1-100):",
        reply_markup=back_keyboard("admin_promo")
    )
    
    await AdminPromoState.promo_discount.set()

@router.message(AdminPromoState.promo_discount)
async def admin_promo_discount_received(message: Message, state: FSMContext):
    """Получение процента скидки"""
    try:
        discount = int(message.text)
        if not 1 <= discount <= 100:
            raise ValueError()
    except:
        await message.answer("❌ Введите число от 1 до 100")
        return
    
    await state.update_data(promo_discount=discount)
    
    data = await state.get_data()
    
    await create_promo_code(
        code=data['promo_code'],
        discount_percent=discount
    )
    
    await log_admin_action(message.from_user.id, "promo_created", f"Code: {data['promo_code']}")
    
    await message.answer(
        f"✅ **Промокод создан!**\n\n"
        f"Код: {data['promo_code']}\n"
        f"Скидка: {discount}%",
        reply_markup=admin_promo_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.clear()

@router.callback_query(F.data == "admin_promo_list")
async def admin_promo_list(callback: CallbackQuery):
    """Список промокодов"""
    if not await check_admin(callback):
        return
    
    promos = await get_all_promo_codes()
    
    if not promos:
        await callback.answer("📭 Промокодов нет", show_alert=True)
        return
    
    text = "🏷 **Активные промокоды:**\n\n"
    
    for promo in promos:
        code, discount, is_active = promo[0], promo[1], promo[5]
        status = "✅" if is_active else "❌"
        text += f"{status} {code} | -{discount}%\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_promo"))
    await callback.answer()

# ============================================
# РАССЫЛКИ
# ============================================

@router.callback_query(F.data == "admin_mailing")
async def admin_mailing(callback: CallbackQuery):
    """Меню управления рассылками"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "📢 **Рассылка пользователям**\n\nВыберите действие:",
        reply_markup=admin_mailing_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_mailing_create")
async def admin_mailing_create_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание рассылки"""
    if not await check_admin(callback):
        return
    
    await callback.message.answer(
        "📢 **Создание рассылки**\n\n"
        "Введите **текст сообщения**:",
        reply_markup=back_keyboard("admin_mailing")
    )
    
    await AdminMailingState.mailing_text.set()
    await callback.answer()

@router.message(AdminMailingState.mailing_text)
async def admin_mailing_text_received(message: Message, state: FSMContext):
    """Получение текста рассылки"""
    await state.update_data(mailing_text=message.text)
    
    await message.answer(
        "📸 Отправьте **фото для рассылки** (или напишите «Пропустить»):",
        reply_markup=back_keyboard("admin_mailing")
    )
    
    await AdminMailingState.mailing_photo.set()

@router.message(F.photo, AdminMailingState.mailing_photo)
async def admin_mailing_photo_received(message: Message, state: FSMContext):
    """Получение фото для рассылки"""
    await state.update_data(mailing_photo=message.photo[-1].file_id)
    await confirm_mailing(message, state)

@router.message(AdminMailingState.mailing_photo)
async def admin_mailing_skip_photo(message: Message, state: FSMContext):
    """Пропустить фото"""
    if message.text.lower() in ["пропустить", "skip", "нет", "-"]:
        await state.update_data(mailing_photo=None)
        await confirm_mailing(message, state)
    else:
        await message.answer("📸 Отправьте фото или напишите «Пропустить»:")

async def confirm_mailing(message: Message, state: FSMContext):
    """Подтверждение рассылки"""
    data = await state.get_data()
    
    await message.answer(
        f"⚠️ **Подтверждение рассылки**\n\n"
        f"Будет отправлено всем пользователям!\n\n"
        f"Текст:\n{data['mailing_text'][:200]}...\n\n"
        f"Нажмите «Подтвердить» для отправки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="mailing_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_mailing")]
        ]),
        parse_mode="Markdown"
    )
    
    await AdminMailingState.mailing_confirm.set()

@router.callback_query(F.data == "mailing_confirm")
async def mailing_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    if not await check_admin(callback):
        return
    
    data = await state.get_data()
    
    # Создаём рассылку
    mailing_id = await create_mailing(data['mailing_text'], data.get('mailing_photo'))
    
    # Получаем всех пользователей
    users = await get_all_users(limit=10000)
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            if data.get('mailing_photo'):
                await callback.bot.send_photo(
                    user[0],
                    data['mailing_photo'],
                    data['mailing_text']
                )
            else:
                await callback.bot.send_message(
                    user[0],
                    data['mailing_text']
                )
            sent += 1
        except:
            failed += 1
        
        # Пауза чтобы не заблокировали
        import asyncio
        await asyncio.sleep(0.05)
    
    await update_mailing_status(mailing_id, 'completed', sent, failed)
    await log_admin_action(callback.from_user.id, "mailing_sent", f"Sent: {sent}, Failed: {failed}")
    
    await callback.message.answer(
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=admin_mailing_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_mailing_history")
async def admin_mailing_history(callback: CallbackQuery):
    """История рассылок"""
    if not await check_admin(callback):
        return
    
    mailings = await get_mailing_history()
    
    if not mailings:
        await callback.answer("📭 История пуста", show_alert=True)
        return
    
    text = "📢 **История рассылок:**\n\n"
    
    for mailing in mailings:
        mid, text_msg, photo, total, sent, failed, status, created = mailing
        text += f"#{mid} | {status} | 📤{sent} ❌{failed} | {created[:16] if created else '—'}\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_mailing"))
    await callback.answer()

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """Настройки бота"""
    if not await check_admin(callback):
        return
    
    maintenance = await get_bot_setting('is_maintenance')
    bonus_percent = await get_bot_setting('bonus_percent')
    
    text = (
        "⚙️ **Настройки бота**\n\n"
        f"🔧 Режим обслуживания: {'✅ ВКЛ' if maintenance == '1' else '❌ ВЫКЛ'}\n"
        f"🎁 Процент бонусов: {bonus_percent}%\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.answer(text, reply_markup=admin_settings_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_toggle_maintenance")
async def admin_toggle_maintenance(callback: CallbackQuery):
    """Переключить режим обслуживания"""
    if not await check_admin(callback):
        return
    
    current = await get_bot_setting('is_maintenance')
    new_value = '0' if current == '1' else '1'
    
    await update_bot_setting('is_maintenance', new_value)
    await log_admin_action(callback.from_user.id, "maintenance_toggled", f"New value: {new_value}")
    
    await callback.answer(f"✅ Режим обслуживания: {'ВКЛ' if new_value == '1' else 'ВЫКЛ'}")
    await admin_settings(callback)

# ============================================
# ЛОГИ АДМИНА
# ============================================

@router.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    """Логи действий админов"""
    if not await check_admin(callback):
        return
    
    logs = await get_admin_logs(limit=20)
    
    text = "📋 **Последние действия админов:**\n\n"
    
    for log in logs:
        lid, admin_id, action, details, created = log
        text += f"👤 {admin_id} | {action} | {created[:16] if created else '—'}\n"
        if details:
            text += f"   📝 {details}\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("admin_main"))
    await callback.answer()

# ============================================
# НАЗАД
# ============================================

@router.callback_query(F.data == "back_admin")
async def back_to_admin(callback: CallbackQuery):
    """Вернуться в админ-панель"""
    await admin_main(callback)
    await callback.answer()

# Импорт для клавиатур внутри файла
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
