import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import aiohttp
import asyncio
from datetime import datetime, timedelta

# Настройки
API_TOKEN = "7699387413:AAErp-pxuVwnnbKK-ramP5kH8sNu27JWymk"  # Замените на токен вашего бота
OPENWEATHER_API_KEY = "c3a0108f5e04f0bcbe70e8c0282863ca"  # Замените на ваш API-ключ OpenWeather
OPENWEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Создаем объект бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранение данных о пользователях в памяти
user_data = {}

# Генерация рекомендаций
def generate_recommendations(temp: float, weather_desc: str, wind_speed: float) -> str:
    recommendations = []

    if "дождь" in weather_desc or "ливень" in weather_desc:
        recommendations.append("Береги себя, возьми зонт — на улице дождик!")
    if "снег" in weather_desc:
        recommendations.append("Надевай тёплую обувь, а то ноги промокнут!")
    if temp < 0:
        recommendations.append("Жесть, какой мороз! Шапка, перчатки — обязательны.")
    elif 0 <= temp < 10:
        recommendations.append("Прохладно, лучше захватить куртку потеплее.")
    elif temp > 30:
        recommendations.append("Жара неимоверная! Не забудь бутылку воды.")
    if wind_speed > 10:
        recommendations.append("На улице сильный ветер, будь осторожен!")

    return " ".join(recommendations)

# Функция для получения данных о погоде
async def get_weather_data(city: str, forecast: bool = False, day_offset: int = 0) -> dict:
    async with aiohttp.ClientSession() as session:
        url = FORECAST_URL if forecast else OPENWEATHER_URL
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "ru",
        }
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if forecast:
                    target_date = (datetime.utcnow() + timedelta(days=day_offset)).date()
                    for entry in data["list"]:
                        forecast_time = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
                        if forecast_time.date() == target_date and forecast_time.hour == 12:
                            return entry
                    return None
                return data
            return None

# Формирование текста прогноза
def format_weather_message(city: str, data: dict, forecast_date: str = None) -> str:
    weather_desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    # Генерация рекомендаций
    recommendations = generate_recommendations(temp, weather_desc, wind_speed)

    # Неформальное сообщение
    day_text = f"на {forecast_date}" if forecast_date else "сейчас"
    return (
        f"Ну что, держи прогноз {day_text} для {city.title()}:\n\n"
        f"🌡️ Температура: {temp:.1f}°C (ощущается как {feels_like:.1f}°C).\n"
        f"💧 Влажность: {humidity}%.\n"
        f"🌬️ Ветер: {wind_speed} м/с.\n"
        f"📜 Описание: {weather_desc.capitalize()}.\n\n"
        f"{recommendations}"
    )

# Обработчик команды /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Погода")],
        [KeyboardButton(text="Погода на завтра"), KeyboardButton(text="Погода на послезавтра")],
    ], resize_keyboard=True)
    await message.reply(
        "Привет! Я готов узнать для тебя погоду. Нажимай на кнопку, или просто напиши свой город, чтобы я его запомнил.",
        reply_markup=keyboard
    )

# Обработчик кнопок
@dp.message(lambda message: message.text in ["Погода", "Погода на завтра", "Погода на послезавтра"])
async def weather_buttons(message: Message):
    user_id = message.from_user.id
    city = user_data.get(user_id)
    if not city:
        await message.reply("Напиши название города, чтобы я мог узнать погоду для тебя!")
        return

    day_offset = 0
    forecast_date = None

    if message.text == "Погода на завтра":
        day_offset = 1
        forecast_date = "завтра"
    elif message.text == "Погода на послезавтра":
        day_offset = 2
        forecast_date = "послезавтра"

    if day_offset == 0:
        data = await get_weather_data(city)
    else:
        data = await get_weather_data(city, forecast=True, day_offset=day_offset)

    if data:
        weather_message = format_weather_message(city, data, forecast_date)
        await message.reply(weather_message)
    else:
        await message.reply("Не получилось узнать прогноз. Проверь название города или попробуй позже.")

# Обработчик текстовых сообщений (сохранение города)
@dp.message()
async def handle_city(message: Message):
    user_id = message.from_user.id
    city = message.text.strip()
    user_data[user_id] = city
    await message.reply(f"Запомнил! Твой город — {city.title()}. Теперь нажимай на кнопку 'Погода', чтобы узнать прогноз.")

# Основная функция
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
