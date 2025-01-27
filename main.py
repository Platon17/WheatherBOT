# bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import API_TOKEN
from weather_functions import get_weather_data, get_historical_weather_data, format_weather_message
from models import analyze_trend, predict_future_temperatures
from data_handler import load_weather_data

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Создаем объект бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранение данных о пользователях в памяти
user_data = {}

# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌤️ Погода сейчас")],
        [KeyboardButton(text="📅 Погода на завтра"), KeyboardButton(text="📆 Погода на послезавтра")],
        [KeyboardButton(text="📊 Анализ тенденции")],
        [KeyboardButton(text="⚙️ Настройки")],
    ], resize_keyboard=True)
    await message.reply(
        "Привет! Я готов узнать для тебя погоду. Нажимай на кнопку, или просто напиши свой город, чтобы я его запомнил.",
        reply_markup=keyboard
    )

# Обработчик кнопок
@dp.message(lambda message: message.text in ["🌤️ Погода сейчас", "📅 Погода на завтра", "📆 Погода на послезавтра"])
async def weather_buttons(message: Message):
    user_id = message.from_user.id
    city = user_data.get(user_id, {}).get("city")
    if not city:
        await message.reply("Напиши название города, чтобы я мог узнать погоду для тебя!")
        return

    day_offset = 0
    forecast_date = None

    if message.text == "📅 Погода на завтра":
        day_offset = 1
        forecast_date = "завтра"
    elif message.text == "📆 Погода на послезавтра":
        day_offset = 2
        forecast_date = "послезавтра"

    units = user_data.get(user_id, {}).get("units", "metric")
    if day_offset == 0:
        data = await get_weather_data(city, units=units)
    else:
        data = await get_weather_data(city, forecast=True, day_offset=day_offset, units=units)

    if data:
        weather_message = format_weather_message(city, data, forecast_date, units)
        await message.reply(weather_message)
    else:
        await message.reply("Не получилось узнать прогноз. Проверь название города или попробуй позже.")

# Обработчик кнопки "Анализ тенденции"
@dp.message(lambda message: message.text == "📊 Анализ тенденции")
async def analyze_trend_button(message: Message):
    user_id = message.from_user.id
    city = user_data.get(user_id, {}).get("city")
    if not city:
        await message.reply("Напиши название города, чтобы я мог проанализировать тенденцию!")
        return

    units = user_data.get(user_id, {}).get("units", "metric")
    temperatures = [temp for _, temp in load_weather_data(city)]
    if len(temperatures) < 2:
        await message.reply("Недостаточно данных для анализа тенденции.")
        return

    trend = analyze_trend(temperatures)
    predictions = predict_future_temperatures(temperatures)
    if predictions:
        predictions_text = "\n".join([f"День {i + 1}: {temp:.1f}°C" for i, temp in enumerate(predictions)])
        await message.reply(
            f"📊 Анализ тенденции для {city.title()}:\n\n"
            f"{trend}\n\n"
            f"Прогноз на следующие {len(predictions)} дней:\n"
            f"{predictions_text}"
        )
    else:
        await message.reply(f"📊 Анализ тенденции для {city.title()}:\n\n{trend}")

# Обработчик кнопки "Настройки"
@dp.message(lambda message: message.text == "⚙️ Настройки")
async def settings_button(message: Message):
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏙️ Сменить город")],
        [KeyboardButton(text="🌡️ Изменить шкалу температуры")],
        [KeyboardButton(text="🔙 Назад")],
    ], resize_keyboard=True)
    await message.reply("Что ты хочешь изменить?", reply_markup=keyboard)