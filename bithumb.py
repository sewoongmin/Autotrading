#! /usr/bin/env python3

import config
import pybithumb

class Bithumb:
    def __init__(self, access, secret) -> None:
        self.bithumb = pybithumb.Bithumb(access, secret)
        self.name = "빗썸"

    def getPrice(self, ticker: str = 'BTC') -> float:
        return self.bithumb.get_current_price(ticker)

    def getBalance(self, ticker: str = 'KRW') -> float:
        if ticker == "KRW":
            return self.bithumb.get_balance("BTC")[2]
        else:
            return self.bithumb.get_balance(ticker)[0]

    def buyMarket(self, ticker: str, amount: float) -> str:
        current_amount = self.getBalance(ticker)
        current_balance = self.getBalance('KRW')
        buy_order = self.bithumb.buy_market_order(ticker, amount)
        bought_amount = self.getBalance(ticker) - current_amount
        bought_balance = self.getBalance('KRW') - current_balance
        avg_price = bought_balance / bought_amount
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
        final_amount = self.getBalance(ticker)
        return "{} 구매 성공! 평단가 {:.2f}원. 총 보유 수량 : {:.2f}.".format(ticker, avg_price, final_amount)

    def sellMarket(self, ticker: str, amount: float) -> str:
        current_amount = self.getBalance(ticker)
        sell_order = self.bithumb.sell_market_order(ticker, amount)
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