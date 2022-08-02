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
from utility import Alarm
from utility import BorrowChecker

class Telegram:
    def __init__(self, token, mc) -> None:
        self.bot = telepot.Bot(token)
        self.mc = mc
        self.ticker = config.ticker
        self.buy_point = config.buy_point
        self.sell_point = config.sell_point
        self.amount = config.amount
        self.start_msg = """
        BOT 기본 명령어
        1. /명령어 : 명령어 표시
        2. /상태 : 봇의 설정값을 조회
        3. /티커변경 티커 : 기준 티커 변경
        4. /잔고조회 : 업비트 원화, 바이낸스 USDT 잔고 조회
        5. /프리미엄 : 티커의 현재 프리미엄 값을 조회
        6. /알람 조회 : 설정된 알람을 조회
        7. /알람 설정 상승 bp : 프리미엄이 bp%를 상승 돌파할때 메세지를 주도록 설정
        8. /알람 설정 하락 bp : 프리미엄이 bp%를 하락 돌파 할때 메세지를 주도록 설정 
        9. /알람 삭제 상승 bp : 상승 bp 알람을 제거
        10. /알람 삭제 하락 bp : 하락 bp 알람을 제거 
        11. /자동거래 시작 : 자동거래를 시작
        12. /자동거래 종료 : 자동거래를 종료 
        13. /자동거래 변경 거래소1 거래소2 : 자동거래에 사용되는 거래소 변경, main = 거래소1, sub = 거래소2
        14. /원클릭매수 : 현재 프리미엄으로 업비트에서 매수, 바이낸스에서 마진 매도
        15. /원클릭매도 : 현재 프리미엄으로 업비트에서 매도, 바이낸스에서 마진 매수
        16. /교차 활성화 : 자동거래시 Cross를 사용
        17. /교차 비활성화 : 자동거래시 Cross를 사용하지 않음
        18. /교차 대여 수량 : Cross에서 수량 만큼 대여함 
        19. /교차 상환 수량 : Cross에서 수량 만큼 상환함 
        20. /격리 활성화 : 자동거래시 Isolated를 사용
        21. /격리 비활성화 : 자동거래시 Isolated를 사용하지 않음
        22. /격리 대여 수량 : Isolated에서 수량 만큼 대여함
        23. /격리 상환 수량 : Isolated에서 수량 만큼 상환함
        24. /대여수량조회 : 바이낸스 Cross/Isolated 대여 수량 및 한도 조회
        25. /대여목록 조회 : 설정된 대여목록을 조회
        26. /대여목록 추가 교차 티커 : 교차 대여목록에 티커를 추가함
        27. /대여목록 추가 격리 티커 : 격리 대여목록에 티커를 추가함
        28. /대여목록 삭제 교차 티커 : 교차 대여목록에서 티커를 삭제함
        29. /대여목록 삭제 격리 티커 : 격리 대여목록에서 티커를 삭제함
        30. /매매기준변경 buy sell : 매매 기준점 변경. 기준 프리미엄 숫자 입력
        31. /매매수량변경 amount : 총 매매 수량 변경
        32. /아이피조회 : 현재 서버의 ip를 조회함
        33. /매매테스트 : 자동거래가 잘 이루어 지는지 최소 금액으로 거래 테스트
        34. /후원주소조회 : 개발자를 후원할 수 있는 주소를 조회함
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
        elif command == "/알람":
            if args[0] == "조회":
                self.send(alarm.showAlert())
            elif args[0] == "설정":
                self.send(alarm.addAlert(args[1], float(args[2])))
            elif args[0] == "삭제":
                self.send(alarm.delAlert(args[1], float(args[2])))
        elif command == '/자동거래':
            if args[0] == '시작':
                config.settings["Auto_trading"] = True
                self.send("자동거래를 시작합니다.")
            elif args[0] == '종료':
                config.settings["Auto_trading"] = False
                self.send("자동거래를 종료합니다.")
            elif args[0] == "변경":
                autotrade.main = exchagneSelection(args[1])
                autotrade.sub = exchagneSelection(args[2])
                self.send("메인 거래소를 {}, 서브 거래소를 {}로 변경합니다.".format(args[1], args[2]))

        elif command == '/원클릭매수':
            autotrade.autoBuy(self.ticker, self.amount)
        elif command == '/원클릭매도':
            autotrade.autoSell(self.ticker, self.amount)
        elif command == '/교차':
            self.setMargin('Cross', args)
        elif command == '/격리':
            self.setMargin("Isolated", args)
        elif command == '/대여수량조회':
            self.send(binance.getMaxMarginLoan("Cross", self.ticker))
            self.send(binance.getMaxMarginLoan("Isolated", self.ticker))
        elif command == "/대여목록":
            if args[0] == "조회":
                self.send(borrow_checker.showAlert())
            elif args[0] == "추가" and args[1] == "교차":
                self.send(borrow_checker.addAlert("Cross", args[2]))
            elif args[0] == "추가" and args[1] == "격리":
                self.send(borrow_checker.addAlert("Isolated", args[2]))
            elif args[0] == "삭제" and args[1] == "교차":
                self.send(borrow_checker.delAlert("Cross", args[2]))
            elif args[0] == "삭제" and args[1] == "격리":
                self.send(borrow_checker.delAlert("Isolated", args[2]))
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

        for key in config.settings:
            if config.settings[key]:
                self.send("{} 사용 설정 됨".format(key))
            else:
                self.send("{} 미사용 설정 됨".format(key))

    def setMargin(self, key, args):
        if args[0] == "활성화":
            config.settings[key] = True
            self.send("다음부터 자동거래시 {}를 사용합니다.".format(key))
        elif args[0] == "비활성화":
            config.settings[key] = False
            self.send("다음부터 자동거래시 {}를 사용하지 않습니다.".format(key))
        elif args[0] == "대여":
            self.send(binance.borrow(key, self.ticker, float(args[1])))
        elif args[0] == "상환":
            self.send(binance.repay(key, self.ticker, float(args[1])))

    def exSelection(self):
        btn1 = BT(text='업비트', callback_data='upbit_balance')
        btn2 = BT(text='빗썸', callback_data='bithumb_balance')
        btn3 = BT(text='바이낸스', callback_data='binance_balance')
        mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
        self.sendBtn('거래소를 선택하세요', mu)

    def exSelection2(self):
        btn1 = BT(text='업비트', callback_data='upbit_test')
        btn2 = BT(text='빗썸', callback_data='bithumb_test')
        btn3 = BT(text='바이낸스 Cross', callback_data='binance_test_Cross')
        btn4 = BT(text='바이낸스 Isolated', callback_data='binance_test_Isolated')
        mu = MU(inline_keyboard = [[btn1, btn2, btn3, btn4]])
        self.sendBtn('테스트할 거래소를 선택하세요', mu)

    def testBuySell(self, exchange):
        btn1 = BT(text='사기', callback_data='{}_buy'.format(exchange))
        btn2 = BT(text='팔기', callback_data='{}_sell'.format(exchange))
        mu = MU(inline_keyboard = [[btn1, btn2]])
        self.sendBtn('테스트할 거래를 선택하세요. 거래는 {}에서 {}를 6천원 가량 사거나 팝니다'.format(exchange, self.ticker), mu)

    def binanceTest(self, key: str):
        btn1 = BT(text='빌리기', callback_data='binance_borrow_{}'.format(key))
        btn2 = BT(text='사기', callback_data='binance_buy_{}'.format(key))
        btn3 = BT(text='팔기', callback_data='binance_sell_{}'.format(key))
        mu = MU(inline_keyboard = [[btn1, btn2, btn3]])
        self.sendBtn('테스트할 거래를 선택하세요. 거래는 바이낸스 {}에서 {}를 20달러 가량 빌리거나 사거나 팝니다'.format(key, self.ticker), mu)

    def query_ans(self, msg):
        query_data = msg["data"]
        args = query_data.split('_')
        keys = ["Cross", "Isolated"]
        if args[0] == "upbit":
            if args[1] == "balance":
                self.send("업비트 잔고 {:.0f}원 입니다.".format(upbit.getBalance('KRW')))
            elif args[1] == "test":
                self.testBuySell(args[0])
            elif args[1] == "buy":
                price = upbit.getPrice(self.ticker)
                if price == 0:
                    self.send("업비트에서 {}의 가격을 불러올 수 없습니다.".format(self.ticker))
                else:
                    self.send(upbit.buyMarket(self.ticker, 6000/price))
            elif args[1] == "sell":
                self.send(upbit.sellMarket(self.ticker, upbit.getBalance(self.ticker)))
        elif args[0] == "bithumb":
            if args[1] == "balance":
                self.send("빗썸 잔고 {:.0f}원 입니다.".format(bithumb.getBalance('KRW')))
            elif args[1] == "test":
                self.testBuySell(args[0])
            elif args[1] == "buy":
                price = bithumb.getPrice(self.ticker)
                if isinstance(price, float):
                    self.send(bithumb.buyMarket(self.ticker, 6000/price))
                else:
                    self.send("빗썸에서 {}의 가격을 불러올 수 없습니다.".format(self.ticker))
            elif args[1] == "sell":
                self.send(bithumb.sellMarket(self.ticker, bithumb.getBalance(self.ticker)))
        elif args[0] == "binance":
            if args[1] == "balance":
                for key in keys:
                    self.send("바이낸스 {} 잔고 {:.2f}USDT 입니다.".format(key, binance.getMarginBalance(key, 'USDT')))
            elif args[1] == "test":
                self.binanceTest(args[2]) 
            elif args[1] == "borrow":
                self.send(binance.testBorrow(args[2], self.ticker))
            elif args[1] == "buy":
                self.send(binance.testMarginBuy(args[2], self.ticker))    
            elif args[1] == "sell":
                self.send(binance.testMarginSell(args[2], self.ticker))

upbit = Upbit(config.Upbit.access_key, config.Upbit.secret_key)
bithumb = Bithumb(config.Bithumb.access_key, config.Bithumb.secret_key)
binance = Binance(config.Binance.access_key,config.Binance.secret_key)
autotrade = Autotrade(upbit, bithumb)
alarm = Alarm()
borrow_checker = BorrowChecker(binance)
bot = Telegram(config.Telegram.token, config.Telegram.mc)

def exchagneSelection(name: str):
    if name == "업비트":
        return upbit
    elif name == "빗썸":
        return bithumb
    elif name == "바이낸스":
        return binance

def handle_exit():
    bot.send("자동거래 서버 종료!")

atexit.register(handle_exit) 

if __name__ == '__main__':
    bot.send("자동거래 봇 시작!")

    MessageLoop(bot.bot, {'chat':bot.handle , 'callback_query' : bot.query_ans}).run_as_thread()

    while(True):
        buy_point = 1 + bot.buy_point/100
        sell_point = 1 + bot.sell_point/100
        premium = autotrade.getPremium(bot.ticker)
        alert = alarm.checkAlert(premium)
        if alert is not None:
            bot.send(alert)
        borrow_alert = borrow_checker.checkAlert()
        if borrow_alert != "":
            bot.send(borrow_alert)
        now = time.time()
        if config.settings["Auto_trading"]:
            if premium > 0 and premium < buy_point and upbit.getBalance(bot.ticker) < bot.amount*0.8:
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매수 시작.".format(bot.ticker, bot.buy_point, premium))
                bot.send(autotrade.autoBuy(bot.ticker, bot.amount))
            
            elif premium > sell_point and upbit.getBalance(bot.ticker) > bot.amount*0.8 :
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매도 시작.".format(bot.ticker, bot.sell_point, premium))
                bot.send(msg = autotrade.autoSell(bot.ticker, bot.amount))

        time.sleep(1)