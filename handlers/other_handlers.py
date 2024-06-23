from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile

from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state

from database.requests import get_list_users, get_user_info
from config_data.config import Config, load_config
from services.get_exel import list_users_to_exel
from services.googlesheets import get_list_all_rows

import asyncio
import logging
import requests as r

router = Router()
config: Config = load_config()


class Admin(StatesGroup):
    message_id = State()
    message_all = State()


def get_telegram_user(user_id, bot_token):
    url = f'https://api.telegram.org/bot{bot_token}/getChat'
    data = {'chat_id': user_id}
    response = r.post(url, data=data)
    return response.json()


@router.callback_query()
async def all_calback(callback: CallbackQuery) -> None:
    logging.info(f'all_callback: {callback.message.chat.id}')


@router.message(StateFilter(Admin.message_id))
async def all_message(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info(f'Admin.message_id')
    message_id = message.html_text
    data = await state.get_data()
    id_user = int(data['id_user'])
    await bot.send_message(chat_id=id_user,
                           text=message_id,
                           parse_mode='html')
    await message.answer(text='Сообщение отправлено')
    await state.set_state(default_state)


@router.message(StateFilter(Admin.message_all))
async def all_message(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info(f'Admin.message_id')
    message_all = message.html_text
    list_user = await get_list_users()
    await message.answer(text='Рассылка запущена...')
    for user in list_user:
        result = get_telegram_user(user_id=user.id,
                                   bot_token=config.tg_bot.token)
        if 'result' in result:
            await asyncio.sleep(0.1)
            try:
                await bot.send_message(chat_id=user[1],
                                       text=message_all,
                                       parse_mode='html')
            except:
                pass
    await message.edit_text(text='Рассылка завершена...')
    await state.set_state(default_state)


@router.message()
async def all_message(message: Message, state: FSMContext) -> None:
    logging.info(f'all_message')
    if message.photo:
        logging.info(f'all_message message.photo')
        print(message.photo[-1].file_id)

    if message.video:
        logging.info(f'all_message message.photo')
        print(message.video.file_id)

    if message.sticker:
        logging.info(f'all_message message.sticker')

    list_super_admin = list(map(int, config.tg_bot.admin_ids.split(',')))
    if message.chat.id in list_super_admin:
        logging.info(f'all_message message.admin')

        if message.text == '/get_logfile':
            logging.info(f'all_message message.admin./get_logfile')
            file_path = "py_log.log"
            await message.answer_document(FSInputFile(file_path))

        if message.text == '/get_dbfile':
            logging.info(f'all_message message.admin./get_dbfile')
            file_path = "database/db.sqlite3"
            await message.answer_document(FSInputFile(file_path))

        if message.text == '/get_listusers':
            logging.info(f'all_message message.admin./get_listusers')
            list_user = await get_list_users()
            text = 'Список пользователей:\n'
            for i, user in enumerate(list_user):
                text += f'{i+1}. {user.id} - @{user.username} - {user.name} - {user.phone}\n'
                if i % 10 == 0 and i > 0:
                    await asyncio.sleep(0.2)
                    await message.answer(text=text)
                    text = ''
            await message.answer(text=text)
            await list_users_to_exel()
            file_path = "list_user.xlsx"
            await message.answer_document(FSInputFile(file_path))

        if '/send_message' in message.text:
            logging.info(f'all_message-/send_message')
            send = message.text.split('_')
            if send[2] == "all":
                await message.answer(text='Пришлите текст чтобы его отправить всем пользователям бота')
                await state.set_state(Admin.message_all)
            else:
                try:
                    id_user = int(send[2])
                    info_user = await get_user_info(tg_id=id_user)
                    if info_user:
                        result = get_telegram_user(user_id=id_user,
                                                   bot_token=config.tg_bot.token)
                        if 'result' in result:
                            await message.answer(text=f'Пришлите текст чтобы его отправить пользователю @{info_user.username}')
                            await state.update_data(id_user=id_user)
                            await state.set_state(Admin.message_id)
                        else:
                            await message.answer(text=f'Бот не нашел пользователя {info_user.username}.'
                                                      f' Возможно он его заблокировал')
                    else:
                        await message.answer(text=f'Бот не нашел пользователя {id_user} в БД')
                except:
                    await message.answer(text=f'Пришлите после команды /send_message_ id телеграм пользователя')

        if message.text == '/googleshhets':
            list_all_rows = await get_list_all_rows()
            print(list_all_rows[0])

