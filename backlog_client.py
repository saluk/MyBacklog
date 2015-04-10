#!python3

#STDLIB
import json
import os
import sys
import time
import requests

#backloglib
import data
import steamapi
import gogapi
import humbleapi
import thegamesdb
import giantbomb
import winicons
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWebKit
print(dir(QtWebKit))
from PyQt5.QtWebKitWidgets import *
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


def make_callback(f, *args):
    return lambda: f(*args)


class RunGameThread(QThread):
    process = None
    stopfunc = None
    def run(self):
        while self.process and self.process.returncode is None:
            self.process.communicate()


class Cookies(QNetworkCookieJar):
    def __init__(self):
        super(Cookies, self).__init__()
        self.cookies = {}
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


class ListGamesForPack(QWidget):
    def __init__(self, game, row_widget, app):
        super(ListGamesForPack, self).__init__()
        self.game = game
        self.game.is_package = 1
        self.app = app
        
        self.row_widget = row_widget
        
        self.oldid = game.gameid
        
        #Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Editing Package:"+game.gameid))
        
        current_games = game.games_for_pack(self.app.games)
        
        #Fields
        self.fields = {}
        for i in range(15):
            label = QLabel("Game %d"%i)
            layout.addWidget(label,i+1,0)
            
            gname = ""
            next_game = None
            if current_games:
                next_game = current_games.pop(0)
                gname = next_game.name
            
            edit = QLineEdit(gname)
            layout.addWidget(edit,i+1,1)
            self.fields[i] = {"w":edit,"g":next_game}
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)
        
        self.setLayout(layout)

    def save_close(self):
        self.app.games.multipack[self.game.gogid] = []
        for field in self.fields:
            field = self.fields[field]
            name = field["w"].text()
            if not name:
                continue
            game = field["g"]
            if not game:
                game = self.game.copy()
                game.is_package = 0
            game.name = name
            game.packageid = name.lower().replace(" ","_")
            self.app.games.multipack[self.game.gogid].append(game.packageid)
            self.app.games.games[game.gameid] = game
            #Add or update row in list
        self.app.games.save("games.json")
        self.app.update_gamelist_widget()
        self.deleteLater()

class EditGame(QWidget):
    def __init__(self, game, row_widget, app, new=False):
        super(EditGame, self).__init__()
        self.game = game.copy()
        self.app = app
        self.games = app.games
        
        self.row_widget = row_widget

        self.oldid = None
        if not new:
            self.oldid = game.gameid
        
        #Layout
        layout = QGridLayout()
        if new:
            layout.addWidget(QLabel("Adding new game"))
        else:
            layout.addWidget(QLabel("Editing:"+game.gameid))
        
        #Fields
        self.fields = {}
        for i,prop in enumerate(game.valid_args):
            prop,proptype = prop
            label = QLabel("%s:"%prop.capitalize())
            layout.addWidget(label,i+1,0)
            edit = QLineEdit(str(getattr(game,prop)))
            layout.addWidget(edit,i+1,1)
            self.fields[prop] = {"w":edit,"t":proptype}
            
            if prop=="install_path":
                button = QPushButton("Set Path")
                layout.addWidget(button,i+1,2)
                button.clicked.connect(make_callback(self.set_filepath,edit))
        if game.source=="gog" or game.source=="humble":
            name = "Make Package"
            if game.is_package:
                name = "Edit Package"
            button = QPushButton(name)
            layout.addWidget(button, i+2, 0)
            button.clicked.connect(make_callback(self.make_package))
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)

        #Delete button
        button = QPushButton("Delete")
        layout.addWidget(button)
        button.clicked.connect(self.delete)
        
        self.setLayout(layout)

    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*.exe *.lnk *.cmd *.bat)")[0]
        w.setText(filename.replace("/","\\"))

    def make_package(self):
        self.lg = ListGamesForPack(self.game,self.row_widget,self.app)
        self.lg.show()

    def save_close(self):
        for field in self.fields:
            value = self.fields[field]["w"].text()
            t = self.fields[field]["t"]
            if t == "i":
                value = int(value)
            elif t == "f":
                value = float(value)
            setattr(self.game,field,value)
        newid = self.game.gameid
        print("save", newid, self.oldid)
        if newid!=self.oldid:
            if self.oldid in self.games.games:
                self.games.games[newid] = self.games.games[self.oldid]
                del self.games.games[self.oldid]
        self.games.update_game(self.game.gameid,self.game,force=True)
        self.games.save("games.json")
        self.app.update_gamelist_widget()
        self.deleteLater()
        self.parent().deleteLater()

    def delete(self):
        self.games.delete(self.game)
        self.games.save("games.json")
        self.deleteLater()
        self.app.update_gamelist_widget()

