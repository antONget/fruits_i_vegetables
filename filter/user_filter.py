from database.requests import get_list_users
import logging
import re


async def check_user(telegram_id: int) -> bool:
    logging.info(f'check_user: {telegram_id}')
    list_user = await get_list_users()
    for info_user in list_user:
        if info_user.id == telegram_id:
            return True
    return False


def validate_russian_phone_number(phone_number):
    # Паттерн для российских номеров телефона
    # Российские номера могут начинаться с +7, 8, или без кода страны
    pattern = re.compile(r'^(\+7|8|7)?(\d{10})$')
    # Проверка соответствия паттерну
    match = pattern.match(phone_number)
    return bool(match)