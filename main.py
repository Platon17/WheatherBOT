import logging
import asyncio
import re
from aiogram.filters import Command
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import start, settings, weather, subscriptions, common
from services import scheduler
from services.storage import user_data
from handlers.factories import subscription_handlers
logging.basicConfig(level=logging.INFO)
handlers = subscription_handlers()

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрация обработчиков
    dp.message.register(start.cmd_start, Command("start"))
    dp.message.register(start.handle_city, lambda msg: msg.text and msg.text not in [
        "🌤️ Сейчас", "📅 Весь день", "🔄 Завтра", "⚙️ Настройки",
        "🌍 Сменить город", "🌡️ Шкала температуры", "⏰ Рассылка погоды",
        "°C Метрическая", "°F Имперская", "✅ Включить рассылку",
        "❌ Отключить рассылку", "🕘 Изменить время", "🔙 Назад"
    ])

    dp.message.register(settings.cmd_settings, lambda msg: msg.text == "⚙️ Настройки")
    dp.message.register(settings.cmd_units, lambda msg: msg.text == "🌡️ Шкала температуры")
    dp.message.register(settings.cmd_change_city, lambda msg: msg.text == "🌍 Сменить город")
    dp.message.register(settings.set_units, lambda msg: msg.text in ["°C Метрическая", "°F Имперская"])

    dp.message.register(handlers["cmd_subscription"], lambda msg: msg.text == "⏰ Рассылка погоды")
    dp.message.register(subscriptions.enable_subscription, lambda msg: msg.text == "✅ Включить рассылку")
    dp.message.register(subscriptions.disable_subscription, lambda msg: msg.text == "❌ Отключить рассылку")
    dp.message.register(subscriptions.change_time, lambda msg: msg.text == "🕘 Изменить время")
    dp.message.register(subscriptions.ask_custom_time, lambda msg: msg.text == "⏱ Указать точное время")
    dp.message.register(subscriptions.set_custom_time,
                        lambda msg: re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', msg.text))

    dp.message.register(weather.cmd_current, lambda msg: msg.text == "🌤️ Сейчас")
    dp.message.register(weather.cmd_tomorrow, lambda msg: msg.text == "🔄 Завтра")
    dp.message.register(weather.cmd_today_forecast, lambda msg: msg.text == "📅 Весь день")

    dp.message.register(common.cmd_back, lambda msg: msg.text == "🔙 Назад")
    dp.message.register(common.back_to_settings, lambda msg: msg.text == "🔙 Назад")

    # Запуск фоновых задач
    asyncio.create_task(scheduler.send_daily_notifications(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())