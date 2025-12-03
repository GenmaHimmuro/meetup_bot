from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from tg_bot.handlers.organizer.organizer_states import EventManagementStates
from tg_bot.utils.db_funcs import db
from tg_bot.utils.decorators import check_role
from tg_bot.keyboards.inline_keyboards import get_event_manage_keyboard


organizer_router = Router()


@organizer_router.message(F.text == "📋 Управление событиями")
@check_role("organizer")
async def manage_current_event(message: Message):
    event = await db.get_happening_now_event()
    
    if not event:
        await message.answer(
            "Нет активного мероприятия\n"
        )
        return

    schedule = await db.get_event_schedule(event.id)
    speakers = await db.get_speakers_for_event(event.id)

    text = (
        f"УПРАВЛЕНИЕ МЕРОПРИЯТИЕМ\n\n"
        f"{event.title}\n"
        f"{event.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"{event.location}\n"
        f"Докладчиков: {len(speakers)}\n"
        f"Докладов: {len(schedule)}\n\n"
        f"Выберите действие:"
    )

    reply_markup = await get_event_manage_keyboard(event.id)
    await message.answer(text, reply_markup=reply_markup)


@organizer_router.callback_query(F.data.startswith("change_time_"))
@check_role("organizer")
async def change_time_start(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[2])

    schedule = await db.get_event_schedule(event_id)
    if not schedule:
        await callback.answer("Расписание пусто", show_alert=True)
        return

    text = "ИЗМЕНЕНИЕ ВРЕМЕНИ ВЫСТУПЛЕНИЯ\n\n"
    text += "Текущее расписание:\n\n"

    for idx, talk in enumerate(schedule, 1):
        text += (
            f"{idx}.{talk.title}\n"
            f"{talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
            f"{talk.speaker.first_and_last_name}\n\n"
        )

    text += (
        "Отправьте номер доклада из списка выше,\n"
        "которого вы хотите изменить:"
    )

    await state.update_data(event_id=event_id, schedule=schedule)
    await callback.message.answer(text)
    await state.set_state(EventManagementStates.waiting_for_talk_selection)
    await callback.answer()


@organizer_router.message(EventManagementStates.waiting_for_talk_selection)
async def process_talk_selection(message: Message, state: FSMContext):
    try:
        talk_num = int(message.text.strip())
        
        data = await state.get_data()
        schedule = data["schedule"]

        if talk_num < 1 or talk_num > len(schedule):
            await message.answer(f"Введите номер от 1 до {len(schedule)}")
            return

        selected_talk = schedule[talk_num - 1]
        
        await state.update_data(selected_talk_id=selected_talk.id)
        
        await message.answer(
            f"Вы выбрали доклад:\n\n"
            f"{selected_talk.title}\n"
            f"{selected_talk.speaker.first_and_last_name}\n\n"
            f"Текущее время:\n"
            f"{selected_talk.start_time.strftime('%H:%M')} - {selected_talk.end_time.strftime('%H:%M')}\n\n"
            f"Отправьте новое время в формате:\n"
            f"ЧЧ:ММ - ЧЧ:ММ\n\n"
            f"Например: 14:00 - 14:45"
        )
        await state.set_state(EventManagementStates.waiting_for_new_time)

    except ValueError:
        await message.answer("Введите корректный номер доклада")


@organizer_router.message(EventManagementStates.waiting_for_new_time)
async def process_new_time(message: Message, state: FSMContext):
    event = await db.get_happening_now_event()
    time_parts = message.text.strip().split(" - ")
    if len(time_parts) != 2:
        await message.answer("Неверный формат. Используйте: ЧЧ:ММ - ЧЧ:ММ")
        return

    start_time_str = time_parts[0].strip()
    end_time_str = time_parts[1].strip()

    data = await state.get_data()
    talk_id = data["selected_talk_id"]
    
    success = await db.update_schedule_time(
        talk_id, 
        start_time_str, 
        end_time_str
    )
    reply_markup = await get_event_manage_keyboard(event.id)
    if success:
        await message.answer(
            f"✅ ВРЕМЯ ОБНОВЛЕНО\n\n"
            f"Новое время: {start_time_str} - {end_time_str}\n\n",
            reply_markup=reply_markup
        )
    else:
        await message.answer("Ошибка при обновлении времени")
    await state.clear()


@organizer_router.callback_query(F.data.startswith("broadcast_"))
@check_role("organizer")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])
    
    await state.update_data(event_id=event_id)
    await callback.message.answer(
        "РАССЫЛКА УЧАСТНИКАМ\n\n"
        "Напишите текст рассылки,\n"
        "который получат все участники события:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(EventManagementStates.waiting_for_broadcast_message)
    await callback.answer()


@organizer_router.message(EventManagementStates.waiting_for_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data["event_id"]

    event = await db.get_event_by_id(event_id)
    if not event:
        await message.answer("Мероприятие не найдено")
        await state.clear()
        return

    broadcast_text = message.text

    users_on_event = await db.get_guests_and_speakers_telegram_ids()
    for user in users_on_event:
        await message.bot.send_message(
            chat_id=user,
            text=f"РАССЫЛКА ОТ ОРГАНИЗАТОРА\n\n"
                    f"Мероприятие: {event.title}\n\n"
                    f"{broadcast_text}"
        )
    result_text = f"РАССЫЛКА ЗАВЕРШЕНА\n\n"
    await message.answer(result_text)
    await state.clear()