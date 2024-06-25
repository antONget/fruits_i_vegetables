import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, LinkPreviewOptions
from aiogram.filters import CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


from config_data.config import Config, load_config
from database.requests import get_user_info, add_user, update_name_phone, get_list_product, \
    get_product, get_title, get_info_product, add_order, get_all_order_id, add_item, get_all_item_id, update_status,\
    OrderStatus, update_address, get_info_item, delete_item, get_info_order, update_amount, update_comment
from keyboards.keyboard_user import keyboards_get_contact, keyboard_confirm_phone, keyboards_main_menu,\
    keyboards_list_product, keyboards_get_count, keyboard_create_item, keyboard_confirm_order, keyboard_delivery, \
    keyboard_confirm_address, keyboard_finish_order_p, keyboard_finish_order_d, keyboards_list_item_change, \
    keyboard_change_item, keyboard_comment, keyboard_change_status
from services.get_exel import list_price_to_exel
from datetime import datetime


import logging
import re

router = Router()
config: Config = load_config()


class User(StatesGroup):
    name = State()
    phone = State()
    address = State()
    comment = State()
    amount = State()


user_dict = {}


def validate_russian_phone_number(phone_number):
    # Паттерн для российских номеров телефона
    # Российские номера могут начинаться с +7, 8, или без кода страны
    pattern = re.compile(r'^(\+7|8|7)?(\d{10})$')

    # Проверка соответствия паттерну
    match = pattern.match(phone_number)

    return bool(match)


@router.message(CommandStart())
async def process_start_command_user(message: Message, state: FSMContext) -> None:
    logging.info("process_start_command_user")
    await state.set_state(default_state)
    user = await get_user_info(tg_id=message.chat.id)
    if not user:
        await message.answer(text='Как вас зовут?')
        await state.set_state(User.name)
    else:
        await message.answer(text=f'{user.name}, рады видеть вас снова!\n'
                                  f'телефон: {user.phone}',
                             reply_markup=keyboard_confirm_phone())


@router.message(F.text, StateFilter(User.name))
async def get_name_user(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer(text='Укажите ваш номер телефона или нажмите внизу 👇\n'
                              '"Отправить свой контакт ☎️"',
                         reply_markup=keyboards_get_contact())
    await state.set_state(User.phone)


@router.callback_query(F.data == 'edit_phone')
async def press_button_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    logging.info(f'press_button_edit_phone: {callback.message.chat.id}')
    await callback.message.answer(text='Укажи свой телефон',
                                  reply_markup=keyboards_get_contact())
    await state.set_state(User.phone)


@router.callback_query(F.data == 'continue_user')
async def press_button_continue_user(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    logging.info(f'press_button_continue_user: {callback.message.chat.id}')
    await callback.answer()
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except:
        pass
    await callback.message.answer(text='Для онлайн-заказа выберите нужный раздел. Если вы не завершили предыдущий '
                                       'заказ, обратите внимание на корзину.',
                                  reply_markup=keyboards_main_menu())
    await state.set_state(default_state)


@router.message(StateFilter(User.phone))
async def get_phone_user(message: Message, state: FSMContext) -> None:
    logging.info(f'get_phone_user: {message.chat.id}')
    if message.contact:
        phone = str(message.contact.phone_number)
    else:
        phone = message.text
        if not validate_russian_phone_number(phone):
            await message.answer(text="Неверный формат номера, повторите ввод.")
            return
    await state.update_data(phone=phone)
    user_dict[message.chat.id] = await state.get_data()
    user = await get_user_info(tg_id=message.chat.id)
    if not user:
        if message.from_user.username:
            await add_user(
                {"id": message.from_user.id,
                 "username": message.from_user.username,
                 "name": user_dict[message.chat.id]['name'],
                 "phone": user_dict[message.chat.id]['phone']})
        else:
            await update_name_phone(tg_id=message.chat.id,
                                    name=user_dict[message.chat.id]['name'],
                                    phone=user_dict[message.chat.id]['phone'])
    # получаем все заказы пользователя
    all_order_id = await get_all_order_id(tg_id=message.chat.id)
    # создаем новый заказ если у пользователя их нет или все завершены
    if not all_order_id or all_order_id[-1].status in ['complete', 'payed', 'cancelled']:
        count_basket = 0
    elif all_order_id[-1].status == 'complete':
        count_basket = 0
    else:
        all_item_id = await get_all_item_id(tg_id=message.chat.id)
        all_order_id = await get_all_order_id(tg_id=message.chat.id)
        count_basket = 0
        for item in all_item_id:
            if item.id_order == all_order_id[-1].id_order:
                count_basket += item.count * item.price
    await message.answer(text=f'Друзья, всем доброго времени суток, рады вас видеть в нашем оптовом маркете.'
                              f' Здесь вы можете выбрать самые свежие и вкусные фрукты и овощи и заказать'
                              f' их доставку или самовывоз!\n'
                              f'Минимальная сумма заказа 5000 руб.\n'
                              f'График работы: 10:00-22:00 без перерывов и выходных\n\n'
                              f'Если меню свернется то вы всегда его сможете развернуть нажав на квадратик с точками'
                              f' в нижней правой части',
                         reply_markup=keyboards_main_menu(basket=count_basket))
    await state.set_state(default_state)


@router.message(F.text == '📋 Наши цены')
async def press_button_home(message: Message):
    logging.info(f'press_button_home: {message.chat.id}')
    current_date = datetime.now()
    current_date_string = current_date.strftime('%d/%m/%Y')
    text = f'<b>Актуальный список цена на {current_date_string}:</b>\n\n'
    for category in ['Фрукты', 'Овощи', 'Ягоды', 'Зелень']:
        list_price = await get_list_product(category=category)
        text += f'<i><u>{category}</u></i>:\n'
        i = 0
        for item in list_price:
            i += 1
            text += f'{i}. {item.title} - {item.price} руб/кг.\n'
    await message.answer(text=text,
                         parse_mode='html')
    await list_price_to_exel()
    file_path = "list_price.xlsx"
    await message.answer_document(FSInputFile(file_path))


@router.message(F.text == 'Фрукты  🍊🍎🍐')
async def press_button_fruits(message: Message):
    logging.info(f'press_button_fruits: {message.chat.id}')
    price_list_model = await get_list_product(category='Фрукты')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=keyboards_list_product(list_product=list_product))


@router.message(F.text == 'Овощи 🍆🥕🥔')
async def press_button_vegetation(message: Message):
    logging.info(f'press_button_vegetation: {message.chat.id}')
    price_list_model = await get_list_product(category='Овощи')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=keyboards_list_product(list_product=list_product))