def icon_for_game(game,size,icon_cache):
    if game.icon_url:
        fpath = "cache/icons/"+game.icon_url.replace("http","").replace("https","").replace(":","").replace("/","")
        if not os.path.exists(fpath):
            r = requests.get(game.icon_url)
            f = open(fpath,"wb")
            f.write(r.content)
            f.close()
    elif game.install_path and game.install_path.endswith(".exe"):
        fpath = "cache/icons/"+game.install_path.replace("http","").replace("https","").replace(":","").replace("/","").replace("\\","")
        if not os.path.exists(fpath):
            p = winicons.get_icon(game.install_path)
            import shutil
            if p:
                shutil.copy(p,fpath)
    elif game.install_path and game.install_path.endswith(".gba"):
        fpath = "cache/icons/"+game.install_path.replace("http","").replace(":","").replace("/","").replace("\\","")
        if not os.path.exists(fpath):
            p = winicons.get_gba(game.install_path)
            import shutil
            if p:
                shutil.copy(p,fpath)
    else:
        fpath = "icons/blank.png"
    if os.path.exists(fpath) and not fpath+"_%d"%size in icon_cache:
        qp = QPixmap(fpath)
        if not qp.isNull():
            qp = qp.scaled(size,size)
        icon_cache[fpath] = qp
    if fpath in icon_cache:
        return QIcon(icon_cache[fpath])

class GameOptions(QWidget):
    def __init__(self, game, widget, app):
        super(GameOptions, self).__init__()
        self.game = game.copy()
        self.app = app
        self.games = app.games

        #Layout
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)

        label_section = QGridLayout()
        label_section.addWidget(QLabel(game.name),1,0)
        icon = icon_for_game(game,128,self.app.gicons)
        if icon:
            iconw = QLabel()
            iconw.setPixmap(icon.pixmap(128,128))
            label_section.addWidget(iconw,0,0)

        layout.addLayout(label_section,0,0)

        if not game.missing_steam_launch():
            run = QPushButton("Play Game")
        else:
            run = QPushButton("Play Game (no steam)")
        run.clicked.connect(make_callback(self.app.run_game,game))
        layout.addWidget(run)

        run_no_timer = QPushButton("Play without time tracking")
        run_no_timer.clicked.connect(make_callback(self.app.run_game_notimer,game))
        layout.addWidget(run_no_timer)

        download = QPushButton("Download")
        download.clicked.connect(make_callback(self.app.download,game))
        layout.addWidget(download)

        edit = QPushButton("Edit")
        edit.clicked.connect(make_callback(self.app.edit_game,game,widget))
        layout.addWidget(edit)

        edit = QPushButton("Uninstall")
        edit.clicked.connect(make_callback(self.app.uninstall_game,game,widget))
        layout.addWidget(edit)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        #super(MainWindow,self).__init__(None,Qt.WindowStaysOnTopHint)
        super(MainWindow,self).__init__(None)
        self.setWindowTitle("MyBacklog")
        self.setWindowIcon(QIcon(QPixmap("icons/steam.png")))
        self.main_form = Form(self)

        menus = {}
        for folder in ["file","import","cleanup","sync","view"]:
            menus[folder] = self.menuBar().addMenu("&"+folder.capitalize())
            for x in dir(self.main_form):
                if x.startswith(folder+"_"):
                    name = " ".join([y.capitalize() for y in x.split("_")[1:]])
                    menus[folder].addAction(QAction("&"+name,self,triggered=getattr(self.main_form,x)))
        menus["view"] = self.menuBar().addMenu("&Add Game")
        for source in data.sources:
            menus["view"].addAction(QAction("&"+source,self,triggered=lambda : self.main_form.add_game(source)))

        menus["file"].addAction(QAction("&Exit",self,triggered=self.really_close))
        self.exit_requested = False

        self.setCentralWidget(self.main_form)

        self.trayicon = QSystemTrayIcon(QIcon(QPixmap("icons/steam.png")))
        self.trayicon.show()
        self.trayicon.activated.connect(self.click_tray_icon)
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

