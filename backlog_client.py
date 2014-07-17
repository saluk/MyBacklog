#!python3

#STDLIB
import json
import os
import time
import requests
import subprocess

#backloglib
import data
import steamapi
import gogapi
import humbleapi
import thegamesdb
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
        r = requests.post("http://dawnsoft.org:9600/users/saluk/upload_games",data=games.save_data())
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
        while self.process.returncode is None:
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
        self.app.get_row_for_game(self.game,self.row_widget)
        self.deleteLater()


class EditGame(QWidget):
    def __init__(self, game, row_widget, app, new=False):
        super(EditGame, self).__init__()
        self.game = game
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
                del self.games.games[self.oldid]
            self.games.games[newid] = self.game
        self.games.save("games.json")
        self.app.get_row_for_game(self.game,self.row_widget)
        self.deleteLater()
        self.parent().deleteLater()

    def delete(self):
        self.games.delete(self.game)
        self.games.save("games.json")
        self.deleteLater()
        self.row_widget.deleteLater()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__(None,Qt.WindowStaysOnTopHint)
        self.main_form = Form()

        menus = {}
        for folder in ["file","import","cleanup","sync"]:
            menus[folder] = self.menuBar().addMenu("&"+folder.capitalize())
            for x in dir(self.main_form):
                if x.startswith(folder+"_"):
                    name = " ".join([y.capitalize() for y in x.split("_")[1:]])
                    menus[folder].addAction(QAction("&"+name,self,triggered=getattr(self.main_form,x)))

        menus["file"].addAction(QAction("&Exit",self,triggered=self.close))

        self.setCentralWidget(self.main_form)

