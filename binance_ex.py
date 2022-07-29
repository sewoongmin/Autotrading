#! /usr/bin/env python3

from binance.client import Client
from binance.enums import *
from binance.exceptions import *
from abc import ABC, abstractclassmethod

class Binance:
    def __init__(self, access, secret):
        self.binance = Client(access,secret)
        self.settings = dict(Cross = True, Isolated = True)
        self.name = "바이낸스"

    def setParam(self, key, value):
        self.settings[key] = value
    
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
    
    def autoBuy(self, ticker: str, amount: float) -> str:
        cross_msg = ""
        isolated_msg = ""
        if self.settings["Cross"]:
            cross_msg = self.marginBuy(ticker, amount)
        if self.settings["Isolated"]:
            isolated_msg = self.marginBuyIsol(ticker, amount)
        return "{} {}".format(cross_msg, isolated_msg)

    def autoSell(self, ticker: str, amount: float) -> str:
        cross_msg = ""
        isolated_msg = ""
        if self.settings["Cross"]:
            cross_msg = self.marginSell(ticker, amount)
        if self.settings["Isolated"]:
            isolated_msg = self.marginSellIsol(ticker, amount)
        return "{} {}".format(cross_msg, isolated_msg)
                

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