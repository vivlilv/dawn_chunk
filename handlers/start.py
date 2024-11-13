from aiogram import Router, types
from aiogram.filters import CommandStart
from database import add_user, get_user
from keyboards import main_menu_keyboard
from datetime import datetime

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    user = get_user(user_id)
    if not user:
        add_user(user_id, username, created_date)
    await message.answer(
        f"👋 Добро пожаловать, {username}! Выберите действие из меню ниже:",
        reply_markup=main_menu_keyboard()
    )
