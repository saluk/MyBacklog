#!python3
import requests
import data
import vdf

MY_API_KEY = "98934075AAB5F4E1223BEC4C40E88AA8"
MY_STEAM_ID = "76561197999655940"
STEAM_GAMES_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%(apikey)s&steamid=%(steamid)s&format=json&include_appinfo=1"

f = open("finished.txt",encoding="utf8")
finished = f.read().split("\n")
#finished = [x.decode("utf8") for x in finished]
f.close()

def get_games(userid=MY_STEAM_ID):
    url = STEAM_GAMES_URL
    r = requests.get(url%{"apikey":MY_API_KEY,"steamid":MY_STEAM_ID})
    data = r.json()["response"]["games"]
    return data
    
def match_finished_games(games,finished):
    matched = []
    for f in finished:
        matches = []
        for g in games:
            if g["name"].lower().startswith(f.lower()):
                matches.append(g)
        if not matches:
            print("no match:",f)
            crash
        #Choose match with shortest name (closest match)
        matches.sort(key=lambda match:len(match["name"]))
        matched.append(matches[0])
    return matched
    
def import_steam(userid=MY_STEAM_ID):
    apps = load_userdata()["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    games = get_games()
    is_finished = match_finished_games(games,finished)
    library = []
    for g in games:
        set_finished = 0
        if g in is_finished:
            set_finished = 1
        icon_url = ""
        if "img_icon_url" in g:
            icon_url  = "http://media.steampowered.com/steamcommunity/public/images/apps/%(appid)s/%(img_icon_url)s.jpg"%g
        lastplayed = None
        if str(g["appid"]) in apps:
            app = apps[str(g["appid"])]
            if "LastPlayed" in app:
                lastplayed=data.sec_to_ts(int(app["LastPlayed"]))
        library.append(
            data.Game(name=g["name"],
                            minutes=g["playtime_forever"],
                            finished=set_finished,
                            source="steam",
                            steamid=g["appid"],
                            lastplayed=lastplayed,
                            icon_url=icon_url
        )
    )
    return library
    
def load_userdata(path="C:\\Steam\\userdata\\39390212\\config\\localconfig.vdf"):
    f = open(path)
    data = vdf.parse(f)
    f.close()
    return data

if __name__=="__main__":
    import json
    for game in import_steam():
        print (game.name,game.icon_url)