class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        
        self.timer_started = 0
        
        self.games = data.Games()
        self.games.load("games.json")
        self.gamelist = []

        self.hide_packages = True
        self.show_hidden = False
 
        buttonLayout1 = QVBoxLayout()
        
        self.searchbar = QWidget()
        self.searchbarlayout = QHBoxLayout()
        self.searchbar.setLayout(self.searchbarlayout)
        buttonLayout1.addWidget(self.searchbar)
        
        self.search_name = QLineEdit()
        self.searchbarlayout.addWidget(self.search_name)
        self.search_name.textChanged.connect(self.dosearch)
        
        self.search_genre = QLineEdit()
        self.searchbarlayout.addWidget(self.search_genre)
        self.search_genre.textChanged.connect(self.dosearch)

        self.search_platform = QLineEdit()
        self.searchbarlayout.addWidget(self.search_platform)
        self.search_platform.textChanged.connect(self.dosearch)

        self.sort = "priority"
        self.games_list_widget = QTableWidget()

        self.game_scroller = QScrollArea()
        self.game_scroller.setWidgetResizable(True)
        self.game_scroller.setWidget(self.games_list_widget)
        buttonLayout1.addWidget(self.game_scroller)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)

        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")

        self.icons = {}
        for icon in os.listdir("icons"):
            self.icons[icon.split(".")[0]] = QPixmap("icons/%s"%icon)
        for source in data.sources:
            if source not in self.icons:
                self.icons[source] = QPixmap("icons/blank.png")
        self.gicons = {}

        self.timer = QTimer(self)
        self.timer.setInterval(300000)
        #self.timer.setInterval(5000)
        self.timer.timeout.connect(self.notify)
        
        self.update_gamelist_widget()
        self.setMinimumSize(740,600)
        self.setMaximumWidth(1080)
        self.adjustSize()

        self.running = None #Game currently being played

        self.game_options_dock = QDockWidget("Game Options",self)
        self.game_options_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.game_options_dock.setMaximumWidth(300)
        self.game_options_dock.setMinimumWidth(300)
        self.game_options_dock.setMaximumHeight(400)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,self.game_options_dock)

    def notify(self):
        if self.running:
            self.parent().trayicon.showMessage("Still Playing","Are you still playing %s ?"%self.running.name)
        
    def get_row_for_game(self,game,w=[]):
        widgets = w[:]
        if not w:
            source = QTableWidgetItem("")
            widgets.append(source)
            source.setData(DATA_GAMEID,game.gameid)
            
            label = QTableWidgetItem("")
            widgets.append(label)
            
            name = QTableWidgetItem("GAME NAME")
            widgets.append(name)
            
            genre = QTableWidgetItem("GAME GENRE")
            widgets.append(genre)
            
            hours = QTableWidgetItem("GAME HOURS")
            widgets.append(hours)
            
            lastplayed = WILastPlayed("GAME LAST PLAYED")
            lastplayed.setData(DATA_SORT,data.stot(game.lastplayed))
            widgets.append(lastplayed)
        
        if game.source in self.icons:
            widgets[0].setIcon(QIcon(self.icons[game.source]))
        icon = icon_for_game(game,48,self.gicons)
        if icon:
            widgets[1].setIcon(icon)
        def setbg(bg):
            [w.setBackground(bg) for w in widgets if hasattr(w,"setBackground")]
        if game.finished:
            setbg(QColor(100,200,150))
        elif game.is_package:
            setbg(QColor(100,100,200))
        else:
            b = max(100,215-game.priority*40)
            setbg(QColor(b,b,b))
        widgets[2].setText(game.widget_name)
        widgets[4].setText("%.2d:%.2d"%game.hours_minutes)
        #w.hours.setStyleSheet("QWidget {}")
        #if game.playtime < 500:
        #    w.hours.setStyleSheet("QWidget {background-color: red}")
        widgets[3].setText(game.genre)
        widgets[5].setText(game.last_played_nice)
        return widgets

    def update_gamelist_widget(self):
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
        for g in self.gamelist:
            if g["widget"]:
                self.games_list_widget.setRowHidden(g["widget"][0],False)
        self.gamelist = []
        for g in self.games.list(self.sort):
            g.widget_name = g.name
            if g.packageid or g.humble_package:
                package = self.games.get_package_for_game(g)
                if package:
                    g.widget_name = "["+abreve(package.name,25)+"] "+g.name
            g.widget_name = abreve(g.widget_name,100)
            self.gamelist.append({"game":g,"widget":None})
        self.games_list_widget.clear()
        self.games_list_widget.setIconSize(QSize(48,48))
        self.games_list_widget.horizontalHeader().setVisible(True)
        self.games_list_widget.verticalHeader().setVisible(False)
        self.games_list_widget.setRowCount(len(self.gamelist))
        self.games_list_widget.setColumnCount(6)
        self.games_list_widget.itemSelectionChanged.connect(self.selected_row)
        for i,g in enumerate(self.gamelist):
            cols = self.get_row_for_game(g["game"])
            g["widget"] = (i,cols)
            for r,col in enumerate(cols):
                if r>=6:
                    pass
                    self.games_list_widget.setCellWidget(i,r,col)
                else:
                    pass
                    self.games_list_widget.setItem(i,r,col)
        self.dosearch()
        self.game_scroller.verticalScrollBar().setValue(0)
        self.games_list_widget.setHorizontalHeaderLabels(["s","icon","name","genre","playtime","lastplay"])
        self.games_list_widget.resizeColumnsToContents()
        self.games_list_widget.setColumnWidth(0,48)
        self.games_list_widget.setColumnWidth(1,48)
        self.games_list_widget.setColumnWidth(2,350)
        self.games_list_widget.setColumnWidth(3,50)
        self.games_list_widget.setColumnWidth(4,50)
        self.games_list_widget.setColumnWidth(5,150)

        self.games_list_widget.setSortingEnabled(True)

        self.dosearch()
        self.update()

    def import_steam(self):
        games = steamapi.import_steam()
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save("games.json")
        
    def cleanup_add_steam_shortcuts(self):
        steamapi.create_nonsteam_shortcuts(self.games.games)

    def import_humble(self):
        games = humbleapi.get_humble_gamelist()
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save("games.json")

    def import_gog(self):
        #self.browser = Browser("https://secure.gog.com/account/games",self)
        gogapi.better_get_shelf()
        self.import_gog_html()

    def import_gog_html(self):
        games = gogapi.import_gog(self.games.multipack)
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save("games.json")

    def cleanup_fix_gog(self):
        self.games.import_packages()
        self.games.save("games.json")

    def sync_uploadgames(self):
        uploadrequest(self.games)

    def sync_downloadgames(self):
        games = downloadrequest()
        self.games = data.Games()
        self.games.translate_json(games)
        self.games.save("games.json")
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
        self.games.save("games.json")

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
        self.games.save("games.json")

    def view_sort_by_added(self):
        self.sort = "added"
        self.update_gamelist_widget()

    def view_sort_by_priority(self):
        self.sort = "priority"
        self.update_gamelist_widget()

    def view_show_packages(self):
        self.hide_packages = not self.hide_packages
        self.update_gamelist_widget()

    def view_show_hidden(self):
        self.show_hidden = not self.show_hidden
        self.update_gamelist_widget()

    def run_game_notimer(self,game):
        return self.run_game(game,track_time=False)

    def run_game(self,game,track_time=True):
        if getattr(self,"stop_playing_button",None):
            return
        if track_time:
            self.timer_started = time.time()
        print ("run game",game.name,game.gameid)
        self.timer.start()
        
        if track_time:
            self.stop_playing_button = QPushButton("Stop Playing "+game.name)
            self.game_options_dock.widget().layout().addWidget(self.stop_playing_button)
            self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))

        self.running = game
        game.run_game()
        self.games.play(game)
        playrequest(game)

    def stop_playing(self,game):
        self.running = None
        self.games.stop(game)
        self.timer.stop()
        #stoprequest()
        #self.buttonLayout1.removeWidget(self.stop_playing_button)
        self.stop_playing_button.deleteLater()
        self.stop_playing_button = None
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.played()
        game.playtime += elapsed_time
        game.priority = -1
        self.games.save("games.json")
        self.update_gamelist_widget()

    def show_edit_widget(self,*args,**kwargs):
        self.egw = EditGame(*args,**kwargs)
        dock = QDockWidget("Edit",self)
        dock.setWidget(self.egw)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,dock)
        return self.egw

    def selected_row(self):
        if self.games_list_widget.selectedItems():
            item = self.games_list_widget.selectedItems()[0]
            row = item.row()
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            game = self.games.games[gameid]
            self.update_game_options(game,self.gamelist[row]["widget"])

    def update_game_options(self,game,widget):
        self.game_options = GameOptions(game,widget,self)
        self.game_options_dock.setWidget(self.game_options)

        return self.game_options

    def edit_game(self,game,row_widget):
        self.show_edit_widget(game,row_widget,self)

    def uninstall_game(self,game,row_widget):
        game.uninstall()

    def download(self,game):
        game.download_method()

    def add_game(self,source):
        game = data.Game(source=source)
        #row = self.get_row_for_game(game)
        self.gamelist.append({"game":game,"widget":None})
        self.show_edit_widget(game,None,self,new=True)

    def dosearch(self,text=None):
        sn = self.search_name.text().lower()
        sg = self.search_genre.text().lower()
        sp = self.search_platform.text().lower()
        if sp == "emu":
            sp = "gba or snes or n64 or nds"
        def showrow(g):
            self.games_list_widget.setRowHidden(g["widget"][0],False)
        def hiderow(g):
            self.games_list_widget.setRowHidden(g["widget"][0],True)
        for g in self.gamelist:
            game = g["game"]
            showrow(g)
            if game.is_package and self.hide_packages:
                hiderow(g)
                continue
            if game.hidden and not self.show_hidden:
                hiderow(g)
                continue
            def match(search,field):
                searches = search.split(" or ")
                for s in searches:
                    if s in field:
                        return True
            if (sn and not match(sn,game.name.lower())) or \
            (sg and not match(sg,game.genre.lower())) or \
            (sp and not match(sp,game.source.lower())):
                hiderow(g)
                continue
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
 
    sys.exit(app.exec_())
