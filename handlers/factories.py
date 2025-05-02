# handlers/factories.py
from services.storage import user_data, subscriptions


def subscription_handlers():
    async def _cmd_subscription(message: Message):
        user_id = message.from_user.id
        if user_id not in user_data or "city" not in user_data[user_id]:
            await message.answer("❌ Сначала укажите город", reply_markup=settings_menu())
            return

        if user_id not in subscriptions:
            subscriptions[user_id] = {"active": False, "time": "08:00"}

        status = "✅ Включена" if subscriptions[user_id]["active"] else "❌ Отключена"
        await message.answer(
            f"⏰ Ежедневная рассылка погоды:\nСтатус: {status}\nВремя: {subscriptions[user_id]['time']}",
            reply_markup=subscription_menu()
        )

    return {
        "cmd_subscription": _cmd_subscription,
        # другие обработчики
    }