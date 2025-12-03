from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_events_keyboard(events):
    buttons = []
    for event in events[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{event.title}",
                callback_data=f"event_{event.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_event_action_keyboard(event_id, is_registered):
    buttons = []
    
    if is_registered:
        buttons.append([
            InlineKeyboardButton(
                text="Отписаться",
                callback_data=f"leave_event_{event_id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="Записаться",
                callback_data=f"join_event_{event_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="Назад",
            callback_data="back_to_events"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_speaker_choice_keyboard(speaker):
    builder = InlineKeyboardBuilder()
    if not speaker:
        return builder.as_markup()
    
    builder.button(
        text=f"{speaker.first_and_last_name}",
        callback_data=f"speaker_question:{speaker}"  
    )
    return builder.as_markup()


async def get_questions_keyboard(questions):
    buttons = []
    for idx, question in enumerate(questions[:5], 1):
        status = "✅" if question.is_answered else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} Вопрос {idx}",
                callback_data=f"question_{question.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_answer_keyboard(question_id):
    buttons = [
        [InlineKeyboardButton(
            text="Ответить",
            callback_data=f"answer_question_{question_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_organizer_events_keyboard(events):
    buttons = []
    for event in events[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{event.title}",
                callback_data=f"manage_event_{event.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_event_manage_keyboard(event_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="Изменить время выступления",
                callback_data=f"change_time_{event_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Рассылка",
                callback_data=f"broadcast_{event_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
