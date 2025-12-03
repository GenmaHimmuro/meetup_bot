from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter


from tg_bot.utils.db_funcs import db
from tg_bot.keyboards.inline_keyboards import get_networking_match_keyboard
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
        "🤝 Нетворкинг\n\nДля участия введите своё имя:",
        reply_markup=get_back_kb()
    )
    await state.set_state(NetworkingStates.waiting_for_name)


@guest_router_netwrkg.message(NetworkingStates.waiting_for_name, F.text == "◀ Назад")
async def back_from_name(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заполнение анкеты отменено.", reply_markup=get_guest_menu())


@guest_router_netwrkg.message(NetworkingStates.waiting_for_name, F.text)
async def get_name_for_networking(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "Расскажите о себе (стек, опыт, интересы).\nМаксимум 200 символов:",
        reply_markup=get_back_kb()
    )
    await state.set_state(NetworkingStates.waiting_for_about)


@guest_router_netwrkg.message(NetworkingStates.waiting_for_about, F.text == "◀ Назад")
async def back_from_about(message: Message, state: FSMContext):
    await message.answer("Введите своё имя заново:", reply_markup=get_back_kb())
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
    
    await message.answer("Анкета сохранена! Ищем контакты для знакомства...")
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    next_profile = await db.get_next_profile_for_matching(user.id, event.id)
    
    if not next_profile:
        await message.answer(
            "Больше нет доступных контактов.",
            reply_markup=get_guest_menu()
        )
        await state.clear()
        return
    
    await state.update_data(
        current_profile_id=next_profile.id,
        current_user_id=next_profile.user_id,
        current_profile_name=next_profile.name,
        current_profile_about=next_profile.about,
        event_id=event.id
    )
    
    await show_profile_from_message(message, next_profile)


async def show_profile(message: Message, profile):
    profile_text = f"""
{profile.name}

О себе:
{profile.about}

─────────────

Что вы хотите?
    """
    try:
        await message.edit_text(
            profile_text,
            reply_markup=await get_networking_match_keyboard(profile.id),
            parse_mode="HTML"
        )
    except Exception as e:
        if "not modified" not in str(e):
            raise


@guest_router_netwrkg.callback_query(F.data.startswith("match_accept:"))
async def accept_contact(callback, state: FSMContext):
    data = await state.get_data()
    
    if not data or 'current_user_id' not in data:
        await callback.answer("Сессия истекла. Начните заново.")
        return
    
    target_user_id = data['current_user_id']
    target_user = await db.get_user_by_id(target_user_id)
    
    await db.save_match_history(
        event_id=data['event_id'],
        initiator_id=callback.from_user.id,
        target_id=target_user_id,
        accepted=True,
        skipped=False
    )
    
    contact_info = f"""
Контакт добавлен!

Имя: {target_user.first_and_last_name or 'Не указано'}
Telegram ID: {target_user.telegram_id}
Юзернейм: @{target_user.telegram_username or 'Не указан'}

О себе:
{target_user.about or 'Не указано'}
    """
    
    await callback.message.edit_text(
        contact_info,
        reply_markup=await get_networking_match_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Контакт добавлен!")


@guest_router_netwrkg.callback_query(F.data.startswith("match_skip:"))
async def skip_contact(callback, state: FSMContext):
    data = await state.get_data()
    
    if not data or 'current_user_id' not in data:
        await callback.answer("Сессия истекла.")
        return
    
    target_user_id = data['current_user_id']
    
    await db.save_match_history(
        event_id=data['event_id'],
        initiator_id=callback.from_user.id,
        target_id=target_user_id,
        accepted=False,
        skipped=True
    )
    
    await callback.answer("Пропущено!")
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    next_profile = await db.get_next_profile_for_matching(user.id, data['event_id'])
    
    if next_profile:
        await state.update_data(
            current_profile_id=next_profile.id,
            current_user_id=next_profile.user_id,
            current_profile_name=next_profile.name,
            current_profile_about=next_profile.about
        )
        await show_profile(callback.message, next_profile)
    else:
        await callback.message.edit_text(
            "Больше нет контактов. Попробуйте позже!",
            reply_markup=await get_networking_match_keyboard(),
            parse_mode="HTML"
        )


@guest_router_netwrkg.callback_query(F.data == "show_next_profile")
async def show_next_profile_handler(callback, state: FSMContext):
    data = await state.get_data()
    
    if not data or 'event_id' not in data:
        await callback.answer("Сессия истекла.")
        return
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    next_profile = await db.get_next_profile_for_matching(user.id, data['event_id'])
    
    if next_profile:
        await state.update_data(
            current_profile_id=next_profile.id,
            current_user_id=next_profile.user_id,
            current_profile_name=next_profile.name,
            current_profile_about=next_profile.about
        )
        await show_profile(callback.message, next_profile)
        await callback.answer()
    else:
        await callback.message.edit_text(
            "Больше нет контактов. Попробуйте позже!",
            reply_markup=await get_networking_match_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()


@guest_router_netwrkg.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>",
            reply_markup=get_guest_menu(),
            parse_mode="HTML"
        )
    except:
        pass
    await callback.answer()


async def show_profile_from_message(message: Message, profile):
    """✅ Показать первый профиль из сообщения"""
    profile_text = f"""
👤 <b>{profile.name}</b>

📝 <b>О себе:</b>
{profile.about}

─────────────

Что вы хотите?
    """
    
    await message.answer(
        profile_text,
        reply_markup=await get_networking_match_keyboard(profile.id),
        parse_mode="HTML"
    )
