from database.models import User, Price, Order, Item
from database.models import async_session
from sqlalchemy.sql import and_
# Для тестов функций надо раскоментить, а выше закомменть
# from models import User
# from models import async_session


import logging
from dataclasses import dataclass
from sqlalchemy import select, update, delete

""" ------------- ADD METHODS -------------"""


async def add_user(data: dict):
    """
    Добавление пользователя в БД, если он еще в нее не добавлен
    :param data:
    :return:
    """
    logging.info(f'add_user {data}')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == data["id"]))
        print(user)
        if not user:
            session.add(User(**data))
            await session.commit()


async def add_order(data: dict):
    """
    Добавление нового заказа
    :param data:
    :return:
    """
    logging.info(f'add_order {data}')
    async with async_session() as session:
        session.add(Order(**data))
        await session.commit()


async def add_item(data: dict):
    """
    Добавление нового товара, если в этом заказе еще нет такого товара, иначе обновляем количество товара
    :param data:
    :return:
    """
    logging.info(f'add_item {data}')
    async with async_session() as session:
        item = await session.scalar(select(Item).where(and_(Item.item == data["item"], Item.id_order == data["id_order"])))
        # print(Item.item == data["item"], Item.item == data["id_order"])
        if not item:
            session.add(Item(**data))
            await session.commit()
        else:
            item.count = data['count']
            await session.commit()


async def replication_database(data: dict):
    """
    Добавление данных в таблицу Price (репликация с google-sheets)
    :param data:
    :return:
    """
    logging.info(f'replication_database {data}')
    async with async_session() as session:
        session.add(Price(**data))
        await session.commit()


""" ------------- GET METHODS -------------"""


async def get_list_users() -> list:
    """
    Получение списка пользователей занесенных в таблицу User
    :return:
    """
    logging.info(f'get_list_users')
    async with async_session() as session:
        user_scalar_result: User = await session.scalars(select(User))
        user_list_model = [item for item in user_scalar_result.all()]
        return user_list_model


async def get_user_info(tg_id: int):
    """
    Получение информации о пользователе по его id телеграм
    :param tg_id: id телеграм пользователя
    :return:
    """
    logging.info(f'get_user {tg_id}')
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user
        else:
            return False


async def get_list_price() -> list:
    """
    Получаем все данные из таблицы с товарами (Price)
    :return:
    """
    logging.info(f'get_list_price')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model


async def get_list_product(category: str) -> list:
    """
    Получаем список продуктов по их категории
    :param category: название категории товара
    :return:
    """
    logging.info(f'get_list_product: {category}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price).where(Price.category == category))
        logging.info(f'{price_scalar_result}')
        price_list_model = [item for item in price_scalar_result.all()]
        logging.info(f'{price_list_model}')
        return price_list_model


async def get_product(product: str) -> list:
    """
    Получаем информацию о товарах по названию продукта
    :param product: название продукта товара (Лук - Лук красный)
    :return:
    """
    logging.info(f'get_list_product: {product}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price).where(Price.product == product))
        logging.info(f'{price_scalar_result}')
        price_list_model = [item for item in price_scalar_result.all()]
        logging.info(f'{price_list_model}')
        return price_list_model


async def get_title(title: str):
    """
    Получаем информацию о товаре по его названию
    :param title: название товара
    :return:
    """
    logging.info(f'get_list_product: {title}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalar(select(Price).where(Price.title == title))
        return price_scalar_result


async def get_info_product(id_product: int):
    """
    Получаем информацию о товаре по его id в таблице Price
    :param id_product: id в таблице Price
    :return:
    """
    logging.info(f'get_list_product: {id_product}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalar(select(Price).where(Price.id == id_product))
        return price_scalar_result


async def get_all_order_id(tg_id: int) -> list:
    """
    Получаем все заказы пользователя по его id телеграм
    :param tg_id: id телеграм пользователя
    :return:
    """
    logging.info(f'get_last_order')
    async with async_session() as session:
        price_scalar_result: Order = await session.scalars(select(Order).where(Order.telegram_id == tg_id))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model


async def get_info_order(id_order: str):
    """
    Получаем информацию о заказе по его id_order
    :param id_order: содержит id телеграм пользователя и время заказа
    :return:
    """
    logging.info(f'get_info_order: {id_order}')
    async with async_session() as session:
        order_scalar_result: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        return order_scalar_result


async def get_all_item_id(tg_id: int) -> list:
    """
    Получаем все товары пользователя по его id телеграм
    :param tg_id: id телеграм пользователя
    :return:
    """
    logging.info(f'get_last_order')
    async with async_session() as session:
        price_scalar_result: Item = await session.scalars(select(Item).where(Item.telegram_id == tg_id))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model


async def get_info_item(id_item: int):
    """
    Получаем информацию о заказанном товаре по его id в таблице Item
    :param id_item: id в таблице Item
    :return:
    """
    logging.info(f'get_list_product: {id_item}')
    async with async_session() as session:
        price_scalar_result: Item = await session.scalar(select(Item).where(Item.id == id_item))
        return price_scalar_result

""" ------------- UPDATE -------------"""


@dataclass
class OrderStatus:
    create = 'create'
    delivery = 'delivery'
    pickup = 'pickup'
    complete = 'complete'
    payed = 'PAYED'
    cancelled = 'cancelled'


async def update_status(id_order: str, status: OrderStatus):
    """
    Обновляем статус заказа по его id_order в таблице Order
    :param id_order: строка из id телеграм и даты формирования заказа
    :param status: ('create', 'delivery', 'pickup', 'complete', 'PAYED')
    :return:
    """
    logging.info(f'update_status')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.status = status
            await session.commit()


async def update_address(id_order: str, address: str):
    """
    Обновляем адрес для заказа по его id_order в таблице Order
    :param id_order: строка из id телеграм и даты формирования заказа
    :param address: строка с адресом доставки
    :return:
    """
    logging.info(f'update_status')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.address_order = address
            await session.commit()


async def update_comment(id_order: str, comment: str):
    """
    Обновляем комментарий для заказа по его id_order в таблице Order
    :param id_order: строка из id телеграм и даты формирования заказа
    :param comment: строка с комментрием
    :return:
    """
    logging.info(f'update_comment')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.comment = comment
            await session.commit()


async def update_amount(id_order: str, amount: int):
    """
    Обновляем сумму заказа по его id_order в таблице Order
    :param id_order: строка из id телеграм и даты формирования заказа
    :param amount: сумма заказа
    :return:
    """
    logging.info(f'update_amount')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.comment = amount
            await session.commit()


async def update_name_phone(tg_id: int, name: str, phone: str):
    """
    Обновляем имя и телефон пользователя по его id телеграм в таблице User
    :param tg_id: id телеграм пользователя
    :param name: имя пользователя
    :param phone: телефон пользователя
    :return:
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            user.name = name
            user.phone = phone
            await session.commit()


""" ------------- DELETE -------------"""


async def delete_item(id_item: int):
    """
    Удаление заказанного товара по его id в таблице Item
    :param id_item: id в таблице Item
    :return:
    """
    async with async_session() as session:
        await session.execute(delete(Item).where(Item.id == id_item))
        await session.commit()


async def delete_price():
    """
    Полная очистка таблицы Price от данных
    :return:
    """
    async with async_session() as session:
        await session.execute(delete(Price))
        await session.commit()