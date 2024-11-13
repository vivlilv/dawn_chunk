from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from keyboards import data_inline_keyboard, captcha_services_keyboard
from handlers.captcha_api import CaptchaAPIStates
from handlers.add_accounts import AddAccountsStates
from handlers.add_proxies import AddProxiesStates

router = Router()

@router.message(F.text == "Data")
async def data_menu(message: types.Message):
    await message.answer("Select registration item:", reply_markup=data_inline_keyboard())

@router.callback_query(F.data == "data_accounts")
async def data_accounts(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        "Пожалуйста, отправьте ваши аккаунты в формате:\nemail:password\nemail:password\nemail:password"
    )
    await state.set_state(AddAccountsStates.waiting_for_accounts)

@router.callback_query(F.data == "data_proxies")
async def data_proxies(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        "Пожалуйста, отправьте ваши прокси в формате:\nhttp://login:password@ip:port\nhttp://login:password@ip:port"
    )
    await state.set_state(AddProxiesStates.waiting_for_proxies)

@router.callback_query(F.data == "data_captcha")
async def data_captcha(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        "Пожалуйста, выберите сервис капчи:", reply_markup=captcha_services_keyboard()
    )
    await state.set_state(CaptchaAPIStates.waiting_for_service)
