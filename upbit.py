#! /usr/bin/env python3

import pyupbit

class Upbit:
    def __init__(self, access, secret) -> None:
        self.upbit = pyupbit.Upbit(access, secret)
        self.name = "업비트"

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
        return self.sellMarket(ticker, amount)