#!python3
import time
import requests
import re
import data
import json

def get_gog_games_from_google():
    """Access google, search for www.gog.com/game/(game_id), return list of (game_id,game_name)"""
    url = "http://www.google.com/search"
    start = 0
    while 1:
        r = requests.get(url,params={"q":"site:gog.com/game/","start":start})
        t = r.text
        f = open("google.html","w",encoding="utf8")
        f.write(t)
        f.close()
        links = [x[0] for x in re.findall('q\=\http\:\/\/www\.gog\.com\/game\/(.*?)(\&|\?)',t)]
        for l in links:
            gog_games[l] = {"gogid":l}
        next = re.findall('<a(.*?)>.*?Next.*?\<\/a>',t)
        if next:
            next = re.findall('href="(.*?)"',next[0])
            if next:
                url = "http://www.google.com"+next[0]
                time.sleep(500)
                continue
        return
        
def get_gog_games_from_web():
    s = requests.Session()
    r = s.get("https://www.gog.com")
    buk = re.findall('<input.*?name="buk".*?>',r.text)
    buk = re.findall('value="(.*?)"',buk[0])
    buk = buk[0]
    print (buk)
    r = s.post("https://secure.gog.com/login",
        params={
            "log_email":"",
            "log_password":"",
            "redirectOk":"/",
            "submitForLoginForm":"Log me in",
            "unlockSettings":"0",
            "buk":buk
        })
    f = open("gog.html","w",encoding="utf8")
    f.write(r.text)
    f.close()
    r = s.get("https://secure.gog.com/account/games/shelf")
    f = open("gog_shelf.html","w",encoding="utf8")
    f.write(r.text)
    f.close()

"""
<div class="shelf_game" data-gameindex="dracula_trilogy" data-gameid="1207659251" data-orderid="3LKULVG353S" data-background="/upload/images/2013/07/50f3b525242c1a0129eabcbf5a6951c2e3f42194.jpg" data-title="dracula trilogy anuman interactive anuman interactive adventure pointandclick horror">
"""
def get_gog_games_html(html):
    from bs4 import BeautifulSoup
    gog_games = {}
    f = open(html)
    t = f.read()
    f.close()
    soup = BeautifulSoup(t)
    games = soup.find_all(lambda tag: tag.has_attr("data-gameindex"))
    for g in games:
        d = {}
        d["gameindex"] = g['data-gameindex']
        d["gameid"] = g['data-gameid']
        d["orderid"] = g['data-orderid']
        d["background"] = g['data-background']
        d["titlekeys"] = g['data-title']
        for image in g.find_all('img'):
            d["icon"] = image['src']
        gog_games[d["gameindex"]] = d
    return gog_games
def import_gog(multipack={}):
    packs = {}
    games = []
    gog_games = get_gog_games_html("mygog_shelf.html")
    for key in gog_games:
        g = gog_games[key]
        multi = multipack.get(g["gameindex"],[""])
        for g2 in multi:
            name = g["gameindex"]
            if g2:
                name = g2
            name = " ".join([x.capitalize() for x in name.replace("_"," ").split(" ")])
            id = g["gameindex"]
            if g2:
                id = id+"."+g2.replace(" ","_")
                if not g["gameindex"] in packs:
                    package = data.Game(name=" ".join([x.capitalize() for x in g["gameindex"].split("_")]),source="gog",gogid=g["gameindex"],is_package=1)
                    packs[package.gameid] = package
                    games.append(package)
            game = data.Game(name=name,source="gog",gogid=g["gameindex"],icon_url="http://www.gog.com"+g["icon"],packageid=g2.replace(" ","_"))
            games.append(game)
    return games
    
def selenium():
    import pickle
    import selenium
    print (selenium.__version__)
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from selenium.webdriver.phantomjs.service import Service as PhantomJSService
    class NewService(PhantomJSService):
        def __init__(self, *args, **kwargs):
            service_args = kwargs.setdefault('service_args', [])
            service_args = [
                '--load-images=no',
                '--ignore-ssl-errors=true'
            ]
            super(NewService, self).__init__(*args, **kwargs)
    webdriver.phantomjs.webdriver.Service = NewService
    #~ browser = webdriver.PhantomJS("phantomjs/phantomjs.exe",
        #~ desired_capabilities={"phantomjs.page.settings.resourceTimeout":"1000"}
    #~ )
    browser = webdriver.Firefox()
    #browser.set_window_size(1024,768)
    browser.set_page_load_timeout(1)
    browser.set_script_timeout(1)
    try:
        browser.get("http://127.0.0.1")
    except:
        pass
    browser.set_page_load_timeout(20)
    browser.set_script_timeout(20)
    cookies = []
    try:
        print("opening cookies")
        cookies = pickle.load(open("cache/cookies","rb"))
    except:
        print("error opening cookies")
    browser.get("http://www.gog.com")
    for cookie in cookies:
        browser.add_cookie(cookie)
    browser.get("http://www.gog.com")
    logged_in = False
    try:
        acct = WebDriverWait(browser,10).until(EC.presence_of_element_located((By.ID,"topMenuAvatarImg")))
        logged_in = True
        print("already logged in")
    except:
        print("Error logging in")
    if not logged_in:
        browser.save_screenshot("phantomshot_prelogin.jpg")
        print("not logged in, logging in")
        acct = WebDriverWait(browser,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,".nav_login")))
        browser.find_element_by_css_selector(".nav_login").click()
        browser.switch_to.frame("GalaxyAccountsFrame")
        browser.find_element_by_id("login_username").send_keys("saluk64007@gmail.com")
        browser.find_element_by_id("login_password").send_keys("wan3bane")
        browser.find_element_by_id("login_login").click()
    try:
        acct = WebDriverWait(browser,10).until(EC.presence_of_element_located((By.ID,"topMenuAvatarImg")))
        logged_in = True
    except:
        print("Error logging in")
    browser.save_screenshot("phantomshot_loggedin.jpg")
    if logged_in:
        print("logged in, dumping cookies")
        pickle.dump(browser.get_cookies(),open("cache/cookies","wb"))
        print("open shelf")
        browser.get("https://secure.gog.com/account/games/shelf")
        print("shelf open, waiting for full game list")
        acct = WebDriverWait(browser,20).until(EC.presence_of_element_located((By.CSS_SELECTOR,"span.all")))
        print("saving screenshot")
        browser.save_screenshot("phantomshot_shelf.jpg")
        f = open("mygog_shelf.html","w")
        f.write("<html>"+browser.find_element_by_css_selector("html").get_attribute("innerHTML")+"</html>")
        f.close()
    browser.quit()

