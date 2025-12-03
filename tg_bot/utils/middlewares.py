from aiogram import BaseMiddleware

from tg_bot.utils.db_funcs import db


class UserCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        message = None
        user_id = None
        username = None

        if event.message:
            message = event.message
            user_id = message.from_user.id
            username = message.from_user.username
        elif event.callback_query:
            message = event.callback_query.message
            user_id = event.callback_query.from_user.id
            username = event.callback_query.from_user.username

        if user_id:
            user = await db.get_or_create_user(user_id, username)
            data['user'] = user

        return await handler(event, data)