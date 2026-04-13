from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_all_products, get_products_by_category, add_to_cart
from keyboards import back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "🛒 Каталог")
@router.callback_query(F.data == "catalog")
async def show_catalog(message: Message | CallbackQuery):
    logger.info("📦 Catalog opened")
    
    products = await get_all_products(limit=20)
    
    if not products:
        text = "📭 Товаров пока нет"
    else:
        text = "🛒 **Каталог товаров:**\n\n"
        for p in products[:10]:
            pid, name, desc, price, cat, photo, stock = p[:7]
            text += f"• {name} — {price} ₽ (остаток: {stock})\n"
    
    kb = back_keyboard("main") if isinstance(message, CallbackQuery) else None
    
    if isinstance(message, CallbackQuery):
        await message.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        await message.answer()
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[3])
    
    await add_to_cart(user_id, product_id, 1)
    
    await callback.answer("✅ Добавлено в корзину!", show_alert=True)
