from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from tg_bot.utils.db_funcs import db
from tg_bot.keyboards.reply_keyboards import get_back_kb, get_guest_menu
from tg_bot.utils.decorators import check_role
from tg_bot.handlers.guests.guest_states import NetworkingStates


guest_router_netwrkg = Router()

@guest_router_netwrkg.message(StateFilter(None), F.text == "🤝 Нетворкинг")
@check_role('guest')
async def networking_menu(message: Message, state: FSMContext):
    event = await db.get_happening_now_event()
    
    if not event:
        await message.answer("Нетворкинг доступен только во время мероприятия")
        return
    
    await message.answer(
        "Нетворкинг\n\n"
        "Для участия в нетворкинге введите свое имя:",
        reply_markup=get_back_kb()
    )
    await state.set_state(NetworkingStates.waiting_for_name)


@guest_router_netwrkg.message(NetworkingStates.waiting_for_name, F.text == "◀ Назад")
async def back_from_name(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Заполнение анкеты отменено.",
        reply_markup=get_guest_menu()
    )

@guest_router_netwrkg.message(NetworkingStates.waiting_for_name, F.text)
async def get_name_for_networking(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "Расскажите о себе (стек, опыт, интересы). Максимум 200 символов:",
        reply_markup=get_back_kb()
    )
    await state.set_state(NetworkingStates.waiting_for_about)


@guest_router_netwrkg.message(NetworkingStates.waiting_for_about, F.text == "◀ Назад")
async def back_from_about(message: Message, state: FSMContext):
    await message.answer(
        "Хорошо, вернёмся к имени. Введите своё имя заново:",
        reply_markup=get_back_kb()
    )
    await state.set_state(NetworkingStates.waiting_for_name)


@guest_router_netwrkg.message(NetworkingStates.waiting_for_about, F.text)
async def get_about_for_networking(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(about=text)
    user_profile_data = await state.get_data()

    event = await db.get_happening_now_event()
    await db.save_networking_profile(
        telegram_id=message.from_user.id,
        event_id=event.id,
        name=user_profile_data['name'],
        about=user_profile_data['about']
    )
    await state.clear()
    await message.answer(
        "Анкета для нетворкинга успешно сохранена! Если хотите обновить анкету, нажмите '🤝 Нетворкинг'",
        reply_markup=get_guest_menu()
    )
