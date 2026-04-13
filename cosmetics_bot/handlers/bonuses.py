from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import (
    get_bonus_balance, get_bonus_history, get_user_level,
    get_referral_code, get_referrals_count, add_bonus
)
from keyboards import bonus_menu_keyboard, back_keyboard

router = Router()

# ============================================
# КНОПКА БОНУСЫ
# ============================================

@router.message(F.text == "🎁 Бонусы")
async def show_bonus_menu(message: Message):
    """Показать меню бонусов"""
    user_id = message.from_user.id
    
    balance = await get_bonus_balance(user_id)
    level_info = await get_user_level(user_id)
    referrals = await get_referrals_count(user_id)
    
    text = (
        f"{level_info['color']} **Ваш уровень: {level_info['level']}**\n\n"
        f"💰 **Баланс: {balance} бонусов**\n"
        f"🎁 Кэшбэк с покупок: **{level_info['percent']}%**\n\n"
        f"👥 Приглашено друзей: {referrals}\n\n"
        f"📊 **Уровни программы:**\n"
        f"🥉 Bronze: 0-5000₽ (5%)\n"
        f"🥈 Silver: 5000-15000₽ (10%)\n"
        f"🥇 Gold: 15000-50000₽ (12%)\n"
        f"💎 Platinum: 50000₽+ (15%)\n\n"
        f"💡 1 бонус = 1 рубль при оплате заказа"
    )
    
    await message.answer(
        text,
        reply_markup=bonus_menu_keyboard(),
        parse_mode="Markdown"
    )

# ============================================
# ИСТОРИЯ БОНУСОВ
# ============================================

@router.callback_query(F.data == "bonus_history")
async def show_bonus_history(callback: CallbackQuery):
    """Показать историю бонусов"""
    user_id = callback.from_user.id
    history = await get_bonus_history(user_id, limit=15)
    
    if not history:
        await callback.answer(
            "📭 История бонусов пуста",
            show_alert=True
        )
        return
    
    text = "📜 **История бонусов:**\n\n"
    
    for item in history:
        amount, reason, created_at = item
        
        if amount > 0:
            emoji = "➕"
            sign = "+"
        else:
            emoji = "➖"
            sign = ""
        
        reason_emoji = {
            "purchase": "🛒",
            "order_payment": "💳",
            "referral_bonus": "👥",
            "referral_welcome": "🎁",
            "review": "📝",
            "contest": "🏆",
            "daily": "📅",
            "admin_bonus": "👨‍💼",
            "order_cancel": "❌"
        }
        
        text += f"{emoji} {sign}{amount} б. | {reason_emoji.get(reason, '⭐')} {reason}\n"
        text += f"   🕐 {created_at[:16] if created_at else '—'}\n\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("bonus"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# РЕФЕРАЛЬНАЯ ПРОГРАММА
# ============================================

@router.callback_query(F.data == "bonus_referral")
async def show_referral_info(callback: CallbackQuery):
    """Показать реферальную информацию"""
    user_id = callback.from_user.id
    
    ref_code = await get_referral_code(user_id)
    referrals = await get_referrals_count(user_id)
    
    # Получаем username бота для ссылки
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username
    
    text = (
        "👥 **Пригласи друзей и получи бонусы!**\n\n"
        f"🔗 **Ваш реферальный код:** `{ref_code}`\n\n"
        f"👫 Приглашено друзей: **{referrals}**\n\n"
        "🎁 **Награды:**\n"
        "• Друг получает 500 бонусов при регистрации\n"
        "• Вы получаете 500 бонусов за каждого друга\n"
        "• Друг совершает первую покупку — вы получаете 10% от суммы\n\n"
        "📤 **Пригласительная ссылка:**\n"
        f"`https://t.me/{bot_username}?start={ref_code}`\n\n"
        "Отправьте ссылку другу или скопируйте код!"
    )
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("bonus"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ПРАВИЛА БОНУСНОЙ ПРОГРАММЫ
# ============================================

@router.callback_query(F.data == "bonus_rules")
async def show_bonus_rules(callback: CallbackQuery):
    """Показать правила бонусной программы"""
    text = (
        "📋 **Правила бонусной программы:**\n\n"
        "✅ **Как получить бонусы:**\n"
        "• 5-15% кэшбэк с каждой покупки (зависит от уровня)\n"
        "• 500 бонусов за приглашённого друга\n"
        "• 10% от первой покупки друга\n"
        "• 100 бонусов за отзыв с фото\n"
        "• 50 бонусов за ежедневный чекин\n\n"
        "💰 **Как потратить:**\n"
        "• Оплата до 50% суммы заказа бонусами\n"
        "• 1 бонус = 1 рубль\n"
        "• Минимальная сумма заказа для оплаты бонусами: 500₽\n\n"
        "⏰ **Срок действия:**\n"
        "• Бонусы действительны 12 месяцев\n"
        "• Сгорают в конце календарного года\n\n"
        "❓ **Вопросы?** Напишите менеджеру!"
    )
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("bonus"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================

@router.message(F.text == "📅 Ежедневный бонус")
async def daily_bonus(message: Message):
    """Ежедневный бонус"""
    from datetime import datetime, timedelta
    from database import get_bonus_history
    
    user_id = message.from_user.id
    
    # Проверяем последний ежедневный бонус
    history = await get_bonus_history(user_id, limit=50)
    
    last_claim = None
    for item in history:
        if item[1] == "daily" and item[2]:
            last_claim = item[2]
            break
    
    if last_claim:
        try:
            last_date = datetime.fromisoformat(last_claim.replace(' ', 'T'))
            now = datetime.now()
            
            if now - last_date < timedelta(hours=24):
                hours_left = 24 - (now - last_date).seconds // 3600
                await message.answer(
                    f"⏰ **Следующий бонус через {hours_left} ч.**\n\n"
                    "Заходите завтра за новым бонусом!",
                    parse_mode="Markdown"
                )
                return
        except:
            pass
    
    # Начисляем бонус
    await add_bonus(user_id, 50, "daily")
    
    await message.answer(
        "🎉 **Ежедневный бонус получен!**\n\n"
        "✅ +50 бонусов зачислено на ваш счёт\n\n"
        "Заходите каждый день за новыми бонусами! 📅",
        parse_mode="Markdown"
    )

# ============================================
# НАЗАД В МЕНЮ БОНУСОВ
# ============================================

@router.callback_query(F.data == "back_bonus")
async def back_to_bonus(callback: CallbackQuery):
    """Вернуться в меню бонусов"""
    user_id = callback.from_user.id
    
    balance = await get_bonus_balance(user_id)
    level_info = await get_user_level(user_id)
    referrals = await get_referrals_count(user_id)
    
    text = (
        f"{level_info['color']} **Ваш уровень: {level_info['level']}**\n\n"
        f"💰 **Баланс: {balance} бонусов**\n"
        f"🎁 Кэшбэк: **{level_info['percent']}%**\n"
        f"👥 Друзей: {referrals}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=bonus_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

