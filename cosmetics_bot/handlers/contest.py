from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from database import (
    get_active_contests, get_contest_by_id, can_join_contest,
    join_contest, get_contest_participants, pick_winner,
    get_user_contests, create_contest, get_user_orders
)
from keyboards import contest_list_keyboard, contest_detail_keyboard, back_keyboard
from config import ADMIN_IDS, ADMIN_GROUP_ID
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# ============================================
# КНОПКА РОЗЫГРЫШ
# ============================================

@router.message(F.text == "🏆 Розыгрыш")
async def show_contests(message: Message):
    """Показать активные конкурсы"""
    contests = await get_active_contests()
    
    if not contests:
        await message.answer(
            "🎉 **Сейчас нет активных розыгрышей**\n\n"
            "Заходите позже — мы регулярно проводим конкурсы! ✨\n\n"
            "📢 Подпишитесь на наш канал, чтобы не пропустить новые розыгрыши!",
            reply_markup=back_keyboard("main"),
            parse_mode="Markdown"
        )
        return
    
    text = "🏆 **Активные розыгрыши:**\n\n"
    
    for contest in contests:
        contest_id, title, desc, prize, ctype, end_date = contest[:6]
        
        # Форматируем дату окончания
        end_formatted = end_date[:16].replace('T', ' ') if end_date else '—'
        
        type_emoji = {"giveaway": "🎁", "photo": "📸", "referral": "👥"}.get(ctype, "🏆")
        
        text += f"{type_emoji} **{title}**\n"
        text += f"🎁 Приз: {prize}\n"
        text += f"⏰ До: {end_formatted}\n\n"
    
    text += "Нажмите на конкурс для участия:"
    
    await message.answer(
        text,
        reply_markup=contest_list_keyboard(),
        parse_mode="Markdown"
    )

# ============================================
# ДЕТАЛИ КОНКУРСА
# ============================================

