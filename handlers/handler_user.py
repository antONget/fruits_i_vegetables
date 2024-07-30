from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, LinkPreviewOptions
from aiogram.filters import CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


from config_data.config import Config, load_config
from database.requests import get_user_info, add_user, update_name_phone, get_list_product, \
    get_all_order_id, get_all_item_id
from keyboards.keyboard_user import keyboards_get_contact, keyboard_confirm_phone, keyboards_main_menu,\
    keyboard_confirm_order
from services.get_exel import list_price_to_exel
from datetime import datetime
import logging
from filter.user_filter import validate_russian_phone_number

router = Router()
config: Config = load_config()


class User(StatesGroup):
    name = State()
    phone = State()
    address = State()
    comment = State()
    amount = State()


user_dict = {}


@router.message(CommandStart())
async def process_start_command_user(message: Message, state: FSMContext) -> None:
    """
    The "start" button is pressed or the "/start" command is entered
    :param message:
    :param state:
    :return:
    """
    logging.info("process_start_command_user")
    await state.set_state(default_state)
    user = await get_user_info(tg_id=message.chat.id)
    # если пользователь еще не в БД
    if not user:
        await message.answer(text='Как вас зовут?')
        await state.set_state(User.name)
    # если пользователь уже взаимодействовал с ботом и есть в БД
    else:
        await message.answer(text=f'{user.name}, рады видеть вас снова!\n'
                                  f'телефон: {user.phone}',
                             reply_markup=keyboard_confirm_phone())
    # await asyncio.sleep(1)
    # await state.update_data(start=True)


@router.message(F.text, StateFilter(User.name))
async def get_name_user(message: Message, state: FSMContext) -> None:
    """
    Получаем имя пользователя и запрашиваем номер телефона
    :param message:
    :param state:
    :return:
    """
    await state.update_data(name=message.text)
    await message.answer(text='Укажите ваш номер телефона или нажмите внизу 👇\n'
                              '"Отправить свой контакт ☎️"',
                         reply_markup=keyboards_get_contact())
    await state.set_state(User.phone)


@router.callback_query(F.data == 'edit_phone')
async def press_button_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение номера телефона, для пользователей которые уже занесены в БД
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'press_button_edit_phone: {callback.message.chat.id}')
    await callback.message.answer(text='Укажи свой телефон',
                                  reply_markup=keyboards_get_contact())
    await state.set_state(User.phone)


