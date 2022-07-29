#! /usr/bin/env python3

import config
import time
import atexit
import requests
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton as BT
from telepot.namedtuple import InlineKeyboardMarkup as MU
from upbit import Upbit
from bithumb import Bithumb
from binance_ex import Binance
from autotrade import Autotrade

class Telegram:
    def __init__(self, token, mc) -> None:
        self.bot = telepot.Bot(token)
        self.mc = mc
        self.ticker = config.ticker
        self.buy_point = config.buy_point
        self.sell_point = config.sell_point
        self.amount = config.amount
        self.settings = dict( Auto_trading = True, Cross = True, Isolated = True)
        self.isolated = True
        self.start_msg = """
        BOT 기본 명령어
        1. /명령어 : 명령어 표시
        2. /상태 : 봇의 설정값을 조회
        3. /티커변경 티커 : 기준 티커 변경
        4. /잔고조회 : 업비트 원화, 바이낸스 USDT 잔고 조회
        5. /프리미엄 : 티커의 현재 프리미엄 값을 조회
        6. /자동거래 시작 : 자동거래를 시작
        7. /자동거래 종료 : 자동거래를 종료 
        8. /자동거래 변경 거래소1 거래소2 : 자동거래에 사용되는 거래소 변경, main = 거래소1, sub = 거래소2
        9. /원클릭매수 : 현재 프리미엄으로 업비트에서 매수, 바이낸스에서 마진 매도
        10. /원클릭매도 : 현재 프리미엄으로 업비트에서 매도, 바이낸스에서 마진 매수
        11. /교차 활성화 : 자동거래시 Cross를 사용
        12. /교차 비활성화 : 자동거래시 Cross를 사용하지 않음
        13. /교차 대여 수량 : Cross에서 수량 만큼 대여함 
        14. /교차 상환 수량 : Cross에서 수량 만큼 상환함 
        15. /격리 활성화 : 자동거래시 Isolated를 사용
        16. /격리 비활성화 : 자동거래시 Isolated를 사용하지 않음
        17. /격리 대여 수량 : Isolated에서 수량 만큼 대여함
        18. /격리 상환 수량 : Isolated에서 수량 만큼 상환함
        19. /대여수량조회 : 바이낸스 Cross/Isolated 대여 수량 및 한도 조회
        20. /매매기준변경 buy sell : 매매 기준점 변경. 기준 프리미엄 숫자 입력
        21. /매매수량변경 amount : 총 매매 수량 변경
        22. /아이피조회 : 현재 서버의 ip를 조회함
        23. /매매테스트 : 자동거래가 잘 이루어 지는지 최소 금액으로 거래 테스트
        24. /후원주소조회 : 개발자를 후원할 수 있는 주소를 조회함
        """
    
    def send(self, msg: str):
        return self.bot.sendMessage(self.mc, msg)

    def sendBtn(self, msg: str, mu):
        return self.bot.sendMessage(self.mc, msg, reply_markup = mu)

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text' and chat_id == int(self.mc):
            _message = msg['text']
            if _message[0:1] == '/': # 명령어
                self.execCmd(_message)

    def execCmd(self, msg: str):
        args = msg.split(' ')
        command = args[0]
        del args[0]

        if command == '/명령어':
            self.send(self.start_msg)
        elif command == '/상태':
            self.stateDisplay()
        elif command == '/티커변경':
            self.ticker = args[0]
            self.send("티커 {} 로 변경 완료!".format(args[0]))
        elif command == '/잔고조회':
            self.exSelection()
        elif command == '/프리미엄':
            premium = autotrade.getPremium(self.ticker)
            self.send("현재 {} 프리미엄은 {:.3f}입니다.".format(self.ticker, premium))
        elif command == '/자동거래':
            if args[0] == '시작':
                self.settings["Auto_trading"] = True
                bot.send("자동거래를 시작합니다.")
            elif args[0] == '종료':
                self.settings["Auto_trading"] = False
                bot.send("자동거래를 종료합니다.")
            elif args[0] == "변경":
                if args[1] == "업비트":
                    autotrade.main = upbit
                elif args[1] == "빗썸":
                    autotrade.main = bithumb
                elif args[1] == "바이낸스":
                    autotrade.main = binance
                if args[2] == "업비트":
                    autotrade.sub = upbit
                elif args[2] == "빗썸":
                    autotrade.sub = bithumb
                elif args[2] == "바이낸스":
                    autotrade.sub = binance
                bot.send("메인 거래소를 {}, 서브 거래소를 {}로 변경합니다.".format(args[1], args[2]))

        elif command == '/원클릭매수':
            autotrade.autoBuy(self.ticker, self.amount)
        elif command == '/원클릭매도':
            autotrade.autoSell(self.ticker, self.amount)
        elif command == '/교차':
            self.setMargin('Cross', args)
        elif command == '/격리':
            if args[0] == "활성화":
                self.isolated = True
                bot.send("다음부터 자동거래시 Isolated를 사용합니다.")
            elif args[0] == "비활성화":
                self.isolated = False
                bot.send("다음부터 자동거래시 Isolated를 사용하지 않습니다.")
            elif args[0] == "대여":
                msg = binance.borrowIsol(self.ticker, float(args[1]))
                bot.send(msg)
            elif args[0] == "상환":
                msg = binance.repayIsol(self.ticker, float(args[1]))
                bot.send(msg)
        elif command == '/대여수량조회':
            borrowCheck(self.ticker)
        elif command == '/매매기준변경':
            self.buy_point = float(args[0])
            self.sell_point = float(args[1])
            self.send("매매 기준점 변경. 다음부터 {}% 이하에서 업비트 매수/바이낸스 매도, {}% 이상에서 업비트 매도/바이낸스 매수합니다.".format(self.buy_point, self.sell_point))
        elif command == '/매매수량변경':
            self.amount = float(args[0])
            self.send("매매 수량 변경. 다음부터 업비트에서 {}개를 매매합니다.".format(self.amount))
        elif command == '/아이피조회':
            self.send(requests.get("http://ip.jsontest.com").json()['ip'])
        elif command == '/매매테스트':
            self.exSelection2()
        elif command == '/후원주소조회':
            self.send("0x1C42F0F4cFf71173C333CFc09206ab44b40e99fA")
            self.send("위 주소를 통해 이더리움, bnb, 클레이튼 등 다양한 토큰을 후원할수 있습니다. 여러분의 작은 후원이 개발자에겐 큰 힘이 됩니다.")

    def stateDisplay(self):
        self.send("현재 설정된 메인거래소 : {}, 서브거래소 : {}".format(autotrade.main.name, autotrade.sub.name))
        self.send("현재 설정된 티커 {}.".format(self.ticker))
        self.send("현재 설정된 구매시작점 {}%, 매도 시작점 {}%.".format(self.buy_point, self.sell_point))
        self.send("현재 설정된 총 매매수량 {}개.".format(self.amount))

        for key in self.settings:
            if self.settings[key]:
                self.send("{} 사용 설정 됨".format(key))
            else:
                self.send("{} 미사용 설정 됨".format(key))

    def setMargin(self, key, args):
        if args[0] == "활성화":
            self.settings[key] = True
            bot.send("다음부터 자동거래시 {}를 사용합니다.".format(key))
        elif args[0] == "비활성화":
            self.settings[key] = False
            bot.send("다음부터 자동거래시 {}를 사용하지 않습니다.".format(key))
        elif args[0] == "대여":
            msg = binance.borrow(self.ticker, float(args[1]))
            bot.send(msg)
        elif args[0] == "상환":
            msg = binance.repay(self.ticker, float(args[1]))
            bot.send(msg)

    def exSelection(self):
        btn1 = BT(text='업비트', callback_data='upbit_balance')
        btn2 = BT(text='바이낸스', callback_data='binance_balance')
        mu = MU(inline_keyboard = [[btn1, btn2]])
        self.sendBtn('거래소를 선택하세요', mu)

    def exSelection2(self):
        btn1 = BT(text='업비트', callback_data='upbit_test')
        btn2 = BT(text='바이낸스 Cross', callback_data='binance_cross_test')
        btn3 = BT(text='바이낸스 Isolated', callback_data='binance_isolated_test')
        mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
        self.sendBtn('테스트할 거래소를 선택하세요', mu)

    def upbitTest(self):
        btn1 = BT(text='사기', callback_data='upbit_buy')
        btn2 = BT(text='팔기', callback_data='upbit_sell')
        mu = MU(inline_keyboard = [[btn1, btn2]])
        self.sendBtn('테스트할 거래를 선택하세요. 거래는 업비트에서 {}를 6천원 가량 사거나 팝니다'.format(self.ticker), mu)

    def binanceCrossTest(self):
        btn1 = BT(text='빌리기', callback_data='binance_borrow_cross')
        btn2 = BT(text='사기', callback_data='binance_buy_cross')
        btn3 = BT(text='팔기', callback_data='binance_sell_cross')
        mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
        self.sendBtn('테스트할 거래를 선택하세요. 거래는 바이낸스 Cross에서 {}를 20달러 가량 빌리거나 사거나 팝니다'.format(self.ticker), mu)

    def binanceIsolTest(self):
        btn1 = BT(text='빌리기', callback_data='binance_borrow_isol')
        btn2 = BT(text='사기', callback_data='binance_buy_isol')
        btn3 = BT(text='팔기', callback_data='binance_sell_isol')
        mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
        self.sendBtn('테스트할 거래를 선택하세요. 거래는 바이낸스 Isolated에서 {}를 20달러 가량 빌리거나 사거나 팝니다'.format(self.ticker), mu)

