from aiogram import Router, types, F
from database import (
    get_user_accounts_count,
    get_user_proxies_count,
    get_total_points,
    get_user_accounts,
)
from keyboards import main_menu_keyboard

router = Router()

@router.message(F.text == "My accounts")
async def my_accounts(message: types.Message):
    user_id = message.from_user.id
    accounts_count = get_user_accounts_count(user_id)
    proxies_count = get_user_proxies_count(user_id)
    total_points = get_total_points(user_id)
    accounts = get_user_accounts(user_id)

    message_text = f"Accounts: {accounts_count}\nProxies: {proxies_count}\nTotal points: {total_points}\n\n"
    message_text += "Account details:\n"
    for account in accounts:
        email = account[0]
        points = account[3] if len(account) > 3 else 0
        message_text += f"{email}: {points}\n"

    await message.answer(message_text)
