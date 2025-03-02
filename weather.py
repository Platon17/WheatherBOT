import requests
from config import WEATHER_API_KEY

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"🌍 Город: {data['name']}\n🌡 Температура: {data['main']['temp']}°C\n💨 Ветер: {data['wind']['speed']} м/с"
    return None