from aiogram import Router, types, F

router = Router()

@router.callback_query(F.data == "no_subscribe")
async def process_no_subscribe(callback_query: types.CallbackQuery):
    await callback_query.answer("Wrong answer. Try again.", show_alert=True)
