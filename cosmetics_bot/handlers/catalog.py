from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_all_products, get_products_by_category, get_product_by_id, add_to_cart
from keyboards import catalog_keyboard, product_keyboard, back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

# =============================================================================
# КНОПКА "КАТАЛОГ" (текстовая из главного меню)
# =============================================================================
@router.message(F.text == "🛒 Каталог")
async def catalog_text(message: Message):
    logger.info(f"📦 Catalog opened by user {message.from_user.id}")
    await show_categories(message)

# =============================================================================
# КНОПКА "КАТАЛОГ" (callback из инлайн)
# =============================================================================
@router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery):
    logger.info(f"📦 Catalog callback by user {callback.from_user.id}")
    await show_categories(callback)
    await callback.answer()

# =============================================================================
# ПОКАЗАТЬ КАТЕГОРИИ
# =============================================================================
async def show_categories(target: Message | CallbackQuery):
    """Показать категории товаров"""
    text = "📚 **Категории товаров:**\n\nВыберите раздел:"
    
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=catalog_keyboard(), parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=catalog_keyboard(), parse_mode="Markdown")

# =============================================================================
# ОБРАБОТКА КАТЕГОРИЙ
# =============================================================================
@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    """Показать товары категории"""
    category_map = {
        "cat_cosmetics": "cosmetics",
        "cat_bads": "bads", 
        "cat_body": "body",
        "cat_sets": "sets"
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    products = await get_products_by_category(category)
    
    if not products:
        await callback.answer("📭 В этой категории пока нет товаров", show_alert=True)
        return
    
    text = f"📦 **{category.replace('_', ' ').title()}**\n\n"
    for p in products[:10]:  # Показываем первые 10
        pid, name, desc, price, cat, photo, stock = p[:7]
        text += f"• {name} — {price} ₽ (остаток: {stock})\n"
    
    await callback.message.answer(text, reply_markup=back_keyboard("catalog"), parse_mode="Markdown")
    await callback.answer()

# =============================================================================
# ДОБАВИТЬ В КОРЗИНУ
# =============================================================================
@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    """Добавить товар в корзину"""
    try:
        product_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        await add_to_cart(user_id, product_id, 1)
        
        # Получаем название товара для сообщения
        product = await get_product_by_id(product_id)
        name = product[1] if product else "Товар"
        
        await callback.answer(f"✅ {name} добавлен в корзину!", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Add to cart error: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)

# =============================================================================
# НАЗАД
# =============================================================================
@router.callback_query(F.data == "back_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Вернуться к категориям"""
    await show_categories(callback)
    await callback.answer()

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    from keyboards import main_menu
    from config import ADMIN_IDS
    
    user_id = callback.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await callback.message.answer(
        "📱 **Главное меню**",
        reply_markup=main_menu(is_admin)
    )
    await callback.answer()
