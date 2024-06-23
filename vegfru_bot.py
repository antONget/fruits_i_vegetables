import asyncio
import logging

from aiogram import Bot, Dispatcher
from config_data.config import Config, load_config
from handlers import handler_user, other_handlers
from handlers.scheduler import database_replication
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(database_replication, 'cron', hour=0, minute=0)
    scheduler.start()
    # Регистрируем router в диспетчере
    dp.include_router(handler_user.router)
    dp.include_router(other_handlers.router)
    # Пропускаем накопившиеся update и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
