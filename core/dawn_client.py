import time
import uuid
import random
import warnings
import asyncio
from datetime import datetime

import httpx
from loguru import logger
from curl_cffi.requests import AsyncSession
from tenacity import retry, stop_after_attempt, wait_fixed

from core.mail import get_verification_link

# Suppress the specific warning
warnings.filterwarnings("ignore", category=UserWarning, message="Curlm already closed!")

exp_token = '2056b72d0eb33beb2a6d2d39c67296afa677fc1f271efaf0d84b5d50cd08aee410c07f2f8a6510b58ab067551517964a9b712a207a15ea4f311b2b0364b0fd4be4b73a16b0be5708eaea1eeecc896238091f290f0f7a173e8a665a8cda3fe8625e6669adee14f08415335e123bac05218478fd5bfaf8810145bd97daf7c53b5039db2dd60cfd0de17ab9bd349623887c02a7789691d1c1fd02de15b2d9061b55c82233432f43b08ee746286fcc9515a18adfc9193e433d8c56c867a3e8a54ade18f11660f597e5fa46099ca5f2cc5f59356039379db30f6dc8af5c355ab82406c41fba212b6b3cc3eb36759c84491347'

class DawnClient:
    def __init__(self, account_details, captcha_service) -> None:
        self.account_details = account_details
        self.session = httpx.AsyncClient(http2=True, proxy=self.account_details['proxy'], verify=False)
        self.captcha_service = captcha_service

    async def set_session(self):
        self.session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.account_details['user_agent']
        })

    # CAPTCHa solving(2)
    async def get_puzzle(self):
        url = "https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle"
        response = await self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('puzzle_id')

    async def get_puzzle_base_64(self, puzzle_id):
        url = f"https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image?puzzle_id={puzzle_id}"
        response = await self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('imgBase64')

    # Registration and logging(4)
    async def register_user(self, puzzle_id, solution):
        url = "https://www.aeropres.in/chromeapi/dawn/v1/puzzle/validate-register"
        registration_data = {
            "ans": solution,
            "country": "+91",
            "firstname": self.account_details['name'],
            "lastname": self.account_details['name'],
            "email": self.account_details['mail'],
            "password": self.account_details['mail_pass'],
            "puzzle_id": puzzle_id,
            "mobile": "",
            "referralCode": ""
        }

        response = await self.session.post(url, json=registration_data)

        if response.status_code == 200:
            return 200
        else:
            print(response.text)
            return 400

    async def verify_mail(self):
        try:
            for i in range(5):
                link = get_verification_link(username=self.account_details['mail'],
                                             password=self.account_details['mail_pass'])
                print(link)
                if link[:5] == 'https':
                    break

            self.session.headers.update({
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "priority": "u=0, i",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Linux\"",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": self.account_details['user_agent']
            })
            response = await self.session.get(link)
            # print(response)
        except:
            print('email retrieving error...')

    async def login(self, puzzle_id, solution):
        self.session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.account_details['user_agent']
        })

        login_data = {
            "username": self.account_details['mail'],
            "password": self.account_details['mail_pass'],
            "logindata": {
                "_v": "1.0.7",
                "datetime": str(datetime.utcnow().isoformat(timespec='milliseconds') + 'Z')
            },
            "puzzle_id": puzzle_id,
            "ans": solution
        }
        status = None
        for i in range(2):
            if status != '200':
                try:
                    response = await self.session.post(url="https://www.aeropres.in/chromeapi/dawn/v1/user/login/v2",
                                                       json=login_data)
                    print(response.json())
                    if response.json()['message'] == 'Successfully logged in!':
                        status = '200'
                except:
                    await asyncio.sleep(5)
        return response.json()['data']['token']

    async def logout(self):
        try:
            await self.get_user_referral_points(token=exp_token)
            await self.keep_alive(token=exp_token)
            print("logged out")
        except:
            print('error logging out (server error 502)...retrying after 15s')

    # Farming
    async def get_user_referral_points(self, token):
        url = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
        self.session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Berear {token}",
            "content-type": "application/json",
            "if-none-match": "W/\"336-jMb+AmW+rUVEfl0AseCEvUmbrVc\"",
            "origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.account_details['user_agent']
        })

        response = await self.session.get(url)
        print(response.json()['data']['rewardPoint']['points'])
        return response.json()

    async def keep_alive(self, token):
        url = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"
        self.session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Berear {token}",
            "content-type": "application/json",
            "origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
            "priority": "u=1, i",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.account_details['user_agent']
        })

        body = {
            "username": self.account_details['name'],
            "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
            "numberoftabs": 0,
            "_v": "1.0.7",
        }

        response = await self.session.post(url, json=body)
        return response.status_code

    # MAIN WORKFLOW FUNCTIONS
    async def full_registration(self):
        for i in range(10):  # max retries
            try:
                await self.set_session()
                puzzle_id = await self.get_puzzle()
                img_base_64 = await self.get_puzzle_base_64(puzzle_id)
                solution = self.captcha_service.get_captcha_token(img_base_64)
                await asyncio.sleep(5)
                response = await self.register_user(puzzle_id, solution)
                print(response)
                if response == 200:
                    await self.verify_mail()  # add try except within function
                    print('success')
                    return 200
            except Exception as e:
                print(f'{i + 1}Error in registration: {e}')

    async def start_farming(self):
        for i in range(10):  # max retries
            try:
                puzzle_id = await self.get_puzzle()
                img_base_64 = await self.get_puzzle_base_64(puzzle_id)
                solution = self.captcha_service.get_captcha_token(img_base_64)
                await asyncio.sleep(10)
                token = await self.login(puzzle_id=puzzle_id, solution=solution)
                if len(token) > 3 and token[:3] == '205':  # valid token
                    break
            except:
                print(f"error logging in...{self.account_details['name']}")
        print(token)
        self.status = 'active'
        while self.status == 'active':
            try:
                await self.get_user_referral_points(token)
                for i in range(5):
                    status = await self.keep_alive(token)
                    print(status)
                    await asyncio.sleep(10)
                    if status == 200:
                        break
            finally:
                print('sleeing 30s')
                await asyncio.sleep(30)

    async def stop_farming(self):
        self.status = 'sleep'

    async def main(self):
        await self.set_session()
        # await self.full_registration()
        await self.start_farming()

    async def safe_close(self):
        try:
            if self.session:
                await asyncio.shield(self.session.aclose())
        except Exception as e:
            logger.error(f'Error closing session: {e}')
        finally:
            self.session = None