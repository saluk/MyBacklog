#!python3
import requests
import data

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
    games = get_games()
    is_finished = match_finished_games(games,finished)
    library = []
    for g in games:
        set_finished = 0
        if g in is_finished:
            set_finished = 1
        library.append(data.Game(name=g["name"],minutes=g["playtime_forever"],finished=set_finished,source="steam",steamid=g["appid"]))
    return library

if __name__=="__main__":
    games = get_games()
    finished = match_finished_games(games,finished)
    for game in finished:
        game = data.Game(name=game["name"],minutes=game["playtime_forever"],finished=1)
        game.display_print()