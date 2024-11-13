import captchatools
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import captcha_services_keyboard, main_menu_keyboard
from database import update_user_captcha_service, update_user_captcha_api_key
from aiogram.types import CallbackQuery

router = Router()

class CaptchaAPIStates(StatesGroup):
    waiting_for_service = State()
    waiting_for_api_key = State()

@router.callback_query(F.data == 'set_captcha_api')
async def captcha_api_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Пожалуйста, выберите сервис капчи:",
        reply_markup=captcha_services_keyboard()
    )
    await state.set_state(CaptchaAPIStates.waiting_for_service)

@router.callback_query(CaptchaAPIStates.waiting_for_service, F.data.func(lambda data: data.startswith('captcha_service_')))
async def captcha_service_chosen(callback_query: CallbackQuery, state: FSMContext):
    service = callback_query.data.split('_', 2)[2]
    await state.update_data(captcha_service=service)
    await callback_query.message.answer("Пожалуйста, отправьте API ключ:")
    await state.set_state(CaptchaAPIStates.waiting_for_api_key)

@router.message(CaptchaAPIStates.waiting_for_api_key)
async def captcha_api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    captcha_service = data.get('captcha_service')
    api_key = message.text
    user_id = message.from_user.id

    try:
        solver = captchatools.new_harvester(**{'solving_site': captcha_service.lower(), 'api_key': api_key})

        update_user_captcha_service(user_id, captcha_service)
        update_user_captcha_api_key(user_id, api_key)

        await message.answer(
            f"API ключ успешно обновлён \n\nВаш новый API ключ: {api_key}\nБаланс: {solver.get_balance()}"
        )
        await message.answer(
            "Выберите следующее действие:", reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        await message.answer(
            "Неверный API key", reply_markup=main_menu_keyboard()
        )
    await state.clear()