class Browser:
    def __init__(self):
        self.cookies = {}
        #self.cookies = {"guc_al":"0","sessions_gog_com":"0","__utma":"95732803.1911890316.1399672018.1399672018.1399672018.1","__utmb":"95732803.5.9.1399672201295","__utmz":"95732803.1399672018.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)"}
        self.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-us,ko;q=0.7,en;q=0.3",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:28.0) Gecko/20100101 Firefox/28.0",
"Referer":"http://www.gog.com"}
    def post(self,url,data={},params={}):
        self.json = {}
        self.text = ""
        answer = requests.post(url,data=data,params=params,cookies=self.cookies,headers=self.headers,allow_redirects=True)
        self.answer = answer
        self.cookies.update(answer.cookies)
        try:
            self.json = answer.json()
        except:
            pass
        try:
            self.text = answer.text
            self.url = answer.url
        except:
            pass
    def get(self,url,params={}):
        self.json = {}
        self.text = ""
        answer = requests.get(url,params=params,cookies=self.cookies,headers=self.headers)
        self.cookies.update(answer.cookies)
        try:
            self.json = answer.json()
        except:
            pass
        try:
            self.text = answer.text
            self.url = answer.url
        except:
            pass
import time
def better_get_shelf():
    print(time.time())
    b = Browser()
    #Try cookies
    logged_in = False
    try:
        f = open("cache/cookies","r")
        b.cookies = eval(f.read())
        f.close()
        b.get("https://secure.gog.com/account/ajax",params={
            "a":"gamesShelfMore",
            "p":0,
            "s":"date_purchased",
            "h":0,
            "q":"",
            "t":"%d"%time.time()*100
            })
        assert b.json["count"]
        print("Logged in")
        logged_in = True
    except:
        print("Not logged in")
        pass
    
    if not logged_in:
        b.get("https://www.gog.com/")
        login_auth = re.findall("https\:\/\/auth\.gog\.com.*?\"",b.text)
        print(login_auth)
        b.get(login_auth[0])
        token = re.findall("<input.*?login\[\_token\].*?>",b.text)
        token_value = re.findall("value\=\"(.*?)\"",token[0])[0]
        print(token_value)
        print("cur url:",b.url)
        b.post("https://login.gog.com/login_check",{
            "login[username]":"saluk64007@gmail.com",
            "login[password]":"wan3bane",
            "login[_token]":token_value,
            #~ "register[email]":"",
            #~ "register[password]":"",
            #~ "register[_token]":token_value,
            "login[login]":"",
            },
            )
        print(b.url)
        
        #Properly follow redirect!
        print(b.answer.history[0].content)
        link = re.findall(b"content\=.*?https(.*?)\"",b.answer.history[0].content)
        print(link)
        linknice = "https"+link[0].decode("utf8").replace("auth?amp;","auth?").replace("%22&amp;amp;","&").replace("https%3A%2F%2F","https://").replace("%2F","/").replace("&amp;amp;","&").replace("&amp;","&")
        print(linknice)
        b.get(linknice)
        print(b.url)
        print(b.cookies)
    
    #Should be logged in now
    f = open("cache/cookies","w")
    f.write(repr(b.cookies))
    f.close()
    count = 50
    page=1
    f = open("mygog_shelf.html","w")
    while count:
        b.get("https://secure.gog.com/account/ajax",params={
            "a":"gamesShelfMore",
            "p":page,
            "s":"date_purchased",
            "h":0,
            "q":"",
            "t":"%d"%time.time()*100
            })
        print(b.json["count"])
        f.write(b.json["html"])
        page+=1
        count=b.json["count"]
    f.close()
    

if __name__ == "__main__":
    better_get_shelf()
    for game in import_gog():
        print (game.name)
