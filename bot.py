from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiohttp
import asyncio
from datetime import datetime, timedelta
import config
from typing import Dict, Any, List
import re

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
user_data: Dict[int, Dict[str, Any]] = {}
subscriptions: Dict[int, Dict[str, Any]] = {}  # Для хранения подписок на рассылку


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
            [KeyboardButton(text="⏰ Рассылка погоды"), KeyboardButton(text="🔙 Назад")]
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


def time_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="07:00"), KeyboardButton(text="08:00"), KeyboardButton(text="09:00")],
            [KeyboardButton(text="10:00"), KeyboardButton(text="11:00"), KeyboardButton(text="12:00")],
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


# Получение текущей погоды
async def get_current_weather(city: str, units: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": units,
            "lang": "ru"
        }
        async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
            if resp.status == 200:
                return await resp.json()
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


# Форматирование утреннего прогноза для рассылки
async def format_morning_forecast(user_id: int) -> str:
    if user_id not in user_data or "city" not in user_data[user_id]:
        return None

    city = user_data[user_id]["city"]
    units = user_data[user_id].get("units", "metric")

    # Получаем текущую погоду
    current_weather = await get_current_weather(city, units)
    if not current_weather:
        return None

    temp = current_weather["main"]["temp"]
    feels_like = current_weather["main"]["feels_like"]
    weather_desc = current_weather["weather"][0]["description"].capitalize()
    wind_speed = current_weather["wind"]["speed"]
    humidity = current_weather["main"]["humidity"]

    # Получаем прогноз на день
    forecast_data = await get_forecast_data(city, units)
    if not forecast_data:
        return None

    now = datetime.now()
    today = now.date()

    # Фильтруем прогноз на оставшийся день (текущее время и позже)
    today_data = [
        f for f in forecast_data
        if datetime.fromtimestamp(f["dt"]).date() == today and
           datetime.fromtimestamp(f["dt"]) >= now
    ]

    if not today_data:
        return None

    # Формируем основное сообщение
    message_parts = [
        f"🌅 Доброе утро! Вот погода в {city.title()} на сегодня {now.strftime('%d.%m.%Y')}:\n",
        f"🌡️ Сейчас: {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})",
        f"📢 {weather_desc}",
        f"💨 Ветер: {wind_speed} {UNITS[units]['speed']}",
        f"💧 Влажность: {humidity}%",
        f"🎯 {generate_recommendations(temp, weather_desc)}",
        "\n⏳ Прогноз на оставшийся день:"
    ]

    # Добавляем почасовой прогноз (группируем по 3 часа)
    for i, item in enumerate(today_data):
        if i % 3 == 0:  # Показываем каждые 3 часа для компактности
            time = datetime.fromtimestamp(item["dt"]).strftime("%H:%M")
            temp = item["main"]["temp"]
            weather_desc = item["weather"][0]["description"].capitalize()

            message_parts.append(
                f"\n🕒 {time}: {temp:.1f}{UNITS[units]['temp']}, {weather_desc}"
            )

    # Добавляем информацию о max/min температуре
    all_day_data = [f for f in forecast_data if datetime.fromtimestamp(f["dt"]).date() == today]
    if all_day_data:
        max_temp = max(item["main"]["temp"] for item in all_day_data)
        min_temp = min(item["main"]["temp"] for item in all_day_data)
        message_parts.append(
            f"\n\n📊 За день: макс. {max_temp:.1f}{UNITS[units]['temp']}, "
            f"мин. {min_temp:.1f}{UNITS[units]['temp']}"
        )

    message_parts.append("\n\nХорошего дня! ☀️")

    return "\n".join(message_parts)

# Функция рассылки погоды
async def send_daily_notifications():
    while True:
        now = datetime.now().strftime("%H:%M")
        for user_id, sub_data in subscriptions.items():
            if sub_data["time"] == now and sub_data["active"]:
                forecast = await format_morning_forecast(user_id)
                if forecast:
                    try:
                        await bot.send_message(user_id, forecast)
                    except Exception as e:
                        logging.error(f"Failed to send notification to {user_id}: {e}")
        await asyncio.sleep(60)  # Проверяем каждую минуту


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


@dp.message(lambda message: message.text == "⏰ Рассылка погоды")
async def cmd_subscription(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or "city" not in user_data[user_id]:
        await message.answer("❌ Сначала укажите город")
        return

    if user_id not in subscriptions:
        subscriptions[user_id] = {"active": False, "time": "08:00"}

    status = "✅ Включена" if subscriptions[user_id]["active"] else "❌ Отключена"
    await message.answer(
        f"⏰ Ежедневная рассылка погоды:\n"
        f"Статус: {status}\n"
        f"Время: {subscriptions[user_id]['time']}",
        reply_markup=subscription_menu()
    )


@dp.message(lambda message: message.text == "✅ Включить рассылку")
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


@dp.message(lambda message: message.text == "❌ Отключить рассылку")
async def disable_subscription(message: Message):
    user_id = message.from_user.id
    if user_id in subscriptions:
        subscriptions[user_id]["active"] = False

    await message.answer(
        "❌ Рассылка отключена",
        reply_markup=subscription_menu()
    )


@dp.message(lambda message: message.text == "🕘 Изменить время")
async def change_time(message: Message):
    await message.answer("Выберите время рассылки:", reply_markup=time_menu())

@dp.message(lambda message: message.text == "⏱ Указать точное время")
async def ask_custom_time(message: Message):
    await message.answer(
        "⏰ Введите время в формате ЧЧ:ММ (например, 08:30 или 15:45):",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(lambda message: re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message.text))
async def set_custom_time(message: Message):
    user_id = message.from_user.id
    time_str = message.text

    # Проверяем корректность времени
    try:
        hours, minutes = map(int, time_str.split(':'))
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректное время. Используйте формат ЧЧ:ММ (например, 08:30)")
        return

    if user_id not in subscriptions:
        subscriptions[user_id] = {"active": True, "time": time_str}
    else:
        subscriptions[user_id]["time"] = time_str

    await message.answer(
        f"✅ Время рассылки установлено на {time_str}",
        reply_markup=subscription_menu()
    )

@dp.message(lambda message: message.text in ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00"])
async def set_time(message: Message):
    user_id = message.from_user.id
    if user_id not in subscriptions:
        subscriptions[user_id] = {"active": True, "time": message.text}
    else:
        subscriptions[user_id]["time"] = message.text

    await message.answer(
        f"✅ Время рассылки изменено на {message.text}",
        reply_markup=subscription_menu()
    )


@dp.message(lambda message: message.text == "🌤️ Сейчас")
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
    # Запускаем рассылку в фоновом режиме
    asyncio.create_task(send_daily_notifications())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())