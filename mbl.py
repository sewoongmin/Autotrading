#! /usr/bin/env python3

import pyupbit
import config
from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton as BT
from telepot.namedtuple import InlineKeyboardMarkup as MU
import time
import atexit

class Upbit:
    def __init__(self, access, secret) -> None:
        self.upbit = pyupbit.Upbit(access, secret)

    def getPrice(self, ticker: str = 'KRW-BTC') -> float:
        upbit_ticker = 'KRW-{}'.format(ticker) 
        try:
            return pyupbit.get_current_price(upbit_ticker)
        except Exception as e:
            if e.name == 404:
                return 0
            else:
                return -1

    def getBalance(self, ticker: str = 'KRW') -> float:
        if ticker == "KRW":
            return self.upbit.get_balance()
        else:
            return self.upbit.get_balance(ticker)

    def buyMarket(self, ticker: str, amount: float) -> str:
        upbit_ticker = 'KRW-{}'.format(ticker) 
        current_amount = self.getBalance(ticker)
        order_price = self.getPrice(ticker)*amount
        buy_order = self.upbit.buy_market_order(upbit_ticker, order_price)
        bought_amount = self.getBalance(ticker) - current_amount
        if bought_amount == 0:
            if buy_order == 'UnderMinTotalBid':
                return "{} 구매 실패! 최소 구매 수량 미달.".format(ticker) 
            elif buy_order == 'InsufficientFundsBid':
                return "{} 구매 실패! 잔액 부족.".format(ticker)
            elif buy_order == "ValidationError":
                return "{} 구매 실패! ticker 오류.".format(ticker)
            else:
                return "{} 구매 실패! 에러 : {}.".format(ticker, buy_order)

        elif bought_amount < amount:
            self.buyMarket(ticker, amount-bought_amount)
        avg_price = self.upbit.get_avg_buy_price(ticker)
        final_amount = self.getBalance(ticker)
        return "{} 구매 성공! 평단가 {:.2f}원. 총 보유 수량 : {:.2f}.".format(ticker, avg_price, final_amount)

    def sellMarket(self, ticker: str, amount: float) -> str:
        upbit_ticker = 'KRW-{}'.format(ticker) 
        current_amount = self.getBalance(ticker)
        sell_order = self.upbit.sell_market_order(upbit_ticker, amount)
        sold_amount = current_amount - self.getBalance(ticker)
        if sold_amount == 0:
            if sell_order == 'UnderMinTotalMarketAsk':
                return "{} 판매 실패! 최소 거래 수량 미달.".format(ticker)
            elif sell_order == 'InsufficientFundsAsk':
                return "{} 판매 실패! 잘못된 수량 입력.".format(ticker)
            elif sell_order == "ValidationError":
                return "{} 판매 실패! ticker 오류.".format(ticker)
            else:
                return "{} 판매 실패! 에러 : {}.".format(ticker, sell_order)
        else:
            balance = self.getBalance("KRW")
            return  "{} {:.2f}개 판매 완료! 판매 후 잔고 {:.0f}원.".format(ticker, sold_amount, balance)

