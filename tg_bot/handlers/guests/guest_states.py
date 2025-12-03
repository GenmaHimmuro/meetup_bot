from aiogram.fsm.state import State, StatesGroup


class QuestionStates(StatesGroup):
    waiting_for_question_text = State()

class SpeakerRequestStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_description = State()

class NetworkingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_about = State()