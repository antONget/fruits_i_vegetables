from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import database.requests as rq
import keyboards.keyboard_user as kb
from datetime import datetime
import logging
import asyncio
router_shop = Router()
user_dict = {}


@router_shop.message(F.text == '🛍 Магазин')
async def press_shop(message: Message):
    logging.info(f'press_shop: {message.chat.id}')
    # получаем все заказы пользователя
    all_order_id = await rq.get_all_order_id(tg_id=message.chat.id)
    # создаем новый заказ если у пользователя их нет или все завершены
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
        # сумма корзины ровна 0
        count_basket = 0
    # если статус заказа 'create'
    else:
        # Получаем все товары пользователя по его id телеграм
        all_item_id = await rq.get_all_item_id(tg_id=message.chat.id)
        # Получаем все заказы пользователя
        all_order_id = await rq.get_all_order_id(tg_id=message.chat.id)
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
    list_price = await rq.get_list_price()
    list_category = list(set([price.category for price in list_price]))
    await message.answer(text='Выберите продукты добавьте их в корзину и оформите заказ',
                         reply_markup=kb.keyboards_main_category(list_category=list_category, basket=count_basket))


@router_shop.message(F.text == 'Фрукты 🍊🍎🍐')
async def press_button_fruits(message: Message):
    """
    Выбор категории фрукты и вывод продуктов по этой категории
    :param message:
    :return:
    """
    logging.info(f'press_button_fruits: {message.chat.id}')
    # получаем список продуктов по категории
    price_list_model = await rq.get_list_product(category='Фрукты 🍊🍎🍐')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=kb.keyboards_list_product(list_product=list_product))


@router_shop.message(F.text == 'Овощи 🍆🥕🥔')
async def press_button_vegetation(message: Message):
    """
    Выбор категории Овощи и вывод продуктов по этой категории
    :param message:
    :return:
    """
    logging.info(f'press_button_vegetation: {message.chat.id}')
    price_list_model = await rq.get_list_product(category='Овощи 🍆🥕🥔')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=kb.keyboards_list_product(list_product=list_product))


@router_shop.message(F.text == 'Зелень 🌿🥦🥬')
async def press_button_green(message: Message):
    """
    Выбор категории Зелень и вывод продуктов по этой категории
    :param message:
    :return:
    """
    logging.info(f'press_button_green: {message.chat.id}')
    price_list_model = await rq.get_list_product(category='Зелень 🌿🥦🥬')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=kb.keyboards_list_product(list_product=list_product))


@router_shop.message(F.text == 'Ягоды 🍓🍒🫐')
async def press_button_berry(message: Message):
    """
    Выбор категории Ягоды и вывод продуктов по этой категории
    :param message:
    :return:
    """
    logging.info(f'press_button_berry: {message.chat.id}')
    price_list_model = await rq.get_list_product(category='Ягоды 🍓🍒🫐')
    list_product = list(set([item.product for item in price_list_model]))
    await message.answer(text=f'Выберите продукт:',
                         reply_markup=kb.keyboards_list_product(list_product=list_product))


