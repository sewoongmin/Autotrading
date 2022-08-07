#! /usr/bin/env python3

from matplotlib.axis import Tick
import pyupbit
import config
import time
from ticker import Ticker, Volume

class Upbit:
    def __init__(self, access, secret) -> None:
        self.upbit = pyupbit.Upbit(access, secret)
        self.name = "업비트"
        self.tickers = pyupbit.get_tickers(fiat="KRW")
        # self.tickers.remove('KRW-BTC')
        # self.tickers.remove('KRW-ETH')
        # self.tickers.remove('KRW-XRP')
        # self.tickers.remove('KRW-ADA')
        # self.tickers.remove('KRW-SOL')
        # self.tickers.remove('KRW-DOGE')
        # self.tickers.remove('KRW-DOT')
        # self.tickers.remove('KRW-MATIC')
        # self.tickers.remove('KRW-AVAX')
        # self.tickers.remove('KRW-TRX')
        # self.tickers.remove('KRW-ETC')
        # self.tickers.remove('KRW-LINK')
        # self.tickers.remove('KRW-CRO')
        # self.tickers.remove('KRW-NEAR')
        # self.tickers.remove('KRW-XLM')
        # self.tickers.remove('KRW-ATOM')
        # self.tickers.remove('KRW-BCH')
        # self.tickers.remove('KRW-ALGO')
        # self.tickers.remove('KRW-FLOW')
        # self.tickers.remove('KRW-VET')
        # self.tickers.remove('KRW-MANA')
        # self.tickers.remove('KRW-SAND')
        # self.tickers.remove('KRW-XTZ')
        # self.tickers.remove('KRW-HBAR')
        # self.tickers.remove('KRW-AXS')
        # self.tickers.remove('KRW-THETA')
        # self.tickers.remove('KRW-AAVE')
        # self.tickers.remove('KRW-EOS')
        # self.tickers.remove('KRW-BSV')
        # self.tickers.remove('KRW-BTT')
        # self.tickers.remove('KRW-IOTA')
        # self.tickers.remove('KRW-XEC')
        # self.tickers.remove('KRW-NEO')
        # self.tickers.remove('KRW-CHZ')
        # self.tickers.remove('KRW-WAVES')
        # self.tickers.remove('KRW-BAT')
        # self.tickers.remove('KRW-STX')
        # self.tickers.remove('KRW-GMT')
        # self.tickers.remove('KRW-ZIL')
        # self.tickers.remove('KRW-ENJ')
        self.ticker_volumes = []
        for ticker in self.tickers:
            self.ticker_volumes.append(Ticker(ticker))

    def volumeChecker(self):
        for ticker in self.ticker_volumes:
            df = pyupbit.get_ohlcv(ticker.name, interval="minute15", count=11)
            time.sleep(0.04)
            if df is not None:
                aver = (sum(df['volume']) - df['volume'][-1])/(len(df['volume']-1))
                ticker.setVolume(15, df['close'][-2], df['close'][-1], df['volume'][-1], df['volume'][-1]/aver)
        ret = list(filter(lambda x: x.checkVolume(15), self.ticker_volumes))
        ret = self.volumeTracker(30, ret)
        ret = self.volumeTracker(60, ret)
        ret = self.volumeTracker(240, ret)
        return ret

    def volumeTracker(self, minute, check_list):
        for ticker in check_list:
            df = pyupbit.get_ohlcv(ticker.name, interval="minute{}".format(minute), count=11)
            time.sleep(0.04)
            if df is not None:
                aver = (sum(df['volume']) - df['volume'][-1])/(len(df['volume']-1))
                ticker.setVolume(minute, df['close'][-2], df['close'][-1], df['volume'][-1], df['volume'][-1]/aver)
        return check_list
        

    def getPrice(self, ticker: str = 'BTC') -> float:
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

    def autoBuy(self, ticker: str, amount: float) -> str:
        return self.buyMarket(ticker, amount)

    def autoSell(self, ticker: str, amount: float) -> str:
        return self.sellMarket(ticker, self.getBalance(ticker))