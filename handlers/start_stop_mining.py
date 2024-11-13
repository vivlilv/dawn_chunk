from aiogram import Router, types, F, Bot
from database import (
    get_user_accounts,
    get_user_proxies,
    get_user_captcha_service_and_key,
    get_user_subscription_status,
    update_user_subscription
)
from keyboards import main_menu_keyboard
from BotManager import BotManager
from config import CHANNEL_ID
from shared import user_bot_managers, user_tasks
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from datetime import datetime, timedelta, timezone
import uuid
import requests
import os
import base64
import hashlib
import aiohttp
import json
import pytz

router = Router()

async def is_subscribed(bot: Bot, channel_username, user_id):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        if member.status.lower() in ["member", "administrator", "creator"]:
            return True
    except Exception:
        return False

async def make_cryptomus_request(url: str, payment_data: dict):
    try:
        # Ensure amount is string
        if 'amount' in payment_data:
            payment_data['amount'] = str(payment_data['amount'])
        
        # Convert to JSON and encode
        payload = json.dumps(payment_data)
        encoded_data = base64.b64encode(payload.encode("utf-8")).decode("utf-8")
        
        # Generate signature
        merchant_key = os.getenv('PAYMENT_KEY')
        signature = hashlib.md5(
            f"{encoded_data}{merchant_key}".encode("utf-8")
        ).hexdigest()
        
        headers = {
            "merchant": os.getenv("MERCHANT_UUID"),
            "sign": signature,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=payment_data, headers=headers) as response:
                response_text = await response.text()
                print(f"Response Status: {response.status}")
                print(f"Response Text: {response_text}")
                
                if not response.ok:
                    raise ValueError(f"Payment API error: {response.status} - {response_text}")
                return await response.json()
                
    except Exception as e:
        print(f"Error in make_cryptomus_request: {str(e)}")
        raise

async def check_payment_status(payment_uuid: str, user_id: int, duration_days: int, message: types.Message):
    while True:
        try:
            payment_data = await make_cryptomus_request(
                url="https://api.cryptomus.com/v1/payment/info",
                payment_data={"uuid": payment_uuid}
            )

            if payment_data['result']['payment_status'] in ('paid', 'paid_over'):
                # Update subscription
                new_expiry = datetime.now() + timedelta(days=duration_days)
                update_user_subscription(user_id, new_expiry)
                await message.answer("Payment completed! Your subscription has been activated.")
                return
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error checking payment status: {e}")
            await asyncio.sleep(5)

