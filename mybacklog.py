#!python3.4.4

#os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

import os
import sys
import PyQt5.Qt
from PyQt5 import QtCore

from mblib.interface.gamelist_form import MyBacklog


def run():

    print(PyQt5.Qt.PYQT_VERSION_STR)
    print(sys.version)

    if os.path.exists("PyQt5/plugins"):
        QtCore.QCoreApplication.addLibraryPath("PyQt5/plugins")
    if os.path.exists("PyQt5/Qt/plugins"):
        QtCore.QCoreApplication.addLibraryPath("PyQt5/Qt/plugins")
    QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(PyQt5.__file__),"Qt", "plugins", "imageformats"))
    
    print("INITIALIZE")
    awareness = ["-platform", "windows:dpiawareness=0"]
    #awareness = []
    app = MyBacklog(base_args=sys.argv+awareness)
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
