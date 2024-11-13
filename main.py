import asyncio
import logging
import sys
# from asyncio import WindowsSelectorEventLoopPolicy

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import register_handlers
from database import init_db

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    init_db()
    register_handlers(dp)

    await dp.start_polling(bot)
    print('System ready')

if __name__ == '__main__':
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
