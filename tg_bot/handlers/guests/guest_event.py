from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from tg_bot.utils.db_funcs import db
from tg_bot.keyboards.inline_keyboards import get_events_keyboard, get_event_action_keyboard
from tg_bot.utils.decorators import check_role


guest_router_event = Router()


@guest_router_event.message(F.text == "📋 События")
@check_role('guest')
async def show_events(message: Message):
    event = await db.get_event_by_id()
    non_active_events = await db.get_non_active_events()
    
    if not event:
        await message.answer("На данный момент нет активных мероприятий")
        return
    
    text = "📋 Сегодня:\n\n"
    text += f"{event.title}\n"
    text += f"{event.date.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"{event.location}\n"
    text += f"{event.description}\n\n"

    if not non_active_events:
        await message.answer("Предстоящих мероприятий пока нет")
    else:
        for event in non_active_events:
            text += f"Предстоящие:{event.title}\n"
            text += f"{event.date.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"{event.location}\n"
            text += f"{event.description}\n"
            text += "Чтобы записаться на предстоящее мероприятие, нажмите кнопку ниже\n"

    reply_markup = await get_events_keyboard(non_active_events)
    await message.answer(text, reply_markup=reply_markup)


@guest_router_event.callback_query(F.data.startswith("event_"))
@check_role('guest')
async def event_detail(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    
    event = await db.get_event_by_id()
    is_registered = await db.is_user_on_event(callback.from_user.id, event_id)
    reply_markup = await get_event_action_keyboard(event_id, is_registered)
    
    if not event:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    
    text = f"{event.title}\n"
    text += f"Дата: {event.date.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"Место: {event.location}\n"
    text += f"Описание: {event.description}\n"
    text +="Вы записаны на это мероприятие" if is_registered else "Вы не записаны"
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@guest_router_event.callback_query(F.data.startswith("join_event_"))
@check_role('guest')
async def join_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    success = await db.add_user_to_event(callback.from_user.id, event_id)
    
    if success:
        await callback.answer("Вы записаны на мероприятие!", show_alert=True)
    else:
        await callback.answer("Ошибка при записи", show_alert=True)


@guest_router_event.callback_query(F.data.startswith("leave_event_"))
@check_role('guest')
async def leave_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    success = await db.remove_user_from_event(callback.from_user.id, event_id)
    
    if success:
        await callback.answer("Вы отписаны от мероприятия", show_alert=True)
    else:
        await callback.answer("Ошибка при отписке", show_alert=True)


@guest_router_event.callback_query(F.data == "back_to_events")
@check_role('guest')
async def back_to_events(callback: CallbackQuery):
    events = await db.get_active_events()
    
    text = "Активные мероприятия:\n"
    
    for event in events:
        text += f"{event.title}\n"
        text += f"{event.date.strftime('%d.%m.%Y %H:%M')}\n"
        text += "Чтобы записаться на предстоящее мероприятие, нажмите кнопку ниже\n"

    non_active_events = await db.get_non_active_events()
    reply_markup = await get_events_keyboard(non_active_events)
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()
