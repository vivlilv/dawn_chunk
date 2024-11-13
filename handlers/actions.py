from aiogram import Router, types, F, Bot
from keyboards import actions_inline_keyboard
from handlers.register_accounts import register_accounts_start
from handlers.start_stop_mining import start_stop_mining
from shared import user_tasks

router = Router()

@router.message(F.text == "Actions")
async def actions_menu(message: types.Message):
    user_id = message.from_user.id
    mining_started = user_id in user_tasks
    await message.answer("Choose an action:", reply_markup=actions_inline_keyboard(mining_started))

@router.callback_query(F.data == "action_registration")
async def action_registration(callback_query: types.CallbackQuery, bot: Bot):
    await register_accounts_start(callback_query, bot)

@router.callback_query(F.data == "action_mining")
async def action_mining(callback_query: types.CallbackQuery, bot: Bot):
    await start_stop_mining(callback_query, bot)
