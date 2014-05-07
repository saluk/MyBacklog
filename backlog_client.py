#!python3
import data
import steamapi
import os
import time
import requests
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]="C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

def make_callback(f,*args):
    return lambda: f(*args)

class EditGame(QWidget):
    def __init__(self, game, row_widget, app):
        super(EditGame, self).__init__()
        self.game = game
        self.app = app
        self.games = app.games
        
        self.row_widget = row_widget
        
        self.oldid = game.gameid
        
        #Layout
        layout = QGridLayout()
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
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)
        
        self.setLayout(layout)
        
    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*.exe *.lnk *.cmd *.bat)")[0]
        w.setText(filename.replace("/","\\"))
    def save_close(self):
        for field in self.fields:
            value = self.fields[field]["w"].text()
            t = self.fields[field]["t"]
            if t=="i":
                value = int(value)
            elif t=="f":
                value = float(value)
            setattr(self.game,field,value)
        newid = self.game.gameid
        print("save",newid,self.oldid)
        if newid!=self.oldid:
            if self.oldid in self.games.games:
                del self.games.games[self.oldid]
            self.games.games[newid] = self.game
        self.games.save("games.json")
        self.app.get_row_for_game(self.game,self.row_widget)
        self.deleteLater()
 
class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        
        self.timer_started = 0
        
        self.games = data.Games()
        self.games.load("games.json")
        self.gamelist = []
 
        buttonLayout1 = QVBoxLayout()
        
        search = QLineEdit()
        buttonLayout1.addWidget(search)
        search.textChanged.connect(self.dosearch)
        
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

        self.import_steam_button = QPushButton("Import Steam")
        buttonLayout1.addWidget(self.import_steam_button)
        self.import_steam_button.clicked.connect(self.import_steam)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)
 
        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")
        
        self.icons = {"steam":QPixmap("steam.bmp").scaled(24,24),"gog":QPixmap("gog.bmp").scaled(24,24)}
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
            
            label = QLabel("GAME HOURS")
            label.setMaximumWidth(50)
            box.addWidget(label)
            w.hours = label
            
            label = QLabel("GAME LAST PLAYED")
            label.setMaximumWidth(150)
            box.addWidget(label)
            w.last_played = label
            
            run = QPushButton("play")
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
        w.label.setText(game.name)
        w.hours.setText("%.2d:%.2d"%game.hours_minutes)
        w.hours.setStyleSheet("QWidget {}")
        if game.playtime < 500:
            w.hours.setStyleSheet("QWidget {background-color: red}")
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
    def run_game(self,game):
        if getattr(self,"stop_playing_button",None):
            return
        self.timer_started = time.time()
        print ("run game",game.name,game.gameid)
        if game.source=="steam":
            os.system("c:\\steam\\steam.exe -applaunch %d"%game.steamid)
        if game.source=="gog":
            curdir = os.path.abspath(os.curdir)
            os.chdir(game.install_path.rsplit("\\",1)[0])
            os.system('"'+game.install_path+'"')
            os.chdir(curdir)
        
        
        self.stop_playing_button = QPushButton("Stop Playing "+game.name)
        self.buttonLayout1.addWidget(self.stop_playing_button)
        self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))
    def stop_playing(self,game):
        self.buttonLayout1.removeWidget(self.stop_playing_button)
        self.stop_playing_button.deleteLater()
        self.stop_playing_button = None
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.played()
        game.playtime += elapsed_time
        self.games.save("games.json")
        for g in self.gamelist:
            if g["game"].gameid == game.gameid:
                self.get_row_for_game(game,g["widget"])
    def edit_game(self,game,row_widget):
        self.egw = EditGame(game,row_widget,self)
        self.egw.show()
    def add_game(self):
        game = data.Game(source="gog")
        row = self.get_row_for_game(game)
        self.gamelist.append({"game":game,"widget":row,"hidden":0})
        self.games_list_widget_layout.addWidget(row)
        self.egw = EditGame(game,row,self)
        self.egw.show()
    def dosearch(self,text):
        for g in self.gamelist:
            if text.lower() in g["game"].name.lower() and not g["game"].hidden:
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
 
    screen = Form()
    screen.show()
 
    sys.exit(app.exec_())