@router.message(F.text == 'Зелень 🌿')
async def press_button_green(message: Message):
    logging.info(f'press_button_green: {message.chat.id}')
    price_list_model = await get_list_product(category='Зелень')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=keyboards_list_product(list_product=list_product))


@router.message(F.text == 'Ягоды 🍓🍒🫐')
async def press_button_berry(message: Message):
    logging.info(f'press_button_berry: {message.chat.id}')
    price_list_model = await get_list_product(category='Ягоды')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=keyboards_list_product(list_product=list_product))


@router.message(F.text.startswith('🛒 Корзина'))
async def press_button_basket(message: Message):
    logging.info(f'press_button_berry: {message.chat.id}')
    all_order_id = await get_all_order_id(tg_id=message.chat.id)
    all_item_id = await get_all_item_id(tg_id=message.chat.id)
    if not all_order_id or all_order_id[-1].status in ['complete', 'payed', 'cancelled']:
        await message.answer('В вашей корзине нет товаров!')
    else:
        text = 'Ваш заказ:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == all_order_id[-1].id_order:
                i += 1
                if item.count % 10:
                    count = item.count / 10
                else:
                    count = int(item.count // 10)
                if (item.price * item.count) % 10:
                    amount = item.price * count
                else:
                    amount = int(item.price * count)
                text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
                total += amount
        text += f'\nИтого: {total} руб.'
        await message.answer(text=text,
                             reply_markup=keyboard_confirm_order(id_order=all_order_id[-1].id_order))


@router.message(F.text.startswith('📍 Наши контакты'))
async def press_button_contact(message: Message):
    logging.info(f'press_button_contact: {message.chat.id}')
    media = []
    image_1 = 'AgACAgIAAxkBAAOpZnmbimV6FaiEk3AICkRs9Mzy_EcAAgLhMRtI39FLSsPzkuwcoccBAAMCAAN4AAM1BA'
    image_2 = 'AgACAgIAAxkBAAOqZnmcQJGncc-rD3T37wsaBvGPs-4AAgjhMRtI39FLFtmbrG3_dy4BAAMCAAN5AAM1BA'
    media.append(InputMediaPhoto(media=image_1,
                                 caption='<b>Наш адрес: проспект Непокорённых, 63к13с2 - отдел овощей и фруктов</b>\n'
                                         '<a href="https://yandex.ru/maps/-/CDvd5Jy7">построить маршрут</a>\n\n'
                                         'Вы можете забрать заказ самостоятельно или заказать доставку.\n'
                                         '<u>Условия доставки:</u> доставка в пределах КАД бесплатно. '
                                         'Если сделаете заказ до 13.00, то доставим в этот же день!\n'
                                         'Контакт для связи: <a href="https://t.me/el_rstmv">@el_rstmv</a>\n',
                                 parse_mode='html',
                                 link_preview_options=LinkPreviewOptions(is_disabled=True)))
    media.append(InputMediaPhoto(media=image_2))
    await message.answer_media_group(media=media)


@router.callback_query(F.data.startswith('product'))
async def get_title_product(callback: CallbackQuery, state: FSMContext):
    logging.info(f'get_title_product: {callback.message.chat.id}')
    await callback.answer()
    product = callback.data.split('_')[1]
    # print(product)
    price_list_model = await get_product(product=product)
    # print(len(price_list_model))
    if len(price_list_model) == 1:
        # print(price_list_model)
        price_list_title = await get_title(title=price_list_model[0].title)
        # print(price_list_title)
        await state.update_data(count_item=0)
        await state.update_data(comma=0)
        if 'шт' in price_list_title.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {price_list_title.title}\n'
                                              f'Стоимость: {price_list_title.price} руб.\n\n'
                                              f'Количество: 0 {e}.',
                                         reply_markup=keyboards_get_count(id_product=price_list_title.id))
    elif len(price_list_model) == 0:
        # print(price_list_model)
        price_list_title = await get_title(title=product)
        # print(price_list_title)
        await state.update_data(count_item=0)
        await state.update_data(comma=0)
        if 'шт' in price_list_title.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {price_list_title.title}\n'
                                              f'Стоимость: {price_list_title.price} руб.\n\n'
                                              f'Количество: 0 {e}.',
                                         reply_markup=keyboards_get_count(id_product=price_list_title.id))
    else:
        title = []
        for item in price_list_model:
            title.append(item.title)
        await callback.message.edit_text(text=f'Выберите товар:',
                                         reply_markup=keyboards_list_product(list_product=title))


