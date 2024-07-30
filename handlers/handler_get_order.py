from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.filters import StateFilter

import database.requests as rq
import keyboards.keyboard_user as kb
from config_data.config import Config, load_config

import logging

router = Router()
user_dict = {}
config: Config = load_config()


class User(StatesGroup):
    address = State()
    comment = State()
    amount = State()


@router.callback_query(F.data == 'pickup')
async def order_delivery(callback: CallbackQuery, state: FSMContext):
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.pickup)
    user_info = await rq.get_user_info(tg_id=callback.message.chat.id)
    phone = user_info.phone
    name = user_info.name
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    info_order = await rq.get_info_order(id_order=id_order)
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
                                     reply_markup=kb.keyboard_finish_order_p())


@router.callback_query(F.data.startswith('finishp_'))
async def process_finish_p(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'process_finish: {callback.message.chat.id}')
    await callback.answer()
    answer = callback.data.split('_')[1]
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    if answer == 'ok':
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(text='Благодарим вас за заказ, в ближайшее время с вами свяжутся'
                                           ' для уточнения деталей заказ!',
                                      reply_markup=kb.keyboards_main_menu(basket=0))
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

        await rq.update_status(id_order=id_order, status=rq.OrderStatus.complete)
        user_info = await rq.get_user_info(tg_id=callback.message.chat.id)
        phone = user_info.phone
        name = user_info.name
        info_order = await rq.get_info_order(id_order=id_order)
        text = f'Заказ №{info_order.id}-{id_order}:\n\n'
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
                f'Номер телефона: {phone}\n' \
                f'Способ получения: самовывоз'

        for admin_id in config.tg_bot.admin_ids.split(','):
            try:
                await bot.send_message(chat_id=int(admin_id),
                                       text=text,
                                       reply_markup=kb.keyboard_change_status(id_order=id_order))
            except IndexError:
                pass
        await bot.send_message(chat_id=config.tg_bot.chanel_id,
                               text=text)
    else:
        all_order_id = await rq.get_all_order_id(tg_id=callback.message.chat.id)
        all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
        if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
            await callback.message.answer('В вашей корзине нет товаров!')
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
            await callback.message.answer(text=text,
                                          reply_markup=kb.keyboard_confirm_order(id_order=all_order_id[-1].id_order))


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
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.delivery)
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
                         reply_markup=kb.keyboard_confirm_address())


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
        await rq.update_address(id_order=id_order, address=address)
        # получаем информацию о пользователе
        user_info = await rq.get_user_info(tg_id=callback.message.chat.id)
        # телефон
        phone = user_info.phone
        # имя
        name = user_info.name
        # все его товары
        all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
        info_order = await rq.get_info_order(id_order=id_order)
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
                                         reply_markup=kb.keyboard_finish_order_d())
    # если адрес введенный пользователем не подтвержден, то запрашиваем его снова
    else:
        await order_delivery(callback=callback, state=state)


@router.callback_query(F.data.startswith('finishd_'))
async def process_finish(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждение информации о заказе и контактных данных, в случае подтверждения благодарим за заказ
    и отправляем заказ администратору
    :param callback:
    :param state:
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
                                      reply_markup=kb.keyboard_comment())
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
                         reply_markup=kb.keyboards_main_menu(basket=0))
    # получаем все товары заказанные пользователем
    all_item_id = await rq.get_all_item_id(tg_id=message.chat.id)
    # обновляем словарь данных
    user_dict[message.chat.id] = await state.get_data()
    # получаем id заказа
    id_order = user_dict[message.chat.id]['id_order']
    # обновляем статус заказа на complete
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.complete)
    # получаем адрес доставки
    address = user_dict[message.chat.id]['address']
    # получаем информацию о пользователе
    user_info = await rq.get_user_info(tg_id=message.chat.id)
    # телефон
    phone = user_info.phone
    # имя
    name = user_info.name
    info_order = await rq.get_info_order(id_order=id_order)
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
                                   reply_markup=kb.keyboard_change_status(id_order))
        except IndexError:
            pass
    await rq.update_comment(id_order=id_order, comment=message.text)
    await bot.send_message(chat_id=config.tg_bot.chanel_id,
                           text=text)


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
                                  reply_markup=kb.keyboards_main_menu(basket=0))
    # получаем все товары заказанные пользователем
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    # обновляем словарь данных
    user_dict[callback.message.chat.id] = await state.get_data()
    # получаем id заказа
    id_order = user_dict[callback.message.chat.id]['id_order']
    # обновляем статус заказа на complete
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.complete)
    # получаем адрес доставки
    address = user_dict[callback.message.chat.id]['address']
    # получаем информацию о пользователе
    user_info = await rq.get_user_info(tg_id=callback.message.chat.id)
    # телефон
    phone = user_info.phone
    # имя
    name = user_info.name
    info_order = await rq.get_info_order(id_order=id_order)
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
    await rq.update_amount(id_order=id_order, amount=total)
    # производим рассылку с заказом менеджерам
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=int(admin_id),
                                   text=text,
                                   reply_markup=kb.keyboard_change_status(id_order))

        except IndexError:
            pass
    await bot.send_message(chat_id=config.tg_bot.chanel_id,
                           text=text)


@router.callback_query(F.data.startswith('payed#'))
async def payed_change_order(callback: CallbackQuery, state: FSMContext):
    logging.info(f'payed_change_order: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    await state.update_data(id_order=id_order)
    await callback.message.answer('Укажите сумму оплаченного заказa')
    await state.set_state(User.amount)


@router.message(StateFilter(User.amount), lambda message: message.text.isdigit())
async def get_amount_order(message: Message, state: FSMContext, bot: Bot):
    logging.info(f'get_amount_order: {message.chat.id}')
    await state.set_state(default_state)
    user_dict[message.chat.id] = await state.get_data()
    id_order = user_dict[message.chat.id]['id_order']
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.payed)
    await rq.update_amount(id_order=id_order, amount=int(message.text))
    info_order = await rq.get_info_order(id_order=id_order)
    await message.edit_reply_markup(reply_markup=None)
    await message.answer(text=f'Сумма {message.text} добавлена в заказ №{info_order.id}-{id_order}')
    await bot.send_message(chat_id=config.tg_bot.chanel_id,
                           text=f'Сумма {message.text} добавлена в заказ №{info_order.id}-{id_order}')


@router.message(StateFilter(User.amount))
async def error_amount_order(message: Message):
    logging.info(f'error_amount_order: {message.chat.id}')
    await message.answer(text='Некорректные данные! Введите целое число.')


@router.callback_query(F.data.startswith('cancelled#'))
async def cancelled_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'cancelled_order: {callback.data}')
    await callback.answer()
    await state.set_state(default_state)
    id_order = callback.data.split('#')[1]
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.cancelled)
    info_order = await rq.get_info_order(id_order=id_order)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text=f'Заказ №{info_order.id}-{id_order} отменен')
    await bot.send_message(chat_id=config.tg_bot.chanel_id,
                           text=f'Заказ №{info_order.id}-{id_order} отменен')


@router.callback_query(F.data.startswith('payedpayed#'))
async def payed_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'payed_order: {callback.data}')
    await callback.answer()
    await state.set_state(default_state)
    id_order = callback.data.split('#')[1]
    await rq.update_status(id_order=id_order, status=rq.OrderStatus.payed)
    info_order = await rq.get_info_order(id_order=id_order)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text=f'Заказ №{info_order.id}-{id_order} оплачен')
    await bot.send_message(chat_id=config.tg_bot.chanel_id,
                           text=f'Заказ №{info_order.id}-{id_order} оплачен')
