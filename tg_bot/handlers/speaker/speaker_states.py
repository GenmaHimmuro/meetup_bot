from aiogram.fsm.state import State, StatesGroup


class AnswerStates(StatesGroup):
    waiting_for_answer = State()