class Binance:
    def __init__(self, access, secret):
        self.binance = Client(access,secret)
    
    def amountCheck(self, amount: float) -> float:
        if amount > 10:
            amount = round(amount-0.5, 0)
        elif amount <10 and amount >= 1:
            amount = round(amount-0.005, 2)
        elif amount < 1:
            amount = round(amount-0.00005, 4)
        return amount

    def getPrice(self, ticker: str) -> float:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            symbol = self.binance.get_symbol_ticker(symbol=binance_ticker)
            return float(symbol['price'])
        except BinanceAPIException as e:
            return e

        except Exception as e:
            return e

    def getMarginBalance(self, ticker: str, type: str = 'free') -> float:
        balance = self.binance.get_margin_account()
        for index, asset in enumerate(balance['userAssets']):
            if asset['asset'] == ticker:
                break

        if ticker == 'USDT':
            return float(balance['userAssets'][index]['free'])
        else:
            return float(balance['userAssets'][index][type])

    def getMarginBalanceIsol(self, ticker: str, type :str = 'free') -> float:
        balance = self.binance.get_isolated_margin_account()
        for index, asset in enumerate(balance['assets']):
            if asset['baseAsset']['asset'] == ticker:
                break
        if ticker == 'USDT':
            return float(balance['assets'][0]['quoteAsset']['free'])
        else:
            return float(balance['assets'][index]['baseAsset'][type])

    def getMaxMarginLoan(self, ticker: str) -> str:
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker)
        except BinanceAPIException as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        except Exception as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])
        borrowed = self.getMarginBalance(ticker)
        return "Cross 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(avbl_amount, limit_amount, borrowed)

    def getMaxMarginLoanIsol(self, ticker: str) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker, isolatedSymbol=binance_ticker)
        except BinanceAPIException as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        except Exception as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])
        borrowed = self.getMarginBalanceIsol(ticker)
        return "Isolated 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(avbl_amount, limit_amount, borrowed)

    def borrow(self, ticker: str, amount: float) -> str:
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker)
        except BinanceAPIException as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        except Exception as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])

        if avbl_amount > 0 and avbl_amount >= amount:
            amount = self.amountCheck(amount)
            try:
                self.binance.create_margin_loan(asset=ticker, amount=amount)
                return "{} {:.2f}개 Cross에서 대여 완료!".format(ticker, amount)
            except Exception as e:
                return "{} Cross에서 대여 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)
        else:
            borrowed = self.getMarginBalance(ticker)
            return "Cross에서 대여 가능 수량 부족! 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(avbl_amount, limit_amount, borrowed)

    def borrowIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker, isolatedSymbol=binance_ticker)
        except BinanceAPIException as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        except Exception as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])

        if avbl_amount > 0 and avbl_amount >= amount:
            amount = self.amountCheck(amount)
            try:
                self.binance.create_margin_loan(asset=ticker, amount=amount, isIsolated='TRUE', symbol=binance_ticker)
                return "{} {:.2f}개 Isolated에서 대여 완료!".format(ticker, amount)
            except Exception as e:
                return "{} Isolated에서 대여 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)
        else:
            borrowed = self.getMarginBalanceIsol(ticker)
            return "Isolated에서 대여 가능 수량 부족! 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(avbl_amount, limit_amount, borrowed)

    def repay(self, ticker: str, amount: float) -> str:
        amount = self.amountCheck(amount)
        try:
            self.binance.repay_margin_loan(asset=ticker, amount= amount)
            return "{} {}개 Cross에서 상환 완료!".format(ticker, amount)
        except Exception as e:
            return "{} Cross에서 상환 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)
    
    def repayIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        amount = self.amountCheck(amount)
        try:
            self.binance.repay_margin_loan(asset=ticker, amount= amount, isIsolated='TRUE', symbol= binance_ticker)
            return "{} {}개 Isolated에서 상환 완료!".format(ticker, amount)
        except Exception as e:
            return "{} Isolated에서 상환 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)   

    def borrowAndSell(self, ticker: str, amount: float) -> str:
        borrow_msg = self.borrow(ticker, amount)
        sell_msg = self.marginSell(ticker, amount)
        return borrow_msg + sell_msg
    
    def borrowAndSellIsol(self, ticker: str, amount: float) -> str:
        borrow_msg = self.borrowIsol(ticker, amount)
        sell_msg = self.marginSellIsol(ticker, amount)
        return borrow_msg + sell_msg

    def marginSell(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            amount = self.amountCheck(amount)
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount)
            return "{} {}개 Cross에서 판매 완료!".format(ticker, amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Cross에서 판매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Cross에서 판매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker)
            else:
                return "{} Cross에서 판매 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)
        
    def marginSellIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            amount = self.amountCheck(amount)
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount, isIsolated='TRUE')
            return "{} {}개 Isolated에서 판매 완료!".format(ticker, amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Isolated에서 판매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Isolated에서 판매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker)
            else:
                return "{} Isolated에서 판매 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)

    def buyAndRepay(self, ticker: str, amount: float) -> str:
        buy_msg = self.marginBuy(ticker, amount)
        repay_msg = self.repay(ticker, amount)
        return buy_msg + repay_msg

    def buyAndRepayIsol(self, ticker: str, amount: float) -> str:
        buy_msg = self.marginBuyIsol(ticker, amount)
        repay_msg = self.repayIsol(ticker, amount)
        return buy_msg + repay_msg

    def marginBuy(self, ticker: str, amount: float) -> str:
        total_amount = self.amountCheck(amount/0.999)
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount)
            return "{} {}개 Cross에서 구매 완료!".format(ticker, total_amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Cross에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Cross에서 구매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker)
            else:
                return "{} Cross에서 구매 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)
    
    def marginBuyIsol(self, ticker: str, amount: float) -> str:
        total_amount = self.amountCheck(amount/0.999)
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount, isIsolated='TRUE')
            return "{} {}개 Isolated에서 구매 완료!".format(ticker, total_amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Isolated에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Isolated에서 구매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker)
            else:
                return "{} Isolated에서 구매 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)

