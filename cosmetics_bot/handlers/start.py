from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS
from database import add_user, get_user
from keyboards import main_menu

router = Router()

# ============================================
# КОМАНДА /START
# ============================================

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем пользователя в БД
    await add_user(user_id, username, first_name)
    
    # Проверяем, админ ли это
    is_admin = user_id in ADMIN_IDS
    
    # Приветственное сообщение
    await message.answer(
        f"🌸 **Привет, {first_name}!**\n\n"
        f"Добро пожаловать в магазин натуральной косметики и БАДов!\n\n"
        f"✨ Только сертифицированная продукция\n"
        f"🎁 Бонусы с каждой покупки\n"
        f"🏆 Регулярные розыгрыши\n\n"
        f"Выберите раздел в меню:",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )

# ============================================
# КНОПКА ГЛАВНОГО МЕНЮ
# ============================================

@router.message(F.text == "🏠 Главное меню")
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await message.answer(
        "📱 **Главное меню**\n\nВыберите раздел:",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )

# ============================================
# КНОПКА МЕНЕДЖЕР
# ============================================

@router.message(F.text == "👩‍⚕️ Менеджер")
async def contact_manager(message: Message):
    """Связь с менеджером"""
    await message.answer(
        "👩‍⚕️ **Наш специалист скоро ответит вам!**\n\n"
        "Напишите ваш вопрос ниже, и мы перешлём его менеджеру 👇",
        parse_mode="Markdown"
    )
    # Здесь можно добавить пересылку сообщения админу

# ============================================
# КНОПКА АКЦИИ
# ============================================

@router.message(F.text == "🔥 Акции")
async def show_promotions(message: Message):
    """Показать акции"""
    await message.answer(
        "🔥 **Текущие акции:**\n\n"
        "1️⃣ **Скидка 10%** на первый заказ\n"
        "   Промокод: `WELCOME10`\n\n"
        "2️⃣ **Бесплатная доставка** от 5000₽\n\n"
        "3️⃣ **Наборы со скидкой 20%**\n"
        "   В разделе «Наборы»\n\n"
        "🎁 Следите за обновлениями!",
        parse_mode="Markdown"
    )
