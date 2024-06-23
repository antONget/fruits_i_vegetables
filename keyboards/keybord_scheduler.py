from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging


def keyboards_confirm_pay(id_anketa: int) -> InlineKeyboardMarkup:
    logging.info(f'keyboards_confirm_pay')
    button_1 = InlineKeyboardButton(text='Подтвердить', callback_data=f'schconfirm_pay_{id_anketa}')
    button_2 = InlineKeyboardButton(text='Отмена', callback_data=f'schcancel_pay_{id_anketa}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]], )
    return keyboard