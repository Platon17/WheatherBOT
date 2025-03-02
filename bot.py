import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import aiohttp
import asyncio
from datetime import datetime, timedelta
import config

# Настройки
API_TOKEN = config.TOKEN
OPENWEATHER_API_KEY = config.WEATHER_API_KEY

UNITS = {
    "metric": {"temp": "°C", "speed": "м/с"},
    "imperial": {"temp": "°F", "speed": "миль/ч"}
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
user_data = {}


# Клавиатуры
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
            [KeyboardButton(text="🔙 Назад")]
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


# Генерация рекомендаций
def generate_recommendations(temp: float, weather_desc: str) -> str:
    recommendations = []
    weather_desc = weather_desc.lower()

    if "дождь" in weather_desc:
        recommendations.append("☔ Возьмите зонт")
    if "снег" in weather_desc:
        recommendations.append("⛄ Осторожно на дорогах")
    if temp < -10:
        recommendations.append("🧊 Экстремальный холод! Оставайтесь дома")
    elif temp < 0:
        recommendations.append("🧤 Термобелье и горячий чай!")
    elif temp > 30:
        recommendations.append("🔥 Кондиционер и прохладительные напитки")

    return " ".join(recommendations) if recommendations else "👍 Идеальная погода!"


# Получение данных о погоде
async def get_forecast_data(city: str, units: str, days: int = None):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    async with aiohttp.ClientSession() as session:
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": units,
            "lang": "ru"
        }
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["list"]
            return None


# Форматирование прогноза на весь день
def format_daily_forecast(forecast_data: list, city: str, units: str) -> str:
    today = datetime.now().date()
    daily_data = [f for f in forecast_data
                  if datetime.fromtimestamp(f["dt"]).date() == today]

    if not daily_data:
        return "❌ Данные за сегодня отсутствуют"

    result = [f"⏳ Погода в {city.title()} на сегодня:\n"]
    for item in daily_data:
        time = datetime.fromtimestamp(item["dt"]).strftime("%H:%M")
        temp = item["main"]["temp"]
        feels_like = item["main"]["feels_like"]
        weather_desc = item["weather"][0]["description"].capitalize()
        wind_speed = item["wind"]["speed"]
        humidity = item["main"]["humidity"]

        result.append(
            f"\n🕒 {time}\n"
            f"🌡️ {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})\n"
            f"📢 {weather_desc}\n"
            f"💨 Ветер: {wind_speed} {UNITS[units]['speed']}\n"
            f"💧 Влажность: {humidity}%\n"
            f"-----------------"
        )
    return "\n".join(result)


# Форматирование прогноза на завтра
def format_tomorrow_forecast(forecast_data: list, city: str, units: str) -> str:
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    daily_data = [f for f in forecast_data
                  if datetime.fromtimestamp(f["dt"]).date() == tomorrow]

    if not daily_data:
        return "❌ Прогноз на завтра недоступен"

    day_forecast = next((f for f in daily_data
                         if datetime.fromtimestamp(f["dt"]).hour == 12), daily_data[0])

    date_str = datetime.fromtimestamp(day_forecast["dt"]).strftime("%d.%m.%Y")
    temp = day_forecast["main"]["temp"]
    feels_like = day_forecast["main"]["feels_like"]
    weather_desc = day_forecast["weather"][0]["description"].capitalize()

    return (
        f"📅 Прогноз на завтра ({date_str}) для {city.title()}:\n"
        f"🌡️ {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})\n"
        f"📢 {weather_desc}\n"
        f"💨 Ветер: {day_forecast['wind']['speed']} {UNITS[units]['speed']}\n"
        f"💧 Влажность: {day_forecast['main']['humidity']}%\n"
        f"🎯 {generate_recommendations(temp, weather_desc)}"
    )


# Обработчики сообщений
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🌍 Введите имя города:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(lambda message: message.text == "⚙️ Настройки")
async def cmd_settings(message: Message):
    await message.answer("⚙️ Настройки:", reply_markup=settings_menu())


@dp.message(lambda message: message.text == "🔙 Назад")
async def cmd_back(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu())


@dp.message(lambda message: message.text == "🌡️ Шкала температуры")
async def cmd_units(message: Message):
    await message.answer("Выберите систему измерения:", reply_markup=units_menu())


@dp.message(lambda message: message.text in ["°C Метрическая", "°F Имперская"])
async def set_units(message: Message):
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


@dp.message(lambda message: message.text == "🌍 Сменить город")
async def cmd_change_city(message: Message):
    await message.answer("Введите новый город:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(lambda message: message.text == "🌤️ Сейчас")
async def cmd_current(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        return await message.answer("❌ Сначала укажите город")

    async with aiohttp.ClientSession() as session:
        params = {
            "q": user_data[user_id]["city"],
            "appid": OPENWEATHER_API_KEY,
            "units": user_data[user_id].get("units", "metric"),
            "lang": "ru"
        }
        async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                weather_desc = data["weather"][0]["description"].capitalize()
                units = user_data[user_id].get("units", "metric")

                response = (
                    f"🌍 Погода в {user_data[user_id]['city'].title()} сейчас:\n"
                    f"🌡️ {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})\n"
                    f"📢 {weather_desc}\n"
                    f"💨 Ветер: {data['wind']['speed']} {UNITS[units]['speed']}\n"
                    f"💧 Влажность: {data['main']['humidity']}%\n"
                    f"🎯 {generate_recommendations(temp, weather_desc)}"
                )
                await message.answer(response)
            else:
                await message.answer("⚠️ Ошибка получения данных")


@dp.message(lambda message: message.text == "🔄 Завтра")
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


@dp.message(lambda message: message.text == "📅 Весь день")
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


@dp.message()
async def handle_city(message: Message):
    user_id = message.from_user.id
    city = message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {"city": city, "units": "metric"}
    else:
        user_data[user_id]["city"] = city

    await message.answer(
        f"✅ Город {city.title()} сохранен!\n"
        "Выберите действие:",
        reply_markup=main_menu()
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())