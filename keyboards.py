from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Data"), KeyboardButton(text="My accounts")],
            [KeyboardButton(text="Actions"), KeyboardButton(text="Web3 Enjoyer")]
        ],
        resize_keyboard=True
    )
    return keyboard

def data_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Accounts", callback_data="data_accounts")],
        [InlineKeyboardButton(text="Proxies", callback_data="data_proxies")],
        [InlineKeyboardButton(text="Captcha", callback_data="data_captcha")]
    ])
    return keyboard

def actions_inline_keyboard(mining_started=False):
    mining_text = "Stop mining" if mining_started else "Start mining"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Registration", callback_data="action_registration")],
        [InlineKeyboardButton(text=mining_text, callback_data="action_mining")]
    ])
    return keyboard

def captcha_services_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="2captcha", callback_data="captcha_service_2captcha"),
            InlineKeyboardButton(text="anticaptcha", callback_data="captcha_service_anticaptcha")
        ],
        [
            InlineKeyboardButton(text="capmonster", callback_data="captcha_service_capmonster"),
            InlineKeyboardButton(text="capsolver", callback_data="captcha_service_capsolver")
        ],
        [InlineKeyboardButton(text="captchaai", callback_data="captcha_service_captchaai")]
    ])
    return keyboard

def channel_link_keyboard(channel_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Web3 Enjoyer Channel", url=f"https://t.me/{channel_id.lstrip('@')}")]
    ])
    return keyboard

def cancel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
    ])
    return keyboard
