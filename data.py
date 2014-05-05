#!python3
import os
import time
import datetime
import json

fmt = "%H:%M:%S %Y-%m-%d"
def now():
    t = time.localtime()
    return time.strftime(fmt,t)
def stot(s):
    if not s:
        return time.localtime(0)
    return time.strptime(s,fmt)
def ttos(t):
    return time.strftime(fmt,t)

class Game:
    args = [("name","s"),("playtime","f"),("lastplayed","s"),("finished","i"),("source","s"),("hidden","i")]
    source_args = {"steam":[("steamid","i")],"gog":[("gogid","s"),("install_path","s")]}
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.name = ""
        self.playtime = 0
        self.finished = 0
        self.hidden = 0
        self.lastplayed = None   #timestamp
        self.source = "steam"
        
        self.steamid = ""
        self.gogid = ""
        self.install_path = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
    def played(self):
        """Resets lastplayed to now"""
        self.lastplayed = now()
    def set_played(self,t):
        self.lastplayed = time.strftime(fmt,t)
    def display_print(self):
        print (self.name)
        print ("  %.2d:%.2d"%self.hours_minutes)
    @property
    def valid_args(self):
        return self.args+self.source_args[self.source]
    @property
    def hours_minutes(self):
        s = self.playtime
        min = s/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        return hour,min
    @property
    def last_played_nice(self):
        if not self.lastplayed:
            return "never"
        t = time.strptime(self.lastplayed,fmt)
        return time.strftime("%a, %d %b %Y %H:%M:%S",t)
    @property
    def gameid(self):
        if self.source == "steam":
            return "steam_%s"%self.steamid
        elif self.source == "gog":
            return "gog_%s"%self.gogid
        return "ERROR"
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
        return d

class Games:
    def __init__(self):
        self.games = {}
    def load(self,file):
        if not os.path.exists(file):
            print("Warning, no save file to load:",file)
            return
        f = open(file,"r")
        d = f.read()
        f.close()
        load_data = json.loads(d)
        for k in load_data:
            self.games[k] = Game(**load_data[k])
    def save(self,file):
        save_data = {}
        for k in self.games:
            save_data[k] = self.games[k].dict()
        f = open(file,"w")
        f.write(json.dumps(save_data,sort_keys=True,indent=4))
        f.close()
    def add_games(self,game_list):
        for g in game_list:
            self.update_game(g.gameid,g)
    def update_game(self,gameid,game,force=False):
        assert(isinstance(game,Game))
        cur_game = self.games.get(gameid,None)
        if not cur_game or force:
            self.games[gameid] = game
            return
        if game.playtime > cur_game.playtime:
            cur_game.playtime = game.playtime
        if game.finished:
            cur_game.finished = 1
        return game
    def list(self):
        v = self.games.values()
        return sorted(v,key=lambda g:(g.finished,-time.mktime(stot(g.lastplayed)),g.name))