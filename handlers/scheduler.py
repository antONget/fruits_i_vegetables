from services.googlesheets import get_list_all_rows
from keyboards.keybord_scheduler import keyboards_confirm_pay

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery
from config_data.config import Config, load_config
from database.requests import delete_all_rows_price, replication_database
import requests
import logging
config: Config = load_config()
router = Router()


async def database_replication():
    logging.info(f'database_replication')
    list_order_price = await get_list_all_rows()
    # await delete_all_rows_price()
    i = 0
    for row in list_order_price[1:]:
        dict_price = {}
        i += 1
        dict_price['id'] = i
        dict_price['category'] = row[0]
        dict_price['product'] = row[1]
        dict_price['title'] = row[2]
        dict_price['price'] = int(row[3])
        dict_price['status'] = row[4]
        print(dict_price)
        await replication_database(data=dict_price)

if __name__ == '__main__':
    import asyncio
    asyncio.run(database_replication())