from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile
from aiogram.types import ErrorEvent
from aiogram.fsm.storage.redis import RedisStorage, Redis

# import aioredis
from config_data.config import Config, load_config
from handlers import handler_user, other_handlers
from handlers.handler_shop import router_shop
from handlers.handler_get_order import router

import asyncio
import logging
import traceback
# Инициализируем logger
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    # create_table_users()
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        # filename="py_log.log",
        # filemode='w',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token)
    storage = RedisStorage.from_url('redis://127.0.0.1:6379/0')
    dp = Dispatcher(storage=storage)

    # Регистрируем router в диспетчере
    dp.include_router(handler_user.router)
    dp.include_routers(router_shop, router)
    dp.include_router(other_handlers.router)

    @dp.error()
    async def error_handler(event: ErrorEvent):
        logger.critical("Критическая ошибка: %s", event.exception, exc_info=True)
        await bot.send_message(chat_id=config.tg_bot.admin_ids,
                               text=f'{event.exception}')
        formatted_lines = traceback.format_exc()
        text_file = open('error.txt', 'w')
        text_file.write(str(formatted_lines))
        text_file.close()
        await bot.send_document(chat_id=config.tg_bot.admin_ids,
                                document=FSInputFile('error.txt'))


    # Пропускаем накопившиеся update и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
