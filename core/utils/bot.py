# bot.py
import asyncio
from typing import List
from loguru import logger
import random
from core.utils import proxy_manager
from core.utils.account_manager import AccountManager
from core.captcha import CaptchaService
from core.utils.file_manager import file_to_list
from core.utils.proxy_manager import ProxyManager

class Bot:
    def __init__(self, account_path, proxy_path, threads, ref_codes, captcha_service):
        self.threads = threads
        self.ref_codes = ref_codes
        self.captcha_service = captcha_service
        self.account_manager = AccountManager(threads, ref_codes, captcha_service)
        self.should_stop = False
        self.proxy_manager = ProxyManager()

        self.accounts: List[str] = file_to_list(account_path)
        logger.success(f'Found {len(self.accounts)} accounts')
        self.proxy_manager.load_proxy(proxy_path)
        logger.success(f'Found {len(self.proxy_manager.proxies)} proxies')

    async def auth_accounts(self):
        accounts = []
        try:
            tasks = [
                self.account_manager.login_account(*account.split(':', 1))
                for account in self.accounts
            ]
            results = await asyncio.gather(*tasks)
            accounts = [account for account in results if account is not None]
        except Exception as e:
            logger.error(f'Ошибка при авторизации: {e}')
        return accounts

    def stop(self):
        self.should_stop = True
        self.account_manager.stop()

    async def start_registration(self):
        tasks = []

        try:
            for account in self.accounts:
                if not self.should_stop:
                    tasks.append(asyncio.create_task(self.account_manager.register_account(*account.split(':', 1))))

            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f'Ошибка регистрации аккаунтов: {e}')

    async def start_mining(self):
        accounts = await self.auth_accounts()
        active_tasks = {}
        try:
            while not self.should_stop:
                for account in accounts:
                    account_key = f"{account.uid}"
                    if account_key not in active_tasks or active_tasks[account_key].done():
                        active_tasks[account_key] = asyncio.create_task(
                            self.account_manager.mining_loop(account)
                        )
                active_tasks = {k: v for k, v in active_tasks.items() if not v.done()}
                await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"An error occurred during mining: {e}")
        finally:
            await asyncio.gather(*active_tasks.values(), return_exceptions=True)
            logger.info("All mining tasks completed or cleaned up.")
