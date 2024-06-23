from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


from config_data.config import Config, load_config
from database.requests import get_user_info, add_user, update_name_phone, get_list_product, \
    get_product, get_title, get_info_product, add_order, get_all_order_id, add_item, get_all_item_id, update_status,\
    OrderStatus, update_address
from keyboards.keyboard_user import keyboards_get_contact, keyboard_confirm_phone, keyboards_main_menu,\
    keyboards_list_product, keyboards_get_count, keyboard_create_item, keyboard_confirm_order, keyboard_delivery, \
    keyboard_confirm_address, keyboard_finish_order_p, keyboard_finish_order_d
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
    if not all_order_id or all_order_id[-1].status == 'complete':
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
    await message.answer(text=f'Друзья, всем доброго времени суток, рады вас видеть в нашем магазине.'
                              f' Здесь вы можете выбрать самые свежие и вкусные фрукты и овощи и заказать'
                              f' их доставку или самовывоз!'
                              f'график работы: 10:00-23:00 без перерывов и выходных',
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
    if not all_order_id or all_order_id[-1].status == 'complete':
        await message.answer('В вашей корзине нет товаров!')
    else:
        text = 'Ваш заказ:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == all_order_id[-1].id_order:
                i += 1
                text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
                total += (item.count/10) * item.price
        text += f'\nИтого: {total} руб.'
        await message.answer(text=text,
                             reply_markup=keyboard_confirm_order(id_order=all_order_id[-1].id_order))


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
        await callback.message.edit_text(text=f'Товар: {price_list_title.title}\n'
                                              f'Стоимость: {price_list_title.price}\n\n'
                                              f'Количество: 0 кг.',
                                         reply_markup=keyboards_get_count(id_product=price_list_title.id))
    elif len(price_list_model) == 0:
        # print(price_list_model)
        price_list_title = await get_title(title=product)
        # print(price_list_title)
        await state.update_data(count_item=0)
        await state.update_data(comma=0)
        await callback.message.edit_text(text=f'Товар: {price_list_title.title}\n'
                                         f'Стоимость: {price_list_title.price} руб.\n\n'
                                         f'Количество: 0 кг.',
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
    digit = input_user[1]
    if digit.isdigit():
        user_dict[callback.message.chat.id] = await state.get_data()
        if user_dict[callback.message.chat.id]['comma'] == 0:
            count_item = int(str(user_dict[callback.message.chat.id]['count_item']) + str(digit))
            await state.update_data(count_item=count_item)
            id_product = input_user[2]
            info_product = await get_info_product(id_product=int(id_product))
            await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                  f'Стоимость: {info_product.price} руб.\n\n'
                                                  f'Количество: {count_item} кг.',
                                             reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                              count_item=count_item * 10))
        else:
            count_item = int(user_dict[callback.message.chat.id]['count_item']) * 10 + int(digit)
            await state.update_data(count_item=0)
            id_product = input_user[2]
            info_product = await get_info_product(id_product=int(id_product))
            # await callback.message.edit_text(text=f'Вы выбрали: {info_product.title}\n\n'
            #                                       f'Количество: {count_item/10}\n'
            #                                       f'Стоимость: {info_product.price} x {count_item/10} = '
            #                                       f'{info_product.price * count_item/10}',
            #                                  reply_markup=keyboard_create_item(
            #                                      id_product=int(callback.data.split('_')[2]),
            #                                      count_item=count_item))
            await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                  f'Стоимость: {info_product.price} руб.\n\n'
                                                  f'Количество: {count_item/10} кг.',
                                             reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                              count_item=count_item))

    elif digit == '#':
        print(',,,,,,,')
        user_dict[callback.message.chat.id] = await state.get_data()
        await state.update_data(comma=1)
        count_item = user_dict[callback.message.chat.id]['count_item']
        id_product = input_user[2]
        info_product = await get_info_product(id_product=int(id_product))
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: {count_item},00 кг.',
                                         reply_markup=keyboards_get_count(id_product=info_product.id,
                                                                          count_item=count_item*10))
    else:
        await state.update_data(comma=0)
        await state.update_data(count_item=0)
        id_product = input_user[2]
        info_product = await get_info_product(id_product=int(id_product))
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: 0 кг.',
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
    # получаем информацию о товаре
    info_product = await get_info_product(id_product=int(callback.data.split('_')[2]))
    await callback.message.edit_text(text=f'Вы выбрали: {info_product.title}\n\n'
                                          f'Количество: {count/10}\n'
                                          f'Стоимость: {info_product.price} x {count/10} = '
                                          f'{info_product.price * count/10}',
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
        # id товара
        id_product = int(callback.data.split('/')[1])
        # информация о товаре
        info_product = await get_info_product(id_product=id_product)

        # получаем все заказы пользователя
        all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
        # создаем новый заказ если у пользователя их нет или все завершены
        if not all_order_id or all_order_id[-1].status == 'complete':
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
                text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
                total += (item.count/10) * item.price
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
    if not all_order_id or all_order_id[-1].status == 'complete':
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
            text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
            total += (item.count/10) * item.price
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
    await callback.message.answer(text='Нужно придумать как удобно производить изменение заказа.')


@router.callback_query(F.data.startswith('confirm#'))
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    await state.update_data(id_order=id_order)
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
    text = f'{name}, давайте проверим ваш заказ:\n\n'
    i = 0
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            i += 1
            text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
            total += (item.count/10) * item.price
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
        await callback.message.edit_reply_markup(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся'
                                                      ' для уточнения деталей заказ!',
                                                 reply_markup=None)
        await callback.message.answer(text='Заказ можно забрать по адресу: АДРЕС',
                                      reply_markup=keyboards_main_menu(basket=0))
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
                text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
                total += (item.count/10) * item.price
        text += f'\nИтого: {total} руб.\n\n' \
                f'Имя заказчика: {name}\n' \
                f'Номер телефона: {phone}\n'

        for admin_id in config.tg_bot.admin_ids.split(','):
            try:
                await bot.send_message(chat_id=int(admin_id),
                                       text=text)
            except:
                pass
    else:
        await press_button_basket(message=callback.message)


@router.callback_query(F.data == 'delivery')
async def order_delivery(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    await update_status(id_order=id_order, status=OrderStatus.delivery)
    await callback.message.edit_text(text='Укажите адрес доставки',
                                     reply_markup=None)
    await state.set_state(User.address)


@router.message(F.text, StateFilter(User.address))
async def get_address(message: Message, state: FSMContext):
    logging.info('get_address')
    await state.set_state(default_state)
    address = message.text
    await state.update_data(address=address)
    await message.answer(text=f'Адрес для доставки вашего заказа {address}.\n'
                              f'Верно?',
                         reply_markup=keyboard_confirm_address())


@router.callback_query(F.data.startswith('address_'))
async def process_address(callback: CallbackQuery, state: FSMContext):
    logging.info(f'process_address: {callback.message.chat.id}')
    await callback.answer()
    answer = callback.data.split('_')[1]
    if answer == 'ok':
        user_dict[callback.message.chat.id] = await state.get_data()
        id_order = user_dict[callback.message.chat.id]['id_order']
        address = user_dict[callback.message.chat.id]['address']
        await update_address(id_order=id_order, address=address)
        user_info = await get_user_info(tg_id=callback.message.chat.id)
        phone = user_info.phone
        name = user_info.name
        all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
        text = f'{name}, давайте проверим ваш заказ:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == id_order:
                i += 1
                text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
                total += (item.count/10) * item.price
        text += f'\nИтого: {total} руб.\n\n' \
                f'Номер телефона: {phone}\n' \
                f'Адрес доставки: {address}'
        await callback.message.edit_text(text=text,
                                         reply_markup=keyboard_finish_order_d())
    else:
        await order_delivery(callback=callback, state=state)


@router.callback_query(F.data.startswith('finishd_'))
async def process_finish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'process_finish: {callback.message.chat.id}')
    await callback.answer()
    answer = callback.data.split('_')[1]
    all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    if answer == 'ok':
        await callback.message.answer(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся для уточнения'
                                           ' деталей доставки!',
                                      reply_markup=keyboards_main_menu(basket=0))
        await update_status(id_order=id_order, status=OrderStatus.complete)
        address = user_dict[callback.message.chat.id]['address']
        user_info = await get_user_info(tg_id=callback.message.chat.id)
        phone = user_info.phone
        name = user_info.name
        text = f'Заказ №{id_order}:\n\n'
        i = 0
        total = 0
        for item in all_item_id:
            if item.id_order == id_order:
                i += 1
                text += f'{i}. {item.item} {item.count/10} x {item.price} = {(item.count/10) * item.price} руб.\n'
                total += (item.count/10) * item.price
        text += f'\nИтого: {total} руб.\n\n' \
                f'Имя заказчика: {name}\n' \
                f'Номер телефона: {phone}\n' \
                f'Адрес доставки: {address}'

        for admin_id in config.tg_bot.admin_ids.split(','):
            try:
                await bot.send_message(chat_id=int(admin_id),
                                       text=text)
            except:
                pass
    else:
        await callback.message.edit_text(text='Оформление заказ отменено',
                                         reply_markup=None)
