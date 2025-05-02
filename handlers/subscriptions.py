import re
from aiogram import types
from aiogram.types import Message, ReplyKeyboardRemove
from keyboards import subscription_menu, time_selection_menu, settings_menu
from services.storage import subscriptions, user_data
from .start import handle_city

async def cmd_subscription(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        await message.answer("❌ Сначала укажите город", reply_markup=settings_menu())
        return

    if user_id not in subscriptions:
        subscriptions[user_id] = {"active": False, "time": "08:00"}

    status = "✅ Включена" if subscriptions[user_id]["active"] else "❌ Отключена"
    await message.answer(
        f"⏰ Ежедневная рассылка погоды:\nСтатус: {status}\nВремя: {subscriptions[user_id]['time']}",
        reply_markup=subscription_menu()
    )


async def enable_subscription(message: Message):
    user_id = message.from_user.id
    if user_id not in subscriptions:
        subscriptions[user_id] = {"active": True, "time": "08:00"}
    else:
        subscriptions[user_id]["active"] = True

    await message.answer(
        f"✅ Рассылка включена. Вы будете получать погоду ежедневно в {subscriptions[user_id]['time']}",
        reply_markup=subscription_menu()
    )


async def disable_subscription(message: Message):
    user_id = message.from_user.id
    if user_id in subscriptions:
        subscriptions[user_id]["active"] = False

    await message.answer("❌ Рассылка отключена", reply_markup=subscription_menu())


async def ask_custom_time(message: Message):
    # Сохраняем состояние, что пользователь вводит время
    user_id = message.from_user.id
    if user_id not in subscriptions:
        subscriptions[user_id] = {"setting_time": True}
    else:
        subscriptions[user_id]["setting_time"] = True

    await message.answer(
        "⏰ Введите время в формате ЧЧ:ММ (например, 08:30 или 15:45):",
        reply_markup=ReplyKeyboardRemove()
    )


async def set_custom_time(message: Message):
    user_id = message.from_user.id

    # Проверяем, что пользователь действительно устанавливает время
    if user_id not in subscriptions or not subscriptions[user_id].get("setting_time"):
        return await handle_city(message)  # Если не в режиме установки времени, обрабатываем как город

    time_str = message.text

    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        await message.answer("❌ Некорректное время. Используйте формат ЧЧ:ММ")
        return

    subscriptions[user_id] = {
        "active": True,
        "time": time_str,
        "setting_time": False  # Сбрасываем флаг установки времени
    }

    await message.answer(
        f"✅ Время рассылки установлено на {time_str}",
        reply_markup=subscription_menu()
    )

async def change_time(message: Message):
    await message.answer("Выберите время рассылки:", reply_markup=time_selection_menu())