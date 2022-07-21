#! /usr/bin/env python3

from distutils.file_util import copy_file
from distutils.log import info
from symtable import Symbol
from click import ClickException
from numpy import not_equal
import pyupbit
from binance.client import Client
from binance.enums import *
from binance.exceptions import *
import config
import time

class Upbit:
    def __init__(self, access, secret) -> None:
        self.upbit = pyupbit.Upbit(access, secret)

    def getPrice(self, ticker: str) -> float:
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
                return "{} 구매 실패! 최소 구매 수량 미달. ".format(ticker)
            elif buy_order == 'InsufficientFundsBid':
                return "{} 구매 실패! 잔액 부족. ".format(ticker)
            elif buy_order == "ValidationError":
                return "{} 구매 실패! ticker 오류. ".format(ticker)
            else:
                return "{} 구매 실패! 에러 : {} ".format(ticker, buy_order)

        elif bought_amount < amount:
            self.buyMarket(ticker, amount-bought_amount)
        avg_price = self.upbit.get_avg_buy_price(ticker)
        final_amount = self.getBalance(ticker)
        return "{} 구매 성공! 평단가 {:.2f}원. 총 보유 수량 : {:.2f}. ".format(ticker, avg_price, final_amount)

    def sellMarket(self, ticker: str, amount: float) -> str:
        upbit_ticker = 'KRW-{}'.format(ticker) 
        current_amount = self.getBalance(ticker)
        sell_order = self.upbit.sell_market_order(upbit_ticker, amount)
        sold_amount = current_amount - self.getBalance(ticker)
        if sold_amount == 0:
            if sell_order == 'UnderMinTotalMarketAsk':
                return "{} 판매 실패! 최소 거래 수량 미달. ".format(ticker)
            elif sell_order == 'InsufficientFundsAsk':
                return "{} 판매 실패! 잘못된 수량 입력. ".format(ticker)
            else:
                return "{} 판매 실패! 에러 : {} ".format(ticker, sell_order)
        else:
            balance = self.getBalance("KRW")
            return  "{} {:.2f}개 판매 완료! 판매 후 잔고 {:.0f}원. ".format(ticker, sold_amount, balance)

