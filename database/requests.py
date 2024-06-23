from database.models import User, Price, Order, Item
from database.models import async_session
from sqlalchemy.sql import and_
# Для тестов функций надо раскоментить, а выше закомменть
# from models import User
# from models import async_session


import logging
from dataclasses import dataclass
from sqlalchemy import select  # , update, delete

""" ------------- ADD METHODS -------------"""


async def add_user(data: dict):
    logging.info(f'add_user {data}')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == data["id"]))
        print(user)
        if not user:
            session.add(User(**data))
            await session.commit()


async def add_order(data: dict):
    logging.info(f'add_order {data}')
    async with async_session() as session:
        session.add(Order(**data))
        await session.commit()


async def add_item(data: dict):
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
    logging.info(f'replication_database {data}')
    async with async_session() as session:
        session.add(Price(**data))
        await session.commit()


""" ------------- GET METHODS -------------"""


async def get_list_users():
    logging.info(f'get_list_users')
    async with async_session() as session:
        user_scalar_result: User = await session.scalars(select(User))
        user_list_model = [item for item in user_scalar_result.all()]
        return user_list_model


async def get_user_info(tg_id: int):
    logging.info(f'get_user {tg_id}')
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user
        else:
            return False


async def get_list_price():
    logging.info(f'get_list_price')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model


async def get_list_product(category: str):
    logging.info(f'get_list_product: {category}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price).where(Price.category == category))
        logging.info(f'{price_scalar_result}')
        price_list_model = [item for item in price_scalar_result.all()]
        logging.info(f'{price_list_model}')
        return price_list_model


async def get_product(product: str):
    logging.info(f'get_list_product: {product}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalars(select(Price).where(Price.product == product))
        logging.info(f'{price_scalar_result}')
        price_list_model = [item for item in price_scalar_result.all()]
        logging.info(f'{price_list_model}')
        return price_list_model


async def get_title(title: str):
    logging.info(f'get_list_product: {title}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalar(select(Price).where(Price.title == title))
        return price_scalar_result


async def get_info_product(id_product: int):
    logging.info(f'get_list_product: {id_product}')
    async with async_session() as session:
        price_scalar_result: Price = await session.scalar(select(Price).where(Price.id == id_product))
        return price_scalar_result


async def get_all_order_id(tg_id: int):
    logging.info(f'get_last_order')
    async with async_session() as session:
        price_scalar_result: Order = await session.scalars(select(Order).where(Order.telegram_id == tg_id))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model


async def get_all_item_id(tg_id: int):
    logging.info(f'get_last_order')
    async with async_session() as session:
        price_scalar_result: Item = await session.scalars(select(Item).where(Item.telegram_id == tg_id))
        price_list_model = [item for item in price_scalar_result.all()]
        return price_list_model

async def get_info_item(id_item: int):
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


async def update_status(id_order: str, status: OrderStatus):
    logging.info(f'update_status')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.status = status
            await session.commit()


async def update_address(id_order: str, address: str):
    logging.info(f'update_status')
    async with async_session() as session:
        order: Order = await session.scalar(select(Order).where(Order.id_order == id_order))
        if order:
            order.address_order = address
            await session.commit()


async def update_name_phone(tg_id: int, name: str, phone: str):
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            user.name = name
            user.phone = phone
            await session.commit()


""" ------------- DELETE -------------"""


async def delete_all_rows_price():
    async with async_session() as session:
        session.scalar(select(Price).delete())
        session.commit()
