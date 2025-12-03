from functools import wraps
from aiogram.types import Message, CallbackQuery

from tg_bot.utils.db_funcs import db


def check_role(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(message_or_callback, *args, **kwargs):
            if isinstance(message_or_callback, Message):
                user_id = message_or_callback.from_user.id
                is_callback = False
            elif isinstance(message_or_callback, CallbackQuery):
                user_id = message_or_callback.from_user.id
                is_callback = True
            else:
                return
            
            user = await db.get_user_by_telegram_id(user_id)
            
            if not user:
                if not is_callback:
                    await message_or_callback.answer(
                        "Пожалуйста, сначала зарегистрируйтесь командой /start"
                    )
                return
            
            if user.role not in allowed_roles:
                role_names = {
                    'guest': 'Гост',
                    'speaker': 'Докладчик',
                    'organizer': 'Организатор'
                }
                
                current_role = role_names.get(user.role, user.role)
                required_roles = ', '.join([role_names.get(r, r) for r in allowed_roles])
                
                message = (
                    f"Доступ запрещён!\n\n"
                    f"Ваша роль: {current_role}\n"
                    f"Требуемая роль: {required_roles}\n\n"
                    "Используйте /start для обновления меню"
                )
                
                if not is_callback:
                    await message_or_callback.answer(message)
                else:
                    await message_or_callback.answer(message, show_alert=True)
                
                return
            
            return await func(message_or_callback, *args, **kwargs)
        
        return wrapper
    return decorator


def check_user_exists(func):
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        if isinstance(message_or_callback, Message):
            user_id = message_or_callback.from_user.id
            is_callback = False
        elif isinstance(message_or_callback, CallbackQuery):
            user_id = message_or_callback.from_user.id
            is_callback = True
        else:
            return
        
        user = await db.get_user_by_telegram_id(user_id)
        
        if not user:
            message = "Пожалуйста, сначала зарегистрируйтесь командой /start"
            
            if not is_callback:
                await message_or_callback.answer(message)
            else:
                await message_or_callback.answer(message, show_alert=True)
            
            return
        
        return await func(message_or_callback, *args, **kwargs)
    
    return wrapper
