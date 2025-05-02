# weather_functions.py
import aiohttp
from datetime import datetime, timedelta
from config import OPENWEATHER_API_KEY, OPENWEATHER_URL, FORECAST_URL, HISTORY_URL
from data_handler import save_weather_data, load_weather_data
from models import analyze_trend, predict_future_temperatures

async def get_weather_data(city: str, forecast: bool = False, day_offset: int = 0, units: str = "metric") -> dict:
    """Получает данные о погоде."""
    async with aiohttp.ClientSession() as session:
        url = FORECAST_URL if forecast else OPENWEATHER_URL
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": units,
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
                    return {}
                return data
            return {}

async def get_historical_weather_data(city: str, days: int = 10, units: str = "metric") -> list:
    """Получает исторические данные о погоде."""
    temperatures = []
    async with aiohttp.ClientSession() as session:
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i + 1)
            timestamp = int(date.timestamp())
            params = {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": units,
                "dt": timestamp,
            }
            async with session.get(HISTORY_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "current" in data:
                        temp = data["current"]["temp"]
                        save_weather_data(city, date.strftime("%Y-%m-%d"), temp)
                        temperatures.append(temp)
    return temperatures[::-1]

def format_weather_message(city: str, data: dict, forecast_date: str = None, units: str = "metric") -> str:
    """Формирует сообщение с прогнозом погоды."""
    weather_desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
    day_text = f"на {forecast_date}" if forecast_date else "сейчас"
    return (
        f"Ну что, держи прогноз {day_text} для {city.title()}:\n\n"
        f"🌡️ Температура: {temp:.1f}{temp_unit} (ощущается как {feels_like:.1f}{temp_unit}).\n"
        f"💧 Влажность: {humidity}%.\n"
        f"🌬️ Ветер: {wind_speed} м/с.\n"
        f"📜 Описание: {weather_desc.capitalize()}.\n"
    )