from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.database import db

class AccessMiddleware(BaseMiddleware):
    """Middleware для проверки доступа"""
    
    def __init__(self, admin_id=None):
        self.admin_id = admin_id
    
    async def __call__(self, handler, event, data):
        # Получаем ID пользователя
        user_id = event.from_user.id
        
        # Если администратор не установлен, устанавливаем первого пользователя
        if not self.admin_id:
            self.admin_id = user_id
            db.set_admin_id(user_id)
            print(f"Установлен администратор: {user_id}")
            return await handler(event, data)
        
        # Проверяем доступ
        if user_id != self.admin_id:
            if isinstance(event, Message):
                await event.answer(
                    "Доступ запрещен. Ваш ID: " + str(user_id)
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("Доступ запрещен", show_alert=True)
            return
        
        # Логируем событие
        print(f"Доступ: {user_id} - {type(event).__name__}")
        
        return await handler(event, data)
