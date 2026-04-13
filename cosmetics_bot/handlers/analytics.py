from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import (
    get_sales_stats, get_dashboard_stats, get_product_stats,
    get_bonus_stats, get_contest_stats, get_daily_revenue,
    get_all_orders, get_all_users, get_all_products,
    get_admin_logs, get_mailing_history, get_review_stats
)
from keyboards import analytics_keyboard, period_keyboard, back_keyboard
from config import ADMIN_IDS

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
# ГЛАВНОЕ МЕНЮ АНАЛИТИКИ
# ============================================

@router.callback_query(F.data == "analytics_main")
@router.message(F.text == "📊 Аналитика")
async def analytics_main(message: Message | CallbackQuery):
    """Главная панель аналитики"""
    if not await check_admin(message):
        return
    
    # Получаем базовые метрики
    sales = await get_sales_stats("7d")
    stats = await get_dashboard_stats()
    
    text = (
        f"📊 **Панель аналитики**\n\n"
        f"🕐 Период: последние 7 дней\n\n"
        f"💰 **Продажи:**\n"
        f"• Выручка: {sales['revenue']:,} ₽\n"
        f"• Заказы: {sales['orders']}\n"
        f"• Средний чек: {sales['avg_check']:,.0f} ₽\n\n"
        f"👥 **Пользователи:**\n"
        f"• Всего: {stats['total_users']}\n"
        f"• Новые (7д): {sales['new_users']}\n\n"
        f"📦 **Товары:**\n"
        f"• Всего: {stats['total_products']}\n"
        f"• Мало на складе: {stats['low_stock']}\n\n"
        f"📝 **Отзывы:**\n"
        f"• Опубликовано: {stats['approved_reviews']}\n"
        f"• На модерации: {stats['pending_reviews']}\n\n"
        f"Выберите отчёт:"
    )
    
    if isinstance(message, CallbackQuery):
        await message.message.answer(text, reply_markup=analytics_keyboard(), parse_mode="Markdown")
        await message.answer()
    else:
        await message.answer(text, reply_markup=analytics_keyboard(), parse_mode="Markdown")

# ============================================
# ОТЧЁТ: ПРОДАЖИ
# ============================================

