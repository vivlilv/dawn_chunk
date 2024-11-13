# account_manager.py
import asyncio
import string

from faker import Faker
from loguru import logger
from core.models.account import Account
from core.dawn_client import DawnClient
from core.captcha import CaptchaService
from core.utils.file_manager import str_to_file
from core.utils.proxy_manager import ProxyManager
from pyuseragents import random as random_useragent
import random

from database import update_account_points


class AccountManager:
    def __init__(self, threads, ref_codes, captcha_service, proxy_manager, user_id):
        self.user_id = user_id
        self.ref_codes = ref_codes + ['']
        self.threads = threads
        self.semaphore = asyncio.Semaphore(self.threads)
        self.fake = Faker()
        self.captcha_service = captcha_service
        self.should_stop = False
        self.proxy_manager = proxy_manager
        self.client = None

    async def register_account(self, email: str, email_password: str, password: str):
        async with self.semaphore:
            if self.should_stop:
                return
            proxy_url = await self.proxy_manager.get_proxy()
            try:
                username = self.fake.user_name()
                user_agent = random_useragent()
                ref_code = random.choice(self.ref_codes)
                account_details = {
                    'name': username,
                    'mail': email,
                    'mail_pass': email_password,
                    'referralCode': ref_code,
                    'user_agent': user_agent,
                    'proxy': proxy_url,
                }
                client = DawnClient(account_details, self.captcha_service)
                await client.full_registration()
                logger.info(f'Успешно зарегистрировано | {email}')
            except Exception as e:
                error_message = str(e)
                if "curl: (7)" in error_message:
                    logger.error(f'{email} | Proxy failed: {proxy_url} | {e}')
                    await self.proxy_manager.release_proxy(proxy_url)
                    return await self.register_account(email, password)
                logger.error(f'{email} | {e}')
            await self.proxy_manager.release_proxy(proxy_url)

    async def login_account(self, email: str, email_password: str, password: str):
        async with self.semaphore:
            if self.should_stop:
                return None
            proxy_url = await self.proxy_manager.get_proxy()
            user_agent = random_useragent()
            try:
                account_details = {
                    'name': ''.join(random.choices(string.ascii_lowercase, k=5)),
                    'mail': email,
                    'mail_pass': email_password,
                    'referralCode': '',
                    'user_agent': user_agent,
                    'proxy': proxy_url,
                }
                client = DawnClient(account_details, self.captcha_service)
                uid, access_token = await client.login(self.captcha_service)
                logger.info(f'Successfully logged in | {email}')
                account_data = Account(
                    email=email,
                    password=password,
                    uid=uid,
                    access_token=access_token,
                    user_agent=user_agent,
                    proxy_url=proxy_url
                )
                return account_data
            except Exception as e:
                error_message = str(e)
                if "curl: (7)" in error_message:
                    logger.error(f'{email} | Proxy failed: {proxy_url} | {e}')
                    await self.proxy_manager.release_proxy(proxy_url)
                    return await self.login_account(email, password)
                logger.error(f'{email} | {e}')
                return None

    async def mining_loop(self, account: Account):
        while not self.should_stop:
            logger.info(f"Starting mining for account {account}")
            await self.start_mining(account)
            await asyncio.sleep(3000)

    async def start_mining(self, account: Account):
        if self.should_stop:
            return

        async with self.semaphore:
            try:
                account_details = {
                    'name': ''.join(random.choices(string.ascii_lowercase, k=5)),
                    'mail': account.email,
                    'mail_pass': account.email_password,
                    'referralCode': '',
                    'user_agent': account.user_agent,
                    'proxy': account.proxy_url,
                }
                self.client = DawnClient(account_details, self.captcha_service)
                await self.client.main()

                await self.client.safe_close()
            except TokenError as e:
                if self.client:
                    await self.client.safe_close()
                logger.warning(f"Token error during mining for {account.email}: {e}")
                raise
            except Exception as e:
                if self.client:
                    await self.client.safe_close()
                logger.error(f'Mining error for {account.email}: {e}')
                raise

    async def stop(self):
        self.should_stop = True
        await self.client.stop_farming()


class TokenError(Exception):
    pass