@router.callback_query(F.data.startswith('digit_'))
async def process_count_product(callback: CallbackQuery, state: FSMContext):
    """
    Формируем количество товара
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'get_count_product: {callback.message.chat.id}')
    await callback.answer()
    input_user = callback.data.split('_')
    # нажатая кнопка
    digit = input_user[1]
    # если нажатая кнопка цифра
    if digit.isdigit():
        user_dict[callback.message.chat.id] = await state.get_data()
        # если запятая не нажата
        if user_dict[callback.message.chat.id]['comma'] == 0:
            # формируем новое число путем добавления в конце строки
            count_item = int(str(user_dict[callback.message.chat.id]['count_item']) + str(digit))
            # обновляем количество товара
            await state.update_data(count_item=count_item)
            # получаем id продукта
            id_product = input_user[2]
            # получаем информацию о продукте
            info_product = await get_info_product(id_product=int(id_product))
            if 'шт' in info_product.title:
                e = 'шт'
            else:
                e = 'кг'
            try:
                await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                      f'Стоимость: {info_product.price} руб.\n\n'
                                                      f'Количество: {count_item} {e}.',
                                                 reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                                  count_item=count_item * 10))
            except:
                pass
        # если запятая нажата и введено число
        else:
            # формируем новое количество товара, увеличиваем на десять текущее количество,
            # чтобы работать с целыми значениями
            count_item = int(user_dict[callback.message.chat.id]['count_item']) * 10 + int(digit)
            # обнуляем количество товара, так как после запятой одно число
            await state.update_data(count_item=0)
            # сбрасываем флаг нажатия запятой
            await state.update_data(comma=0)
            # получаем id товара
            id_product = input_user[2]
            # получаем информацию о товаре
            info_product = await get_info_product(id_product=int(id_product))
            if 'шт' in info_product.title:
                e = 'шт'
            else:
                e = 'кг'
            try:
                await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                      f'Стоимость: {info_product.price} руб.\n\n'
                                                      f'Количество: {count_item/10} {e}.',
                                                 reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                                  count_item=count_item))
            except:
                pass
    # если нажата запятая
    elif digit == '#':
        # обновляем словарь данных
        user_dict[callback.message.chat.id] = await state.get_data()
        # выставляем флаг ввода десятичных значений
        await state.update_data(comma=1)
        # получаем текущее количество товара
        count_item = user_dict[callback.message.chat.id]['count_item']
        # получаем id товара
        id_product = input_user[2]
        # получаем информацию о товаре
        info_product = await get_info_product(id_product=int(id_product))
        # отправляем сообщение, добавив десятичную часть и умножив на 10 текущее количество товара
        if 'шт' in info_product.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: {count_item},00 {e}.',
                                         reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                          count_item=count_item*10))
    else:
        await state.update_data(comma=0)
        await state.update_data(count_item=0)
        id_product = input_user[2]
        info_product = await get_info_product(id_product=int(id_product))
        if 'шт' in info_product.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: 0 {e}.',
                                         reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                          count_item=0))


@router.callback_query(F.data.startswith('count'))
async def get_count_product(callback: CallbackQuery):
    """
    Получаем количество товара
    :param callback:
    :return:
    """
    logging.info(f'get_count_product: {callback.message.chat.id}')
    await callback.answer()
    # получаем количество товара
    count = int(callback.data.split('_')[1])
    print("count", count)
    # получаем информацию о товаре
    info_product = await get_info_product(id_product=int(callback.data.split('_')[2]))
    if 'шт' in info_product.title:
        e = 'шт'
    else:
        e = 'кг'
    if count % 10:
        count_ = count / 10
    else:
        count_ = int(count // 10)
    if (info_product.price * count) % 10:
        amount = info_product.price * count_
    else:
        amount = int(info_product.price * count_)
    await callback.message.edit_text(text=f'Вы выбрали: {info_product.title}\n\n'
                                          f'Количество: {count_} {e}.\n'
                                          f'Стоимость: {info_product.price} x {count_} = '
                                          f'{amount} руб.',
                                     reply_markup=keyboard_create_item(id_product=int(callback.data.split('_')[2]),
                                                                       count_item=count))


@router.callback_query(F.data.startswith('add_item/'))
async def add_item_order(callback: CallbackQuery, bot: Bot):
    """
    Добавляем товар в корзину
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'add_item_order: {callback.message.chat.id} - {callback.data}')
    await callback.answer()
    if callback.data.split('/')[1] != 'cancel':
        # количество товара
        count_item = int(callback.data.split('/')[2])
        # id товара в таблице price
        id_product = int(callback.data.split('/')[1])
        # информация о товаре
        info_product = await get_info_product(id_product=id_product)

        # получаем все заказы пользователя
        all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
        # создаем новый заказ если у пользователя их нет или все завершены
        if not all_order_id or all_order_id[-1].status in ['complete', 'payed', 'cancelled']:
            create_order = {}
            # формирование строки даты для номера заказа
            current_date = datetime.now()
            current_date_string = current_date.strftime('%m/%d/%y_%H:%M:%S')
            # уникальный номер заказа
            id_order = f'{callback.message.chat.id}_{current_date_string}'
            create_order['id_order'] = id_order
            create_order['telegram_id'] = callback.message.chat.id
            await add_order(data=create_order)
            create_item = {}
            create_item['id_order'] = id_order
            create_item['telegram_id'] = callback.message.chat.id
            create_item['item'] = info_product.title
            create_item['count'] = count_item
            create_item['price'] = info_product.price
            await add_item(data=create_item)
        else:
            create_item = {}
            create_item['id_order'] = all_order_id[-1].id_order
            create_item['telegram_id'] = callback.message.chat.id
            create_item['item'] = info_product.title
            create_item['count'] = count_item
            create_item['price'] = info_product.price
            await add_item(data=create_item)
        all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
        all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
        text = 'Ваш заказ:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == all_order_id[-1].id_order:
                i += 1
                if item.count % 10:
                    count = item.count / 10
                else:
                    count = int(item.count // 10)
                if (info_product.price * item.count) % 10:
                    amount = item.price * count
                else:
                    amount = int(item.price * count)
                text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
                total += amount
        text += f'\nИтого: {total} руб.'
        await callback.message.answer(text='Товар добавлен в заказ',
                                      reply_markup=keyboards_main_menu(basket=total))
        await callback.message.answer(text=text,
                                      reply_markup=keyboard_confirm_order(id_order=all_order_id[-1].id_order))
        try:
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id)
        except:
            pass
    else:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id)
        except:
            pass
        await callback.message.answer(text='Добавление товара отменено!')


