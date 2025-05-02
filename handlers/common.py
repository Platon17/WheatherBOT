from aiogram.types import Message
from keyboards import main_menu, settings_menu

async def cmd_back(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu())

async def back_to_settings(message: Message):
    await message.answer("⚙️ Настройки:", reply_markup=settings_menu())