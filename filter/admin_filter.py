from config_data.config import load_config, Config
import logging

config: Config = load_config()


def check_super_admin(telegram_id: int) -> bool:
    """
    Проверка на администратора
    :param telegram_id: id пользователя телеграм
    :return: true если пользователь администратор, false в противном случае
    """
    logging.info('cheсk_manager')
    list_super_admin = config.tg_bot.admin_ids.split(',')
    print("list_super_admin", list_super_admin, str(telegram_id) in list_super_admin)
    return str(telegram_id) in list_super_admin