@router.callback_query(F.data.startswith('place_an_order/'))
async def place_an_order(callback: CallbackQuery, bot: Bot):
    """
    Получаем количество товара
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'place_an_order: {callback.message.chat.id}')
    await callback.answer()
    count_item = int(callback.data.split('/')[2])
    id_product = int(callback.data.split('/')[1])
    info_product = await get_info_product(id_product=id_product)
    all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
    if not all_order_id or all_order_id[-1].status in ['complete', 'payed', 'cancelled']:
        create_order = {}
        # формирование строки даты для номера заказа
        current_date = datetime.now()
        current_date_string = current_date.strftime('%m/%d/%y_%H:%M:%S')
        # уникальный номер заказа
        id_order = f'{callback.message.chat.id}_{current_date_string}'
        create_order['id_order'] = id_order
        create_order['telegram_id'] = callback.message.chat.id
        await add_order(data=create_order)
        create_item = {}
        create_item['id_order'] = id_order
        create_item['telegram_id'] = callback.message.chat.id
        create_item['item'] = info_product.title
        create_item['count'] = count_item
        create_item['price'] = info_product.price
        await add_item(data=create_item)
    else:
        create_item = {}
        create_item['id_order'] = all_order_id[-1].id_order
        create_item['telegram_id'] = callback.message.chat.id
        create_item['item'] = info_product.title
        create_item['count'] = count_item
        create_item['price'] = info_product.price
        await add_item(data=create_item)
    all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    text = 'Ваш заказ:\n\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == all_order_id[-1].id_order:
            i += 1
            if item.count % 10:
                count = item.count / 10
            else:
                count = int(item.count // 10)
            if (info_product.price * item.count) % 10:
                amount = item.price * count
            else:
                amount = int(item.price * count)
            text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
            total += amount
    text += f'\nИтого: {total} руб.'
    await callback.message.answer(text=text,
                                  reply_markup=keyboards_main_menu(basket=total))
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except:
        pass
    await callback.message.answer(text='Подтвердите или измените заказ',
                                  reply_markup=keyboard_confirm_order(id_order=all_order_id[-1].id_order))


@router.callback_query(F.data.startswith('change#'))
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    await state.update_data(id_order=id_order)
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    list_item = []
    for item in all_item_id:
        if item.id_order == id_order:
            list_item.append(item)

    await callback.message.edit_text(text='Выберите товар для изменения',
                                     reply_markup=keyboards_list_item_change(list_item=list_item))


@router.callback_query(F.data.startswith('itemchange_'))
async def item_change(callback: CallbackQuery, state: FSMContext):
    logging.info(f'item_change: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    id_item = int(callback.data.split('_')[1])
    await callback.message.edit_text(text='Вы хотите изменить количество товара или удалить его из заказа?',
                                     reply_markup=keyboard_change_item(id_item=id_item, id_order=id_order))


@router.callback_query(F.data.startswith('itemdel#'))
async def process_item_change(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'process_item_change: {callback.message.chat.id}')
    await callback.answer()
    id_item = int(callback.data.split('#')[1])
    await delete_item(id_item=id_item)
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    # all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    # list_item = []
    # for item in all_item_id:
    #     if item.id_order == id_order:
    #         list_item.append(item)
    #
    # await callback.message.edit_text(text='Ввберите товар для изменния',
    #                                  reply_markup=keyboards_list_item_change(list_item=list_item))
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    text = 'Ваш заказ:\n\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            i += 1
            if item.count % 10:
                count = item.count / 10
            else:
                count = int(item.count // 10)
            if (item.price * item.count) % 10:
                amount = item.price * count
            else:
                amount = int(item.price * count)
            text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
            total += amount
    text += f'\nИтого: {total} руб.'
    await callback.message.answer(text=text,
                                  reply_markup=keyboards_main_menu(basket=total))
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except:
        pass
    await callback.message.answer(text='Подтвердите или измените заказ',
                                  reply_markup=keyboard_confirm_order(id_order=id_order))


@router.callback_query(F.data.startswith('itemchange#'))
async def process_item_change(callback: CallbackQuery, state: FSMContext):
    logging.info(f'process_item_change: {callback.message.chat.id}')
    await callback.answer()
    id_item = int(callback.data.split('#')[1])
    await state.update_data(comma=0)

    info_item = await get_info_item(id_item=id_item)
    await state.update_data(count_item=0)
    info_price = await get_title(title=info_item.item)
    if 'шт' in info_price.title:
        e = 'шт'
    else:
        e = 'кг'
    if info_item.count % 10:
        count = info_item.count / 10
    else:
        count = int(info_item.count // 10)
    if (info_item.price * info_item.count) % 10:
        amount = info_item.price * count
    else:
        amount = int(info_item.price * count)
    await callback.message.edit_text(text=f'Вы выбрали: {info_item.item}\n\n'
                                          f'Количество: {count} {e}.\n'
                                          f'Стоимость: {info_item.price} x {count} = '
                                          f'{amount} руб.',
                                     reply_markup=keyboards_get_count(id_product=info_price.id,
                                                                      count_item=info_item.count))


@router.callback_query(F.data.startswith('confirm#'))
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            total += (item.count / 10) * item.price
    await state.update_data(id_order=id_order)
    if total < 5000:
        await callback.message.edit_text(text='Минимальная сумма заказа 5000 руб.',
                                         reply_markup=None)
        await asyncio.sleep(1)
        await press_button_basket(message=callback.message)
    else:
        await callback.message.edit_text(text='Как бы вы хотели получить ваш заказ?',
                                         reply_markup=keyboard_delivery())


@router.callback_query(F.data == 'pickup')
async def order_delivery(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    await update_status(id_order=id_order, status=OrderStatus.pickup)
    user_info = await get_user_info(tg_id=callback.message.chat.id)
    phone = user_info.phone
    name = user_info.name
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    info_order = await get_info_order(id_order=id_order)
    text = f'{name}, давайте проверим ваш заказ:\n\n' \
           f'Заказ №{info_order.id}\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            i += 1
            if item.count % 10:
                count = item.count / 10
            else:
                count = int(item.count // 10)
            if (item.price * item.count) % 10:
                amount = item.price * count
            else:
                amount = int(item.price * count)
            text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
            total += amount
    text += f'\nИтого: {total} руб.\n\n' \
            f'Номер телефона: {phone}\n'
    await callback.message.edit_text(text=text,
                                     reply_markup=keyboard_finish_order_p())


@router.callback_query(F.data.startswith('finishp_'))
async def process_finish_p(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'process_finish: {callback.message.chat.id}')
    await callback.answer()
    answer = callback.data.split('_')[1]
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    if answer == 'ok':
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся'
                                           ' для уточнения деталей заказ!',
                                      reply_markup=keyboards_main_menu(basket=0))
        media = []
        image_1 = 'AgACAgIAAxkBAAOpZnmbimV6FaiEk3AICkRs9Mzy_EcAAgLhMRtI39FLSsPzkuwcoccBAAMCAAN4AAM1BA'
        image_2 = 'AgACAgIAAxkBAAOqZnmcQJGncc-rD3T37wsaBvGPs-4AAgjhMRtI39FLFtmbrG3_dy4BAAMCAAN5AAM1BA'
        media.append(InputMediaPhoto(media=image_1,
                                     caption='<b>Наш адрес: проспект Непокорённых, 63к13с2 - отдел овощей'
                                             ' и фруктов</b>\n'
                                             '<a href="https://yandex.ru/maps/-/CDvd5Jy7">построить маршрут</a>\n\n'
                                             'Вы можете забрать заказ самостоятельно или заказать доставку.\n'
                                             '<u>Условия доставки:</u> доставка в пределах КАД бесплатно. '
                                             'Если сделаете заказ до 13.00, то доставим в этот же день!\n'
                                             'Контакт для связи: <a href="https://t.me/el_rstmv">@el_rstmv</a>\n',
                                     link_preview_options=LinkPreviewOptions(is_disabled=True),
                                     parse_mode='html'))
        media.append(InputMediaPhoto(media=image_2))
        await callback.message.answer_media_group(media=media)

        await update_status(id_order=id_order, status=OrderStatus.complete)
        user_info = await get_user_info(tg_id=callback.message.chat.id)
        phone = user_info.phone
        name = user_info.name
        text = f'Заказ №{id_order}:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == id_order:
                i += 1
                if item.count // 10:
                    count = item.count/10
                else:
                    count = int(item.count // 10)
                if (item.price * item.count) % 10:
                    amount = item.price * count
                else:
                    amount = int(item.price * count)
                text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
                total += amount
        text += f'\nИтого: {total} руб.\n\n' \
                f'Имя заказчика: {name}\n' \
                f'Номер телефона: {phone}\n'

        for admin_id in config.tg_bot.admin_ids.split(','):
            try:
                await bot.send_message(chat_id=int(admin_id),
                                       text=text,
                                       reply_markup=keyboard_change_status(id_order=id_order))
            except:
                pass
    else:
        await press_button_basket(message=callback.message)


@router.callback_query(F.data == 'delivery')
async def order_delivery(callback: CallbackQuery, state: FSMContext):
    """
    Запрос адреса доставки у пользователя (обновление статуса заказа -> "delivery")
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    await update_status(id_order=id_order, status=OrderStatus.delivery)
    await callback.message.edit_text(text='<u>Условия доставки:</u> доставка в пределах КАД бесплатно.\n'
                                          'Если сделаете заказ до 13.00, то доставим в этот же день!\n'
                                          'Укажите адрес доставки',
                                     reply_markup=None,
                                     parse_mode='html')
    await state.set_state(User.address)


