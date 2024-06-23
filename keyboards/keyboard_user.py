from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import logging


def keyboards_get_contact() -> ReplyKeyboardMarkup:
    logging.info("keyboards_get_contact")
    button_1 = KeyboardButton(text='Отправить свой контакт ☎️',
                              request_contact=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_1]],
        resize_keyboard=True
    )
    return keyboard


def keyboard_confirm_phone():
    logging.info(f'keyboard_confirm_phone')
    button_1 = InlineKeyboardButton(text='Изменить телефон', callback_data='edit_phone')
    button_2 = InlineKeyboardButton(text='Продолжить', callback_data='continue_user')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboards_main_menu(basket: int = 0):
    button_1 = KeyboardButton(text='Фрукты  🍊🍎🍐')
    button_2 = KeyboardButton(text='Овощи 🍆🥕🥔')
    button_3 = KeyboardButton(text='Ягоды 🍓🍒🫐')
    button_4 = KeyboardButton(text='Зелень 🌿')
    button_5 = KeyboardButton(text='📋 Наши цены')
    button_6 = KeyboardButton(text=f'🛒 Корзина {basket} руб.')
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_1, button_2], [button_3, button_4], [button_5], [button_6]],
        resize_keyboard=True
    )
    return keyboard


def keyboards_list_product(list_product: list):
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for row in list_product:
        text = row
        button = f'product_{row}'
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=button))
    kb_builder.row(*buttons, width=3)
    return kb_builder.as_markup()


def keyboards_get_count(id_product: int, count_item: int = 0):
    """
    Клавиатура ввода количества кг товара
    :param id_product:
    :param count_item:
    :return:
    """
    logging.info(f'keyboards_get_count')
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for row in range(1, 10):
        text = str(row)
        button = f'digit_{row}_{id_product}'
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=button))
    buttons.append(InlineKeyboardButton(
        text='Очистить ❌',
        callback_data=f'digit_c_{id_product}'))
    buttons.append(InlineKeyboardButton(
        text='0',
        callback_data=f'digit_0_{id_product}'))
    buttons.append(InlineKeyboardButton(
        text=',',
        callback_data=f'digit_#_{id_product}'))
    buttons.append(InlineKeyboardButton(
        text='Готово',
        callback_data=f'count_{count_item}_{id_product}'))
    kb_builder.row(*buttons, width=3)
    return kb_builder.as_markup()


def keyboard_create_item(id_product: int, count_item: int):
    logging.info(f'keyboard_create_item')
    button_1 = InlineKeyboardButton(text='Добавить в корзину', callback_data=f'add_item/{id_product}/{count_item}')
    button_2 = InlineKeyboardButton(text='Оформить заказ', callback_data=f'place_an_order/{id_product}/{count_item}')
    button_3 = InlineKeyboardButton(text='Отменить', callback_data=f'add_item/cancel')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2], [button_3]])
    return keyboard


def keyboard_confirm_order(id_order: str):
    logging.info(f'keyboard_confirm_order')
    button_1 = InlineKeyboardButton(text='Изменить', callback_data=f'change#{id_order}')
    button_2 = InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm#{id_order}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboard_delivery():
    logging.info(f'keyboard_delivery')
    button_1 = InlineKeyboardButton(text='Доставка', callback_data=f'delivery')
    button_2 = InlineKeyboardButton(text='Самовывоз', callback_data=f'pickup')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboard_confirm_address():
    logging.info(f'keyboard_confirm_address')
    button_1 = InlineKeyboardButton(text='Да, все верно', callback_data=f'address_ok')
    button_2 = InlineKeyboardButton(text='Исправить', callback_data=f'address_change')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboard_finish_order_d():
    logging.info(f'keyboard_finish_order')
    button_1 = InlineKeyboardButton(text='Да, все верно', callback_data=f'finishd_ok')
    button_2 = InlineKeyboardButton(text='Отмена', callback_data=f'finishd_cancel')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboard_finish_order_p():
    logging.info(f'keyboard_finish_order')
    button_1 = InlineKeyboardButton(text='Да, все верно', callback_data=f'finishp_ok')
    button_2 = InlineKeyboardButton(text='Отмена', callback_data=f'finishp_cancel')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard