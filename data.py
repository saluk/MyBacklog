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
def sec_to_ts(sec):
    return ttos(time.localtime(sec))

class Game:
    args = [("name","s"),("playtime","f"),("finished","i"),("genre","s"),("source","s"),("hidden","i"),("icon_url","s"),
    ("packageid","s"),("is_package","i"),("notes","s"),("priority","i")]
    source_args = {"steam":[("steamid","i")],"gog":[("gogid","s"),("install_path","s")],"none":[("install_path","s"),("website","s")],
                   "gba":[("install_path","s")]}
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.name = ""
        self.playtime = 0
        self.finished = 0
        self.hidden = 0
        self.is_package = 0   #Set to 1 if it includes multiple games
        self.lastplayed = None   #timestamp in fmt
        self.source = "steam"
        self.packageid = ""  #Id of game within a package
        self.genre = ""
        self.icon_url = ""
        self.notes = ""
        self.priority = 0
        
        self.steamid = ""
        self.gogid = ""
        self.install_path = ""
        self.website = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
        if stot(self.lastplayed).tm_year<1971:
            self.lastplayed = None
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
        return self.args+self.source_args.get(self.source,[])
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
        s = ""
        if self.source == "steam" and self.steamid:
            s = "steam_%s"%self.steamid
        elif self.source == "gog" and self.gogid:
            s = "gog_%s"%self.gogid
        elif self.source in ["none","gba"]:
            print(self.name)
            s = [x.lower() for x in self.name if x.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 "]
            s = "".join(s).replace(" ","_")
        else:
            raise Exception("Invalid source")
        if self.packageid and s:
            s += ".%s"%self.packageid
        return s
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
        return d
    def copy(self):
        return Game(**self.dict())
    def games_for_pack(self,games):
        if not self.is_package:
            raise Exception("Not a package")
        gamelist = []
        for g in games.games.values():
            if g==self:
                continue
            if g.is_package:
                continue
            if g.gogid == self.gogid and self.source=="gog" and g.source=="gog":
                gamelist.append(g)
        return gamelist

class Games:
    def __init__(self):
        self.games = {}
        self.multipack = json.loads(open("gog_packages.json").read())
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
    def import_packages(self):
        for gkey in list(self.games.keys()):
            game = self.games[gkey]
            if game.source=="gog" and "." in game.gogid:
                gogid,packageid = game.gogid.rsplit(".",1)
                game.gogid = gogid
                game.packageid = packageid
                package = Game(name=" ".join([x.capitalize() for x in gogid.split("_")]),
                        is_package=1,source="gog",gogid=gogid)
                if not package.gameid in self.games:
                    self.games[package.gameid] = package
                del self.games[gkey]
                self.games[game.gameid] = game
    def save(self,file):
        save_data = {}
        for k in self.games:
            save_data[k] = self.games[k].dict()
        f = open(file,"w")
        f.write(json.dumps(save_data,sort_keys=True,indent=4))
        f.close()
        f = open("gog_packages.json","w")
        f.write(json.dumps(self.multipack))
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
        if game.icon_url:
            cur_game.icon_url = game.icon_url
        if game.playtime > cur_game.playtime:
            cur_game.playtime = game.playtime
        if game.finished:
            cur_game.finished = 1
        if game.lastplayed and (not cur_game.lastplayed or stot(game.lastplayed)>stot(cur_game.lastplayed)):
            cur_game.lastplayed = game.lastplayed
        cur_game.is_package = game.is_package
        cur_game.packageid = game.packageid
        return game
    def list(self):
        v = self.games.values()
        return sorted(v,key=lambda g:(g.finished,g.priority,-time.mktime(stot(g.lastplayed)),g.name))
    def delete(self, game):
        del self.games[game.gameid]