import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_IDS, ADMIN_GROUP_ID
from database import init_db, add_user, get_user, track_event
from keyboards import main_menu

# Импорт всех роутеров из обработчиков
from handlers import start, catalog, cart, order, bonuses, reviews, contest, admin, analytics

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# ============================================

dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(cart.router)
dp.include_router(order.router)
dp.include_router(bonuses.router)
dp.include_router(reviews.router)
dp.include_router(contest.router)
dp.include_router(admin.router)
dp.include_router(analytics.router)

# ============================================
# ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем пользователя в БД
    await add_user(user_id, username, first_name)
    
    # Трекаем событие
    try:
        await track_event(user_id, "user_started")
    except:
        pass
    
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

@dp.message(F.text == "🏠 Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await message.answer(
        "📱 **Главное меню**\n\nВыберите раздел:",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "back_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню (callback)"""
    await state.clear()
    
    user_id = callback.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    await callback.message.answer(
        "📱 **Главное меню**\n\nВыберите раздел:",
        reply_markup=main_menu(is_admin),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    
    await callback.message.answer(
        "❌ Действие отменено\n\n"
        "Выберите раздел в меню:",
        reply_markup=main_menu(callback.from_user.id in ADMIN_IDS)
    )
    await callback.answer()

# ============================================
# ОБРАБОТКА ОШИБОК
# ============================================

@dp.errors()
async def errors_handler(update, exception):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {exception}")
    return True

# ============================================
# ФОНОВЫЕ ЗАДАЧИ
# ============================================

async def check_ended_contests():
    """Проверка завершённых конкурсов"""
    from database import get_active_contests, pick_winner
    
    while True:
        try:
            contests = await get_active_contests()
            from datetime import datetime
            
            for contest in contests:
                contest_id = contest[0]
                end_date = contest[5]
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace(' ', 'T'))
                    if end_dt < datetime.now():
                        winner = await pick_winner(contest_id)
                        if winner:
                            user_id, username, first_name, _ = winner
                            try:
                                await bot.send_message(
                                    user_id,
                                    f"🎉 **ВЫ ПОБЕДИЛИ!**\n\n🏆 {contest[1]}\n🎁 Приз: {contest[3]}",
                                    parse_mode="Markdown"
                                )
                            except:
                                pass
                        logger.info(f"Конкурс {contest_id} завершён")
            
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Ошибка в check_ended_contests: {e}")
            await asyncio.sleep(3600)

async def check_maintenance_mode():
    """Проверка режима обслуживания"""
    from database import get_bot_setting
    
    while True:
        try:
            is_maintenance = await get_bot_setting('is_maintenance')
            logger.info(f"Режим обслуживания: {is_maintenance}")
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Ошибка в check_maintenance_mode: {e}")
            await asyncio.sleep(300)

# ============================================
# ЗАПУСК БОТА
# ============================================

async def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск бота...")
    
    try:
        # Инициализация базы данных
        await init_db()
        logger.info("✅ База данных инициализирована")
        
        # Создаём тестовые товары если база пустая
        from database import get_all_products, add_product, create_promo_code, check_promo_code
        
        products = await get_all_products(limit=1)
        if not products:
            logger.info("📦 Создаём тестовые товары...")
            
            await add_product(
                name="Витамин C 1000мг",
                description="Аскорбиновая кислота для иммунитета. 60 таблеток.",
                price=500,
                category="bads",
                photo_id=None,
                stock=50
            )
            
            await add_product(
                name="Крем увлажняющий",
                description="Гиалуроновая кислота, алоэ вера. Для всех типов кожи.",
                price=1200,
                category="cosmetics",
                photo_id=None,
                stock=30
            )
            
            await add_product(
                name="Набор 'Сияние'",
                description="Крем + сыворотка + маска. Подарочная упаковка.",
                price=3500,
                category="sets",
                photo_id=None,
                stock=10
            )
            
            logger.info("✅ Тестовые товары созданы")
        
        # Создаём тестовый промокод
        promo = await check_promo_code("WELCOME10")
        if not promo:
            await create_promo_code(
                code="WELCOME10",
                discount_percent=10,
                min_order=0,
                max_uses=None,
                expires_at=None
            )
            logger.info("✅ Промокод WELCOME10 создан")
        
        # Запускаем фоновые задачи
        logger.info("🔄 Запуск фоновых задач...")
        asyncio.create_task(check_ended_contests())
        asyncio.create_task(check_maintenance_mode())
        
        # Запускаем поллинг
        logger.info("🤖 Бот запущен и готов к работе!")
        logger.info(f"👨‍ Админы: {ADMIN_IDS}")
        logger.info(f"📢 Группа: {ADMIN_GROUP_ID}")
        
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("👋 Сессия бота закрыта")

# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
