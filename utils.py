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