#! /usr/bin/env python3

from upbit import Upbit
from bithumb import Bithumb
from binance_ex import Binance


class Autotrade:
    def __init__(self, main, sub) -> None:
        self._main = main
        self._sub = sub
        self.beast = False

    def autoBuy(self, ticker: str, amount: float) -> str:
        main_msg = self._main.autoBuy(ticker, amount)
        if self.beast:
            return "매수 완료. {}".format(main_msg)
        else:
            sub_msg = self._sub.autoSell(ticker, amount)
            return "매수 완료. {} {}".format(main_msg, sub_msg)

    def autoSell(self, ticker: str, amount: float) -> str:
        main_msg = self._main.autoSell(ticker, amount)
        if self.beast:
            return "매도 완료. {}".format(main_msg)
        else:
            sub_msg = self._sub.autoBuy(ticker, amount)
            return "매도 완료. {} {}".format(main_msg, sub_msg)
    
    def setBeast(self, beast: bool):
        self.beast = beast

    def getPremium(self, ticker: str = 'BTC') -> float:
        if isinstance(self._main, (Upbit, Bithumb)) and isinstance(self._sub, (Upbit, Bithumb)):
            main_price = self._main.getPrice(ticker)
            sub_price = self._sub.getPrice(ticker)
            if isinstance(main_price, float) and isinstance(sub_price, float) and main_price != 0 and sub_price != 0:
                return main_price/sub_price
            else:
                return -1

        elif isinstance(self._main, (Upbit, Bithumb)) and isinstance(self._sub, (Binance)):
            main_btc = self._main.getPrice('BTC')
            sub_btc = self._sub.getPrice('BTC')
            main_price = self._main.getPrice(ticker)
            sub_price = self._sub.getPrice(ticker)
            if isinstance(main_price, float) and isinstance(sub_price, float) and main_price != 0 and sub_price != 0:
                ref_er = main_btc / sub_btc
                ticker_er = main_price / sub_price 
                return ticker_er/ref_er
            else:
                return -1
            
    @property
    def main(self):
        return self._main
    @main.setter
    def main(self, exchange):
        self._main = exchange

    @property
    def sub(self):
        return self._sub
    @sub.setter
    def sub(self, exchange):
        self._sub = exchange
