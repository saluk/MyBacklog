#!python3
import time
from datetime import timedelta

class Game:
    def __init__(self,**kwargs):
        self.name = ""
        self.playtime = timedelta(minutes=0)
        self.finished = 0
        self.source = "steam"
        self.gameid = ""
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = timedelta(minutes=kwargs["minutes"])
    def display_print(self):
        print (self.name)
        print ("  %.2d:%.2d"%self.hours_minutes)
    @property
    def hours_minutes(self):
        s = self.playtime.total_seconds()
        min = s/60.0
        hour = min/60.0
        min = min-int(hour)*60.0
        return hour,min