@router.message(F.text, StateFilter(User.address))
async def get_address(message: Message, state: FSMContext):
    """
    Получение адреса доставки заказа от пользователя, запрос его подтверждения
    :param message:
    :param state:
    :return:
    """
    logging.info('get_address')
    await state.set_state(default_state)
    # получаем введенный пользователем адрес доставки заказа
    address = message.text
    # обновляем словарь данных (вносим адрес доставки)
    await state.update_data(address=address)
    await message.answer(text=f'Адрес для доставки вашего заказа {address}.\n'
                              f'Верно?',
                         reply_markup=keyboard_confirm_address())


@router.callback_query(F.data.startswith('address_'))
async def process_address(callback: CallbackQuery, state: FSMContext):
    """
    Обработка подтверждения введенного пользователем адреса доставки и формирование в случае его подтверждения
    информации о заказе и контактных данных
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'process_address: {callback.message.chat.id}')
    await callback.answer()
    # получаем ответ пользователя
    answer = callback.data.split('_')[1]
    # если адрес введенный пользователем подтвержден
    if answer == 'ok':
        # получаем данные
        user_dict[callback.message.chat.id] = await state.get_data()
        # id заказа пользователя
        id_order = user_dict[callback.message.chat.id]['id_order']
        # адрес доставки
        address = user_dict[callback.message.chat.id]['address']
        # обновляем адрес доставки в БД для заказа
        await update_address(id_order=id_order, address=address)
        # получаем информацию о пользователе
        user_info = await get_user_info(tg_id=callback.message.chat.id)
        # телефон
        phone = user_info.phone
        # имя
        name = user_info.name
        # все его товары
        all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
        info_order = await get_info_order(id_order=id_order)
        # формируем сообщение для подтверждения заказа и контактных данных
        text = f'{name}, давайте проверим ваш заказ:\n\n' \
               f'Заказ № {info_order.id}\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == id_order:
                i += 1
                if item.count % 10:
                    count = item.count / 10
                else:
                    count = int(item.count // 10)
                if (item.price * item.count) % 10:
                    amount = item.price * count
                else:
                    amount = int(item.price * count)
                text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
                total += amount
        text += f'\nИтого: {total} руб.\n\n' \
                f'Номер телефона: {phone}\n' \
                f'Адрес доставки: {address}'
        await callback.message.edit_text(text=text,
                                         reply_markup=keyboard_finish_order_d())
    # если адрес введенный пользователем не подтвержден, то запрашиваем его снова
    else:
        await order_delivery(callback=callback, state=state)


@router.callback_query(F.data.startswith('finishd_'))
async def process_finish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Подтверждение информации о заказе и контактных данных, в случае подтверждения благодарим за заказ
    и отправляем заказ администратору
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_finish: {callback.message.chat.id}')
    await callback.answer()
    # получаем ответ пользователя
    answer = callback.data.split('_')[1]
    # если пользователь подтвердил заказ и контактные данные
    if answer == 'ok':
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text='У вас есть пожелания к заказу?',
                                      reply_markup=keyboard_comment())
        await state.set_state(User.comment)
    else:
        await callback.message.edit_text(text='Оформление заказ отменено',
                                         reply_markup=None)


@router.message(F.text, StateFilter(User.comment))
async def get_comment(message: Message, state: FSMContext, bot: Bot):
    """
    Получаем комментарий от пользователя
    :param message: message.text содержит комментарий пользователя
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_comment: {message.chat.id}')
    await state.set_state(default_state)
    await message.answer(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся для уточнения'
                              ' деталей доставки!',
                         reply_markup=keyboards_main_menu(basket=0))
    # получаем все товары заказанные пользователем
    all_item_id = await get_all_item_id(tg_id=message.chat.id)
    # обновляем словарь данных
    user_dict[message.chat.id] = await state.get_data()
    # получаем id заказа
    id_order = user_dict[message.chat.id]['id_order']
    # обновляем статус заказа на complete
    await update_status(id_order=id_order, status=OrderStatus.complete)
    # получаем адрес доставки
    address = user_dict[message.chat.id]['address']
    # получаем информацию о пользователе
    user_info = await get_user_info(tg_id=message.chat.id)
    # телефон
    phone = user_info.phone
    # имя
    name = user_info.name
    info_order = await get_info_order(id_order=id_order)
    # формируем сообщение для менеджера
    text = f'Заказ №{info_order.id}-{id_order}:\n\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            i += 1
            if item.count % 10:
                count = item.count / 10
            else:
                count = int(item.count // 10)
            if (item.price * item.count) % 10:
                amount = item.price * count
            else:
                amount = int(item.price * count)
            text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
            total += amount
    text += f'\nИтого: {total} руб.\n\n' \
            f'Имя заказчика: {name}\n' \
            f'Номер телефона: {phone}\n' \
            f'Адрес доставки: {address}\n' \
            f'Комментария к заказу: {message.text}'
    # производим рассылку с заказом менеджерам
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=int(admin_id),
                                   text=text,
                                   reply_markup=keyboard_change_status(id_order))
        except:
            pass
    await update_comment(id_order=id_order, comment=message.text)


