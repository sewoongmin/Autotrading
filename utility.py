#! /usr/bin/env python3

from pickletools import read_string1
import time
from tkinter import N
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

class Alarm:
    def __init__(self) -> None:
        self.ups = []
        self.downs = []
        self.pre_bp = 0

    def addAlert(self, direction: str, bp: float) -> str:
        if direction == "상승":
            self.ups.append(bp)
        elif direction == "하락":
            self.downs.append(bp)
        return "{}% {} 알람 설정완료.".format(bp, direction)
            
    def delAlert(self, direction: str, bp: float) -> str:
        if direction == "상승":
            try:
                self.ups.remove(bp)
            except Exception as e:
                return "{}에 {}% 알람이 없습니다.".format(direction, bp)
        if direction == "하락":
            try:
                self.downs.remove(bp)
            except Exception as e:
                return "{}에 {}% 알람이 없습니다.".format(direction, bp)
        return "{}% {} 알람 제거완료.".format(bp, direction)

    def showAlert(self) -> str:
        ups = "상승 알람 : "
        for up in self.ups:
            ups += "{}% ".format(up)
        downs = "하락 알람 : "
        for down in self.downs:
            downs += "{}% ".format(down)
        return "{}. {}".format(ups, downs)

    def checkAlert(self, premium):
        cur_bp = (premium-1)*100
        for up in self.ups:
            if up > self.pre_bp and up < cur_bp:
                self.pre_bp = cur_bp
                return "프리미엄 {}% 상승 돌파! 현재 {:.2f}%".format(up, cur_bp)
        for down in self.downs:
            if down < self.pre_bp and down > cur_bp:
                self.pre_bp = cur_bp
                return "프리미엄 {}% 하락 돌파! 현재 {:.2f}%".format(down, cur_bp)
        self.pre_bp = cur_bp
