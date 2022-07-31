#! /usr/bin/env python3

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
from abc import ABC, abstractclassmethod
import config

class Binance:
    def __init__(self, access, secret):
        self.binance = Client(access,secret)
        self.name = "바이낸스"
    
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

    def getMarginBalance(self, key: str, ticker: str, type: str = 'free') -> float:
        if key == "Cross":
            balance = self.binance.get_margin_account()
            for index, asset in enumerate(balance['userAssets']):
                if asset['asset'] == ticker:
                    break

            if ticker == 'USDT':
                return float(balance['userAssets'][index]['free'])
            else:
                return float(balance['userAssets'][index][type])
        elif key == "Isolated":
            balance = self.binance.get_isolated_margin_account()
            for index, asset in enumerate(balance['assets']):
                if asset['baseAsset']['asset'] == ticker:
                    break
            if ticker == 'USDT':
                return float(balance['assets'][0]['quoteAsset']['free'])
            else:
                return float(balance['assets'][index]['baseAsset'][type])

    def getMaxMarginLoan(self, key: str ,ticker: str) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            if key == "Cross":
                max_margin_loan = self.binance.get_max_margin_loan(asset=ticker)
            elif key == "Isolated":
                max_margin_loan = self.binance.get_max_margin_loan(asset=ticker, isolatedSymbol=binance_ticker)
        except BinanceAPIException as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        except Exception as e:
            return "대여 잔고 확인 실패! 에러 코드 : {} {}.".format(e.status_code, e.message)
        avbl_amount = float(max_margin_loan['amount'])
        limit_amount = float(max_margin_loan['borrowLimit'])
        borrowed = self.getMarginBalance(key, ticker)
        return "{} 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(key, avbl_amount, limit_amount, borrowed)

    def borrow(self, key: str, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        try:
            if key == "Cross":
                max_margin_loan = self.binance.get_max_margin_loan(asset=ticker)
            elif key == "Isolated":
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
                if key == "Cross":
                    self.binance.create_margin_loan(asset=ticker, amount=amount)
                elif key == "Isolated":
                    self.binance.create_margin_loan(asset=ticker, amount=amount, isIsolated='TRUE', symbol=binance_ticker)
                return "{} {:.2f}개 {}에서 대여 완료!".format(ticker, amount, key)
            except Exception as e:
                return "{} {}에서 대여 실패! 에러 코드 : {} {}.".format(ticker, key, e.status_code, e.message)
        else:
            borrowed = self.getMarginBalance(key, ticker)
            return "{}에서 대여 가능 수량 부족! 대여 가능 수량 : {:.2f}, 최대 한도 : {:.2f}, 대여 중 : {:.2f}.".format(key, avbl_amount, limit_amount, borrowed)

    def repay(self, key: str, ticker: str, amount: float) -> str:
        binance_ticker = '{}USDT'.format(ticker)
        amount = self.amountCheck(amount)
        try:
            if key == "Cross":
                self.binance.repay_margin_loan(asset=ticker, amount= amount)
            elif key == "Isolated":
                self.binance.repay_margin_loan(asset=ticker, amount= amount, isIsolated='TRUE', symbol= binance_ticker)
            return "{} {}개 {}에서 상환 완료!".format(ticker, amount, key)
        except Exception as e:
            return "{} {}에서 상환 실패! 에러 코드 : {} {}.".format(ticker, key, e.status_code, e.message)  

    def borrowAndSell(self, key: str, ticker: str, amount: float) -> str:
        borrow_msg = self.borrow(key, ticker, amount)
        sell_msg = self.marginSell(key, ticker, amount)
        return borrow_msg + sell_msg

    def marginSell(self, key: str, ticker: str, amount: float) -> str:
        if config.settings[key]:
            binance_ticker = '{}USDT'.format(ticker)
            try:
                amount = self.amountCheck(amount)
                if key == "Cross":
                    self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount)
                elif key == "Isolated":
                    self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=amount, isIsolated='TRUE')
                return "{} {}개 {}에서 판매 완료!".format(ticker, amount, key)
            except BinanceAPIException as e:
                if e.message == "Filter failure: MIN_NOTIONAL":
                    return "{} {}에서 판매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker, key)
                elif e.message == "Account has insufficient balance for requested action.":
                    return "{} {}에서 판매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker, key)
                else:
                    return "{} {}에서 판매 실패! 에러 코드 : {} {}.".format(ticker, key, e.status_code, e.message)
        else:
            return ""

    def buyAndRepay(self, key: str, ticker: str, amount: float) -> str:
        buy_msg = self.marginBuy(key, ticker, amount)
        repay_msg = self.repay(key, ticker, amount)
        return buy_msg + repay_msg

    def marginBuy(self, key: str, ticker: str, amount: float) -> str:
        if config.settings[key]:
            total_amount = self.amountCheck(amount/0.999)
            binance_ticker = '{}USDT'.format(ticker)
            try:
                if key == "Cross":
                    self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount)
                elif key == "Isolated":
                    self.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount, isIsolated='TRUE')
                return "{} {}개 {}에서 구매 완료!".format(ticker, total_amount, key)
            except BinanceAPIException as e:
                if e.message == "Filter failure: MIN_NOTIONAL":
                    return "{} {}에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker, key)
                elif e.message == "Account has insufficient balance for requested action.":
                    return "{} {}에서 구매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker, key)
                else:
                    return "{} {}에서 구매 실패! 에러 코드 : {} {}.".format(ticker, key, e.status_code, e.message)
        else:
            return ""

    def testBorrow(self, key: str, ticker: str) -> str:
        price = self.getPrice(ticker)
        if isinstance(price, float):
            return self.borrow(key, ticker, 12/price)
        else:
            return "바이낸스에서 {}의 가격을 불러올 수 없습니다.".format(ticker)

    def testMarginBuy(self, key: str, ticker: str) -> str:
        balance = -self.getMarginBalance(key, ticker, 'netAsset')
        return self.marginBuy(key, ticker, balance)

    def testMarginSell(self, key: str, ticker: str) -> str:
        return self.marginSell(key, ticker, self.getMarginBalance(key, ticker))
    
    def autoBuy(self, ticker: str, amount: float) -> str:
        return "{} {}".format(self.marginBuy("Cross", ticker, amount), self.marginBuy("Isolated", ticker, amount))

    def autoSell(self, ticker: str, amount: float) -> str:
        return "{} {}".format(self.marginSell("Cross", ticker, amount), self.marginSell("Isolated", ticker, amount))
                

