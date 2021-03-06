import os
import sys
import subprocess
import webbrowser

try:
    import winreg
except:
    winreg = None


import psutil


run_with_steam = 1
#   NEW METHOD TO RUN THROUGH STEAM:
#   Export function which creates shortcuts to all non-steam games that aren't in steam yet
#   Manually creat shortcut for often played game, and put it in cache/steamshortcuts
#   When running a game, if a steam shortcut exists in cache/steamshortcuts, run that


class Source:
    extra_args = []
    source_args = []
    generate_website = None
    runnable = True

    def __init__(self, name):
        """app = app should contain fields for api's sources may need"""
        self.name = name

    def args(self):
        return self.extra_args

    def is_installed(self, game, source):
        return True

    def needs_download(self, game, source):
        if self.is_installed(game, source):
            return False
        return True

    def download_link(self, game, source):
        return ""

    def download_method(self, game, source):
        if game.download_link:
            webbrowser.open(game.download_link)

    def uninstall(self):
        return

    def run_game(self, game, source, cache_root):
        return

    def rom_extension(self, game):
        return ""

    def game_is_running(self, game, data, app):
        """By default return true and force user to control when to stop the timer"""
        return True


class ExeSource(Source):
    """Definition of a source of games"""

    def args(self):
        """Return editable arguments that are unique to this source
        Defaults to install_path as that is pretty common"""
        return [("install_path", "s")] + self.extra_args

    def is_installed(self, game, source):
        return os.path.exists(game.get_path())

    def uninstall(self, game, source):
        if game.install_folder:
            subprocess.Popen(
                ["explorer.exe", game.install_folder],
                cwd=game.install_folder,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )

    def get_run_args_win(self, game, source, cache_root, write_batch=True):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        folder = game.install_folder  # Navigate to executable's directory
        root = folder.split(os.path.sep, 1)[0]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        import winshell, shlex

        path = game.get_path()
        if path.endswith(".lnk"):
            with winshell.shortcut(path) as link:
                print(dir(link))
                args = [link.path] + shlex.split(link.arguments)
                folder = link.working_directory
                search = os.path.basename(link.path)
                print(folder)
        else:
            # Make batch file to run
            filepath = os.path.basename(path)
            exe, args = filepath.split(".exe")
            exe = exe + ".exe"
            search = exe
            if write_batch:
                with open(
                    cache_root + "/cache/batches/" + game.gameid + ".bat", "w"
                ) as f:
                    f.write('%s\ncd "%s"\n' % (root, folder))
                    f.write('"%s" %s\n' % (exe, args))
            args = [game.gameid + ".bat"]
            folder = os.path.abspath(cache_root + "/cache/batches/")
        return args, folder, search

    def get_run_args_mac(self, game, source, cache_root, write_batch=True):
        """Returns the method to run the game."""
        folder = game.install_folder  # Navigate to executable's directory
        root = folder.split("/", 1)[0]
        exe = game.install_path.rsplit("/", 1)[1]
        args = ['open', exe]
        search = exe
        return args, folder, search

    def get_run_args(self, game, source, cache_root, write_batch=True):
        if os.system == 'win':
            return self.get_run_args_win(game, source, cache_root, write_batch)
        return self.get_run_args_mac(game, source, cache_root, write_batch)

    def run_game(self, game, source, cache_root):
        creationflags = 0
        shell = True
        if sys.platform == "darwin":
            shell = False
        args, folder, search = self.get_run_args(game, source, cache_root)
        print("run args:", args, folder)

        if args and folder:
            print(args)
            curdir = os.path.abspath(os.curdir)
            os.chdir(folder)
            print(os.path.abspath(os.curdir))
            self.running = subprocess.Popen(
                args,
                cwd=folder,
                stdout=sys.stdout,
                stderr=sys.stderr,
                creationflags=creationflags,
                shell=shell,
            )
            print("subprocess open")
            os.chdir(curdir)

    def game_is_running(self, game, data, app):
        args, folder, search = self.get_run_args(
            game, data, app.config["root"], write_batch=False
        )
        print("search:", search)
        search = search.lower()
        for proc in psutil.process_iter():
            if search in proc.name().lower():
                return True
            try:
                cmd = " ".join(proc.cmdline()).lower()
                print(cmd)
                if search in cmd:
                    return True
            except Exception:
                pass
            try:
                exe = proc.exe().lower()
                print(exe)
                if search in exe:
                    return True
            except Exception:
                pass


class EpicSource(ExeSource):
    def get_run_args(self, game, source, cache_root, write_batch=True):
        import webbrowser
        import json

        folder = game.install_folder
        root = folder.split(os.path.sep, 1)[0]
        appname = None
        for filename in os.listdir(folder + "/.egstore"):
            if filename.endswith(".mancpn"):
                with open(folder + "/.egstore/" + filename) as f:
                    dat = json.loads(f.read())
                    appname = dat["AppName"]
        if not appname:
            return None
        with open(cache_root + "/cache/batches/" + game.gameid + ".bat", "w") as f:
            f.write('%s\ncd "%s"\n' % (root, folder))
            f.write(
                'start "" "com.epicgames.launcher://apps/%s?action=launch&silent=true"\n'
                % appname
            )
        args = [game.gameid + ".bat"]
        folder = os.path.abspath(cache_root + "/cache/batches/")
        path = game.get_path()
        filepath = os.path.basename(path)
        exe, args2 = filepath.split(".exe")
        exe = exe + ".exe"
        search = exe
        return args, folder, search


class HumbleSource(ExeSource):
    source_args = [("id", "s"), ("package", "s")]


class SteamSource(Source):
    """Needs .api to be set to steamapi.Steam"""

    extra_args = []
    source_args = [("id", "s")]

    def run_game(self, game, source, cache_root):
        if "id" not in source:
            return
        webbrowser.open("steam://rungameid/%s" % source["id"])

    def missing_steam_launch(self, game, source):
        return False

    def download_method(self, game, source):
        if "id" not in source:
            return
        webbrowser.open("steam://install/%s" % source["id"])

    def uninstall(self, game, source):
        if "id" not in source:
            return
        webbrowser.open("steam://uninstall/%s" % source["id"])

    def is_installed(self, game, source):
        if "id" not in source:
            return
        return self.api.is_installed(source["id"])

    def generate_website(self, game, source):
        if "id" in source:
            return "http://store.steampowered.com/app/%s" % source["id"]
        return ""

    def game_is_running(self, game, data, app):
        if app.steam.running_game_id() == data["id"]:
            return True


def windows_registry_entries(path):
    if not winreg:
        return []

    def get_key(path, item):
        return winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path + "\\" + item)

    gog_games = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
        gog_games = [
            get_key(winreg.EnumKey(key, i)) for i in range(winreg.QueryInfoKey(key)[0])
        ]
    return gog_games


class GogSource(ExeSource):
    """Needs .api to be set to gogapi.Gog"""

    extra_args = []
    source_args = [("id", "s"), ("id2", "s")]

    def args(self):
        return [("install_path", "s")] + self.extra_args

    def download_link_downloader(self, game, source):
        if "id" not in source:
            return ""
        return "gogdownloader://%s/installer_win_en" % source["id"]

    def download_link_galaxy(self, game, source):
        if "id2" not in source:
            return ""
        return "goggalaxy://openGameView/%s" % source["id2"]

    download_link = download_link_galaxy

    def generate_website(self, game, source):
        if "id" in source:
            return "https://www.gog.com/game/%s" % source["id"]
        return ""

    def run_game(self, game, source, cache_root):
        if game.get_path():
            return super(GogSource, self).run_game(game, source, cache_root)
        webbrowser.open("goggalaxy://openGameView/%s" % source["id2"])

    def is_installed(self, game, source):
        if game.get_path():
            return True
        if "id2" not in source:
            return False
        for gog_game in windows_registry_entries(
            "SOFTWARE\\WOW6432Node\\GOG.com\\Games"
        ):
            if winreg.QueryValueEx(gog_game, "gameID")[0] != source["id2"]:
                continue
            return True

    def game_is_running(self, game, data, app):
        if not winreg:
            return super().game_is_running(game, data, app)
        cwd, exe = None, None
        for gog_game in windows_registry_entries(
            "SOFTWARE\\WOW6432Node\\GOG.com\\Games"
        ):
            if winreg.QueryValueEx(gog_game, "gameID")[0] != data["id2"]:
                continue
            cwd, exe = os.path.split(winreg.QueryValueEx(gog_game, "EXE")[0])
        print("EXE", exe, "cwd", cwd)
        procs = [
            proc
            for proc in psutil().process_iter()
            if exe.lower() in proc.name().lower() and proc.cwd() == cwd
        ]
        # if procs:
        #    print(dir(procs[0]))
        #    print(procs[0].environ())   #weird error for Rime on this print
        #    print(procs[0].cwd())
        return bool(procs)


class EmulatorSource(ExeSource):
    source_args = []

    def args(self):
        return [("install_path", "s")] + self.extra_args

    def get_run_args(self, game, source, cache_root, write_batch=False):
        emu_info = game.games.local["emulators"][self.name]
        args = emu_info["args"] + [game.get_path()]
        path, exe = os.path.split(args[0])
        return args, path, exe

    def rom_extension(self, game):
        emu_info = game.games.local["emulators"][self.name]
        return emu_info.get("rom_extension", "*.*")


class OfflineSource(Source):
    def args(self):
        return self.extra_args

    def is_installed(self, game, source):
        return False


class LinkSource(OfflineSource):
    source_args = [("id", "s")]

    def is_installed(self, game, source):
        return False


default_definitions = {
    "gog": {"class": "GogSource", "editable": False},
    "steam": {"class": "SteamSource", "editable": False},
    "offline": {
        "class": "OfflineSource",
    },
    "none": {"class": "ExeSource", "editable": False},
    "humble": {"class": "HumbleSource", "editable": False},
    "origin": {"class": "ExeSource"},
    "gamersgate": {"class": "ExeSource"},
    "itch": {"class": "ExeSource"},
    "offline": {"class": "OfflineSource"},
    "gba": {"class": "EmulatorSource"},
    "snes": {"class": "EmulatorSource"},
    "n64": {"class": "EmulatorSource"},
    "nds": {"class": "EmulatorSource"},
    "thegamesdb": {"class": "LinkSource"},
    "giantbomb": {"class": "LinkSource"},
}
all = {}


def register_sources(definitions):
    for sourcekey in definitions:
        source = definitions[sourcekey]
        cls = eval(source["class"])
        inst = cls(name=sourcekey)
        for key in source:
            if key in ["class"]:
                continue
            setattr(inst, key, source[key])
        all[sourcekey] = inst


classes = []
for x in dir():
    if "Source" in x and not x == "Source":
        classes.append(x)

assert classes
