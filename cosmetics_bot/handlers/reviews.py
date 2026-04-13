from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import (
    create_review, get_product_reviews, get_user_reviews,
    get_pending_reviews, approve_review, reject_review,
    get_product_rating, get_user_orders, add_bonus, get_user
)
from keyboards import reviews_keyboard, rating_keyboard, back_keyboard
from states import ReviewState
from config import ADMIN_IDS, ADMIN_GROUP_ID

router = Router()

# ============================================
# КНОПКА ОТЗЫВЫ
# ============================================

@router.message(F.text == "📝 Отзывы")
async def show_reviews_menu(message: Message):
    """Показать меню отзывов"""
    await message.answer(
        "📝 **Отзывы наших клиентов**\n\n"
        "Мы ценим каждое мнение! Ваши отзывы помогают нам становиться лучше.\n\n"
        "✨ **Преимущества отзывов:**\n"
        "• Помогают другим сделать выбор\n"
        "• +100 бонусов за каждый опубликованный отзыв\n"
        "• +50 бонусов за фото в отзыве\n\n"
        "Выберите действие:",
        reply_markup=reviews_keyboard(),
        parse_mode="Markdown"
    )

# ============================================
# ЧТЕНИЕ ОТЗЫВОВ
# ============================================

@router.callback_query(F.data == "read_reviews")
async def read_reviews(callback: CallbackQuery):
    """Показать последние опубликованные отзывы"""
    from database import get_all_products
    
    # Получаем все товары с отзывами
    products = await get_all_products(limit=50)
    
    if not products:
        await callback.answer("📭 Пока нет отзывов", show_alert=True)
        return
    
    reviews_count = 0
    text = "📚 **Последние отзывы:**\n\n"
    
    for product in products[:5]:  # Показываем отзывы для 5 товаров
        product_id = product[0]
        product_name = product[1]
        
        reviews = await get_product_reviews(product_id, approved_only=True, limit=2)
        
        for review in reviews:
            rid, user_id, order_id, pid, rating, comment, photos, approved, verified, response, created, updated, first_name, username = review
            
            stars = "⭐" * rating + "☆" * (5 - rating)
            
            text += f"📦 **{product_name}**\n"
            text += f"{stars} ({rating}/5)\n"
            text += f"👤 {first_name}\n"
            text += f"📝 {comment[:100]}{'...' if len(comment) > 100 else ''}\n\n"
            
            reviews_count += 1
    
    if reviews_count == 0:
        await callback.answer(
            "📭 Пока нет опубликованных отзывов\n\n"
            "Станьте первым, кто оставит отзыв!",
            show_alert=True
        )
        return
    
    text += f"\nВсего опубликовано отзывов: {reviews_count}"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("reviews"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# НАПИСАТЬ ОТЗЫВ
# ============================================

@router.callback_query(F.data == "write_review")
async def write_review_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание отзыва"""
    # Проверяем, есть ли у пользователя завершённые заказы
    orders = await get_user_orders(callback.from_user.id)
    
    delivered_orders = [o for o in orders if o[5] == 'delivered']  # status = delivered
    
    if not delivered_orders:
        await callback.answer(
            "⚠️ Вы можете оставить отзыв только после получения заказа!\n\n"
            "Как только ваш заказ будет доставлен, вы сможете поделиться впечатлениями.",
            show_alert=True
        )
        return
    
    await callback.message.answer(
        "📦 **Выберите товар для отзыва**\n\n"
        "Введите ID товара или название:\n"
        "(ID можно посмотреть в каталоге)",
        reply_markup=back_keyboard("reviews")
    )
    
    await ReviewState.product_id.set()
    await callback.answer()

@router.message(ReviewState.product_id)
async def review_product_selected(message: Message, state: FSMContext):
    """Выбор товара для отзыва"""
    from database import get_product_by_id
    
    try:
        product_id = int(message.text)
    except:
        # Пытаемся найти по названию
        from database import get_all_products
        products = await get_all_products(limit=100)
        
        found = None
        for p in products:
            if message.text.lower() in p[1].lower():
                found = p
                break
        
        if found:
            product_id = found[0]
        else:
            await message.answer(
                "❌ Товар не найден\n\n"
                "Введите ID товара цифрами или точное название:"
            )
            return
    
    product = await get_product_by_id(product_id)
    
    if not product:
        await message.answer("❌ Товар не найден\nПопробуйте ещё раз:")
        return
    
    await state.update_data(product_id=product_id, product_name=product[1])
    
    await message.answer(
        f"📦 **{product[1]}**\n\n"
        "⭐ **Оцените товар:**\n"
        "Нажмите на количество звёзд:",
        reply_markup=rating_keyboard(),
        parse_mode="Markdown"
    )
    
    await ReviewState.rating.set()

@router.callback_query(F.data.startswith("rating_"))
async def review_rating_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор рейтинга"""
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    
    await callback.message.answer(
        "📝 **Напишите ваш отзыв:**\n\n"
        "Расскажите о качестве, эффекте, впечатлениях.\n"
        "Минимум 10 символов.\n\n"
        "Или отправьте фото с подписью:",
        reply_markup=back_keyboard("reviews")
    )
    
    await ReviewState.comment.set()
    await callback.answer()

@router.message(ReviewState.comment)
async def review_comment_received(message: Message, state: FSMContext):
    """Получение текста отзыва"""
    comment = message.text
    
    if len(comment) < 10:
        await message.answer(
            "❌ Отзыв слишком короткий. Минимум 10 символов.\n\n"
            "Попробуйте ещё раз:"
        )
        return
    
    await state.update_data(comment=comment)
    await finalize_review(message, state)

@router.message(F.photo, ReviewState.comment)
async def review_photo_received(message: Message, state: FSMContext):
    """Получение фото к отзыву"""
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    if len(caption) < 10:
        await message.answer(
            "❌ Подпись к фото слишком короткая. Минимум 10 символов.\n\n"
            "Отправьте фото с более подробной подписью:"
        )
        return
    
    await state.update_data(comment=caption, photos=[photo_id])
    await finalize_review(message, state)

async def finalize_review(message: Message, state: FSMContext):
    """Завершение создания отзыва"""
    data = await state.get_data()
    user_id = message.from_user.id
    
    product_id = data.get("product_id")
    rating = data.get("rating")
    comment = data.get("comment", "")
    photos = data.get("photos", [])
    
    # Получаем ID последнего заказа для привязки
    orders = await get_user_orders(user_id)
    order_id = orders[0][0] if orders else 0
    
    # Создаём отзыв (на модерации)
    review_id = await create_review(
        user_id=user_id,
        order_id=order_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
        photos=photos
    )
    
    if not review_id:
        await message.answer("❌ Вы уже оставляли отзыв на этот товар!")
        await state.clear()
        return
    
    # Уведомляем админов о новом отзыве
    await notify_admins_review(message.bot, review_id, user_id, product_id, rating, comment)
    
    # Начисляем бонусы (после одобрения - но пока обещаем)
    bonus = 100
    if photos:
        bonus += 50
    
    await message.answer(
        f"✅ **Отзыв отправлен на модерацию!**\n\n"
        f"После публикации вы получите **{bonus} бонусов**.\n"
        f"Обычно модерация занимает до 24 часов.\n\n"
        f"Спасибо за ваш отзыв! 🙏",
        reply_markup=back_keyboard("main"),
        parse_mode="Markdown"
    )
    
    await state.clear()

# ============================================
# УВЕДОМЛЕНИЕ АДМИНАМ ОБ ОТЗЫВЕ
# ============================================

async def notify_admins_review(bot, review_id: int, user_id: int, product_id: int, rating: int, comment: str):
    """Отправить уведомление админам о новом отзыве"""
    from database import get_product_by_id, get_user
    
    user = await get_user(user_id)
    product = await get_product_by_id(product_id)
    
    stars = "⭐" * rating + "☆" * (5 - rating)
    
    text = (
        f"🔍 **НОВЫЙ ОТЗЫВ НА МОДЕРАЦИИ #{review_id}**\n\n"
        f"📦 Товар: {product[1] if product else 'Неизвестно'}\n"
        f"👤 Клиент: {user[2] if user else 'Неизвестно'} (@{user[1] if user and user[1] else 'нет'})\n"
        f"{stars} ({rating}/5)\n\n"
        f"📝 Текст:\n{comment}\n\n"
        f"🕐 {str(review_id)[:19]}"
    )
    
    # Отправляем в админ-группу
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
# МОИ ОТЗЫВЫ
# ============================================

@router.callback_query(F.data == "my_reviews")
async def show_my_reviews(callback: CallbackQuery):
    """Показать отзывы пользователя"""
    user_id = callback.from_user.id
    reviews = await get_user_reviews(user_id, limit=10)
    
    if not reviews:
        await callback.answer(
            "📭 Вы пока не оставляли отзывов",
            show_alert=True
        )
        return
    
    text = "📝 **Ваши отзывы:**\n\n"
    
    for review in reviews:
        rid, user_id, order_id, product_id, rating, comment, photos, approved, verified, response, created, updated, product_name = review
        
        stars = "⭐" * rating + "☆" * (5 - rating)
        status = "✅ Опубликовано" if approved else "⏳ На модерации"
        
        text += f"{status}\n"
        text += f"📦 {product_name}\n"
        text += f"{stars}\n"
        text += f"📝 {comment[:50]}{'...' if len(comment) > 50 else ''}\n\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("reviews"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# АДМИН: МОДЕРАЦИЯ ОТЗЫВОВ
# ============================================

@router.callback_query(F.data == "admin_reviews_pending")
async def admin_pending_reviews(callback: CallbackQuery):
    """Показать отзывы на модерации"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Доступ запрещён", show_alert=True)
        return
    
    reviews = await get_pending_reviews(limit=10)
    
    if not reviews:
        await callback.answer("✅ Все отзывы обработаны!", show_alert=True)
        return
    
    for review in reviews:
        rid = review[0]
        product_name = review[14]
        first_name = review[12]
        username = review[13]
        rating = review[4]
        comment = review[5]
        photos = review[6]
        
        stars = "⭐" * rating + "☆" * (5 - rating)
        
        text = (
            f"🔍 **Отзыв #{rid}**\n\n"
            f"📦 {product_name}\n"
            f"👤 {first_name} (@{username or 'нет'})\n"
            f"{stars}\n\n"
            f"📝 {comment}\n\n"
            f"{'📸 Есть фото' if photos else 'Без фото'}"
        )
        
        kb = back_keyboard("admin_reviews")
        
        # Если есть фото
        if photos:
            import json
            photo_ids = json.loads(photos) if photos else []
            if photo_ids:
                await callback.message.answer_photo(
                    photo=photo_ids[0],
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"review_approve_{rid}"),
                            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"review_reject_{rid}")
                        ],
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")]
                    ])
                )
                continue
        
        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"review_approve_{rid}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"review_reject_{rid}")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")]
            ]),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("review_approve_"))
async def admin_approve_review(callback: CallbackQuery):
    """Одобрить отзыв"""
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    review_id = int(callback.data.split("_")[2])
    
    # Одобрить отзыв
    await approve_review(review_id)
    
    # Получить данные для начисления бонусов
    from database import get_user
    async with __import__('aiosqlite').connect("cosmetics.db") as db:
        cursor = await db.execute("SELECT user_id, photos FROM reviews WHERE id = ?", (review_id,))
        result = await cursor.fetchone()
    
    if result:
        user_id, photos = result
        bonus = 100
        if photos:
            import json
            if json.loads(photos):
                bonus += 50
        
        await add_bonus(user_id, bonus, "review")
        
        # Уведомить пользователя
        try:
            await callback.bot.send_message(
                user_id,
                f"✅ **Ваш отзыв опубликован!**\n\n"
                f"🎁 Вам начислено **{bonus} бонусов**.\n"
                f"Спасибо за ваш вклад! 🙏",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await callback.message.delete()
    await callback.answer("✅ Отзыв одобрен!")

@router.callback_query(F.data.startswith("review_reject_"))
async def admin_reject_review(callback: CallbackQuery):
    """Отклонить отзыв"""
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    review_id = int(callback.data.split("_")[2])
    
    await reject_review(review_id)
    
    await callback.message.delete()
    await callback.answer("❌ Отзыв отклонён")

# ============================================
# НАЗАД
# ============================================

@router.callback_query(F.data == "back_reviews")
async def back_to_reviews(callback: CallbackQuery):
    """Вернуться в меню отзывов"""
    await callback.message.edit_text(
        "📝 **Отзывы наших клиентов**\n\n"
        "Выберите действие:",
        reply_markup=reviews_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Импорт для клавиатур внутри файла
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
