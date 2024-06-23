from module.data_base import get_list_user
import logging


def check_user(telegram_id: int) -> bool:
    logging.info(f'check_user: {telegram_id}')
    list_user = get_list_user()
    for info_user in list_user:
        if info_user[0] == telegram_id:
            return True
    return False