@router.callback_query(F.data == 'action_mining')
async def start_stop_mining(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id

    if user_id in user_tasks:
        bot_manager = user_bot_managers[user_id]
        await bot_manager.stop()
        task = user_tasks[user_id]
        task.cancel()
        del user_tasks[user_id]
        del user_bot_managers[user_id]
        await callback_query.message.answer("Фарминг остановлен.")
    else:
        subscribed = await is_subscribed(bot, CHANNEL_ID, user_id)

        if not subscribed:
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="Yes", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"
                ),
                types.InlineKeyboardButton(
                    text="No", callback_data="no_subscribe"
                )
            )
            await callback_query.message.answer(
                "Do you want to subscribe to Web3 Enjoyer Club?",
                reply_markup=builder.as_markup()
            )
            return

        accounts = get_user_accounts(user_id)
        proxies = get_user_proxies(user_id)
        captcha_service, captcha_api_key = get_user_captcha_service_and_key(user_id)

        if not accounts:
            await callback_query.message.answer(
                "У вас нет добавленных аккаунтов. Пожалуйста, добавьте аккаунты сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if not proxies:
            await callback_query.message.answer(
                "У вас нет добавленных прокси. Пожалуйста, добавьте прокси сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if len(proxies) < len(accounts):
            await callback_query.message.answer(
                "Количество прокси меньше количества аккаунтов. Пожалуйста, добавьте больше прокси."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if not captcha_service or not captcha_api_key:
            await callback_query.message.answer(
                "Не указан сервис капчи или API ключ. Пожалуйста, установите их сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if len(accounts) > 1:
            has_subscription = await check_user_subscription(user_id)
            if not has_subscription:
                builder = InlineKeyboardBuilder()
                builder.row(
                    types.InlineKeyboardButton(text="1 Month ($0.1)", callback_data="pay_1month"),
                    types.InlineKeyboardButton(text="3 Months ($0.12)", callback_data="pay_3months"),
                    types.InlineKeyboardButton(text="6 Months ($0.13)", callback_data="pay_6months")
                )
                await callback_query.message.answer(
                    "You need an active subscription to farm with multiple accounts. Please choose a plan:",
                    reply_markup=builder.as_markup()
                )
                return

        bot_manager = BotManager(
            accounts, proxies, captcha_service, captcha_api_key, user_id
        )
        user_bot_managers[user_id] = bot_manager
        task = asyncio.create_task(bot_manager.start_mining())
        user_tasks[user_id] = task
        await callback_query.message.answer("Фарминг запущен.")

    await callback_query.message.answer(
        "Выберите следующее действие:", reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "no_subscribe")
async def process_no_subscribe(callback_query: types.CallbackQuery):
    await callback_query.answer("Wrong answer. Try again.", show_alert=True)

@router.callback_query(F.data.startswith('pay_'))
async def handle_payment(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        duration = callback_query.data.replace('pay_', '')
        
        prices = {
            '1month': 0.1,
            '3months': 0.12,
            '6months': 0.13
        }
        duration_days = {
            '1month': 30,
            '3months': 90,
            '6months': 180
        }
        
        timestamp = str(int(datetime.now().timestamp()))[-6:]
        short_uuid = str(uuid.uuid4()).replace('-', '')[:4]
        duration_short = duration.replace('month', 'm')
        order_id = f"u{user_id}_{duration_short}_{timestamp}{short_uuid}"
        
        # Minimal required payment data according to Cryptomus docs
        payment_data = {
            'amount': "{:.2f}".format(prices[duration]),
            'currency': 'USD',
            'order_id': order_id,
            'in_currencies': [
                {'currency': 'USDT', 'network': 'ETH'},
                {'currency': 'USDT', 'network': 'BNB'},
                {'currency': 'USDT', 'network': 'MATIC'},
                {'currency': 'USDT', 'network': 'ARBITRUM'},
                {'currency': 'USDT', 'network': 'OPTIMISM'},
                {'currency': 'USDT', 'network': 'AVAXC'},
                {'currency': 'USDT', 'network': 'FTM'},
                {'currency': 'USDT', 'network': 'BASE'},
                {'currency': 'BTC', 'network': 'BTC'},
                {'currency': 'ETH', 'network': 'ETH'},
                {'currency': 'BNB', 'network': 'BNB'},
                {'currency': 'MATIC', 'network': 'MATIC'},]
        }
        
        await callback_query.message.answer("Processing payment request...")
        
        payment_response = await make_cryptomus_request(
            url="https://api.cryptomus.com/v1/payment",
            payment_data=payment_data
        )
        
        payment_url = payment_response['result']['url']
        payment_uuid = payment_response['result']['uuid']
        
        # Start payment status checking task
        asyncio.create_task(
            check_payment_status(
                payment_uuid,
                user_id,
                duration_days[duration],#
                callback_query.message
            )
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Pay Now", url=payment_url))
        await callback_query.message.answer(
            f"Please complete the payment for {duration} subscription. "
            "The system will automatically check your payment status.",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await callback_query.message.answer(
            f"Sorry, there was an error processing your payment: {str(e)}"
        )



async def check_user_subscription(user_id: int) -> bool:
    try:
        payment_data = {
            'status': 'paid',
            'is_final': True
        }
        
        response = await make_cryptomus_request(
            url="https://api.cryptomus.com/v1/payment/list",
            payment_data=payment_data
        )
        
        items = response.get('result', {}).get('items', [])
        if not items:
            return False
            
        current_time = datetime.now(pytz.UTC)
        user_prefix = f"user_{user_id}_"
        
        # Check each payment to find valid subscriptions
        for payment in items:
            order_id = payment.get('order_id', '')
            if not order_id.startswith(user_prefix):
                continue
                
            payment_date = datetime.fromisoformat(payment['created_at'].replace('Z', '+00:00'))
            
            # Get duration from payment amount
            amount = float(payment['amount'])
            if amount >= 0.13:  # 6 months
                duration_days = 180
            elif amount >= 0.12:  # 3 months
                duration_days = 90
            elif amount >= 0.1:  # 1 month
                duration_days = 30
            else:
                continue
                
            expiry_date = payment_date + timedelta(days=duration_days)
            if expiry_date > current_time:
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking Cryptomus subscription: {e}")
        return False