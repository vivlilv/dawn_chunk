from aiogram import Router, types, F
from database import (
    get_user_accounts_count,
    get_user_proxies_count,
    get_total_points,
)
from keyboards import main_menu_keyboard

router = Router()

@router.callback_query(F.data == 'statistics')
async def statistics(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    accounts_count = get_user_accounts_count(user_id)
    proxies_count = get_user_proxies_count(user_id)
    total_points = get_total_points(user_id)
    await callback_query.message.answer(
        f"Статистика:\n\nАккаунты: {accounts_count}\nПрокси: {proxies_count}\nЗаработано поинтов: {total_points}"
    )
    await callback_query.message.answer(
        "Выберите следующее действие:", reply_markup=main_menu_keyboard()
    )
