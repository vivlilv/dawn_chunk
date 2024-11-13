from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_menu_keyboard, cancel_keyboard
from database import add_proxies_to_user, delete_user_proxies

router = Router()

class AddProxiesStates(StatesGroup):
    waiting_for_proxies = State()

@router.callback_query(F.data == 'data_proxies')
async def add_proxies_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        "Пожалуйста, отправьте ваши прокси в формате:\nhttp://login:password@ip:port\nhttp://login:password@ip:port",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddProxiesStates.waiting_for_proxies)

@router.callback_query(AddProxiesStates.waiting_for_proxies, F.data == 'cancel')
async def cancel_add_proxies(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Добавление прокси отменено.")
    await state.clear()

@router.message(AddProxiesStates.waiting_for_proxies)
async def proxies_received(message: types.Message, state: FSMContext):
    proxies_text = message.text
    proxies_list = proxies_text.strip().split('\n')
    parsed_proxies = []
    for proxy in proxies_list:
        proxy = proxy.strip()
        if proxy.startswith('http://') or proxy.startswith('https://'):
            parsed_proxies.append(proxy)
        else:
            await message.answer(
                "Ошибка в формате прокси. Добавление прокси отменено."
            )
            await state.clear()
            return
    user_id = message.from_user.id
    delete_user_proxies(user_id)
    add_proxies_to_user(user_id, parsed_proxies)
    await message.answer(f"Прокси успешно добавлены: {len(parsed_proxies)}")
    await message.answer(
        "Выберите следующее действие:", reply_markup=main_menu_keyboard()
    )
    await state.clear()
