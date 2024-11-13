from aiogram import Router, types, F
from config import CHANNEL_ID

router = Router()

@router.message(F.text == "Web3 Enjoyer")
async def web3_enjoyer(message: types.Message):
    await message.answer(f"https://t.me/{CHANNEL_ID.lstrip('@')}")
