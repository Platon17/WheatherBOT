import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import UNITS, WEATHER_API_KEY
from datetime import datetime, timedelta
from config import UNITS
from utils import generate_recommendations

async def get_forecast_data(city: str, units: str) -> List[Dict[str, Any]]:
    url = "http://api.openweathermap.org/data/2.5/forecast"
    async with aiohttp.ClientSession() as session:
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units,
            "lang": "ru"
        }
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["list"]
            return None


async def get_current_weather(city: str, units: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units,
            "lang": "ru"
        }
        async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            return None



async def format_morning_forecast(user_id: int, user_data: Dict[int, Dict[str, Any]]) -> str:
    if user_id not in user_data or "city" not in user_data[user_id]:
        return None

    city = user_data[user_id]["city"]
    units = user_data[user_id].get("units", "metric")

    current_weather = await get_current_weather(city, units)
    if not current_weather:
        return None

    temp = current_weather["main"]["temp"]
    feels_like = current_weather["main"]["feels_like"]
    weather_desc = current_weather["weather"][0]["description"].capitalize()
    wind_speed = current_weather["wind"]["speed"]
    humidity = current_weather["main"]["humidity"]

    forecast_data = await get_forecast_data(city, units)
    if not forecast_data:
        return None

    now = datetime.now()
    today = now.date()
    today_data = [
        f for f in forecast_data
        if datetime.fromtimestamp(f["dt"]).date() == today and
           datetime.fromtimestamp(f["dt"]) >= now
    ]

    if not today_data:
        return None

    message_parts = [
        f"🌅 Доброе утро! Вот погода в {city.title()} на сегодня {now.strftime('%d.%m.%Y')}:\n",
        f"🌡️ Сейчас: {temp:.1f}{UNITS[units]['temp']} (ощущается {feels_like:.1f}{UNITS[units]['temp']})",
        f"📢 {weather_desc}",
        f"💨 Ветер: {wind_speed} {UNITS[units]['speed']}",
        f"💧 Влажность: {humidity}%",
        f"🎯 {generate_recommendations(temp, weather_desc)}",
        "\n⏳ Прогноз на оставшийся день:"
    ]

    for i, item in enumerate(today_data):
        if i % 3 == 0:
            time = datetime.fromtimestamp(item["dt"]).strftime("%H:%M")
            temp = item["main"]["temp"]
            weather_desc = item["weather"][0]["description"].capitalize()
            message_parts.append(f"\n🕒 {time}: {temp:.1f}{UNITS[units]['temp']}, {weather_desc}")

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