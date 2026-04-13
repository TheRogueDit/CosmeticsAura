from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_cart, clear_cart, remove_from_cart
from keyboards import back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "🛒 Корзина")
@router.callback_query(F.data == "cart")
async def show_cart(message: Message | CallbackQuery):
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.from_user.id
    cart = await get_cart(user_id)
    
    if not cart:
        text = "🛒 **Корзина пуста**"
    else:
        total = sum(item[3] * item[1] for item in cart)
        text = "🛒 **Ваша корзина:**\n\n"
        for item in cart:
            text += f"• {item[2]} x{item[1]} — {item[3]*item[1]} ₽\n"
        text += f"\n💰 **Итого: {total} ₽**"
    
    kb = back_keyboard("main")
    
    if isinstance(message, CallbackQuery):
        await message.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        await message.answer()
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    await callback.answer("🔄 Переход к оформлению...")
