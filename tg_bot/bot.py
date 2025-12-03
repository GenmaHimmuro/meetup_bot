import os
import django
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetup_bot.settings')
django.setup()

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from environs import Env

from tg_bot.handlers.base import router as base_router
from tg_bot.handlers.organizer.organizer import organizer_router
from tg_bot.handlers.guests.guest_event import guest_router_event
from tg_bot.handlers.guests.guest_netwrkg import guest_router_netwrkg
from tg_bot.handlers.guests.guest_q import guest_router_q
from tg_bot.handlers.guests.guest_to_speaker import guest_router_to_speaker
from tg_bot.handlers.speaker.speaker import speaker_router


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="about", description="Информация о боте"),
    ]
    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault()
    )


async def main():
    env = Env()
    env.read_env()
    TOKEN = env.str('TG_BOT_TOKEN')
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_routers(
        guest_router_event,
        guest_router_netwrkg,
        guest_router_q,
        guest_router_to_speaker,
        base_router,
        speaker_router,
        organizer_router
    )
    await set_commands(bot)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")