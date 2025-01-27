# data_handler.py
import csv
from datetime import datetime
import os
import config

def save_weather_data(city: str, date: str, temperature: float):
    """Сохраняет данные о погоде в CSV файл."""
    file_exists = os.path.isfile(config.DATA_FILE)
    with open(config.DATA_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["city", "date", "temperature"])  # Заголовок
        writer.writerow([city, date, temperature])

def load_weather_data(city: str) -> list:
    """Загружает исторические данные о погоде для конкретного города."""
    data = []
    if not os.path.isfile(config.DATA_FILE):
        return data

    with open(config.DATA_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["city"] == city:
                data.append((row["date"], float(row["temperature"])))
    return data