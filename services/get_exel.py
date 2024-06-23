import pandas as pd
from database.requests import get_list_users, get_list_product
from datetime import datetime


async def list_users_to_exel():
    dict_stat = {"№ п/п": [], "ID_telegram": [], "username": [], "name": [], "phone": []}
    i = 0
    list_user = await get_list_users()
    for user in list_user:
        i += 1
        dict_stat["№ п/п"].append(i)
        dict_stat["ID_telegram"].append(user.id)
        dict_stat["username"].append(user.username)
        dict_stat["name"].append(user.name)
        dict_stat["phone"].append(user.phone)
    df_stat = pd.DataFrame(dict_stat)
    with pd.ExcelWriter(path='./list_user.xlsx', engine='xlsxwriter') as writer:
        df_stat.to_excel(writer, sheet_name=f'Список пользователей', index=False)


async def list_price_to_exel():
    dict_stat = {"№ п/п": [], "Категория": [], "Название": [],  "Цена": []}
    current_date = datetime.now()
    current_date_string = current_date.strftime('%d.%m.%Y')
    i = 0
    for category in ['Фрукты', 'Овощи', 'Ягоды', 'Зелень']:
        list_price = await get_list_product(category=category)
        for price in list_price:
            i += 1
            dict_stat["№ п/п"].append(i)
            dict_stat["Категория"].append(category)
            dict_stat["Название"].append(price.title)
            dict_stat["Цена"].append(price.price)
    df_stat = pd.DataFrame(dict_stat)
    with pd.ExcelWriter(path='./list_price.xlsx', engine='xlsxwriter') as writer:
        df_stat.to_excel(writer, sheet_name=f'PRICE {current_date_string}', index=False)