@router.callback_query(F.data.startswith('comment_pass'))
async def pass_comment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пропустить добавление комментария к заказу
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'pass_comment: {callback.message.chat.id}')
    await callback.answer()
    await state.set_state(default_state)
    await callback.message.answer(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся для уточнения'
                                       ' деталей доставки!',
                                  reply_markup=keyboards_main_menu(basket=0))
    # получаем все товары заказанные пользователем
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    # обновляем словарь данных
    user_dict[callback.message.chat.id] = await state.get_data()
    # получаем id заказа
    id_order = user_dict[callback.message.chat.id]['id_order']
    # обновляем статус заказа на complete
    await update_status(id_order=id_order, status=OrderStatus.complete)
    # получаем адрес доставки
    address = user_dict[callback.message.chat.id]['address']
    # получаем информацию о пользователе
    user_info = await get_user_info(tg_id=callback.message.chat.id)
    # телефон
    phone = user_info.phone
    # имя
    name = user_info.name
    info_order = await get_info_order(id_order=id_order)
    # формируем сообщение для менеджера
    text = f'Заказ №{info_order.id}-{id_order}:\n\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            i += 1
            if item.count % 10:
                count = item.count / 10
            else:
                count = int(item.count // 10)
            if (item.price * item.count) % 10:
                amount = item.price * count
            else:
                amount = int(item.price * count)
            text += f'{i}. {item.item} {count} x {item.price} = {amount} руб.\n'
            total += amount
    text += f'\nИтого: {total} руб.\n\n' \
            f'Имя заказчика: {name}\n' \
            f'Номер телефона: {phone}\n' \
            f'Адрес доставки: {address}\n' \
            f'Комментария к заказу нет'
    # производим рассылку с заказом менеджерам
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=int(admin_id),
                                   text=text,
                                   reply_markup=keyboard_change_status(id_order))
        except:
            pass


