# -*- coding=utf-8 -*-
# @Author: wzy
# @Time: 2022/5/12
#

import telegram

TOKEN = "5318688479:AAGoz-uUmAPK3oiPQQcndmuHpSIVEAPIUXc"
GROUP_CHAT_ID = "-714275156"

tgBot = telegram.Bot(token=TOKEN)


def tg_bot_send_text(msg: str):
    tgBot.send_message(chat_id=GROUP_CHAT_ID, text=msg, timeout=15)


if __name__ == '__main__':
    pass