@router_shop.callback_query(F.data.startswith('product'))
async def get_title_product(callback: CallbackQuery, state: FSMContext):
    """
    Выбор продукта в категории и вывод товаров этого продукта если их более одного,
     вывод клавиатуры для ввода количества товара
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'get_title_product: {callback.message.chat.id}')
    await callback.answer()
    # получаем продукт
    product = callback.data.split('_')[1]
    # получаем список товаров по продукту
    price_list_model = await rq.get_product(product=product)
    # если количество товаров этого продукта == 1
    if len(price_list_model) == 1:
        # получаем название товара
        price_list_title = await rq.get_title(title=price_list_model[0].title)
        # создаем переменную для количества
        await state.update_data(count_item=0)
        # флаг того что нажата запятая при указании веса
        await state.update_data(comma=0)
        # если в названии товара присутствует "шт.", то используем это обозначение для количества
        if 'шт' in price_list_title.title:
            e = 'шт'
        else:
            e = 'кг'
        # выводим название выбранного продукта, его стоимость за кг (шт.) и выбранное количество
        await callback.message.edit_text(text=f'Товар: {price_list_title.title}\n'
                                              f'Стоимость: {price_list_title.price} руб.\n\n'
                                              f'Количество: 0 {e}.',
                                         reply_markup=kb.keyboards_get_count(id_product=price_list_title.id))
    # если товаров этого продукта нет (такое получается после выбора товара продукта содержащего несколько товаров)
    elif len(price_list_model) == 0:
        # получаем список названий товаров
        price_list_title = await rq.get_title(title=product)
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
                                         reply_markup=kb.keyboards_get_count(id_product=price_list_title.id))
    # если товаров этого продукта более одного, то предлагаем выбрать товар
    else:
        title = []
        for item in price_list_model:
            title.append(item.title)
        await callback.message.edit_text(text=f'Выберите товар:',
                                         reply_markup=kb.keyboards_list_product(list_product=title))


@router_shop.callback_query(F.data.startswith('digit_'))
async def process_count_product(callback: CallbackQuery, state: FSMContext):
    """
    Обработка нажатия на клавиши клавиатуры ввода количества товара
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
        # обновляем словарь пользователя
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
            info_product = await rq.get_info_product(id_product=int(id_product))
            if 'шт' in info_product.title:
                e = 'шт'
            else:
                e = 'кг'
            try:
                await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                      f'Стоимость: {info_product.price} руб.\n\n'
                                                      f'Количество: {count_item} {e}.',
                                                 reply_markup=kb.keyboards_get_count(id_product=info_product.id,
                                                                                     count_item=count_item * 10))
            except :
                await callback.message.edit_text(text=f'Тoвар: {info_product.title}\n'
                                                      f'Стoимость: {info_product.price} руб.\n\n'
                                                      f'Количество: {count_item} {e}.',
                                                 reply_markup=kb.keyboards_get_count(id_product=info_product.id,
                                                                                     count_item=count_item * 10))
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
            info_product = await rq.get_info_product(id_product=int(id_product))
            if 'шт' in info_product.title:
                e = 'шт'
            else:
                e = 'кг'
            try:
                await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                                      f'Стоимость: {info_product.price} руб.\n\n'
                                                      f'Количество: {count_item/10} {e}.',
                                                 reply_markup=kb.keyboards_get_count(id_product=info_product.id,
                                                                                     count_item=count_item))
            except IndexError:
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
        info_product = await rq.get_info_product(id_product=int(id_product))
        # отправляем сообщение, добавив десятичную часть и умножив на 10 текущее количество товара
        if 'шт' in info_product.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: {count_item},00 {e}.',
                                         reply_markup=kb.keyboards_get_count(id_product=info_product.id,
                                                                             count_item=count_item*10))
    # если нажата кнопка очистить
    else:
        await state.update_data(comma=0)
        await state.update_data(count_item=0)
        id_product = input_user[2]
        info_product = await rq.get_info_product(id_product=int(id_product))
        if 'шт' in info_product.title:
            e = 'шт'
        else:
            e = 'кг'
        await callback.message.edit_text(text=f'Товар: {info_product.title}\n'
                                              f'Стоимость: {info_product.price} руб.\n\n'
                                              f'Количество: 0 {e}.',
                                         reply_markup=kb.keyboards_get_count(id_product=info_product.id,
                                                                             count_item=0))


@router_shop.callback_query(F.data.startswith('count'))
async def get_count_product(callback: CallbackQuery):
    """
    Получаем количество товара
    :param callback:
    :return:
    """
    logging.info(f'get_count_product: {callback.message.chat.id}')

    # получаем количество товара
    count = int(callback.data.split('_')[1])
    if count == 0:
        await callback.answer('Количество товара не может быть равное нулю.', show_alert=True)
        return
    await callback.answer()
    # получаем информацию о товаре
    info_product = await rq.get_info_product(id_product=int(callback.data.split('_')[2]))
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
                                     reply_markup=kb.keyboard_create_item(id_product=int(callback.data.split('_')[2]),
                                                                          count_item=count))