class Telegram:
    def __init__(self, token, mc) -> None:
        self.bot = telepot.Bot(token)
        self.mc = mc
        self.ticker = config.ticker
        self.buy_point = config.buy_point
        self.sell_point = config.sell_point
        self.amount = config.amount
        self.auto_trading = True
        self.cross = True
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
        8. /원클릭매수 : 현재 프리미엄으로 업비트에서 매수, 바이낸스에서 마진 매도
        9. /원클릭매도 : 현재 프리미엄으로 업비트에서 매도, 바이낸스에서 마진 매수
        10. /교차 활성화 : 자동거래시 Cross를 사용
        11. /교차 비활성화 : 자동거래시 Cross를 사용하지 않음
        12. /교차 대여 수량 : Cross에서 수량 만큼 대여함 
        13. /교차 상환 수량 : Cross에서 수량 만큼 상환함 
        14. /격리 활성화 : 자동거래시 Isolated를 사용
        15. /격리 비활성화 : 자동거래시 Isolated를 사용하지 않음
        16. /격리 대여 수량 : Isolated에서 수량 만큼 대여함
        17. /격리 상환 수량 : Isolated에서 수량 만큼 상환함
        18. /대여수량조회 : 바이낸스 Cross/Isolated 대여 수량 및 한도 조회
        19. /매매기준변경 buy sell : 매매 기준점 변경. 기준 프리미엄 숫자 입력
        20. /매매수량변경 amount : 총 매매 수량 변경 
        21. /매매테스트 : 자동거래가 잘 이루어 지는지 최소 금액으로 거래 테스트
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
            else:
                self.firstMenu()

    def execCmd(self, msg: str):
        args = msg.split(' ')
        command = args[0]
        del args[0]

        if command == '/명령어':
            self.send(self.start_msg)
        elif command == '/상태':
            self.send("현재 설정된 티커 {}.".format(self.ticker))
            self.send("현재 설정된 구매시작점 {}%, 매도 시작점 {}%.".format(self.buy_point, self.sell_point))
            self.send("현재 설정된 총 매매수량 {}개.".format(self.amount))
            if self.auto_trading:
                self.send("자동거래 동작 중.")
            else:
                self.send("자동거래 중지 됨.")
            if self.cross:
                self.send("Cross 사용 설정됨.")
            else:
                self.send("Cross 미사용 설정됨.")
            if self.isolated:
                self.send("Isolated 사용 설정됨.")
            else:
                self.send("Isolated 미사용 설정됨.")
        elif command == '/티커변경':
            self.ticker = args[0]
            self.send("티커 {} 로 변경 완료!".format(args[0]))
        elif command == '/잔고조회':
            self.exSelection()
        elif command == '/프리미엄':
            premium = getPremium(self.ticker)
            self.send("현재 {} 프리미엄은 {:.3f}입니다.".format(self.ticker, premium))
        elif command == '/자동거래':
            if args[0] == '시작':
                self.auto_trading = True
                bot.send("자동거래를 시작합니다.")
            elif args[0] == '종료':
                self.auto_trading = False
                bot.send("자동거래를 종료합니다.")
        elif command == '/원클릭매수':
            autoBuy()
        elif command == '/원클릭매도':
            autoSell()
        elif command == '/교차':
            if args[0] == "활성화":
                self.cross = True
                bot.send("다음부터 자동거래시 Cross를 사용합니다.")
            elif args[0] == "비활성화":
                self.cross = False
                bot.send("다음부터 자동거래시 Cross를 사용하지 않습니다.")
            elif args[0] == "대여":
                msg = binance.borrow(self.ticker, float(args[1]))
                bot.send(msg)
            elif args[0] == "상환":
                msg = binance.repay(self.ticker, float(args[1]))
                bot.send(msg)
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
        elif command == '/매매테스트':
            self.exSelection2()

    def firstMenu(self):
        btn1 = BT(text='사고 팔기', callback_data='buy_sell')
        mu = MU(inline_keyboard = [[btn1]])
        self.sendBtn("할 일을 선택하세요", mu)

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

class TradeTimer:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.premium = 0
        self.switch = False

    def buyTimming(self, premium: float) -> bool:
        now = time.time()
        if now - self.start_time > config.waiting:
            return True
        elif premium < self.premium:
            self.premium = premium
            self.start_time = now
            return False
        else:
            return False

    def sellTimming(self, premium: float) -> bool:
        now = time.time()
        if now - self.start_time > config.waiting:
            return True
        elif premium > self.premium:
            self.premium = premium
            self.start_time = now
            return False
        else:
            return False

    def getState(self) -> bool:
        return self.switch

    def set(self, on_off: bool, premium: float) -> None:
        self.switch = on_off
        if self.switch:
            self.start_time = time.time()
            self.premium = premium
            

upbit = Upbit(config.Upbit.access_key, config.Upbit.secret_key)
binance = Binance(config.Binance.access_key,config.Binance.secret_key)
bot = Telegram(config.Telegram.token, config.Telegram.mc)
timmer = TradeTimer()

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
    if query_data == 'buy_sell':
        pass
        # btnShowBinance()
    elif query_data == 'settings':
        bot.settingsDisplay()
    elif query_data == 'upbit_balance':
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
        if bot.auto_trading:
            if premium > 0 and premium < buy_point and upbit.getBalance(bot.ticker) < bot.amount*0.8:
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매수 시작.".format(bot.ticker, bot.buy_point, premium))
                autoBuy()
            
            elif premium > sell_point and upbit.getBalance(bot.ticker) > bot.amount*0.8 :
                bot.send("{} 프리미엄 {:.3f} 도달. {:.3f}에서 매도 시작.".format(bot.ticker, bot.sell_point, premium))
                autoSell()

        time.sleep(1)