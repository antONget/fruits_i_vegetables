from aiogram.types import CallbackQuery, LinkPreviewOptions
from aiogram import Bot, Router, F

import logging
from services.googlesheets import get_list_anketa, update_status_anketa
from handlers.scheduler import send_ton
from TonCrypto.contract.CryptoHelper import TonWallet
from database.requests import increase_ton_balance, update_status, UserStatus, _get_username_from_id,\
    update_user_ton_addr, get_user_ton_addr_by_id, get_user_from_id

router = Router()


@router.callback_query(F.data.startswith('schcancel_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Отмена начисления вознаграждения, изменяем статус анкеты и запускаем поиск нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}-{callback.data}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} отменено', show_alert=True)
    update_status_anketa(status='❌', telegram_id=int(info_anketa[1]))
    try:
        await bot.send_message(chat_id=int(info_anketa[1]),
                               text='Оплата была не одобрена администрацией')
    except:
        pass
    await callback.answer()
    await send_ton(bot=bot)


@router.callback_query(F.data.startswith('schconfirm_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Подтверждение начисления вознаграждения пользователю и его рефереру, запуск поиска нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}-{callback.data}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    user = await get_user_from_id(int(info_anketa[1]))
    if user.status != UserStatus.payed:
        await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} подтверждено', show_alert=True)
        user_id = info_anketa[1]
        user_addr = await get_user_ton_addr_by_id(user_id)

        tr = await TonWallet.transfer(amount=0.001, to_addr=user_addr)
        if tr == 'ok':
            await increase_ton_balance(tg_id=int(info_anketa[1]), s=0.001)
            update_status_anketa(status='💰', telegram_id=int(info_anketa[1]))
            await update_status(int(info_anketa[1]), UserStatus.payed)

            try:
                await bot.send_message(chat_id=int(info_anketa[1]),
                                       text=f'Вам было отправлено 0.001 TON\n\n'
                                            f'Проверьте ваш кошелек'
                                            f' <a href="https://tonscan.org/address/{user_addr}>кошелек.</a>',
                                       parse_mode='html',
                                       link_preview_options=LinkPreviewOptions(is_disabled=True))
            except:
                pass
        if int(info_anketa[3]):
            tr = await TonWallet.transfer(amount=0.001, to_addr=user_addr)
            if tr == 'ok':

                await increase_ton_balance(tg_id=int(info_anketa[3]), s=0.001)

                try:
                    await bot.send_message(chat_id=int(info_anketa[3]),
                                           text=f'Вам отправлено <strong>0.15 TON</strong> за приглашенного пользователя'
                                                f' @{await _get_username_from_id(int(info_anketa[1]))}',
                                           parse_mode='html')
                except:
                    pass
    else:
        await callback.answer(text='Этот пользователь уже получил вознаграждение!',
                              show_alert=True)
    await callback.answer()
    await send_ton(bot=bot)
