from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_products_by_category, get_product_by_id, add_to_cart
from keyboards import catalog_keyboard, product_keyboard, back_keyboard
from database import track_event

router = Router()

# ============================================
# КНОПКА КАТАЛОГ
# ============================================

@router.message(F.text == "🛒 Каталог")
async def show_catalog(message: Message):
    """Показать категории товаров"""
    await message.answer(
        "📚 **Выберите категорию:**\n\n"
        "У нас только сертифицированная продукция! ✨",
        reply_markup=catalog_keyboard()
    )

# ============================================
# ВЫБОР КАТЕГОРИИ
# ============================================

@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: CallbackQuery):
    """Показать товары выбранной категории"""
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
        await callback.answer(
            "📭 В этой категории пока нет товаров",
            show_alert=True
        )
        return
    
    # Показываем товары
    for product in products:
        product_id, name, desc, price, cat, photo_id, stock, is_active = product[:8]
        
        text = (
            f"💎 **{name}**\n\n"
            f"📝 {desc}\n\n"
            f"💰 **{price} ₽**\n"
            f"📦 В наличии: {stock} шт."
        )
        
        # Если есть фото, отправляем с фото
        if photo_id:
            try:
                await callback.message.answer_photo(
                    photo=photo_id,
                    caption=text,
                    reply_markup=product_keyboard(product_id)
                )
                continue
            except:
                pass
        
        # Если фото нет или ошибка, отправляем текст
        await callback.message.answer(
            text,
            reply_markup=product_keyboard(product_id)
        )
    
    # Кнопка назад
    await callback.message.answer(
        "🔙 Выберите товар выше или вернитесь назад:",
        reply_markup=back_keyboard("catalog")
    )
    
    await callback.answer()

# ============================================
# ПРОСМОТР ТОВАРА
# ============================================

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показать детали товара"""
    try:
        product_id = int(callback.data.split("_")[1])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    pid, name, desc, price, category, photo_id, stock, is_active = product[:8]
    
    # Трекаем просмотр товара (аналитика)
    await track_event(
        callback.from_user.id,
        "view_product",
        {"product_id": product_id, "name": name}
    )
    
    text = (
        f"💎 **{name}**\n\n"
        f"📝 {desc}\n\n"
        f"💰 **{price} ₽**\n"
        f"📦 В наличии: {stock} шт.\n\n"
        f"⚠️ Не является лекарственным средством"
    )
    
    if photo_id:
        try:
            await callback.message.answer_photo(
                photo=photo_id,
                caption=text,
                reply_markup=product_keyboard(product_id)
            )
            await callback.answer()
            return
        except:
            pass
    
    await callback.message.answer(
        text,
        reply_markup=product_keyboard(product_id)
    )
    await callback.answer()

# ============================================
# ДОБАВЛЕНИЕ В КОРЗИНУ
# ============================================

@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    """Добавить товар в корзину"""
    try:
        product_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Проверяем наличие
    if product[6] <= 0:  # stock
        await callback.answer("❌ Товар закончился!", show_alert=True)
        return
    
    # Добавляем в корзину
    await add_to_cart(callback.from_user.id, product_id, 1)
    
    # Трекаем событие (аналитика)
    await track_event(
        callback.from_user.id,
        "add_to_cart",
        {"product_id": product_id, "name": product[1]}
    )
    
    await callback.answer(
        f"✅ {product[1]} добавлен в корзину!",
        show_alert=True
    )

# ============================================
# НАЗАД В КАТАЛОГ
# ============================================

@router.callback_query(F.data == "back_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Вернуться к категориям"""
    await callback.message.edit_text(
        "📚 **Выберите категорию:**",
        reply_markup=catalog_keyboard()
    )
    await callback.answer()

# ============================================
# ОТЗЫВ О ТОВАРЕ (заглушка)
# ============================================

@router.callback_query(F.data.startswith("review_"))
async def product_review(callback: CallbackQuery):
    """Переход к отзыву о товаре"""
    await callback.answer(
        "📝 Чтобы оставить отзыв, перейдите в раздел «Отзывы»",
        show_alert=True
    )

