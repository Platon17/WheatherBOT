import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import aiohttp
import asyncio
from datetime import datetime, timedelta
import config
# Настройки
API_TOKEN = config.TOKEN  # Ваш токен бота
OPENWEATHER_API_KEY = config.WEATHER_API_KEY  # API-ключ OpenWeather

# Константы
UNITS = {
    "metric": {"temp": "°C", "speed": "м/с"},
    "imperial": {"temp": "°F", "speed": "миль/ч"}
}

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранение пользовательских данных
user_data = {}


# Клавиатуры
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌤️ Сейчас"), KeyboardButton(text="📆 Прогноз")],
            [KeyboardButton(text="⚙️ Настройки")]
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
async def get_weather_data(city: str, units: str, forecast: bool = False, days: int = 1) -> dict:
    url = "http://api.openweathermap.org/data/2.5/forecast" if forecast else "http://api.openweathermap.org/data/2.5/weather"

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
                if forecast:
                    return [item for item in data["list"] if "12:00:00" in item["dt_txt"]][:days]
                return data
            return None


# Форматирование сообщения
def format_weather(data: dict, city: str, units: str) -> str:
    current_time = datetime.fromtimestamp(data["dt"]).strftime("%H:%M")
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    weather_desc = data["weather"][0]["description"].capitalize()

    return (
        f"🌡️ Погода в {city.title()} ({current_time}):\n"
        f"{temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})\n"
        f"📢 {weather_desc}\n"
        f"💨 Ветер: {data['wind']['speed']} {UNITS[units]['speed']}\n"
        f"💧 Влажность: {data['main']['humidity']}%\n"
        f"🎯 {generate_recommendations(temp, weather_desc)}"
    )


# Обработчики сообщений
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🌍 Введите название города:", reply_markup=types.ReplyKeyboardRemove())


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
        f"Система измерений изменена на {message.text.split()[0]}",
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

    data = await get_weather_data(
        city=user_data[user_id]["city"],
        units=user_data[user_id].get("units", "metric")
    )

    if data:
        await message.answer(
            format_weather(data, user_data[user_id]["city"], user_data[user_id].get("units", "metric")))
    else:
        await message.answer("⚠️ Ошибка получения данных")


@dp.message(lambda message: message.text == "📆 Прогноз")
async def cmd_forecast(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        return await message.answer("❌ Сначала укажите город")

    data = await get_weather_data(
        city=user_data[user_id]["city"],
        units=user_data[user_id].get("units", "metric"),
        forecast=True,
        days=3
    )

    if data:
        forecast_text = "\n\n".join(
            [format_weather(item, user_data[user_id]["city"], user_data[user_id].get("units", "metric"))
             for item in data]
        )
        await message.answer(f"📆 Прогноз на 3 дня:\n{forecast_text}")
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