@router_shop.callback_query(F.data.startswith('add_item/'))
async def add_item_order(callback: CallbackQuery, bot: Bot):
    """
    Добавляем товар в корзину
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'add_item_order: {callback.message.chat.id} - {callback.data}')
    await callback.answer()
    # если нажата кнопка не Отмена
    if callback.data.split('/')[1] != 'cancel':
        # количество товара
        count_item = int(callback.data.split('/')[2])
        # id товара в таблице price
        id_product = int(callback.data.split('/')[1])
        # информация о товаре
        info_product = await rq.get_info_product(id_product=id_product)

        # получаем все заказы пользователя
        all_order_id = await rq.get_all_order_id(tg_id=callback.message.chat.id)
        # создаем новый заказ если у пользователя их нет или все завершены
        create_item = {}
        if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
            # словарь для заказа
            create_order = {}
            # формирование строки даты для номера заказа
            current_date = datetime.now()
            current_date_string = current_date.strftime('%m/%d/%y_%H:%M:%S')
            # уникальный номер заказа
            id_order = f'{callback.message.chat.id}_{current_date_string}'
            create_order['id_order'] = id_order
            create_order['telegram_id'] = callback.message.chat.id
            await rq.add_order(data=create_order)

            create_item['id_order'] = id_order
            create_item['telegram_id'] = callback.message.chat.id
            create_item['item'] = info_product.title
            create_item['count'] = count_item
            create_item['price'] = info_product.price
            await rq.add_item(data=create_item)
        # если есть незавершенный заказ
        else:
            create_item['id_order'] = all_order_id[-1].id_order
            create_item['telegram_id'] = callback.message.chat.id
            create_item['item'] = info_product.title
            create_item['count'] = count_item
            create_item['price'] = info_product.price
            await rq.add_item(data=create_item)
        # получаем заказы и товары пользователя для формирования списка текущего заказа
        all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
        all_order_id = await rq.get_all_order_id(tg_id=callback.message.chat.id)
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
        list_price = await rq.get_list_price()
        list_category = list(set([price.category for price in list_price]))
        await callback.message.answer(text='Товар добавлен в заказ',
                                      reply_markup=kb.keyboards_main_category(list_category=list_category,
                                                                              basket=total))
        await callback.message.answer(text=text,
                                      reply_markup=kb.keyboard_confirm_order(id_order=all_order_id[-1].id_order))
        try:
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id)
        except IndexError:
            pass
    else:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id)
        except IndexError:
            pass
        await callback.message.answer(text='Добавление товара отменено!')


@router_shop.callback_query(F.data.startswith('place_an_order/'))
async def place_an_order(callback: CallbackQuery, bot: Bot):
    """
    Нажата кнопка "Оформить заказ"
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'place_an_order: {callback.message.chat.id}')
    await callback.answer()
    count_item = int(callback.data.split('/')[2])
    id_product = int(callback.data.split('/')[1])
    info_product = await rq.get_info_product(id_product=id_product)
    all_order_id = await rq.get_all_order_id(tg_id=callback.message.chat.id)
    create_item = {}
    if not all_order_id or all_order_id[-1].status in ['complete', 'PAYED', 'cancelled']:
        create_order = {}
        # формирование строки даты для номера заказа
        current_date = datetime.now()
        current_date_string = current_date.strftime('%m/%d/%y_%H:%M:%S')
        # уникальный номер заказа
        id_order = f'{callback.message.chat.id}_{current_date_string}'
        create_order['id_order'] = id_order
        create_order['telegram_id'] = callback.message.chat.id
        await rq.add_order(data=create_order)

        create_item['id_order'] = id_order
        create_item['telegram_id'] = callback.message.chat.id
        create_item['item'] = info_product.title
        create_item['count'] = count_item
        create_item['price'] = info_product.price
        await rq.add_item(data=create_item)
    else:

        create_item['id_order'] = all_order_id[-1].id_order
        create_item['telegram_id'] = callback.message.chat.id
        create_item['item'] = info_product.title
        create_item['count'] = count_item
        create_item['price'] = info_product.price
        await rq.add_item(data=create_item)
    all_order_id = await rq.get_all_order_id(tg_id=callback.message.chat.id)
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
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
                                  reply_markup=kb.keyboards_main_menu(basket=total))
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except IndexError:
        pass
    await callback.message.answer(text='Подтвердите или измените заказ',
                                  reply_markup=kb.keyboard_confirm_order(id_order=all_order_id[-1].id_order))


