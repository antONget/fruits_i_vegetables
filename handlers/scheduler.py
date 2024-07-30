from services.googlesheets import get_list_all_rows
from config_data.config import Config, load_config
from database.requests import delete_price, replication_database
import logging
config: Config = load_config()


async def database_replication():
    """
    Репликация гугл-таблицы с БД
    :return:
    """
    logging.info(f'database_replication')
    # получаем все строки из гугл-таблицы
    list_order_price = await get_list_all_rows()
    # полная очистка таблицы Price от данных
    await delete_price()
    # счетчик строк
    i = 0

    # проходим по всем строкам начиная с первой
    for row in list_order_price[1:]:
        # если статус товара в наличии и все ячейки строки заполнены
        if row[4] == '✅' and '' not in row[1:4]:
            # словарь для обновления таблицы Price
            dict_price = {}
            # увеличиваем счетчик
            i += 1
            # создаем
            dict_price['id'] = i
            dict_price['category'] = row[0]
            dict_price['product'] = row[1]
            dict_price['title'] = row[2]
            dict_price['price'] = int(row[3])
            dict_price['status'] = row[4]
            # Добавление данных в таблицу Price (репликация с google-sheets)
            await replication_database(data=dict_price)


if __name__ == '__main__':
    import asyncio
    asyncio.run(database_replication())