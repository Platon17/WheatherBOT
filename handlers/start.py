from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message
from keyboards import main_menu
from services.storage import user_data, subscriptions

async def cmd_start(message: Message):
    await message.answer("🌍 Введите имя города:", reply_markup=types.ReplyKeyboardRemove())



async def handle_city(message: Message):
    user_id = message.from_user.id

    # Проверяем, не устанавливает ли пользователь время
    if user_id in subscriptions and subscriptions[user_id].get("setting_time"):
        return  # Пропускаем обработку, если это ввод времени

    city = message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"city": city, "units": "metric"}
    else:
        user_data[user_id]["city"] = city

    await message.answer(
        f"✅ Город {city.title()} сохранен!\nВыберите действие:",
        reply_markup=main_menu()
    )