class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        
        self.timer_started = 0
        
        self.games = data.Games()
        self.games.load("games.json")
        self.gamelist = []
 
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
        
        self.games_list_widget = QWidget()
        self.games_list_widget_layout = QGridLayout()
        self.games_list_widget_layout.setSpacing(0)
        self.games_list_widget.setLayout(self.games_list_widget_layout)

        self.game_scroller = QScrollArea()
        self.game_scroller.setWidgetResizable(True)
        #self.game_scroller.setFixedHeight(400)
        #self.game_scroller.setFixedWidth(600)
        self.game_scroller.setWidget(self.games_list_widget)
        buttonLayout1.addWidget(self.game_scroller)
        
        b = QPushButton("Add Game")
        buttonLayout1.addWidget(b)
        b.clicked.connect(self.add_game)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)

        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")
        
        self.icons = {"steam":QPixmap("steam.bmp").scaled(24,24),
                      "gog":QPixmap("gog.bmp").scaled(24,24),
                      "humble":QPixmap("humble.bmp").scaled(24,24)}
        self.gicons = {}
        
        self.update_gamelist_widget()
        self.setMinimumSize(800,600)
        self.adjustSize()
        
    def get_row_for_game(self,game,w=None):
        if not w:
            w = QWidget()
            box = QHBoxLayout()
            w.setLayout(box)
            
            label = QLabel("source icon")
            label.setFixedWidth(24)
            box.addWidget(label)
            w.icon = label
            
            label = QLabel("")
            label.setFixedWidth(24)
            box.addWidget(label)
            w.gicon = label
            
            label = QLabel("GAME NAME")
            box.addWidget(label)
            w.label = label
            
            label = QLabel("GAME GENRE")
            box.addWidget(label)
            w.genre = label
            
            label = QLabel("GAME HOURS")
            label.setMaximumWidth(50)
            box.addWidget(label)
            w.hours = label
            
            label = QLabel("GAME LAST PLAYED")
            label.setMaximumWidth(150)
            box.addWidget(label)
            w.last_played = label

            if not game.missing_steam_launch():
                run = QPushButton("play")
            else:
                run = QPushButton("playalone")
            run.setFixedWidth(50)
            box.addWidget(run)
            run.clicked.connect(make_callback(self.run_game,game))
            
            run = QPushButton("edit")
            run.setFixedWidth(50)
            box.addWidget(run)
            run.clicked.connect(make_callback(self.edit_game,game,w))
        
        if game.source in self.icons:
            w.icon.setPixmap(self.icons[game.source])
        if game.icon_url:
            fpath = "cache/icons/"+game.icon_url.replace("http","").replace(":","").replace("/","")
            if not os.path.exists(fpath):
                r = requests.get(game.icon_url)
                f = open(fpath,"wb")
                f.write(r.content)
                f.close()
            if not fpath in self.gicons:
                self.gicons[fpath] = QPixmap(fpath).scaled(24,24)
            w.gicon.setPixmap(self.gicons[fpath])
        w.setStyleSheet("QWidget {}")
        if game.finished:
            w.setStyleSheet("QWidget {background-color: rgb(100,200,150);}")
        elif game.priority:
            b = max(100,215-game.priority*40)
            w.setStyleSheet("QWidget {background-color: rgb(%(bright)d,%(bright)d,%(bright)d);}"%{"bright":b})
        w.label.setText(game.name)
        w.hours.setText("%.2d:%.2d"%game.hours_minutes)
        w.hours.setStyleSheet("QWidget {}")
        if game.playtime < 500:
            w.hours.setStyleSheet("QWidget {background-color: red}")
        w.genre.setText(game.genre)
        if game.hidden:
            w.hide()
        w.last_played.setText(game.last_played_nice)
        return w

    def update_gamelist_widget(self):
        self.gamelist = [{"game":g,"widget":None,"hidden":g.hidden} for g in self.games.list()]
        child = self.games_list_widget_layout.takeAt(0)
        while child:
            child.widget().deleteLater()
            child = self.games_list_widget_layout.takeAt(0)
        for g in self.gamelist:
            w = self.get_row_for_game(g["game"])
            g["widget"] = w
            self.games_list_widget_layout.addWidget(w)
        self.game_scroller.verticalScrollBar().setValue(0)
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
        games = gogapi.import_gog()
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
        self.update_gamelist_widget()

    def cleanup_gamesdb(self):
        for g in self.games.games.values():
            gdbg = thegamesdb.find_game(g.name)
            if gdbg:
                data = thegamesdb.get_game_info(gdbg["id"])
                #print(data)
                if data and "Game" in data and "Genres" in data["Game"]:
                    genre = data["Game"]["Genres"]["genre"]
                    if type(genre) not in [str,bytes]:
                        genre = [x for x in genre if type(x) in [str,bytes]][0]
                    print(genre)
                    g.genre = genre.lower()
                    print(g.genre)
        self.games.save("games.json")

    def run_game(self,game):
        if getattr(self,"stop_playing_button",None):
            return
        self.timer_started = time.time()
        print ("run game",game.name,game.gameid)
        args = []
        folder = "."
        startupinfo = None
        creationflags = 0
        args,folder = game.get_run_args()

        print(args)
        import sys
        curdir = os.path.abspath(os.curdir)
        os.chdir(folder)
        print(os.path.abspath(os.curdir))
        self.running = subprocess.Popen(args, cwd=folder, stdout=sys.stdout, stderr=sys.stderr, creationflags=creationflags, shell=True)
        print("subprocess open")
        os.chdir(curdir)
        
        
        self.stop_playing_button = QPushButton("Stop Playing "+game.name)
        self.buttonLayout1.addWidget(self.stop_playing_button)
        self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))

        self.runthread = RunGameThread()
        self.runthread.process = self.running
        self.runthread.finished.connect(make_callback(self.stop_playing,game))
        playrequest(game)
        #self.runthread.start()

    def stop_playing(self,game):
        stoprequest()
        self.buttonLayout1.removeWidget(self.stop_playing_button)
        self.stop_playing_button.deleteLater()
        self.stop_playing_button = None
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.played()
        game.playtime += elapsed_time
        game.priority = -1
        self.games.save("games.json")
        for g in self.gamelist:
            if g["game"].gameid == game.gameid:
                self.get_row_for_game(game,g["widget"])

    def show_edit_widget(self,*args,**kwargs):
        self.egw = EditGame(*args,**kwargs)
        dock = QDockWidget("Dock Widget",self)
        dock.setWidget(self.egw)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,dock)
        return self.egw

    def edit_game(self,game,row_widget):
        self.show_edit_widget(game,row_widget,self)

    def add_game(self):
        game = data.Game(source="none")
        row = self.get_row_for_game(game)
        self.gamelist.append({"game":game,"widget":row,"hidden":0})
        self.games_list_widget_layout.addWidget(row)
        self.show_edit_widget(game,row,self,new=True)

    def dosearch(self,text):
        sn = self.search_name.text().lower()
        sg = self.search_genre.text().lower()
        sp = self.search_platform.text().lower()
        for g in self.gamelist:
            if (not sn or sn in g["game"].name.lower()) and \
            (not sg or sg in g["game"].genre.lower()) and \
            (not sp or sp in g["game"].source.lower()) and \
            not g["game"].hidden:
                if g["hidden"]:
                    g["widget"].show()
                    g["hidden"] = 0
            else:
                if not g["hidden"]:
                    g["widget"].hide()
                    g["hidden"] = 1
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
 
    sys.exit(app.exec_())