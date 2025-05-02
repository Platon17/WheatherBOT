from aiogram import types
from aiogram.types import Message
from keyboards import settings_menu, units_menu, main_menu

async def cmd_settings(message: Message):
    await message.answer("⚙️ Настройки:", reply_markup=settings_menu())

async def cmd_units(message: Message):
    await message.answer("Выберите систему измерения:", reply_markup=units_menu())

async def cmd_change_city(message: Message):
    await message.answer("Введите новый город:", reply_markup=types.ReplyKeyboardRemove())

async def set_units(message: Message, user_data: dict):
    user_id = message.from_user.id
    units = "metric" if "°C" in message.text else "imperial"

    if user_id not in user_data:
        user_data[user_id] = {"units": units}
    else:
        user_data[user_id]["units"] = units

    await message.answer(
        f"✅ Система измерений изменена на {message.text.split()[0]}",
        reply_markup=settings_menu()
    )