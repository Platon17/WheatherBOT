import asyncio
import logging
from datetime import datetime
from services.storage import subscriptions
from weather_api import format_morning_forecast
from services.storage import user_data

async def send_daily_notifications(bot):
    while True:
        now = datetime.now().strftime("%H:%M")
        for user_id, sub_data in subscriptions.items():
            if sub_data.get("time") == now and sub_data.get("active", False):
                forecast = await format_morning_forecast(user_id, user_data)
                if forecast:
                    try:
                        await bot.send_message(user_id, forecast)
                    except Exception as e:
                        logging.error(f"Failed to send notification to {user_id}: {e}")
        await asyncio.sleep(60)