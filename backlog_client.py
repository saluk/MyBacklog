#!python3
import data
import steamapi
import os
import time
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]="C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
 
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

    def update_gamelist_widget(self):
        self.gamelist = self.games.list()
        while not self.games_list_widget_layout.isEmpty():
            self.games_list_widget_layout.removeWidget(self.games_list_widget_layout.itemAt(0))
        for g in self.gamelist:
            w = QWidget()
            box = QHBoxLayout()
            w.setLayout(box)
            
            if g.finished:
                w.setStyleSheet("QWidget {background-color: green}")
            
            label = QLabel(g.name)
            box.addWidget(label)
            
            label = QLabel("%.2d:%.2d"%g.hours_minutes)
            box.addWidget(label)
            if g.playtime < 500:
                label.setStyleSheet("QWidget {background-color: red}")
            
            run = QPushButton("play")
            box.addWidget(run)
            run.clicked.connect(self.make_callback(g))
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
        self.stop_playing_button.clicked.connect(self.stop_callback(game))
    def stop_playing(self,game):
        self.buttonLayout1.removeWidget(self.stop_playing_button)
        self.stop_playing_button.close()
        del self.stop_playing_button
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.playtime += elapsed_time
        self.games.save("games.json")
    def make_callback(self,game):
        return lambda: self.run_game(game)
    def stop_callback(self,game):
        return lambda: self.stop_playing(game)
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)
 
    screen = Form()
    screen.show()
 
    sys.exit(app.exec_())