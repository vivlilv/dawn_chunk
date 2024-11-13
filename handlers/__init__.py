from aiogram import Dispatcher

from .start import router as start_router
from .captcha_api import router as captcha_api_router
from .add_accounts import router as add_accounts_router
from .add_proxies import router as add_proxies_router
from .register_accounts import router as register_accounts_router
from .start_stop_mining import router as start_stop_mining_router
from .data import router as data_router
from .actions import router as actions_router
from .my_accounts import router as my_accounts_router
from .web3_enjoyer import router as web3_enjoyer_router
from .subscription import router as subscription_router

def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(captcha_api_router)
    dp.include_router(add_accounts_router)
    dp.include_router(add_proxies_router)
    dp.include_router(register_accounts_router)
    dp.include_router(start_stop_mining_router)
    dp.include_router(data_router)
    dp.include_router(actions_router)
    dp.include_router(my_accounts_router)
    dp.include_router(web3_enjoyer_router)
    dp.include_router(subscription_router)
