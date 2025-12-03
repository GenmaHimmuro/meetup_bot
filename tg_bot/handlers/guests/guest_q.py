from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from tg_bot.utils.db_funcs import db
from tg_bot.keyboards.inline_keyboards import get_speaker_choice_keyboard
from tg_bot.utils.decorators import check_role
from tg_bot.handlers.guests.guest_states import QuestionStates
from tg_bot.keyboards.reply_keyboards import get_guest_menu


guest_router_q = Router()

@guest_router_q.message(F.text == "💬 Задать вопрос")
@check_role('guest')
async def ask_question_select_speaker(message: Message):
    event = await db.get_happening_now_event()
    
    if not event:
        await message.answer("Нет активного мероприятия...")
        return
    
    speaker = await db.get_current_speaker(event.id)
    reply_markup = await get_speaker_choice_keyboard(speaker)
    await message.answer("Выберите докладчика...", reply_markup=reply_markup)


@guest_router_q.callback_query(F.data.startswith("speaker_question:"))
@check_role('guest')
async def process_speaker_selection(callback: CallbackQuery, state: FSMContext):
    event = await db.get_happening_now_event()
    current_speaker = await db.get_current_speaker(event.id)
    await state.update_data(speaker_id=current_speaker.id, event_id=event.id)
    
    await callback.message.answer("Напишите ваш вопрос (максимум 500 символов):")
    await state.set_state(QuestionStates.waiting_for_question_text)
    await callback.answer()


@guest_router_q.message(QuestionStates.waiting_for_question_text)
async def process_question_text(message: Message, state: FSMContext):
    data = await state.get_data()
    event = await db.get_happening_now_event()
    speaker = await db.get_current_speaker(event.id)
    question = await db.save_question(
        event.id,
        message.from_user.id,
        speaker.telegram_id,
        message.text
    )
    
    if question:
        await message.answer(
            "Ваш вопрос отправлен докладчику!",
            reply_markup=get_guest_menu()
        )
    else:
        await message.answer("Ошибка при отправке вопроса",get_guest_menu())
    await state.clear()