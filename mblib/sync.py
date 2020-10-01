import requests
import shutil, os

import mblib
from mblib import games

app = None
user = "saluk"
host = "mybacklog.tinycrease.com"

mblib.last_revision_sent = -1
mblib.last_revision_received = -1
mblib.last_revision_loaded = -1


def get_server_revision():
    try:
        r = requests.get("http://%s/games_revision?user=%s" % (host, user), timeout=2)
        return r.json()["server_revision"]
    except:
        print("COULDN'T ACCESS SERVER")
        return


def download_games():
    print("DOWNLOAD GAMES")
    game_file = app.config["games"]
    downloading = game_file + ".d"
    r = requests.get("http://%s/game_database?user=%s" % (host, user), stream=True)
    read = 0
    with open(downloading, "wb") as f:
        while 1:
            next = r.raw.read(128)
            if not len(next):
                break
            read += len(next)
            f.write(next)
    print("read", read)


def refresh_games():
    print("REFRESHING GAMES")
    game_file = app.config["games"]
    gamedb = app.games
    downloading = game_file + ".d"
    downloaded = games.Games(app.log)
    downloaded.load(downloading)
    # force update all games from server into games
    for g in downloaded.games.values():
        gamedb.force_update_game(g.gameid, g)
    # Delete games that are gone on server
    for gameid in list(gamedb.games.keys()):
        if gameid in gamedb.games and gameid not in downloaded.games:
            print("DELETING", gamedb.games[gameid])
            del gamedb.games[gameid]
    # Update local revision to match server
    gamedb.revision = downloaded.revision


def download():
    print("check to download")
    if not app:
        print(" no app, no need")
        return False
    games = app.games
    revision = get_server_revision()
    mblib.last_revision_received = revision
    if not revision:
        print(" no db on server")
        raise Exception("SERVER NOT RUNNING")
        return False
    print("SERVER VERSION", revision)
    if revision < games.revision:
        print(
            " MAJOR ERROR, server is older than client. shouldn't happen, but we are uploading the version"
        )
        upload()
        return False
    if revision == games.revision:
        # We are already in sync
        print(" we are good")
        return False
    download_games()
    refresh_games()
    return True


def upload():
    print("UPLOAD GAMES")
    mblib.last_revision_sent = app.games.revision
    game_file = app.config["games"]
    with open(game_file, "rb") as f:
        data = f.read()
    r = requests.put(
        "http://%s/game_database?user=%s" % (host, user),
        data=data,
        headers={"Content-Type": "application/ubjson"},
    )
    print(r.json())
    if r.json().get("error", ""):
        raise Exception(r.text)