class Binance:
    def __init__(self, access, secret):
        self.binance = Client(access,secret)

    def getPrice(self, ticker: str) -> float:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            symbol = self.binance.get_symbol_ticker(symbol=binance_ticker)
            return float(symbol['price'])
        except BinanceAPIException as e:
            return e

        except Exception as e:
            return e

    def getMarginBalance(self, ticker: str, type: str = 'borrowed') -> float:
        balance = self.binance.get_margin_account()
        for index, asset in enumerate(balance['userAssets']):
            if asset['asset'] == ticker:
                break

        if ticker == 'USDT':
            return float(balance['userAssets'][index]['free'])
        else:
            if type == 'borrowed':
                return float(balance['userAssets'][index][type])
            else:
                return float(balance['userAssets'][index]['borrowed']) + float(balance['userAssets'][index]['interest'])

    def getMarginBalanceIsol(self, ticker: str, type :str = 'borrowed') -> float:
        balance = self.binance.get_isolated_margin_account()
        for index, asset in enumerate(balance['assets']):
            if asset['baseAsset']['asset'] == ticker:
                break
        if ticker == 'USDT':
            return float(balance['assets'][0]['quoteAsset']['free'])
        else:
            if type == 'borrowed':
                return float(balance['assets'][index]['baseAsset'][type])
            else:
                return float(balance['assets'][index]['baseAsset']['borrowed']) + float(balance['assets'][index]['baseAsset']['interest'])

    def borrow(self, ticker: str, amount: float) -> str:
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker)
        except BinanceAPIException as e:
            return "대여 실패! 에러 코드 : {} {}".format(e.status_code, e.message)
        except Exception as e:
            return "대여 실패! 에러 코드 : {} {}".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])

        if avbl_amount > 0 and avbl_amount >= amount:
            try:
                self.binance.create_margin_loan(asset=ticker, amount=amount)
                return "{} {:.2f}개 Cross에서 대여 완료! ".format(ticker, amount)
            except Exception as e:
                return "{} Cross에서 대여 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)
        else:
            borrowed = self.getMarginBalance(ticker)
            return "Cross에서 대여 가능 수량 부족! 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f} ".format(avbl_amount, limit_amount, borrowed)

    def borrowIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            max_margin_loan = self.binance.get_max_margin_loan(asset=ticker, isolatedSymbol=binance_ticker)
        except BinanceAPIException as e:
            return "대여 실패! 에러 코드 : {} {}".format(e.status_code, e.message)
        except Exception as e:
            return "대여 실패! 에러 코드 : {} {}".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])

        if avbl_amount > 0 and avbl_amount >= amount:
            try:
                self.binance.create_margin_loan(asset=ticker, amount=amount, isIsolated='TRUE', symbol=binance_ticker)
                return "{} {:.2f}개 Isolated에서 대여 완료! ".format(ticker, amount)
            except Exception as e:
                return "{} Isolated에서 대여 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)
        else:
            borrowed = self.getMarginBalanceIsol(ticker)
            return "Isolated에서 대여 가능 수량 부족! 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}".format(avbl_amount, limit_amount, borrowed)

    def repay(self, ticker: str, amount: float) -> str:
        try:
            self.binance.repay_margin_loan(asset=ticker, amount= amount)
            return "{} {}개 Cross에서 상환 완료! ".format(ticker, amount)
        except Exception as e:
            return "{} Cross에서 상환 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)
    
    def repayIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.repay_margin_loan(asset=ticker, amount= amount, isIsolated='TRUE', symbol= binance_ticker)
            return "{} {}개 Isolated에서 상환 완료! ".format(ticker, amount)
        except Exception as e:
            return "{} Isolated에서 상환 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)

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
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount)
            return "{} {}개 Cross에서 판매 완료! ".format(ticker, amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Cross에서 판매 실패! 최소 거래 수량 이상의 값을 입력하세요. ".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Cross에서 판매 실패! 보유 수량 이하의 값을 입력하세요. ".format(ticker)
            else:
                return "{} Cross에서 판매 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)
        
    def marginSellIsol(self, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount, isIsolated='TRUE')
            return "{} {}개 Isolated에서 판매 완료! ".format(ticker, amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Isolated에서 판매 실패! 최소 거래 수량 이상의 값을 입력하세요. ".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Isolated에서 판매 실패! 보유 수량 이하의 값을 입력하세요. ".format(ticker)
            else:
                return "{} Isolated에서 판매 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)

    def buyAndRepay(self, ticker: str, amount: float) -> str:
        buy_msg = self.marginBuy(ticker, amount)
        repay_msg = self.repay(ticker, amount)
        return buy_msg + repay_msg

    def buyAndRepayIsol(self, ticker: str, amount: float) -> str:
        buy_msg = self.marginBuyIsol(ticker, amount)
        repay_msg = self.repayIsol(ticker, amount)
        return buy_msg + repay_msg

    def marginBuy(self, ticker: str, amount: float) -> str:
        total_amount = round(amount/0.999, 0)
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount)
            return "{} {}개 Cross에서 구매 완료! ".format(ticker, total_amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Cross에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요. ".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Cross에서 구매 실패! 보유 수량 이하의 값을 입력하세요. ".format(ticker)
            else:
                return "{} Cross에서 구매 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)
    
    def marginBuyIsol(self, ticker: str, amount: float) -> str:
        total_amount = round(amount/0.999, 0)
        binance_ticker = '{}USDT'.format(ticker)
        try:
            self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount, isIsolated='TRUE')
            return "{} {}개 Isolated에서 구매 완료! ".format(ticker, total_amount)
        except BinanceAPIException as e:
            if e.message == "Filter failure: MIN_NOTIONAL":
                return "{} Isolated에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요. ".format(ticker)
            elif e.message == "Account has insufficient balance for requested action.":
                return "{} Isolated에서 구매 실패! 보유 수량 이하의 값을 입력하세요. ".format(ticker)
            else:
                return "{} Isolated에서 구매 실패! 에러 코드 : {} {} ".format(ticker, e.status_code, e.message)

upbit = Upbit(config.Upbit.access_key, config.Upbit.secret_key)
binance = Binance(config.Binance.access_key,config.Binance.secret_key)

def getPremium(ticker: str):
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


if __name__ == '__main__':
    print(getPremium(config.ticker))
    binance.borrow(config.ticker, 1)
    binance_ticker = '{}USDT'.format(config.ticker)
    point = binance.binance.options_positions()
    
    print(point)
        