@router_shop.callback_query(F.data.startswith('change#'))
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    """
    Изменение состава и количества товаров в заказе в процессе оформления
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    # получаем id заказа
    id_order = callback.data.split('#')[1]
    # обновляем state
    await state.update_data(id_order=id_order)
    # получаем все товары пользователя
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    list_item = []
    # проходим по всем товаром из текущего заказа и создаем список товаров
    for item in all_item_id:
        if item.id_order == id_order:
            list_item.append(item)
    # выводим клавиатуру с наименованием товаров и количеством
    await callback.message.edit_text(text='Выберите товар для изменения',
                                     reply_markup=kb.keyboards_list_item_change(list_item=list_item))


@router_shop.callback_query(F.data.startswith('itemchange_'))
async def item_change(callback: CallbackQuery, state: FSMContext):
    """
    Товар для изменения его в заказе при оформлении (Изменить-Удалить-Продолжить)
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'item_change: {callback.message.chat.id}')
    await callback.answer()
    user_dict[callback.message.chat.id] = await state.get_data()
    id_order = user_dict[callback.message.chat.id]['id_order']
    id_item = int(callback.data.split('_')[1])
    await callback.message.edit_text(text='Вы хотите изменить количество товара или удалить его из заказа?',
                                     reply_markup=kb.keyboard_change_item(id_item=id_item, id_order=id_order))


@router_shop.callback_query(F.data.startswith('itemdel#'))
async def process_item_change(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Удаление выбранного товара при оформлении заказа
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_item_change: {callback.message.chat.id}')
    await callback.answer()
    # id товара
    id_item = int(callback.data.split('#')[1])
    # удаление заказанного товара по его id в таблице Item
    await rq.delete_item(id_item=id_item)
    # обновляем словарь пользователя
    user_dict[callback.message.chat.id] = await state.get_data()
    # получаем id заказа
    id_order = user_dict[callback.message.chat.id]['id_order']
    # получаем все товары пользователя
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    text = 'Ваш заказ:\n\n'
    i = 0
    total = 0
    # формируем список товаров и их количество в заказе и итоговую стоимость
    for item in all_item_id:
        # если товар есть в заказе
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
    list_price = await rq.get_list_price()
    list_category = list(set([price.category for price in list_price]))
    await callback.message.answer(text=text,
                                  reply_markup=kb.keyboards_main_category(list_category=list_category, basket=total))
    try:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    except IndexError:
        pass
    await callback.message.answer(text='Подтвердите или измените заказ',
                                  reply_markup=kb.keyboard_confirm_order(id_order=id_order))


@router_shop.callback_query(F.data.startswith('itemchange#'))
async def process_item_change(callback: CallbackQuery, state: FSMContext):
    """
    Изменение количества выбранного товара при его оформлении
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'process_item_change: {callback.message.chat.id}')
    await callback.answer()
    id_item = int(callback.data.split('#')[1])
    await state.update_data(comma=0)

    info_item = await rq.get_info_item(id_item=id_item)
    await state.update_data(count_item=0)
    info_price = await rq.get_title(title=info_item.item)
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
                                     reply_markup=kb.keyboards_get_count(id_product=info_price.id,
                                                                         count_item=info_item.count))


@router_shop.callback_query(F.data.startswith('confirm#'))
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждение сформированного заказа
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'order_confirm: {callback.message.chat.id}')
    await callback.answer()
    id_order = callback.data.split('#')[1]
    all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
    total = 0
    for item in all_item_id:
        if item.id_order == id_order:
            total += (item.count / 10) * item.price
    await state.update_data(id_order=id_order)
    if total < 5000:
        await callback.message.edit_text(text='Минимальная сумма заказа 5000 руб.',
                                         reply_markup=None)
        await asyncio.sleep(1)
        # обновляем словарь пользователя
        user_dict[callback.message.chat.id] = await state.get_data()
        # получаем id заказа
        id_order = user_dict[callback.message.chat.id]['id_order']
        # получаем все товары пользователя
        all_item_id = await rq.get_all_item_id(tg_id=callback.message.chat.id)
        text = 'Ваш заказ:\n\n'
        i = 0
        total = 0
        # формируем список товаров и их количество в заказе и итоговую стоимость
        for item in all_item_id:
            # если товар есть в заказе
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
        list_price = await rq.get_list_price()
        list_category = list(set([price.category for price in list_price]))
        await callback.message.answer(text=text,
                                      reply_markup=kb.keyboards_main_category(list_category=list_category,
                                                                              basket=total))
    else:
        await callback.message.edit_text(text='Как бы вы хотели получить ваш заказ?',
                                         reply_markup=kb.keyboard_delivery())
