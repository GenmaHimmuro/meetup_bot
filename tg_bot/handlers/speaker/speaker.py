from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from tg_bot.utils.db_funcs import db
from tg_bot.utils.decorators import check_role
from tg_bot.handlers.speaker.speaker_states import AnswerStates
from tg_bot.keyboards.inline_keyboards import get_questions_keyboard, get_answer_keyboard
from tg_bot.keyboards.reply_keyboards import get_speaker_menu


speaker_router = Router()


@speaker_router.message(F.text == "❓ Вопросы")
@check_role('speaker')
async def show_questions(message: Message):
    event = await db.get_happening_now_event()
    
    if not event:
        await message.answer("Нет активного мероприятия")
        return
    
    questions = await db.get_speaker_questions(message.from_user.id, event.id)

    text = f"Вопросы ({len(questions)} шт.):\n\n"
    for idx, q in enumerate(questions, 1):
        sender = q.sender.first_and_last_name if q.sender else "Аноним"
        status = "✅" if q.is_answered else "⏳"
        text += f"{idx}. {status} От {sender}: {q.text}...\n"
    
    reply_markup = await get_questions_keyboard(questions)
    await message.answer(text, reply_markup=reply_markup)


@speaker_router.callback_query(F.data.startswith("question_"))
@check_role('speaker')
async def view_question(callback: CallbackQuery, state: FSMContext):
    question_id = int(callback.data.split("_")[1])
    question = await db.get_question_by_id(question_id)
    await db.mark_question_read(question_id)
    
    text = f"Вопрос от {question.sender.first_and_last_name}\n"
    text += f"{question.text}\n"
    text += f"Ответ: {question.answer}"
    
    await state.update_data(question_id=question_id)
    
    reply_markup = await get_answer_keyboard(question_id)
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@speaker_router.callback_query(F.data.startswith("answer_question_"))
@check_role('speaker')
async def answer_question(callback: CallbackQuery, state: FSMContext):
    question_id = int(callback.data.split("_")[2])
    
    await state.update_data(question_id=question_id)
    await callback.message.answer("Введите ваш ответ:")
    await state.set_state(AnswerStates.waiting_for_answer)
    await callback.answer()


@speaker_router.message(AnswerStates.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    question_id = data['question_id']
    
    question = await db.save_answer(question_id, message.text)
    
    if question:
        await message.answer(
            "Ваш ответ отправлен!\n"
            f"Вопрос: {question.text}\n"
            f"Ваш ответ: {message.text}", reply_markup=get_speaker_menu()
        )
    else:
        await message.answer("Ошибка при сохранении ответа")
    await state.clear()


@speaker_router.message(F.text == "📅 График")
@check_role('speaker')
async def show_schedules(message: Message):
    event = await db.get_happening_now_event()
    
    if not event:
        await message.answer("Нет активного мероприятия")
        return
    
    schedule = await db.get_event_schedule(event.id)
    
    text = f"Расписание на {event.title}:\n"
    
    for talk in schedule:
        text += f"{talk.speaker.first_and_last_name}\n"
        text += f"{talk.title}\n"
        text += f"{talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
        text += f"{talk.description}\n"
        text += "\n"
    await message.answer(text)