@router.callback_query(F.data == "analytics_sales")
async def analytics_sales(callback: CallbackQuery):
    """Отчёт по продажам"""
    if not await check_admin(callback):
        return
    
    stats = await get_sales_stats("7d")
    
    text = (
        "💰 **Отчёт по продажам**\n"
        f"🕐 Период: 7 дней\n\n"
        f"📦 Заказы: {stats['orders']}\n"
        f"💵 Выручка: {stats['revenue']:,} ₽\n"
        f"🧾 Средний чек: {stats['avg_check']:,.0f} ₽\n"
    )
    
    # Топ заказов
    orders = await get_all_orders(status=None, limit=10)
    
    if orders:
        text += "\n📋 **Последние заказы:**\n"
        for order in orders[:5]:
            oid = order[0]
            total = order[2]
            status = order[4]
            text += f"• #{oid} | {total:,} ₽ | {status}\n"
    
    await callback.message.answer(
        text,
        reply_markup=period_keyboard("sales"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ОТЧЁТ: ПОЛЬЗОВАТЕЛИ
# ============================================

@router.callback_query(F.data == "analytics_users")
async def analytics_users(callback: CallbackQuery):
    """Отчёт по пользователям"""
    if not await check_admin(callback):
        return
    
    users = await get_all_users(limit=100)
    total = len(users)
    
    # Активные (с заказами)
    active = sum(1 for u in users if u[4] > 0)  # total_purchases > 0
    
    # С бонусами
    with_bonus = sum(1 for u in users if u[3] > 0)  # bonus_balance > 0
    
    text = (
        "👥 **Отчёт по пользователям**\n\n"
        f"📊 Всего пользователей: {total}\n"
        f"✅ Активных (покупали): {active}\n"
        f"🎁 С бонусами: {with_bonus}\n"
        f"📈 Активность: {active/total*100:.1f}%\n\n"
    )
    
    # Топ пользователей по покупкам
    top_users = sorted(users, key=lambda x: x[4] if x[4] else 0, reverse=True)[:5]
    
    if top_users:
        text += "🏆 **Топ-5 по покупкам:**\n"
        for i, user in enumerate(top_users, 1):
            uid, username, first_name, bonus, purchases = user[:5]
            text += f"{i}. {first_name} (@{username or 'нет'}) | {purchases:,} ₽\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("analytics"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ОТЧЁТ: ТОВАРЫ
# ============================================

@router.callback_query(F.data == "analytics_products")
async def analytics_products(callback: CallbackQuery):
    """Отчёт по товарам"""
    if not await check_admin(callback):
        return
    
    products = await get_all_products(limit=50)
    
    if not products:
        await callback.answer("📭 Нет данных о товарах", show_alert=True)
        return
    
    text = "📦 **Статистика товаров**\n\n"
    
    # Сортируем по цене и запасу
    by_price = sorted(products, key=lambda x: x[3], reverse=True)[:5]  # price
    by_stock = sorted(products, key=lambda x: x[6])[:5]  # stock
    
    text += "💰 **Самые дорогие:**\n"
    for p in by_price:
        text += f"• {p[1]} | {p[3]:,} ₽\n"
    
    text += "\n⚠️ **Заканчиваются:**\n"
    for p in by_stock:
        if p[6] < 10:
            text += f"• {p[1]} | осталось {p[6]} шт.\n"
    
    # Категории
    categories = {}
    for p in products:
        cat = p[4] or "other"
        categories[cat] = categories.get(cat, 0) + 1
    
    text += "\n📂 **По категориям:**\n"
    for cat, count in categories.items():
        cat_names = {"cosmetics": "Косметика", "bads": "БАДы", "body": "Уход за телом", "sets": "Наборы"}
        text += f"• {cat_names.get(cat, cat)}: {count}\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("analytics"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ОТЧЁТ: БОНУСЫ
# ============================================

@router.callback_query(F.data == "analytics_bonuses")
async def analytics_bonuses(callback: CallbackQuery):
    """Отчёт по бонусам"""
    if not await check_admin(callback):
        return
    
    stats = await get_bonus_stats()
    
    text = (
        "🎁 **Статистика бонусной программы**\n\n"
        f"➕ Начислено всего: {stats['issued']:,} б.\n"
        f"➖ Списано всего: {stats['spent']:,} б.\n"
        f"📊 Использовано: {stats['spent']/stats['issued']*100 if stats['issued'] > 0 else 0:.1f}%\n\n"
    )
    
    # Топ пользователей по бонусам
    if stats['top_users']:
        text += "🏆 **Топ-5 по балансу:**\n"
        for first_name, balance, purchases in stats['top_users'][:5]:
            text += f"• {first_name}: {balance:,} б. (потрачено {purchases:,} ₽)\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("analytics"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ОТЧЁТ: КОНКУРСЫ
# ============================================

@router.callback_query(F.data == "analytics_contests")
async def analytics_contests(callback: CallbackQuery):
    """Отчёт по конкурсам"""
    if not await check_admin(callback):
        return
    
    stats = await get_contest_stats()
    
    if not stats:
        await callback.answer("📭 Нет активных конкурсов", show_alert=True)
        return
    
    text = "🏆 **Статистика конкурсов**\n\n"
    
    for contest in stats:
        title, prize, participants, is_active, end_date = contest
        
        status = "🟢 Активен" if is_active else "🔴 Завершён"
        text += f"🎁 {title}\n"
        text += f"   Приз: {prize}\n"
        text += f"   👥 Участников: {participants}\n"
        text += f"   {status}\n\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("analytics"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ОТЧЁТ: ОТЗЫВЫ
# ============================================

@router.callback_query(F.data == "analytics_reviews")
async def analytics_reviews(callback: CallbackQuery):
    """Отчёт по отзывам"""
    if not await check_admin(callback):
        return
    
    stats = await get_review_stats()
    
    text = (
        "📝 **Статистика отзывов**\n\n"
        f"✅ Опубликовано: {stats['approved']}\n"
        f"🔍 На модерации: {stats['pending']}\n"
        f"⭐ Средний рейтинг: {stats['avg_rating']}/5\n\n"
    )
    
    if stats['top_products']:
        text += "🏆 **Топ товаров по отзывам:**\n"
        for name, count, rating in stats['top_products'][:5]:
            text += f"• {name} | {count} отзывов | {rating}/5 ⭐\n"
    
    await callback.message.answer(
        text,
        reply_markup=back_keyboard("analytics"),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================
# ЭКСПОРТ ДАННЫХ
# ============================================

@router.callback_query(F.data == "analytics_export")
async def export_analytics(callback: CallbackQuery):
    """Экспорт данных в CSV"""
    if not await check_admin(callback):
        return
    
    import csv
    import io
    from datetime import datetime
    
    # Экспорт заказов
    orders = await get_all_orders(limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User_ID", "Amount", "Bonus_Used", "Status", "Payment_Status", "Address", "Created"])
    
    for order in orders:
        writer.writerow(order[:11])  # Первые 11 колонок
    
    output.seek(0)
    
    # Отправляем файл
    from aiogram.types import BufferedInputFile
    
    file = BufferedInputFile(
        output.getvalue().encode(),
        filename=f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    await callback.message.answer_document(
        file,
        caption="📊 **Экспорт заказов завершён!**\n\nФайл содержит все заказы."
    )
    
    await callback.answer("✅ Файл отправлен!")

# ============================================
# СМЕНА ПЕРИОДА
# ============================================

@router.callback_query(F.data.startswith("period_"))
async def change_period(callback: CallbackQuery):
    """Изменить период отчёта"""
    if not await check_admin(callback):
        return
    
    data = callback.data.split("_")
    report_type = data[1]
    period = data[2]
    
    period_names = {"1d": "1 день", "7d": "7 дней", "30d": "30 дней", "all": "Все время"}
    
    await callback.answer(f"🕐 Период изменён: {period_names.get(period, period)}", show_alert=True)
    
    # Перенаправляем на нужный отчёт
    if report_type == "sales":
        await analytics_sales(callback)
    elif report_type == "users":
        await analytics_users(callback)

# ============================================
# БЫСТРАЯ СТАТИСТИКА (КОМАНДА)
# ============================================

@router.message(F.text == "/stats")
async def quick_stats(message: Message):
    """Быстрая статистика для админов"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    stats = await get_dashboard_stats()
    sales = await get_sales_stats("1d")
    
    text = (
        "⚡ **Быстрая статистика (24ч)**\n\n"
        f"💰 Выручка: {sales['revenue']:,} ₽\n"
        f"📦 Заказы: {sales['orders']}\n"
        f"👥 Новые: {sales['new_users']}\n\n"
        f"📊 **Всего:**\n"
        f"• Пользователей: {stats['total_users']}\n"
        f"• Выручка: {stats['total_revenue']:,} ₽\n"
        f"• Товаров: {stats['total_products']}"
    )
    
    await message.answer(text, parse_mode="Markdown")

# ============================================
# НАЗАД
# ============================================

@router.callback_query(F.data == "back_analytics")
async def back_to_analytics(callback: CallbackQuery):
    """Вернуться в аналитику"""
    await analytics_main(callback)
    await callback.answer()
