from aiogram import Router, F, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from keyboards import main_menu
from database import add_user, track_event
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"📩 /start from user {message.from_user.id}")
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await add_user(user_id, username, first_name)
    
    try:
        await track_event(user_id, "user_started")
    except:
        pass
    
    is_admin = user_id in ADMIN_IDS
    
    await message.answer(
        f"🌸 **Привет, {first_name}!**\n\n"
        f"Добро пожаловать в магазин косметики!\n\n"
        f"Выберите раздел:",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await callback.message.answer(
        "📱 **Главное меню**",
        reply_markup=main_menu(is_admin)
    )
    await callback.answer()
