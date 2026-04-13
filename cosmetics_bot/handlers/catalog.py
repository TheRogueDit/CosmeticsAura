from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_all_products, get_products_by_category, get_product_by_id, add_to_cart
from keyboards import catalog_keyboard, product_keyboard, back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

# =============================================================================
# МАППИНГ КАТЕГОРИЙ (callback_data → название для отображения → название в БД)
# =============================================================================
CATEGORIES = {
    "cat_cosmetics": {"name": "💄 Косметика", "db_name": "cosmetics"},
    "cat_bads": {"name": "💊 БАДы", "db_name": "bads"},
    "cat_body": {"name": "🧴 Уход за телом", "db_name": "body"},
    "cat_sets": {"name": "🎁 Наборы", "db_name": "sets"},
}

# =============================================================================
# ТЕКСТОВАЯ КНОПКА "🛒 Каталог"
# =============================================================================
@router.message(F.text == "🛒 Каталог")
async def catalog_from_main_menu(message: Message):
    """Показать категории при нажатии на текстовую кнопку"""
    logger.info(f"📦 Catalog from main menu: user {message.from_user.id}")
    text = "📚 **Категории товаров:**\n\nВыберите раздел:"
    await message.answer(text, reply_markup=catalog_keyboard(), parse_mode="Markdown")

# =============================================================================
# CALLBACK КНОПКА "Каталог"
# =============================================================================
@router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery):
    """Показать категории по callback"""
    logger.info(f"📦 Catalog callback: user {callback.from_user.id}")
    text = "📚 **Категории товаров:**\n\nВыберите раздел:"
    await callback.message.answer(text, reply_markup=catalog_keyboard(), parse_mode="Markdown")
    await callback.answer()

# =============================================================================
# ОБРАБОТКА ВЫБОРА КАТЕГОРИИ
# =============================================================================
@router.callback_query(F.data.startswith("cat_"))
async def show_category_products(callback: CallbackQuery):
    """Показать товары выбранной категории"""
    cat_key = callback.data  # например, "cat_cosmetics"
    
    if cat_key not in CATEGORIES:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    category = CATEGORIES[cat_key]
    category_name = category["name"]        # "💄 Косметика"
    db_category = category["db_name"]       # "cosmetics"
    
    logger.info(f"📦 Show category {category_name} (db: {db_category})")
    
    # Получаем товары ТОЛЬКО этой категории
    products = await get_products_by_category(db_category)
    
    if not products:
        await callback.answer(f"📭 В категории {category_name} пока нет товаров", show_alert=True)
        return
    
    # Формируем текст с товарами
    text = f"{category_name}\n\n"
    for p in products:
        # p: (id, name, description, price, category, photo_id, stock, ...)
        pid = p[0]
        name = p[1]
        price = p[3]
        stock = p[6] if len(p) > 6 else 0
        
        stock_status = "✅" if stock > 10 else "⚠️" if stock > 0 else "❌"
        text += f"{stock_status} {name} — {price} ₽ (остаток: {stock})\n"
    
    # Кнопка "Назад"
    kb = back_keyboard("catalog")
    
    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
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
        
        # Получаем название товара
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
    text = "📚 **Категории товаров:**\n\nВыберите раздел:"
    await callback.message.answer(text, reply_markup=catalog_keyboard(), parse_mode="Markdown")
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
