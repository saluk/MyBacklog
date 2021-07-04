from mblib.resources import icons
from PyQt5.QtCore import QSize, QThread
import time
import traceback
from mblib import sync


class ProcessThread(QThread):
    gamelist = None

    def run(self):
        while not self.gamelist.window().exit_requested:
            try:
                self.process_icons(self.gamelist, limit=100)
            except Exception:
                pass
            self.handle_importers()
            self.handle_sync()
            time.sleep(0.10)

    def handle_importers(self):
        if not self.gamelist.importer_threads:
            return
        next_importer = self.gamelist.importer_threads.pop()
        next_importer[1](self.gamelist)

    def process_icons(self, app, limit):
        processed = 0
        for widget, game, size in app.icon_processes:
            icon = icons.icon_for_game(
                game, app.icon_size, app.gicons, app.config["root"]
            )
            if icon:
                widget.setSizeHint(QSize(size, size))
                widget.setIcon(icon)
            processed += 1
            if processed >= limit:
                app.icon_processes[:] = app.icon_processes[processed:]
                return

    func = None
    func2 = None
    do_upload = True
    do_download = True
    work = False

    def handle_sync(self):
        if not self.work:
            return
        self.work = False
        if self.do_download:
            try:
                if sync.download():
                    self.app.update_gamelist_widget()
            except Exception:
                traceback.print_exc()
            self.do_download = None
        if self.func:
            self.func()
            self.func = None
        if self.do_upload:
            try:
                sync.upload()
            except Exception:
                traceback.print_exc()
            self.do_upload = None
        if self.func2:
            self.func2()
            self.func2 = None
        self.gamelist.sync_status = {'msg': "done"}

    def begin_work(self):
        self.gamelist.sync_status = {'msg': "syncing"}
        self.work = True

    def upload(self, func=None):
        self.func = func
        self.do_download = False
        self.do_upload = True
        self.begin_work()

    def download(self, func=None):
        self.func = func
        self.do_download = True
        self.do_upload = False
        self.begin_work()

    def sync(self, func1, func2):
        self.func = func1
        self.func2 = func2
        self.do_download = True
        self.do_upload = True
        self.begin_work()

    def export_steam(self):
        def func1():
            self.gamelist.steam.export()

        self.func = func1
        self.do_download = self.do_upload = False
        self.begin_work()