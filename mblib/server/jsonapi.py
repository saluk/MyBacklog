import hug
import sys, os, traceback
import base64

sys.path.insert(0, "../..")
import mblib
from mblib import games, syslog

#game_log = syslog.SysLog("games_log.txt")

@hug.not_found()
def not_found_handler():
    return "Not Found"


def nice_user(user):
    fixed_user = "".join(
        [x for x in user if x in "abcdefghijklmnopqrstuvwxyz0123456789"]
    )
    if user != fixed_user:
        raise Exception("Username must only contain english alpha and digits")
    return fixed_user


class User:
    def __init__(self, user, load_games=False):
        self.user = nice_user(user)
        self.up = os.path.join("__users__",user)
        self.game_path = os.path.join(self.up,"games.json")
        self.games = None
        if load_games:
            self.load_games()

    def is_ready(self):
        return os.path.exists(self.game_path)

    def make_ready(self):
        if not os.path.exists("__users__"):
            os.mkdir("__users__")
        if not os.path.exists(self.up):
            os.mkdir(self.up)
    def load_games(self):
        try:
            self.games = games.Games()
            self.games.load_games(filename=self.game_path)
        except:
            traceback.print_exc()
    def save_games(self):
        try:
            self.games.save(self.game_path)
            return (True, "")
        except:
            return (False, traceback.format_exc())


@hug.format.content_type("application/ubjson")
def raw(data, request=None, response=None):
    return data

@hug.get(examples="user=saluk&start=0&count=50&name_filter=mario&source_filter=steam&finished_filter=1")
def list(user,start=0,count=50,name_filter='',source_filter='',finished_filter=''):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    l = user.games.list()
    len_total = len(l)
    if source_filter:
        l = [game for game in l if game.get_source(source_filter)]
    if finished_filter:
        l = [game for game in l if bool(game.finished)==bool(int(finished_filter))]
    if name_filter:
        l = [game for game in l if name_filter.lower() in game.name.lower()]
    len_filtered = len(l)
    l = l[int(start):int(start)+int(count)]
    games_dict = [game.dict() for game in l]
    playing = user.games.playing_game
    if playing:
        playing["game"] = playing["game"].dict()
    return {"length":len_filtered, "total": len_total, "games":games_dict, "playing":playing}

@hug.put(examples="user=saluk&game_name=Mario&source_name=NES")
def game(user, game_name, source_name):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    game = games.Game(sources=[{"source": source_name}],
            import_date=games.now(), games=user.games)
    game.name = game_name
    game.generate_gameid()
    if user.games.find_matching_game(game):
        return {"error":"game exists"}
    game, diff = user.games.force_update_game(game.gameid, game)
    user.games.revision += 1
    success, message = user.save_games()
    if success:
        return {"gameid": game.gameid, "diff": diff}
    else:
        return {"gameid": game.gameid, "diff": diff, "error": message}

@hug.patch(examples="user=saluk&gameid=1234&finished=true")
def game(user, gameid, finished=None, playtime=None, rawdata=None):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    game = user.games.find(gameid).copy()
    if not game:
        return {"error":"no game found"}
    toggle = False
    if finished != None:
        toggle = True
        if finished:
            game.finish()
        else:
            game.unfinish()
    if playtime != None:
        if playtime != game.playtime:
            toggle = True
            game.playtime = playtime
    if rawdata != None:
        game_d = game.dict()
        game_d.update(rawdata)
        game = games.Game(**game_d)
    updated_game, diff = user.games.force_update_game(game.gameid, game)
    if not diff:
        return {"gameid": game.gameid, "diff": diff, "error": "No change was made"}
    user.games.revision += 1
    success, message = user.save_games()
    if success:
        return {"gameid": game.gameid, "diff": diff}
    else:
        return {"gameid": game.gameid, "diff": diff, "error": message}


@hug.patch(examples="user=saluk&method=start&gameid=123")
def games_method(user, method, gameid):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    if method not in ["start_playing_game", "stop_playing_game"]:
        return {"error":"invalid method"}
    game = user.games.find(gameid)
    if not game:
        return {"error":"no game found"}
    f = getattr(user.games, method)
    if not f(gameid=gameid):
        return {"error": "No operation needed."}
    user.games.revision += 1
    success, message = user.save_games()
    if success:
        return {"gameid": game.gameid}
    else:
        return {"gameid": game.gameid, "error": message}


@hug.patch(examples="user=saluk&method=screenshots&source=switch")
def update_method(user, method, source=None):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    if method not in ["screenshots"]:
        return {"error":"invalid method"}

    if source=="switch":
        from mblib.apis import nintendo
        converter = nintendo.find_screenshot
    elif source=="epic":
        from mblib.apis import epic
        converter = epic.find_screenshot
    else:
        return {"error":"no image converter for source "+source}
    
    changed = None
    for g in user.games.list():
        if not g.get_source(source):
            continue
        #if g.images:
        #    continue
        img_url = converter(g.name)
        g.images = []
        g.images.append({"url": img_url, "size": "icon"})
        changed = True

    user.games.revision += 1
    success, message = user.save_games()
    if success:
        return {}
    else:
        return {"error": message}


@hug.get(examples="user=saluk")
def sources(user):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    return user.games.source_definitions

@hug.get(examples="user=saluk",output=raw)
def game_database(user):
    user = User(user)
    if not user.is_ready():
        return {"error": "no_games_saved"}
    with open(user.game_path, "rb") as gamef:
        data = gamef.read()
    return data


@hug.put(examples="user=saluk")
def game_database(body, user, input=raw):
    user = User(user, load_games=True)
    user.make_ready()
    try:
        data = body.read()
        gdbmu = games.Games()
        gdbmu.load_games(filedata=data)
    except:
        traceback.print_exc()
        return {"error":"Not a valid game database"}
    if user.games and gdbmu.revision < user.games.revision:
        return {
            "error":"server has newer revision",
            "client_revision":user.games.revision,
            "server_revision":gdbmu.revision
        }
    with open(user.game_path,"wb") as gamef:
        gamef.write(data)
    return {"msg": "success", "size": len(data)}


@hug.get(examples="user=saluk")
def games_revision(user):
    user = User(user)
    if not user.is_ready():
        return {"server_revision": None}
    try:
        gdbm = games.Games()
        gdbm.load_games(filename=user.game_path)
    except:
        traceback.print_exc()
        return {"error": "Error loading game database"}
    return {"server_revision": gdbm.revision}


@hug.post(examples="user=saluk")
def bump_revision(user):
    user = User(user, load_games=True)
    if not user.is_ready():
        return {"error":"user not initialized"}
    if not user.games:
        return {"error":"Error loading game database"}
    user.games.revision += 1
    user.save_games()
    return {"server_revision":user.games.revision}

@hug.get('/js', output=hug.output_format.file)
def get_js_file(js_file):
    if js_file in ['moment.js', 'mybacklog.js']:
        return 'js/'+js_file

@hug.get('/', output=hug.output_format.html)
def index():
    return open("game_list.html").read()
