from aiogram.types import Message
from keyboards import main_menu
from weather_api import get_current_weather, get_forecast_data, format_tomorrow_forecast, format_daily_forecast
from config import UNITS
from services.storage import user_data

async def cmd_current(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        return await message.answer("❌ Сначала укажите город")

    weather_data = await get_current_weather(
        city=user_data[user_id]["city"],
        units=user_data[user_id].get("units", "metric")
    )

    if weather_data:
        temp = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        weather_desc = weather_data["weather"][0]["description"].capitalize()
        units = user_data[user_id].get("units", "metric")

        response = (
            f"🌍 Погода в {user_data[user_id]['city'].title()} сейчас:\n"
            f"🌡️ {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})\n"
            f"📢 {weather_desc}\n"
            f"💨 Ветер: {weather_data['wind']['speed']} {UNITS[units]['speed']}\n"
            f"💧 Влажность: {weather_data['main']['humidity']}%\n"
            f"🎯 {generate_recommendations(temp, weather_desc)}"
        )
        await message.answer(response)
    else:
        await message.answer("⚠️ Ошибка получения данных")

async def cmd_tomorrow(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        return await message.answer("❌ Сначала укажите город")

    forecast_data = await get_forecast_data(
        city=user_data[user_id]["city"],
        units=user_data[user_id].get("units", "metric")
    )

    if forecast_data:
        formatted = format_tomorrow_forecast(
            forecast_data=forecast_data,
            city=user_data[user_id]["city"],
            units=user_data[user_id].get("units", "metric")
        )
        await message.answer(formatted, reply_markup=main_menu())
    else:
        await message.answer("⚠️ Ошибка получения прогноза")

async def cmd_today_forecast(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        return await message.answer("❌ Сначала укажите город")

    forecast_data = await get_forecast_data(
        city=user_data[user_id]["city"],
        units=user_data[user_id].get("units", "metric")
    )

    if forecast_data:
        formatted = format_daily_forecast(
            forecast_data=forecast_data,
            city=user_data[user_id]["city"],
            units=user_data[user_id].get("units", "metric")
        )
        await message.answer(formatted, reply_markup=main_menu())
    else:
        await message.answer("⚠️ Ошибка получения прогноза")