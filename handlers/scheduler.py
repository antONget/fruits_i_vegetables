from services.googlesheets import get_list_all_rows
from config_data.config import Config, load_config
from database.requests import delete_price, replication_database
import logging
config: Config = load_config()


async def database_replication():
    logging.info(f'database_replication')
    list_order_price = await get_list_all_rows()
    await delete_price()
    i = 0
    for row in list_order_price[1:]:
        print(row)
        if row[4] == '✅' and '' not in row[1:4]:
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