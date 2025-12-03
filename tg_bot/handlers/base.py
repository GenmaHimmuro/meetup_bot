from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from tg_bot.utils.db_funcs import db
from tg_bot.keyboards.reply_keyboards import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = await db.get_or_create_user(
        message.from_user.id,
        message.from_user.username
    )
    
    role_display = dict(user.ROLE_CHOICES).get(user.role, user.role)
    
    await message.answer(
        f"👋 Добро пожаловать!\n\n"
        f"Ваша роль: {role_display}\n\n",
        reply_markup=await get_main_menu(user.role)
    )
    
    await state.clear()


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
Доступные команды:
/start - Главное меню
/help - Эта справка
/about - О боте
"""
    await message.answer(help_text)


@router.message(Command("about"))
async def cmd_about(message: Message):
    about_text = """
MeetUpBOT

Взаимодействие между участниками:
• Гости записываются и знакомятся между собой
• Докладчики получают вопросы
• Организаторы управляют событиями

"""
    await message.answer(about_text)