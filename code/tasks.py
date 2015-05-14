import os
import subprocess
import sys
import webbrowser

run_with_steam = 1
#   NEW METHOD TO RUN THROUGH STEAM:
#   Export function which creates shortcuts to all non-steam games that aren't in steam yet
#   Manually creat shortcut for often played game, and put it in cache/steamshortcuts
#   When running a game, if a steam shortcut exists in cache/steamshortcuts, run that

class Task:
    def get_run_args(self,game):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        folder = game.install_folder #Navigate to executable's directory
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        import winshell, shlex
        if game.install_path.endswith(".lnk"):
            with winshell.shortcut(game.install_path) as link:
                args = [link.path] + shlex.split(link.arguments)
                folder = link.working_directory
        else:
            #Make batch file to run
            if 1:#not os.path.exists("cache/batches/"+game.gameid+".bat"):
                with open("cache/batches/"+game.gameid+".bat", "w") as f:
                    f.write('cd "%s"\n'%folder)
                    path = game.install_path.split("\\")[-1]
                    exe,args = path.split(".exe")
                    exe = exe+".exe"
                    f.write('"%s" %s\n'%(exe,args))
            args = [game.gameid+".bat"]
            folder = os.path.abspath("cache\\batches\\")
            #args = [game.install_path.split("\\")[-1]]
            #folder = game.install_path.rsplit("\\",1)[0]


            #if not self.missing_steam_launch(game):
            #HACKY - run game through steam
            #    args = ["cache\\steamshortcuts\\%s.url"%game.shortcut_name]
            #    folder = os.path.abspath("")

        return args,folder
    def run_game(self,game,source):
        creationflags = 0
        shell = True
        if sys.platform=='darwin':
            shell = False
        args,folder = self.get_run_args(game,source)
        print("run args:",args,folder)

        if args and folder:
            print(args)
            curdir = os.path.abspath(os.curdir)
            os.chdir(folder)
            print(os.path.abspath(os.curdir))
            self.running = subprocess.Popen(args, cwd=folder, stdout=sys.stdout, stderr=sys.stderr, creationflags=creationflags, shell=shell)
            print("subprocess open")
            os.chdir(curdir)
    def missing_steam_launch(self,game,source):
        """Returns True if the game type wants a steam launcher and it doesn't exist"""
        if not run_with_steam:
            return False
        dest_shortcut_path = "cache/steamshortcuts/%s.url"%game.shortcut_name
        userhome = os.path.expanduser("~")
        desktop = userhome + "/Desktop/"
        shortcut_path = desktop+"%s.url"%game.shortcut_name
        if os.path.exists(shortcut_path):
            import shutil
            shutil.move(shortcut_path,dest_shortcut_path)
        if os.path.exists(dest_shortcut_path):
            return False
        return True
    def steam_launch(self,game,source):
        webbrowser.open("steam://rungameid/%d"%source["id"])