@router.message(StateFilter(User.phone))
async def get_phone_user(message: Message, state: FSMContext) -> None:
    """
    Получаем номер телефона проверяем его на валидность и заносим его в БД
    :param message:
    :param state:
    :return:
    """
    logging.info(f'get_phone_user: {message.chat.id}')
    # если номер телефона отправлен через кнопку "Поделится"
    if message.contact:
        phone = str(message.contact.phone_number)
    # если введен в поле ввода
    else:
        phone = message.text
        # проверка валидности отправленного номера телефона, если не валиден просим ввести его повторно
        if not validate_russian_phone_number(phone):
            await message.answer(text="Неверный формат номера, повторите ввод.")
            return
    # обновляем поле номера телефона
    await state.update_data(phone=phone)
    # получаем данные словаря пользователя
    user_dict[message.chat.id] = await state.get_data()
    # информация по пользователю
    user = await get_user_info(tg_id=message.chat.id)
    # если пользователя нет, то добавляем его в БД
    if not user:
        # если у пользователя есть username
        if message.from_user.username:
            await add_user(
                {"id": message.from_user.id,
                 "username": message.from_user.username,
                 "name": user_dict[message.chat.id]['name'],
                 "phone": user_dict[message.chat.id]['phone']})
        # если нет то его оставляем по умолчанию
        else:
            await update_name_phone(tg_id=message.chat.id,
                                    name=user_dict[message.chat.id]['name'],
                                    phone=user_dict[message.chat.id]['phone'])
    # получаем все заказы пользователя
    all_order_id = await get_all_order_id(tg_id=message.chat.id)
    # создаем новый заказ если у пользователя их нет или все завершены
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
        # сумма корзины ровна 0
        count_basket = 0
    # если статус заказа 'create'
    else:
        # Получаем все товары пользователя по его id телеграм
        all_item_id = await get_all_item_id(tg_id=message.chat.id)
        # Получаем все заказы пользователя
        all_order_id = await get_all_order_id(tg_id=message.chat.id)
        # обнуляем корзину
        count_basket = 0
        # проходим по всем товарам пользователя
        for item in all_item_id:
            # если товары входят в последний заказ пользователя
            if item.id_order == all_order_id[-1].id_order:
                # если последнее число количества товара не 0
                if item.count % 10:
                    # количество делим на 10
                    count = item.count / 10
                else:
                    # берем только целое число
                    count = int(item.count // 10)
                # если произведение не завершается нулем
                if (item.price * item.count) % 10:
                    count_basket += item.price * count
                else:
                    count_basket += int(item.price * count)
    await message.answer(text=f'Друзья, всем доброго времени суток, рады вас видеть в нашем оптовом маркете.'
                              f' Здесь вы можете выбрать самые свежие и вкусные фрукты и овощи и заказать'
                              f' их доставку или самовывоз!\n'
                              f'Минимальная сумма заказа 5000 руб.\n'
                              f'График работы: 10:00-22:00 без перерывов и выходных\n\n'
                              f'Если меню свернется то вы всегда его сможете развернуть нажав на квадратик с точками'
                              f' в нижней правой части',
                         reply_markup=keyboards_main_menu(basket=count_basket))
    await state.set_state(default_state)


@router.callback_query(F.data == 'continue_user')
async def press_button_continue_user(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Контактные данные верны - переход к основному меню (для пользователей, которые уже занесены в БД)
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'press_button_continue_user: {callback.message.chat.id}')
    await callback.answer()
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except IndexError:
        pass
    # получаем все заказы пользователя
    all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
    # создаем новый заказ если у пользователя их нет или все завершены
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
        # сумма корзины ровна 0
        count_basket = 0
    # если статус заказа 'create'
    else:
        # Получаем все товары пользователя по его id телеграм
        all_item_id = await get_all_item_id(tg_id=callback.message.chat.id)
        # Получаем все заказы пользователя
        all_order_id = await get_all_order_id(tg_id=callback.message.chat.id)
        # обнуляем корзину
        count_basket = 0
        # проходим по всем товарам пользователя
        for item in all_item_id:
            # если товары входят в последний заказ пользователя
            if item.id_order == all_order_id[-1].id_order:
                # если последнее число количества товара не 0
                if item.count % 10:
                    # количество делим на 10
                    count = item.count / 10
                else:
                    # берем только целое число
                    count = int(item.count // 10)
                # если произведение не завершается нулем
                if (item.price * item.count) % 10:
                    count_basket += item.price * count
                else:
                    count_basket += int(item.price * count)
    await callback.message.answer(text='Для онлайн-заказа выберите нужный раздел. Если вы не завершили предыдущий '
                                       'заказ, обратите внимание на корзину.',
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


@router.message(F.text == '🏠 Главное')
async def press_home(message: Message, state: FSMContext):
    logging.info(f'press_home: {message.chat.id}')
    # получаем все заказы пользователя
    all_order_id = await get_all_order_id(tg_id=message.chat.id)
    # создаем новый заказ если у пользователя их нет или все завершены
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
        # сумма корзины ровна 0
        count_basket = 0
    # если статус заказа 'create'
    else:
        # Получаем все товары пользователя по его id телеграм
        all_item_id = await get_all_item_id(tg_id=message.chat.id)
        # Получаем все заказы пользователя
        all_order_id = await get_all_order_id(tg_id=message.chat.id)
        # обнуляем корзину
        count_basket = 0
        # проходим по всем товарам пользователя
        for item in all_item_id:
            # если товары входят в последний заказ пользователя
            if item.id_order == all_order_id[-1].id_order:
                # увеличиваем сумму корзины
                count_basket += item.count * item.price
    await message.answer(text='Для онлайн-заказа выберите нужный раздел. Если вы не завершили предыдущий '
                              'заказ, обратите внимание на корзину.',
                         reply_markup=keyboards_main_menu(basket=count_basket))
    await state.set_state(default_state)


@router.message(F.text.startswith('🛒 Корзина'))
async def press_button_basket(message: Message):
    logging.info(f'press_button_berry: {message.chat.id}')
    all_order_id = await get_all_order_id(tg_id=message.chat.id)
    all_item_id = await get_all_item_id(tg_id=message.chat.id)
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
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
                                 caption=f'<b>Наш адрес: проспект Непокорённых, 63к13с2 - отдел овощей и фруктов</b>\n'
                                         f'<a href="https://yandex.ru/maps/-/CDvd5Jy7">построить маршрут</a>\n\n'
                                         f'Вы можете забрать заказ самостоятельно или заказать доставку.\n'
                                         f'<u>Условия доставки:</u> доставка в пределах КАД бесплатно. '
                                         f'Если сделаете заказ до 13.00, то доставим в этот же день!\n'
                                         f'Контакт для связи: <a href="https://t.me/{config.tg_bot.support}">@'
                                         f'{config.tg_bot.support}</a>\n',
                                 parse_mode='html',
                                 link_preview_options=LinkPreviewOptions(is_disabled=True)))
    media.append(InputMediaPhoto(media=image_2))
    await message.answer_media_group(media=media)


@router.message(F.text.startswith('👤 Личный кабинет'))
async def press_button_cabinet(message: Message):
    logging.info(f'press_button_cabinet: {message.chat.id}')
    await message.answer(text='Раздел в разработке.\n'
                              'Здесь вы сможете увидеть ваши заказы и узнать о накопительной системе скидок!')
