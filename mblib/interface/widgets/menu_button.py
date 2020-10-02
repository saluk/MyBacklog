from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QToolButton, QMenu
from PyQt5.QtGui import QPalette


class MenuButton(QToolButton):
    def __init__(self, options):
        super().__init__()
        self.setText(options[0][0])
        self.clicked.connect(options[0][1])
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setFixedHeight(40)
        self.setMinimumWidth(100)
        self.setBackgroundRole(QPalette.Highlight)
        if options[1:]:
            m = QMenu()
            self.setMenu(m)
        else:
            self.setArrowType(Qt.NoArrow)
        for opt in options[1:]:
            action = m.addAction(opt[0])
            action.triggered.connect(opt[1])