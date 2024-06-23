import gspread
import logging
# TEST
# gp = gspread.service_account(filename='services/test.json')
gp = gspread.service_account(filename='/Users/antonponomarev/PycharmProjects/vegetables_fruits/services/test.json')
gsheet = gp.open('Овощи и Фрукты')
sheet = gsheet.worksheet("price")


async def append_row() -> None:
    logging.info(f'append_row')
    sheet.append_row([])


async def get_list_all_rows() -> list:
    logging.info(f'get_list_all_rows')
    values = sheet.get_all_values()
    list_product = []
    for item in values:
        list_product.append(item)
    return list_product


async def get_list_one_row(row: int) -> list:
    logging.info(f'get_list_one_row')
    username_referer = sheet.row_values(row=row)
    return username_referer


async def update_cell(status: str, telegram_id: int) -> None:
    logging.info(f'update_status_anketa: {telegram_id}')
    values = sheet.get_all_values()
    id_anketa = 0
    for i, row in enumerate(values[1:]):
        if int(row[1]) == telegram_id:
            id_anketa = i
    sheet.update_cell(row=id_anketa+2, col=10, value=status)