upbit = Upbit(config.Upbit.access_key, config.Upbit.secret_key)
bithumb = Bithumb(config.Bithumb.access_key, config.Bithumb.secret_key)
binance = Binance(config.Binance.access_key,config.Binance.secret_key)
autotrade = Autotrade(upbit, binance)
bot = Telegram(config.Telegram.token, config.Telegram.mc)

def getPremium(ticker: str = 'BTC'):
    btc_krw = upbit.getPrice('BTC')
    btc_usdt = binance.getPrice('BTC')
    krw_price = upbit.getPrice(ticker)
    usdt_price = binance.getPrice(ticker)
    if str(type(usdt_price)) == "<class 'float'>" and krw_price != 0:
        ref_er = btc_krw/btc_usdt
        tar_er = krw_price/usdt_price
        return tar_er/ref_er
    else:
        return -1

def borrowCheck(ticker):
    cross_msg = binance.getMaxMarginLoan(ticker)
    isol_msg = binance.getMaxMarginLoanIsol(ticker)
    bot.send(cross_msg)
    bot.send(isol_msg)

def autoBuy():
    upbit_msg = upbit.buyMarket(bot.ticker, bot.amount)
    binance_cross_msg = ""
    binance_isolated_msg = ""
    if bot.cross:
        binance_cross_msg = binance.marginSell(bot.ticker, binance.getMarginBalance(bot.ticker))
    if bot.isolated:
        binance_isolated_msg = binance.marginSellIsol(bot.ticker, binance.getMarginBalanceIsol(bot.ticker))
    bot.send("매수 완료. {} {} {}".format(upbit_msg, binance_cross_msg, binance_isolated_msg))

