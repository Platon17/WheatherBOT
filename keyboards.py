from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌤️ Сейчас"), KeyboardButton(text="📅 Весь день")],
            [KeyboardButton(text="🔄 Завтра"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )

def settings_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌍 Сменить город"), KeyboardButton(text="🌡️ Шкала температуры")],
            [KeyboardButton(text="⏰ Рассылка погоды"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def units_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="°C Метрическая"), KeyboardButton(text="°F Имперская")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def subscription_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Включить рассылку"), KeyboardButton(text="❌ Отключить рассылку")],
            [KeyboardButton(text="🕘 Изменить время"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def time_selection_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="07:00"), KeyboardButton(text="08:00"), KeyboardButton(text="09:00")],
            [KeyboardButton(text="10:00"), KeyboardButton(text="11:00"), KeyboardButton(text="12:00")],
            [KeyboardButton(text="⏱ Указать точное время"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )