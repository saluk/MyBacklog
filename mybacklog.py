#!python3

#STDLIB
import json
import os
import time
import threading

import requests

#backloglib
from code.apis import giantbomb, steamapi, gogapi, humbleapi, thegamesdb
from code.interface import account, gameoptions, base_paths, logwindow, sourcesform, emulatorform
from code import games,syslog

from code.resources import icons,enc

#os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"
VERSION = "0.25 alpha"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWebKit
#from PyQt5.QtWebKitWidgets import *
from PyQt5.QtNetwork import *

#steam_session = steamapi.login_for_chat()

def playrequest(game):
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/play",data={"game":game.name})
    except:
        pass
    #steamapi.set_username(steam_session,"saluk [Playing %s]"%game.name)
def stoprequest():
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/play",data={"game":""})
    except:
        pass
    #steamapi.set_username(steam_session,"saluk")
def uploadrequest(games):
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/upload_games",data={"games":games.save_data()})
    except:
        pass
def downloadrequest():
    r = requests.get("http://dawnsoft.org:9600/users/saluk/download_games")
    j = r.json()
    return j["games"]


class RunGameThread(QThread):
    process = None
    stopfunc = None
    def run(self):
        while self.process and self.process.returncode is None:
            self.process.communicate()

class ProcessIconsThread(QThread):
    app = None
    def run(self):
        print("running icons")
        try:
            self.app.process_icons()
        except:
            import traceback
            traceback.print_exc()
            
class ImportThread(QThread):
    app = None
    func = None
    def run(self):
        try:
            self.func(self.app)
        except:
            import traceback
            traceback.print_exc()

class Cookies(QNetworkCookieJar):
    def __init__(self):
        super(Cookies, self).__init__()
        self.cookies = {}
        #TODO: change path to cache path if browser is reinstated
        if os.path.exists("cache/qtcookies"):
            with open("cache/qtcookies", "r") as f:
                self.cookies = json.loads(f.read())

    def cookiesForUrl(self, url):
        cookies = []
        for name in self.cookies:
            c = self.cookies[name]
            qnc = QNetworkCookie(c["name"], c["value"])
            qnc.setDomain(c["domain"])
            qnc.setPath(c["path"])
            cookies.append(qnc)
        return cookies

    def setCookiesFromUrl(self, cookielist, url):
        for c in cookielist:
            self.cookies[c.name().data().decode("utf8")] = {
                "name": c.name().data().decode("utf8"),
                "path": c.path(),
                "value": c.value().data().decode("utf8"),
                "domain": c.domain()}
        print(self.cookies)
        #TODO: change path to cache path if browser is reinstated
        with open("cache/qtcookies", "w") as f:
            f.write(json.dumps(self.cookies))


class Browser(QWidget):
    def __init__(self, url, app):
        super(Browser, self).__init__()
        self.app = app
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        button = QPushButton("Do Import")
        layout.addWidget(button)
        button.clicked.connect(self.do_import)
        
        #self.cookiem = Cookies()
        self.webkit = QWebView()
        #self.webkit.page().networkAccessManager().setCookieJar(self.cookiem)
        layout.addWidget(self.webkit)
        
        self.webkit.load(QUrl(url))
        self.show()

    def do_import(self):
        html = self.webkit.page().mainFrame().toHtml()
        f = open("mygog_shelf.html","w",encoding="utf8")
        f.write(html)
        f.close()
        self.app.import_gog_html()
        self.deleteLater()


class MyBacklog(QMainWindow):
    def __init__(self):
        #super(MainWindow,self).__init__(None,Qt.WindowStaysOnTopHint)
        super(MyBacklog,self).__init__(None)
        self.setWindowTitle("MyBacklog %s"%VERSION)
        self.setWindowIcon(QIcon(QPixmap("icons/main.png")))
        self.main_form = GamelistForm(self)

        menus = {}
        for folder in ["file","edit","import","view"]:
            menus[folder] = self.menuBar().addMenu("&"+folder.capitalize())
            for x in dir(self.main_form):
                if x.startswith(folder+"_"):
                    name = " ".join([y.capitalize() for y in x.split("_")[1:]])
                    action = QAction("&"+name,self,triggered=getattr(self.main_form,x))
                    if "show_" in x:
                        action.setCheckable(True)
                    menus[folder].addAction(action)
        menus["view"] = self.menuBar().addMenu("&Add Game")

        menus["file"].addAction(QAction("&Exit",self,triggered=self.really_close))
        self.menus = menus
        self.exit_requested = False

        self.setCentralWidget(self.main_form)

        self.trayicon = QSystemTrayIcon(QIcon(QPixmap("icons/main.png")))
        self.trayicon.show()
        self.trayicon.activated.connect(self.click_tray_icon)
    def reset_games(self):
        #self.main_form.deleteLater()
        #self.main_form = GamelistForm(self)
        self.setCentralWidget(self.main_form)
        self.main_form.init_config()
        self.main_form.init_gamelist()
        self.build_add_game_menu()
    def build_add_game_menu(self):
        self.menus["view"].clear()
        for source in sorted(games.sources.all):
            print("Create menu to add",source)
            def gen_func():
                def ag(*args,**kwargs):
                    self.main_form.add_game(ag.source)
                ag.source = source
                return ag
            action = QAction("&"+source,self,triggered=gen_func())
            i = self.main_form.icons["blank"]
            if source in self.main_form.icons:
                i = self.main_form.icons[source]
            action.setIcon(QIcon(i))
            self.menus["view"].addAction(action)
    def click_tray_icon(self):
        self.show()
    def really_close(self):
        self.exit_requested = True
        self.trayicon.hide()
        self.close()
    def closeEvent(self, event):
        if self.exit_requested:
            event.accept()
        else:
            event.ignore()
            self.hide()

DATA_GAMEID = 101
DATA_SORT = 12
DATA_EDIT = 145
class WILastPlayed(QTableWidgetItem):
    def __lt__(self, other):
        first = self.data(DATA_SORT)
        last = other.data(DATA_SORT)
        if not first:
            first = 0
        if not last:
            last = 0
        return first<last

a = WILastPlayed()
b = WILastPlayed()
a.setText("Wed")
a.setData(DATA_SORT,"a")
b.setText("Mon")
b.setData(DATA_SORT,"b")
assert a<b
assert b>a

def make_callback(f, *args):
    return lambda: f(*args)

class GamelistForm(QWidget):
    log_trigger = pyqtSignal(str)
    error_trigger = pyqtSignal(str)
    def __init__(self, parent=None):
        super(GamelistForm, self).__init__(parent)
        
        self.timer_started = 0

        self.init_config()
        self.log = syslog.SysLog(self.config["root"]+"/log.txt")
        self.log.add_callback(self.log_if_window)
        self.logwindow_lock = threading.Lock()
        self.logwindow_messages = []
        self.log_trigger.connect(self.handle_log_message)
        self.log.write("Root config:",self.config)
        
        self.error_trigger.connect(self.handle_error)
        
        self.columns = [("s",None,None),("icon",None,None),("name","widget_name","name"),
                        ("genre","genre","genre"),("playtime",None,"playtime_hours_minutes"),("lastplay",None,None)]
        self.changed = []

        self.hide_packages = True
        self.show_hidden = False
        self.show_installed = False #If True, games not installed are hidden
 
        buttonLayout1 = QVBoxLayout()
        
        self.searchbar = QWidget()
        self.searchbarlayout = QHBoxLayout()
        self.searchbar.setLayout(self.searchbarlayout)
        buttonLayout1.addWidget(self.searchbar)
        
        self.search_name = QLineEdit()
        self.search_name.setPlaceholderText("Search: Name")
        self.searchbarlayout.addWidget(self.search_name)
        self.search_name.textChanged.connect(self.dosearch)
        
        self.search_genre = QLineEdit()
        self.search_genre.setPlaceholderText("Search: Genre")
        self.searchbarlayout.addWidget(self.search_genre)
        self.search_genre.textChanged.connect(self.dosearch)

        self.search_platform = QLineEdit()
        self.search_platform.setPlaceholderText("Search: Source")
        self.searchbarlayout.addWidget(self.search_platform)
        self.search_platform.textChanged.connect(self.dosearch)

        self.sort = "priority"
        self.games_list_widget = QTableWidget()
        self.total_played_list = QTableWidget()
        self.total_played_list.setRowCount(1)
        self.total_played_list.setColumnCount(5)
        self.total_played_list.resizeColumnsToContents()
        self.total_played_list.resizeRowsToContents()
        self.total_played_list.horizontalHeader().setVisible(False)
        self.total_played_list.verticalHeader().setVisible(False)
        self.total_played_list.setFixedHeight(22)

        self.game_scroller = QScrollArea()
        self.game_scroller.setWidgetResizable(True)
        self.game_scroller.setWidget(self.games_list_widget)
        buttonLayout1.addWidget(self.game_scroller)
        buttonLayout1.addWidget(self.total_played_list)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)

        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")

        self.icons = {}
        for icon in os.listdir("icons"):
            self.icons[icon.split(".")[0]] = QPixmap("icons/%s"%icon)
        for source in games.sources.all:
            if source not in self.icons:
                self.icons[source] = QPixmap("icons/blank.png")
        self.gicons = {}
        self.icon_processes = []
        self.icon_thread = ProcessIconsThread()
        self.icon_thread.app = self
        
        ImportThread.app = self
        self.importer_threads = {"gog":ImportThread(),"steam":ImportThread(),"humble":ImportThread()}

        self.timer = QTimer(self)
        self.timer.setInterval(300000)
        #self.timer.setInterval(5000)
        #self.timer.timeout.connect(self.notify)
        
        self.setMinimumSize(600,640)
        #self.setMaximumWidth(1080)
        self.adjustSize()

        self.running = None #Game currently being played

        self.game_options_dock = QDockWidget("Game Options",self)
        self.game_options_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.game_options_dock.setMaximumWidth(300)
        self.game_options_dock.setMinimumWidth(300)
        self.game_options_dock.setMaximumHeight(800)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,self.game_options_dock)
        
    def log_if_window(self,text):
        self.logwindow_lock.acquire()
        if hasattr(self,"log_window") and self.log_window.isVisible():
            self.log_trigger.emit(text)
        self.logwindow_lock.release()
        
    def handle_log_message(self,text):
        self.log_window.add_text(text)
        
    def handle_error(self,text):
        message = {"steam":"Steam api key or account name may be invalid",
                        "gog":"Gog username or password may be invalid",
                        "humble":"Humble username or password may be invalid"}[text]
        highlight_fields = {"steam":["steam_id","steam_api"],
                                "gog":["gog_user","gog_password"],
                                "humble":["humble_username","humble_password"]}[text]
        af = account.AccountForm(self,message,highlight_fields)
        af.show()
        
    def init_config(self):
        self.crypter = enc.Crypter()
        from code.appdirs import appdirs
        self.path_base = appdirs.user_data_dir("MyBacklog").replace("\\","/")
        if not os.path.exists(self.path_base):
            os.makedirs(self.path_base)
        #~ root = {"games":self.path_base+"/games.json",
                    #~ "local":self.path_base+"/local.json",
                    #~ "accounts":self.path_base+"/accounts.json",
                    #~ "root_config":self.path_base+"/root.json",
                    #~ "root":self.path_base}
        root = {"games":"",
                    "local":self.path_base+"/local.json",
                    "accounts":self.path_base+"/accounts.json",
                    "root_config":self.path_base+"/root.json",
                    "root":self.path_base,
                    "rk":str(self.crypter.root_key)}
        if os.path.exists(root["root_config"]):
            f = open(root["root_config"])
            d = json.loads(f.read())
            f.close()
            root.update(d)
        self.config = root
        self.crypter.root_key = eval(self.config["rk"])
        self.save_config()
        
        account = {"steam": {"api": "", "shortcut_folder": "", "id": "","userfile":""},
                   "gog": {"user": "", "pass": ""},
                   "humble": {"username": "", "password": ""}}
        if os.path.exists(root["accounts"]):
            try:
                saved_accounts = json.loads(self.crypter.read(open(root["accounts"]).read(),"{}"))
            except:
                raise
                saved_accounts = {}
            for k in saved_accounts:
                account[k].update(saved_accounts[k])
        self.set_accounts(account)
        
        for path in ["/cache","/cache/batches","/cache/icons","/cache/extract"]:
            if not os.path.exists(root["root"]+path):
                os.mkdir(root["root"]+path)

        if not root["games"]:
            self.options = base_paths.PathsForm(self,"Please define where to store your game database",["games"])
            self.options.show()

    def init_gamelist(self):
        self.games = games.Games(self.log)
        self.games_lock = threading.Lock()
        print("loading games",self.config["games"])
        self.games.load(self.config["games"],self.config["local"])
        self.gamelist = []
        self.update_gamelist_widget()
        
    def save_config(self):
        f = open(self.config["root_config"],"w")
        f.write(json.dumps(self.config,indent=4,sort_keys=True))
        f.close()

    def set_accounts(self,account):
        self.gog = gogapi.Gog(self,account["gog"]["user"],account["gog"]["pass"])
        self.steam = steamapi.Steam(self,account["steam"]["api"],account["steam"]["id"],account["steam"]["userfile"],account["steam"]["shortcut_folder"])
        self.humble = humbleapi.Humble(self,account["humble"]["username"],account["humble"]["password"])
        games.sources.SteamSource.api = self.steam
        games.sources.GogSource.api = self.gog

    def disable_edit_notify(self):
        try:
            self.games_list_widget.cellChanged.disconnect(self.cell_changed)
        except:
            pass

    def enable_edit_notify(self):
        self.games_list_widget.cellChanged.connect(self.cell_changed)
        
    def save(self):
        self.disable_edit_notify()
        self.games.save(self.config["games"],self.config["local"])
        for row in range(self.games_list_widget.rowCount()):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid in self.changed:
                self.update_game_row(self.games.games[gameid],row)
        self.changed = []
        self.enable_edit_notify()

    def file_save(self):
        self.save()

    def file_options(self):
        print("start","SELF=",self)
        self.edit_account = account.AccountForm(self,dock=True)
        self.edit_paths = base_paths.PathsForm(self,dock=True)
        self.options_window = w = QMainWindow()
        dock1 = QDockWidget("Accounts",self)
        dock1.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock1.setWidget(self.edit_account)
        w.addDockWidget(Qt.LeftDockWidgetArea,dock1)
        dock2 = QDockWidget("Paths",self)
        dock2.setWidget(self.edit_paths)
        dock2.setFeatures(QDockWidget.NoDockWidgetFeatures)
        w.addDockWidget(Qt.LeftDockWidgetArea,dock2)
        
        def save_all():
            self.edit_account.save_close()
            self.edit_paths.save_close()
            self.options_window.deleteLater()
        
        button = QPushButton("Save")
        dock2.widget().layout().addWidget(button,15,1)
        button.clicked.connect(save_all)

        print("showing widget")
        w.setWindowTitle("Options")
        w.window().setWindowFlags(Qt.WindowStaysOnTopHint)
        w.show()
        

    def notify(self):
        if self.running:
            self.parent().trayicon.showMessage("Still Playing","Are you still playing %s ?"%self.running.name)

    def get_row_for_game(self,game):
        for row in range(self.games_list_widget.rowCount()):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid == game.gameid:
                return row

    def select_game(self,game):
        row = self.get_row_for_game(game)
        self.games_list_widget.setCurrentCell(row,2)

    def process_icons(self):
        for widget,game,size in self.icon_processes:
            icon = icons.icon_for_game(game,48,self.gicons,self.config["root"])
            if icon:
                try:
                    widget.setIcon(icon)
                except:
                    pass

    def set_icon(self,widget,game,size):
        cached = icons.icon_in_cache(game,self.gicons,self.config["root"])
        if cached:
            widget.setIcon(cached)
            return
        self.icon_processes.append((widget,game,48))
        
    def update_game_row(self,game,row=None,list_widget=None):
        if list_widget is None:
            list_widget = self.games_list_widget
        if row is None:
            row = self.get_row_for_game(game)
        if row is None:
            #Add a row
            row = list_widget.rowCount()
            list_widget.setRowCount(row+1)

        def abreve(t,l):
            if len(t)<l:
                return t
            words = t.split(" ")
            for i in range(len(words)):
                t = " ".join(words)
                if len(t)<l:
                    return t
                words[-i] = words[-i].replace("a","").replace("e","").replace("i","").replace("o","").replace("u","")
            return " ".join(words)[:l]

        game.widget_name = game.name
        if game.is_in_package:
            package = self.games.get_package_for_game(game)
            if package:
                game.widget_name = "["+abreve(package.name,25)+"] "+game.name
        game.widget_name = abreve(game.widget_name,100)
        if game.finished:
            bg = QColor(100,200,150)
        elif game.is_package:
            bg = QColor(100,100,200)
        else:
            b = max(100,215-game.priority*40)
            bg = QColor(285-b,285-b,285-b)
            #bg = QColor(self.palette().Background)

        source = QTableWidgetItem("")
        source.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        source.setBackground(bg)
        source.setData(DATA_GAMEID,game.gameid)
        for s in game.sources:
            if s["source"] in self.icons:
                source.setIcon(QIcon(self.icons[s["source"]]))
            else:
                source.setIcon(QIcon(self.icons["blank"]))
        list_widget.setItem(row,0,source)
            
        label = QTableWidgetItem("")
        label.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        label.setBackground(bg)
        self.set_icon(label,game,48)
        self.icon_thread.start()
        list_widget.setItem(row,1,label)
            
        name = QTableWidgetItem("GAME NAME")
        name.setBackground(bg)
        #TODO: Currently disabled
        name.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        name.setText(game.widget_name)
        list_widget.setItem(row,2,name)

        genre = QTableWidgetItem("GAME GENRE")
        #TODO: Currently disabled
        genre.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        genre.setBackground(bg)
        genre.setText(game.genre)
        list_widget.setItem(row,3,genre)

        hours = QTableWidgetItem("GAME HOURS")
        #TODO: CURRENTLY DISABLED
        hours.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        hours.setBackground(bg)
        hours.setText(game.playtime_hours_minutes)
        list_widget.setItem(row,4,hours)

        lastplayed = WILastPlayed("GAME LAST PLAYED")
        lastplayed.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        lastplayed.setBackground(bg)
        lastplayed.setText(game.last_played_nice)
        lastplayed.setData(DATA_SORT,time.mktime(games.stot(game.lastplayed)))
        list_widget.setItem(row,5,lastplayed)

    def update_gamelist_widget(self):
        self.disable_edit_hooks()
        self.gamelist = []
        for g in self.games.list(self.sort):
            self.gamelist.append({"game":g,"widget":None})
        self.games_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.games_list_widget.clear()
        self.games_list_widget.setIconSize(QSize(28,28))
        self.games_list_widget.horizontalHeader().setVisible(True)
        self.games_list_widget.verticalHeader().setVisible(False)
        self.games_list_widget.setRowCount(len(self.gamelist))
        self.games_list_widget.setColumnCount(6)
        self.games_list_widget.itemSelectionChanged.connect(self.selected_row)
        
        i = -1
        for i,g in enumerate(self.gamelist):
            self.update_game_row(g["game"],i)
        self.update_game_row(games.Game(name="Total Time Played"),0,list_widget=self.total_played_list)
        self.dosearch()
        self.total_played_list.resizeColumnsToContents()

        self.game_scroller.verticalScrollBar().setValue(0)
        self.games_list_widget.setHorizontalHeaderLabels([x[0] for x in self.columns])
        self.games_list_widget.resizeColumnsToContents()
        self.games_list_widget.setColumnWidth(0,34)
        self.games_list_widget.setColumnWidth(1,34)
        self.games_list_widget.setColumnWidth(2,200)
        self.games_list_widget.setColumnWidth(3,80)
        self.games_list_widget.setColumnWidth(4,60)
        self.games_list_widget.setColumnWidth(5,150)
        self.games_list_widget.resizeRowsToContents()

        self.games_list_widget.setSortingEnabled(True)

        self.enable_edit_hooks()

        self.dosearch()
        self.update()
        
    def disable_edit_hooks(self):
        try:
            self.games_list_widget.cellChanged.disconnect(self.cell_changed)
        except TypeError:
            pass
            
    def enable_edit_hooks(self):
        self.games_list_widget.cellChanged.connect(self.cell_changed)
        self.games_list_widget.cellDoubleClicked.connect(self.cell_activated)
        
    def edit_emulators(self):
        self.emulator_form = emulatorform.EmulatorForm(self)
        self.emulator_form.show()
        
    def edit_sources(self):
        self.sources_form = sourcesform.SourcesForm(self)
        self.sources_form.show()
        
    def import_all(self):
        self.import_steam()
        self.import_gog()
        self.import_humble()

    def import_steam(self):
        self.view_log()
        def f(self):
            self.log.write("STEAM IMPORT BEGUN... please wait...")
            try:
                games = self.steam.import_steam()
            except steamapi.ApiError:
                self.log.write("STEAM IMPORT... ERROR. Check options.")
                self.error_trigger.emit("steam")
                return
            self.games.add_games(games)
            self.update_gamelist_widget()
            self.save()
            self.log.write("STEAM IMPORT FINISHED")
        self.importer_threads["steam"].func = f
        self.importer_threads["steam"].start()

    def import_humble(self):
        self.view_log()
        def f(self):
            self.log.write("HUMBLE IMPORT BEGUN... please wait...")
            try:
                games = self.humble.get_gamelist()
            except humbleapi.ApiError:
                self.log.write("HUMBLE IMPORT... ERROR. Check options.")
                self.error_trigger.emit("humble")
                return
            self.games.add_games(games)
            self.update_gamelist_widget()
            self.save()
            self.log.write("HUMBLE IMPORT FINISHED")
        self.importer_threads["humble"].func = f
        self.importer_threads["humble"].start()

    def import_gog(self):
        #self.browser = Browser("https://secure.gog.com/account/games",self)
        self.view_log()
        def f(self):
            self.log.write("GOG IMPORT BEGUN... please wait...")
            try:
                games = self.gog.better_get_shelf(self.games.multipack)
            except gogapi.BadAccount:
                self.log.write("GOG IMPORT... ERROR. Check options.")
                self.error_trigger.emit("gog")
                return
            self.games.add_games(games)
            self.update_gamelist_widget()
            self.save()
            self.log.write("GOG IMPORT FINISHED")
        self.importer_threads["gog"].func = f
        self.importer_threads["gog"].start()
        
    def cleanup_add_steam_shortcuts(self):
        self.steam.create_nonsteam_shortcuts(self.games.games)

    def sync_uploadgames(self):
        uploadrequest(self.games)

    def sync_downloadgames(self):
        games = downloadrequest()
        self.games = games.Games(self.log)
        self.games.translate_json(games)
        self.save()
        self.update_gamelist_widget()

    def cleanup_gamesdb(self):
        for g in self.games.games.values():
            gdbg = thegamesdb.find_game(g.name)
            if gdbg:
                data = thegamesdb.get_game_info(gdbg["id"])
                if data and "Game" in data:
                    print (data["Game"])
                    genre = data["Game"].get("Genres",{}).get("genre","")
                    coop = data["Game"].get("Co-op","No").lower().strip()=="yes"
                    if type(genre) not in [str,bytes]:
                        genre = [x for x in genre if type(x) in [str,bytes]][0]
                    print(genre,coop)
                    g.genre = genre.lower()
                    if coop:
                        g.genre = g.genre+"; co-op"
                    print(g.genre)
        self.save()

    def cleanup_giantbomb(self):
        for g in self.games.games.values():
            gdbg = giantbomb.find_game(g.name)
            if gdbg:
                data = thegamesdb.get_game_info(gdbg["id"])
                if data and "Game" in data:
                    print (data["Game"])
                    genre = data["Game"]["Genres"].get("genre","")
                    coop = data["Game"]["Co-op"]
                    if type(genre) not in [str,bytes]:
                        genre = [x for x in genre if type(x) in [str,bytes]][0]
                    print(genre,coop)
                    g.genre = genre.lower()
                    if coop:
                        g.genre = g.genre+"; co-op"
                    print(g.genre)
        self.save()
        
    def view_log(self):
        #self.log_dock = QDockWidget("Log Window",self)
        self.log_window = logwindow.LogForm(self)
        #self.window().addDockWidget(Qt.BottomDockWidgetArea,self.log_dock)
        #self.log_dock.setWidget(self.log_window)
        self.log_window.show()

    def view_sort_by_added(self):
        self.sort = "added"
        self.update_gamelist_widget()

    def view_sort_by_priority(self):
        self.sort = "priority"
        self.update_gamelist_widget()

    def view_sort_by_changed(self):
        self.sort = "changed"
        self.update_gamelist_widget()

    def view_show_packages(self):
        self.hide_packages = not self.hide_packages
        self.update_gamelist_widget()

    def view_show_hidden(self):
        self.show_hidden = not self.show_hidden
        self.update_gamelist_widget()

    def view_show_installed(self):
        self.show_installed = not self.show_installed
        self.update_gamelist_widget()

    def run_game_notimer(self,game):
        return self.run_game(game,track_time=False)

    def run_game(self,game,track_time=True):
        if getattr(self,"stop_playing_button",None):
            return
        #self.setStyleSheet("background-color:red;")
        self.old_style = self.parent().styleSheet()
        if track_time:
            self.timer_started = time.time()
        print ("run game",game.name,game.gameid)
        self.timer.start()
        
        if track_time:
            self.stop_playing_button = QPushButton("Stop Playing "+game.name)
            self.game_options_dock.widget().layout().addWidget(self.stop_playing_button)
            self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))
            self.stop_playing_button.setStyleSheet("background-color:green;")
            self.stop_playing_button.setFixedHeight(64)
            self.parent().setWindowIcon(QIcon(QPixmap("icons/playing.png")))
            self.parent().trayicon.setIcon(QIcon(QPixmap("icons/playing.png")))
            self.parent().setStyleSheet("background-color:red;")
            self.parent().setWindowTitle("MyBacklog %s (Playing %s)"%(VERSION,game.name))

        self.running = game
        game.run_game(self.config["root"])
        self.games.play(game)
        playrequest(game)

    def stop_playing(self,game):
        self.parent().setStyleSheet(self.old_style)
        self.parent().setWindowIcon(QIcon(QPixmap("icons/main.png")))
        self.parent().trayicon.setIcon(QIcon(QPixmap("icons/main.png")))
        self.parent().setWindowTitle("MyBacklog %s"%VERSION)
        self.running = None
        self.games.stop(game)
        self.timer.stop()
        #stoprequest()
        #self.buttonLayout1.removeWidget(self.stop_playing_button)
        if getattr(self,"stop_playing_button",None):
            self.stop_playing_button.deleteLater()
        self.stop_playing_button = None
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.played()
        game.playtime += elapsed_time
        game.priority = -1
        self.save()
        self.update_gamelist_widget()

    def show_edit_widget(self,*args,**kwargs):
        self.egw = gameoptions.EditGame(*args,**kwargs)
        dock = QDockWidget("Edit",self)
        dock.setWidget(self.egw)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,dock)
        return self.egw

    def selected_row(self):
        #Clean up from before if we messed with a field
        if getattr(self,"editing_section",None):
            print("FIXING EDITING SECTION")
            self.cell_changed(*self.editing_section)
            self.editing_section = None
        if self.games_list_widget.selectedItems():
            item = self.games_list_widget.selectedItems()[0]
            row = item.row()
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid not in self.games.games:
                return
            game = self.games.games[gameid]
            self.update_game_options(game)

            if getattr(self,"stop_playing_button",None):
                self.game_options_dock.widget().layout().addWidget(self.stop_playing_button)
                #self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))

    def cell_changed(self,row,col):
        if getattr(self,"editing_section",None) == (row,col):
            self.editing_section = None
        print("changed",row,col)
        gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
        if gameid not in self.games.games:
            return
        self.disable_edit_hooks()
        game = self.games.games[gameid]
        changed = True
        nv = self.games_list_widget.item(row,col).text()
        #Reset title
        if col==2:
            changed = False
            nv = self.games_list_widget.item(row,col).text()
            if nv != game.name:
                changed = True
            print("setting widget name to",game.widget_name)
        if changed:
            if self.columns[col][2]:
                print("setting",gameid,self.columns[col][2],"to",nv)
                setattr(game,self.columns[col][2],nv)
            self.changed.append(gameid)
            self.update_game_row(game,row)
            self.games_list_widget.item(row,col).setBackground(QColor(200,10,10))
        else:
            oldbg = self.games_list_widget.item(row,col).background()
            self.update_game_row(game,row)
            self.games_list_widget.item(row,col).setBackground(oldbg)
        #self.selected_row()
        self.enable_edit_hooks()

    def cell_activated(self,row,col):
        self.disable_edit_hooks()
        if self.columns[col][2]:
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            game = self.games.games[gameid]
            print("SETTING EDITING SECTION")
            self.editing_section = (row,col)
            self.games_list_widget.item(row,col).setText(getattr(game,self.columns[col][2]))
        self.enable_edit_hooks()

    def update_game_options(self,game,new=False):
        self.game_options = gameoptions.GameOptions(game,self,new)
        self.game_options_dock.setWidget(self.game_options)

        return self.game_options

    def uninstall_game(self,game):
        game.uninstall()
        
    def hide_game(self,game):
        game.hidden = 1
        self.save()
        self.update_gamelist_widget()
        self.update_game_options(game)
        
    def unhide_game(self,game):
        game.hidden = 0
        self.save()
        self.update_gamelist_widget()
        self.update_game_options(game)
        
    def finish_game(self,game):
        game.finished = 1
        game.finish_date = games.now()
        self.save()
        self.update_gamelist_widget()
        self.update_game_options(game)
        
    def unfinish_game(self,game):
        game.finished = 0
        game.finish_date = ""
        self.save()
        self.update_gamelist_widget()
        self.update_game_options(game)

    def download(self,game):
        game.download_method()

    def add_game(self,source):
        print("adding game with source:",source)
        game = games.Game(sources=[{"source":source}],import_date=games.now(),games=self.games)
        self.gamelist.append({"game":game,"widget":None})
        #self.show_edit_widget(game,self,new=True)
        self.update_game_options(game,new=True)

    def dosearch(self):
        played = 0

        sn = self.search_name.text().lower()
        sg = self.search_genre.text().lower()
        sp = self.search_platform.text().lower()
        if sp == "emu":
            sp = "gba or snes or n64 or nds"
        row = -1 #For when game list is empty
        for row in range(self.games_list_widget.rowCount()):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            game = self.games.games[gameid]
            self.games_list_widget.setRowHidden(row,False)
            if game.is_package and self.hide_packages:
                self.games_list_widget.setRowHidden(row,True)
                continue
            if self.show_installed:
                if not game.is_installed():
                    self.games_list_widget.setRowHidden(row,True)
                    continue
            if game.hidden and not self.show_hidden:
                self.games_list_widget.setRowHidden(row,True)
                continue
            def match(search,field):
                searches = search.split(" or ")
                for s in searches:
                    if s in field:
                        return True
            if (sn and not (match(sn,game.name.lower()) or match(sn,game.package_data.get("parent",{}).get("name","").lower()) )) or \
            (sg and not match(sg,game.genre.lower())) or \
            (sp and not match(sp," ".join([s["source"] for s in game.sources]))):
                self.games_list_widget.setRowHidden(row,True)
                continue

            played += game.playtime

        #Total playtime
        total_hours = QTableWidgetItem("GAME HOURS")
        min = played/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        day = int(hour/24.0)
        if day:
            hour = hour-day*24.0
            total_hours.setText("%.2dd%.2d:%.2d"%(day,hour,min))
        else:
            total_hours.setText("%.2d:%.2d"%(hour,min))
        self.total_played_list.setItem(0,4,total_hours)
 
def run():
    import sys
    import PyQt5.Qt

    from PyQt5 import QtCore
    if os.path.exists("PyQt5/plugins"):
        QtCore.QCoreApplication.addLibraryPath("PyQt5/plugins")

    print("INITIALIZE")
    app = PyQt5.Qt.QApplication(sys.argv)

    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53,53,53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15,15,15))
    palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53,53,53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    
    palette.setColor(QPalette.Highlight, QColor(142,45,197).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    print("Build mybacklog")
    window = MyBacklog()
    print("Show mybacklog")
    window.show()
    window.reset_games()
 
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