@router.callback_query(F.data.startswith('payed'))
async def pass_comment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'pass_comment: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    await state.update_data(id_order=id_order)
    await callback.message.answer('Укажите сумму оплаченного заказa')
    await state.set_state(User.amount)


@router.message(StateFilter(User.amount), lambda message: message.text.isdigit())
async def get_amount_order(message: Message, state: FSMContext):
    logging.info(f'get_amount_order: {message.chat.id}')
    await state.set_state(default_state)
    user_dict[message.chat.id] = await state.get_data()
    id_order = user_dict[message.chat.id]['id_order']
    await update_status(id_order=id_order, status=OrderStatus.payed)
    await update_amount(id_order=id_order, amount=int(message.text))
    info_order = await get_info_order(id_order=id_order)
    await message.answer(text=f'Сумма {message.text} добавлена в заказ №{info_order.id}-{id_order}')


@router.message(StateFilter(User.amount))
async def error_amount_order(message: Message, state: FSMContext):
    logging.info(f'error_amount_order: {message.chat.id}')
    await message.answer(text='Некорректные данные! Введите целое число.')


@router.callback_query(F.data.startswith('cancelled'))
async def cancelled_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'cancelled_order: {callback.data}')
    await callback.answer()
    await state.set_state(default_state)
    id_order = callback.data.split('#')[1]
    await update_status(id_order=id_order, status=OrderStatus.cancelled)
    info_order = await get_info_order(id_order=id_order)
    await callback.message.answer(text=f'Заказ №{info_order.id}-{id_order} отменен')
