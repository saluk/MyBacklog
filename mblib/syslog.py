import threading
import sys
import traceback

class SysLog:
    def __init__(self,logfile=None):
        self.log = []
        self.callbacks = []
        self.logfile = None
        print("initializing logfile ",logfile)
        if logfile:
            self.logfile = open(logfile,"w",errors="ignore")
            self.callbacks.append(self.logfile_write)
            sys.stderr = self.logfile
            sys.stdout = self.logfile
            sys.excepthook = self.uncaught_exception
        self.lock = threading.Lock()
    def add_callback(self,f):
        self.callbacks.append(f)
    def write(self,*message):
        self.lock.acquire()
        s = "> "+"".join(str(x) for x in message)
        self.log.append(s)
        [f(s) for f in self.callbacks]
        self.lock.release()
    def logfile_write(self,s):
        self.logfile.write(s+"\n")
        self.logfile.flush()
    def read(self):
        return "\n".join(self.log)
    def uncaught_exception(self, etype, value, tb):
        self.write(*traceback.format_exception(etype, value, tb))

class PrintLog(SysLog):
    def write(self,*message):
        print(*message)