def autoSell():
    upbit_msg = upbit.sellMarket(bot.ticker, upbit.getBalance(bot.ticker))
    binance_cross_msg = ""
    binance_isolated_msg = ""
    if bot.cross:
        binance_cross_msg = binance.marginBuy(bot.ticker, -binance.getMarginBalance(bot.ticker, 'netAsset'))
    if bot.isolated:
        binance_isolated_msg = binance.marginBuyIsol(bot.ticker, -binance.getMarginBalanceIsol(bot.ticker, 'netAsset'))
    bot.send("매도 완료. {} {} {}".format(upbit_msg, binance_cross_msg, binance_isolated_msg))

def handle_exit():
    bot.send("자동거래 서버 종료!")

atexit.register(handle_exit) 

def query_ans(msg):
    query_data = msg["data"]
    if query_data == 'upbit_balance':
        balance = upbit.getBalance('KRW')
        bot.send("업비트 잔고 {:.0f}원 입니다.".format(balance))
    elif query_data == 'binance_balance':
        balance = binance.getMarginBalance('USDT')
        balance_isol = binance.getMarginBalanceIsol('USDT')
        bot.send("바이낸스 Cross 잔고 {:.2f}USDT 입니다.".format(balance))
        bot.send("바이낸스 Isolated 잔고 {:.2f}USDT 입니다.".format(balance_isol))
    elif query_data == 'upbit_test':
        bot.upbitTest()
    elif query_data == 'binance_cross_test':
        bot.binanceCrossTest()
    elif query_data == 'binance_isolated_test':
        bot.binanceIsolTest()
    elif query_data == 'upbit_buy':
        price = upbit.getPrice(bot.ticker)
        if price == 0:
            bot.send("업비트에서 {}의 가격을 불러올 수 없습니다.".format(bot.ticker))
        else:
            msg = upbit.buyMarket(bot.ticker, 6000/price)
            bot.send(msg)
    elif query_data == 'upbit_sell':
        balance = upbit.getBalance(bot.ticker)
        msg = upbit.sellMarket(bot.ticker, balance)
        bot.send(msg)
    elif query_data == 'binance_borrow_cross':
        price = binance.getPrice(bot.ticker)
        if str(type(price)) == "<class 'float'>":
            msg = binance.borrow(bot.ticker, 20/price)
            bot.send(msg)
        else:
            bot.send("바이낸스에서 {}의 가격을 불러올 수 없습니다.".format(bot.ticker))
    elif query_data == 'binance_buy_cross':
        balance = -binance.getMarginBalance(bot.ticker, 'netAsset')
        msg = binance.marginBuy(bot.ticker, balance)
        bot.send(msg)
    elif query_data == 'binance_sell_cross':
        balance = binance.getMarginBalance(bot.ticker)
        msg = binance.marginSell(bot.ticker, balance)
        bot.send(msg)
    elif query_data == 'binance_borrow_isol':
        price = binance.getPrice(bot.ticker)
        if str(type(price)) == "<class 'float'>":
            msg = binance.borrowIsol(bot.ticker, 20/price)
            bot.send(msg)
        else:
            bot.send("바이낸스에서 {}의 가격을 불러올 수 없습니다.".format(bot.ticker))
    elif query_data == 'binance_buy_isol':
        balance = -binance.getMarginBalanceIsol(bot.ticker, 'netAsset')
        msg = binance.marginBuyIsol(bot.ticker, balance)
        bot.send(msg)
    elif query_data == 'binance_sell_isol':
        balance = binance.getMarginBalanceIsol(bot.ticker)
        msg = binance.marginSellIsol(bot.ticker, balance)
        bot.send(msg)

if __name__ == '__main__':
    bot.send("자동거래 봇 시작!")

    MessageLoop(bot.bot, {'chat':bot.handle , 'callback_query' : query_ans}).run_as_thread()

    while(True):
        buy_point = 1 + bot.buy_point/100
        sell_point = 1 + bot.sell_point/100
        premium = getPremium(bot.ticker)
        now = time.time()
        if bot.settings["Auto_trading"]:
            if premium > 0 and premium < buy_point and upbit.getBalance(bot.ticker) < bot.amount*0.8:
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매수 시작.".format(bot.ticker, bot.buy_point, premium))
                msg = autotrade.autoBuy(bot.ticker, bot.amount)
                bot.send(msg)
            
            elif premium > sell_point and upbit.getBalance(bot.ticker) > bot.amount*0.8 :
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매도 시작.".format(bot.ticker, bot.sell_point, premium))
                msg = autotrade.autoSell(bot.ticker, bot.amount)
                bot.send(msg)

        time.sleep(1)