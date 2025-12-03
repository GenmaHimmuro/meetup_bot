from aiogram.fsm.state import State, StatesGroup


class EventManagementStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_talk_selection = State()
    waiting_for_new_time = State()