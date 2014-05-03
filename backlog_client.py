#!python3
import data
import steamapi
import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]="C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
 
class Form(QWidget):
    def __init__(self, parent=None):
        self.games = []
        
        super(Form, self).__init__(parent)
 
        buttonLayout1 = QVBoxLayout()
        
        self.games_list_widget = QWidget()
        self.games_list_widget_layout = QGridLayout()
        self.games_list_widget_layout.setSpacing(0)
        self.games_list_widget.setLayout(self.games_list_widget_layout)

        self.game_scroller = QScrollArea()
        self.game_scroller.setWidgetResizable(True)
        self.game_scroller.setFixedHeight(400)
        self.game_scroller.setFixedWidth(600)
        self.game_scroller.setWidget(self.games_list_widget)
        buttonLayout1.addWidget(self.game_scroller)
        #self.games_list_widget.setFixedHeight(400)
        
        self.import_steam_button = QPushButton("Import Steam")
        buttonLayout1.addWidget(self.import_steam_button)
        self.import_steam_button.clicked.connect(self.import_steam)
 
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)
 
        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")
        
        self.update_gamelist_widget()
 
    #~ def submitContact(self):
        #~ name = self.nameLine.text()
 
        #~ if name == "":
            #~ QMessageBox.information(self, "Empty Field",
                                    #~ "Please enter a name and address.")
            #~ return
        #~ else:
            #~ QMessageBox.information(self, "Success!",
                                    #~ "Hello \"%s\"!" % name)
    def update_gamelist_widget(self):
        while not self.games_list_widget_layout.isEmpty():
            self.games_list_widget_layout.removeWidget(self.games_list_widget_layout.itemAt(0))
        for g in self.games:
            w = QWidget()
            box = QHBoxLayout()
            w.setLayout(box)
            
            label = QLabel(g.name)
            box.addWidget(label)
            
            run = QPushButton("play")
            box.addWidget(run)
            run.clicked.connect(self.make_callback(g))
            self.games_list_widget_layout.addWidget(w)
        self.game_scroller.verticalScrollBar().setValue(0)
        self.update()
    def import_steam(self):
        self.games = steamapi.import_steam()
        self.update_gamelist_widget()
    def run_game(self,game):
        print ("run game",game.name,game.gameid)
        if game.source=="steam":
            os.system("c:\\steam\\steam.exe -applaunch %d"%game.gameid)
    def make_callback(self,game):
        return lambda: self.run_game(game)
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)
 
    screen = Form()
    screen.show()
 
    sys.exit(app.exec_())