class State(ABC):
    @property
    def exchange(self):
        return self._exchange
    
    @exchange.setter
    def exchage(self, exchange) -> None:
        self._exchange = exchange

    @abstractclassmethod
    def buy(self, ticker: str, amount: float) -> str:
        pass

    @abstractclassmethod
    def sell(self, ticker: str, amount: float) -> str:
        pass

class Margin(State):
    def __init__(self, account) -> None:
        super().__init__()
        self._account = account

    @property
    def activation(self):
        return self._activation
    
    @activation.setter
    def activation(self, activation) -> None:
        self._activation = activation

    def buy(self, ticker: str, amount: float) -> str:
        if self.activation :
            total_amount = self._exchange.amountCheck(amount/0.999)
            binance_ticker = '{}USDT'.format(ticker)
            try:
                self.exchage.binance.create_margin_order(symbol=binance_ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=total_amount)
                return "{} {}개 Cross에서 구매 완료!".format(ticker, total_amount)
            except BinanceAPIException as e:
                if e.message == "Filter failure: MIN_NOTIONAL":
                    return "{} Cross에서 구매 실패! 최소 거래 수량 이상의 값을 입력하세요.".format(ticker)
                elif e.message == "Account has insufficient balance for requested action.":
                    return "{} Cross에서 구매 실패! 보유 수량 이하의 값을 입력하세요.".format(ticker)
                else:
                    return "{} Cross에서 구매 실패! 에러 코드 : {} {}.".format(ticker, e.status_code, e.message)