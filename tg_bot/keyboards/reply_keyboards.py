from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_main_menu(role):
    if role == 'guest':
        return get_guest_menu()
    elif role == 'speaker':
        return get_speaker_menu()
    elif role == 'organizer':
        return get_organizer_menu()
    else:
        return get_guest_menu()


def get_guest_menu():
    buttons = [
        [KeyboardButton(text="📋 События")],
        [KeyboardButton(text="💬 Задать вопрос")],
        [KeyboardButton(text="🤝 Нетворкинг")],
        [KeyboardButton(text="🎤 Хочу быть докладчиком")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_speaker_menu():
    buttons = [
        [KeyboardButton(text="❓ Вопросы")],
        [KeyboardButton(text="📅 График")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_organizer_menu():
    buttons = [
        [KeyboardButton(text="📋 Управление событиями")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )