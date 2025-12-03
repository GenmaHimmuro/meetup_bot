from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from tg_bot.utils.db_funcs import db
from tg_bot.utils.decorators import check_role
from tg_bot.handlers.guests.guest_states import SpeakerRequestStates
from tg_bot.keyboards.reply_keyboards import get_guest_menu


guest_router_to_speaker = Router()

@guest_router_to_speaker.message(F.text == "🎤 Хочу быть докладчиком")
@check_role('guest')
async def request_speaker_role(message: Message, state: FSMContext):
    await message.answer("Тема вашего доклада:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SpeakerRequestStates.waiting_for_topic)


@guest_router_to_speaker.message(SpeakerRequestStates.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.answer("Краткое описание доклада:")
    await state.set_state(SpeakerRequestStates.waiting_for_description)


@guest_router_to_speaker.message(SpeakerRequestStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    organizers = await db.get_organizers_telegram_ids()
    for organizer in organizers:
        await message.bot.send_message(chat_id=organizer,
                text=f"Заявка {data}\n"
            )
    await message.answer(
        "Ваша заявка отправлена!\n\n"
        f"Тема: {data['topic']}\n"
        f"Описание: {message.text}\n\n"
        "Организатор свяжется с вами вскоре.",
        reply_markup=get_guest_menu()
    )
    await state.clear()
