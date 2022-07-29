#! /usr/bin/env python3

import time
import config

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