#! /usr/bin/env python3

from turtle import up
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup as MU
from telepot.namedtuple import InlineKeyboardButton as BT
import config
from mbl import Upbit
from mbl import Binance

mc = config.Telegram.mc
bot = telepot.Bot(config.Telegram.token)
upbit = Upbit(config.Upbit.access_key, config.Upbit.secret_key)
binance = Binance(config.Binance.access_key,config.Binance.secret_key)


def exSelection(msg):
    btn1 = BT(text='Upbit', callback_data='upbit')
    btn2 = BT(text='Binance', callback_data='binance')
    mu = MU(inline_keyboard = [[btn1, btn2]])
    bot.sendMessage(mc, '거래소를 선택하세요', reply_markup = mu)

def btnShowUpbit():
    btn1 = BT(text='Buy', callback_data='buy_u')
    btn2 = BT(text='Sell', callback_data='sell_u')
    btn3 = BT(text='Balance', callback_data='balance_u')
    mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
    bot.sendMessage(mc, 'Upbit에서 살까요 팔까요?', reply_markup = mu)

def btnShowBinance():
    btn1 = BT(text='Buy', callback_data='buy_b')
    btn2 = BT(text='Sell', callback_data='sell_b')
    btn3 = BT(text='Borrow', callback_data='borrow_b')
    btn4 = BT(text='Repay', callback_data='repay_b')
    mu = MU(inline_keyboard = [[btn1, btn2, btn3, btn4]])
    bot.sendMessage(mc, 'Binance 에서 뭘 할까요?', reply_markup = mu)


def query_ans(msg):
    query_data = msg["data"]
    if query_data == 'upbit':
        btnShowUpbit()
    elif query_data == 'binance':
        btnShowBinance()
    elif query_data == 'buy_u':
        bot.sendMessage(mc, text="업비트에서 {} 삽니다".format(config.ticker))
    elif query_data == 'sell_u':
        bot.sendMessage(mc, text="업비트에서 {} 팝니다".format(config.ticker))
    elif query_data == 'balance_u':
        balance = upbit.getBalance('KRW')
        bot.sendMessage(mc, text="업비트의 현재 잔고는 {:.0f}원 입니다".format(balance))
    elif query_data == 'buy_b':
        bot.sendMessage(mc, text="바이낸스에서 {} 삽니다".format(config.ticker))
    elif query_data == 'sell_b':
        bot.sendMessage(mc, text="바이낸스에서 {} 팝니다".format(config.ticker))
    elif query_data == 'borrow_b':
        bot.sendMessage(mc, text="바이낸스에서 {} 빌립니다".format(config.ticker))
    elif query_data == 'repay_b':
        msg = binance.repay(config.ticker, binance.getMarginBalance(config.ticker, 'net'))
        msg_isol = binance.repayIsol(config.ticker, binance.getMarginBalanceIsol(config.ticker, 'net'))
        bot.sendMessage(mc, text='{} {}'.format(msg, msg_isol))


MessageLoop(bot, {'chat':exSelection , 'callback_query' : query_ans}).run_forever()