@router.callback_query(F.data.startswith("contest_"))
async def contest_detail(callback: CallbackQuery):
    """Показать детали конкурса"""
    try:
        contest_id = int(callback.data.split("_")[1])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    contest = await get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    contest_id, title, desc, prize, ctype, end_date, channel_req = contest[:7]
    
    type_names = {
        "giveaway": "🎁 Простой розыгрыш",
        "photo": "📸 Фотоконкурс",
        "referral": "👥 Конкурс рефералов"
    }
    
    end_formatted = end_date[:16].replace('T', ' ') if end_date else '—'
    
    text = (
        f"🏆 **{title}**\n\n"
        f"📋 {type_names.get(ctype, 'Конкурс')}\n\n"
        f"📝 {desc}\n\n"
        f"🎁 **Приз:** {prize}\n\n"
        f"⏰ **Окончание:** {end_formatted}\n\n"
    )
    
    if channel_req:
        text += f"📢 **Обязательно:** Подписка на {channel_req}\n\n"
    
    # Считаем участников
    participants = await get_contest_participants(contest_id)
    text += f"👥 Участников: {len(participants)}\n\n"
    
    # Кнопки
    kb = contest_detail_keyboard(contest_id, channel_req)
    
    await callback.message.answer(
        text,
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# УЧАСТИЕ В КОНКУРСЕ
# ============================================

@router.callback_query(F.data.startswith("join_contest_"))
async def join_contest_handler(callback: CallbackQuery):
    """Участие в конкурсе"""
    try:
        contest_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    contest = await get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    # Проверяем возможность участия
    can_join, message_text = await can_join_contest(callback.from_user.id, contest)
    
    if not can_join:
        # Если проблема с подпиской — показываем кнопку подписки
        if "подписаны" in message_text and contest[6]:
            kb = [[InlineKeyboardButton(
                text="✅ Я подписался!",
                callback_data=f"check_sub_{contest_id}"
            )]]
            await callback.message.answer(
                message_text + "\n\nПодпишитесь и нажмите кнопку ниже:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
            )
        else:
            await callback.answer(message_text, show_alert=True)
        return
    
    # Добавляем в участники
    await join_contest(callback.from_user.id, contest_id)
    
    # Если фотоконкурс — просим фото
    if contest[4] == "photo":
        await callback.message.answer(
            "📸 **Отлично! Теперь отправьте фото**\n\n"
            "Сделайте фото с нашей продукцией или в стиле конкурса.\n"
            "Администратор проверит и одобрит вашу заявку! ✨"
        )
    else:
        await callback.answer("🎉 Вы участвуете! Удачи! 🍀", show_alert=True)
    
    # Обновляем сообщение с конкурсом
    await contest_detail(callback)

# ============================================
# ПРОВЕРКА ПОДПИСКИ
# ============================================

@router.callback_query(F.data.startswith("check_sub_"))
async def check_subscription(callback: CallbackQuery):
    """Проверить подписку на канал"""
    try:
        contest_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    contest = await get_contest_by_id(contest_id)
    
    if not contest or not contest[6]:
        await callback.answer("❌ Ошибка конкурса", show_alert=True)
        return
    
    try:
        member = await callback.bot.get_chat_member(contest[6], callback.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            await join_contest(callback.from_user.id, contest_id)
            await callback.answer("✅ Подписка подтверждена! Вы участвуете! 🎉", show_alert=True)
            await contest_detail(callback)
        else:
            await callback.answer("❌ Вы ещё не подписаны", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Не удалось проверить подписку. Убедитесь, что канал не частный.", show_alert=True)

# ============================================
# МОИ УЧАСТИЯ
# ============================================

@router.callback_query(F.data == "my_contests")
async def show_my_contests(callback: CallbackQuery):
    """Показать конкурсы пользователя"""
    user_contests = await get_user_contests(callback.from_user.id)
    
    if not user_contests:
        await callback.answer(
            "📭 Вы пока не участвуете в розыгрышах\n\n"
            "Загляните в активные конкурсы! 🏆",
            show_alert=True
        )
        return
    
    text = "🎫 **Ваши участия:**\n\n"
    
    for contest in user_contests:
        cid, title, prize, end_date, winner_id = contest
        
        if winner_id == callback.from_user.id:
            status = "🏆 ВЫ ПОБЕДИЛИ!"
        elif winner_id:
            status = "😔 Победитель выбран"
        else:
            status = "⏳ Ожидание"
        
        end_formatted = end_date[:16].replace('T', ' ') if end_date else '—'
        
        text += f"{status}\n"
        text += f"🎁 {title}: {prize}\n"
        text += f"⏰ {end_formatted}\n\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("contests"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ПРАВИЛА КОНКУРСОВ
# ============================================

@router.callback_query(F.data == "contest_rules")
async def show_contest_rules(callback: CallbackQuery):
    """Показать правила конкурсов"""
    text = (
        "📋 **Правила участия в конкурсах:**\n\n"
        "✅ **Общие требования:**\n"
        "• Быть подписанным на наш канал\n"
        "• Один участник = один аккаунт\n"
        "• Соблюдение правил Telegram\n\n"
        "🎁 **Типы конкурсов:**\n"
        "• 🎁 Простой розыгрыш — случайный выбор победителя\n"
        "• 📸 Фотоконкурс — лучшее фото побеждает\n"
        "• 👥 Конкурс рефералов — кто пригласил больше друзей\n\n"
        "🏆 **Определение победителя:**\n"
        "• Случайный выбор через бота\n"
        "• Публикация результатов в канале\n"
        "• Уведомление победителя в ЛС\n\n"
        "📦 **Получение приза:**\n"
        "• Победитель связывается с менеджером в течение 48 часов\n"
        "• Приз отправляется за наш счёт\n"
        "• Возможна замена приза на бонусы"
    )
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("contests"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# НАЗАД
# ============================================

@router.callback_query(F.data == "back_contests")
async def back_to_contests(callback: CallbackQuery):
    """Вернуться к списку конкурсов"""
    contests = await get_active_contests()
    
    if not contests:
        text = "🎉 **Сейчас нет активных розыгрышей**\n\nЗаходите позже!"
    else:
        text = "🏆 **Активные розыгрыши:**\n\n"
        for contest in contests:
            text += f"🎁 {contest[1]} | До: {contest[5][:16] if contest[5] else '—'}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=contest_list_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# АДМИН: СОЗДАНИЕ КОНКУРСА
# ============================================

@router.callback_query(F.data == "admin_contest_create")
async def admin_create_contest_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание конкурса"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Доступ запрещён", show_alert=True)
        return
    
    from states import AdminContestState
    
    await callback.message.answer(
        "🏆 **Создание нового конкурса**\n\n"
        "Введите **название конкурса**:",
        reply_markup=back_keyboard("admin_main")
    )
    
    await AdminContestState.contest_title.set()
    await callback.answer()

@router.message(F.text.startswith("contest_title_"))
async def admin_contest_title_received(message: Message, state: FSMContext):
    """Получение названия конкурса"""
    from states import AdminContestState
    
    await state.update_data(contest_title=message.text)
    
    await message.answer(
        "📝 Введите **описание конкурса**:"
    )
    
    await AdminContestState.contest_desc.set()

@router.message(F.text.startswith("contest_desc_"))
async def admin_contest_desc_received(message: Message, state: FSMContext):
    """Получение описания конкурса"""
    from states import AdminContestState
    
    await state.update_data(contest_desc=message.text)
    
    await message.answer(
        "🎁 Введите **приз**:"
    )
    
    await AdminContestState.contest_prize.set()

@router.message(F.text.startswith("contest_prize_"))
async def admin_contest_prize_received(message: Message, state: FSMContext):
    """Получение информации о призе"""
    from states import AdminContestState
    from datetime import datetime, timedelta
    
    data = await state.get_data()
    
    # Конкурс на 7 дней
    end_date = (datetime.now() + timedelta(days=7)).isoformat()
    
    contest_id = await create_contest(
        title=data.get("contest_title", "Конкурс"),
        description=data.get("contest_desc", ""),
        prize=message.text,
        contest_type="giveaway",
        end_date=end_date,
        channel_required=CHANNEL_ID,
        min_purchases=0
    )
    
    await message.answer(
        f"✅ **Конкурс создан!**\n\n"
        f"ID: {contest_id}\n"
        f"Название: {data.get('contest_title')}\n"
        f"Приз: {message.text}\n"
        f"Окончание: через 7 дней",
        parse_mode="Markdown"
    )
    
    await state.clear()

# ============================================
# АДМИН: ЗАВЕРШЕНИЕ КОНКУРСА
# ============================================

@router.callback_query(F.data.startswith("end_contest_"))
async def admin_end_contest(callback: CallbackQuery):
    """Завершить конкурс и выбрать победителя"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Доступ запрещён", show_alert=True)
        return
    
    try:
        contest_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    contest = await get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    # Выбираем победителя
    winner = await pick_winner(contest_id)
    
    if winner:
        user_id, username, first_name, joined_at = winner
        
        # Уведомляем победителя
        try:
            await callback.bot.send_message(
                user_id,
                f"🎉 **ПОЗДРАВЛЯЕМ! Вы победили в конкурсе!**\n\n"
                f"🏆 {contest[1]}\n"
                f"🎁 Ваш приз: {contest[3]}\n\n"
                f"Свяжитесь с менеджером в течение 48 часов для получения приза! 📩",
                parse_mode="Markdown"
            )
        except:
            pass
        
        # Уведомляем админа
        winner_mention = f"@{username}" if username else f"[{first_name}](tg://user?id={user_id})"
        
        await callback.message.answer(
            f"✅ **Конкурс завершён!**\n\n"
            f"🏆 Победитель: {winner_mention}\n"
            f"🎁 Приз: {contest[3]}\n\n"
            f"Победителю отправлено уведомление! ✨",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer("⚠️ Конкурс завершён без победителя (не было участников)")
    
    await callback.answer()

# Импорт для клавиатур внутри файла
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

