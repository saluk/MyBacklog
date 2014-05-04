#!python3
import data
import steamapi
import os
import time
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]="C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PySide.QtCore import *
from PySide.QtGui import *

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
        
        #Fields
        self.fields = {}
        for i,prop in enumerate(game.savekeys):
            label = QLabel("%s:"%prop.capitalize())
            layout.addWidget(label,i,0)
            edit = QLineEdit(str(getattr(game,prop)))
            layout.addWidget(edit,i,1)
            self.fields[prop] = edit
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)
        
        self.setLayout(layout)
    def save_close(self):
        for field in self.fields:
            value = self.fields[field].text()
            if field in ["finished"]:
                value = int(value)
            elif field in ["playtime"]:
                value = float(value)
            setattr(self.game,field,value)
        newid = self.game.gameid
        if newid!=self.oldid:
            del self.games[self.oldid]
            self.games[newid] = self.game
        self.games.save("games.json")
        self.app.get_row_for_game(self.game,self.row_widget)
        self.deleteLater()
 
class Form(QWidget):
    def __init__(self, parent=None):
        self.timer_started = 0
        
        self.games = data.Games()
        self.games.load("games.json")
        self.gamelist = []
        
        super(Form, self).__init__(parent)
 
        buttonLayout1 = QVBoxLayout()
        
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
        
        self.import_steam_button = QPushButton("Import Steam")
        buttonLayout1.addWidget(self.import_steam_button)
        self.import_steam_button.clicked.connect(self.import_steam)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)
 
        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")
        
        self.update_gamelist_widget()
        
    def get_row_for_game(self,game,w=None):
        if not w:
            w = QWidget()
            box = QHBoxLayout()
            w.setLayout(box)
            
            label = QLabel("GAME NAME")
            box.addWidget(label)
            w.label = label
            
            label = QLabel("GAME HOURS")
            box.addWidget(label)
            w.hours = label
            
            run = QPushButton("play")
            box.addWidget(run)
            run.clicked.connect(make_callback(self.run_game,game))
            
            run = QPushButton("edit")
            box.addWidget(run)
            run.clicked.connect(make_callback(self.edit_game,game,w))
        
        w.setStyleSheet("QWidget {}")
        if game.finished:
            w.setStyleSheet("QWidget {background-color: green}")
        w.label.setText(game.name)
        w.hours.setText("%.2d:%.2d"%game.hours_minutes)
        w.hours.setStyleSheet("QWidget {}")
        if game.playtime < 500:
            w.hours.setStyleSheet("QWidget {background-color: red}")
        return w

    def update_gamelist_widget(self):
        self.gamelist = self.games.list()
        child = self.games_list_widget_layout.takeAt(0)
        while child:
            child.widget().deleteLater()
            child = self.games_list_widget_layout.takeAt(0)
        for g in self.gamelist:
            w = self.get_row_for_game(g)
            self.games_list_widget_layout.addWidget(w)
        self.game_scroller.verticalScrollBar().setValue(0)
        self.update()
    def import_steam(self):
        games = steamapi.import_steam()
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save("games.json")
    def run_game(self,game):
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
        self.stop_playing_button.close()
        del self.stop_playing_button
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.playtime += elapsed_time
        self.games.save("games.json")
    def edit_game(self,game,row_widget):
        self.egw = EditGame(game,row_widget,self)
        self.egw.show()
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)
 
    screen = Form()
    screen.show()
 
    sys.exit(app.exec_())