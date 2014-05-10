#!python3
import time
import requests
import re
import data

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

multipack = {"leisure_suit_larry":["leisure suit larry 1","leisure suit larry 2","leisure suit larry 3","leisure suit larry 4","leisure suit larry 5","leisure suit larry 6","softporn adventures"],
                "cultures_12":["cultures 1","cultures 2"],
                "space_quest_4_5_6":["space quest 4","space quest 5","space quest 6"],
                "space_quest_1_2_3":["space quest 1","space quest 2","space quest 3"],
                "cossacks_anthology":["cossacks euro wars","cossacks art of war","cossacks back to war"],
                "castles_castles_2":["castles 1","castles 2"],
                "starflight_1_2":["starflight 1","starflight 2"],
                "quest_for_glory":["quest for glory 1","quest for glory 2","quest for glory 3","quest for glory 4","quest for glory 5"],
                "ultima_1_2_3":["ultima 1","ultima 2","ultima 3"],
                "ultima_456":["ultima 4","ultima 5","ultima 6"],
                "lands_of_lore_1_2":["lands of lore 1","lands of lore 2"],
                "ultima_underworld_1_2":["ultima underworld 1","ultima underworld 2"],
                "wing_commander_1_2":["wing commander 1","wing commander 2"],
                "commandos_2_3":["commandos 2","commandos 3"],
                "descent_1_descent_2":["descent 1","descent 2"],
                "m_a_x_m_a_x_2":["m.a.x 1","m.a.x 2"],
                "realms_of_arkania_1_2":["realms of arkania 1","realms of arkania 2"],
                "red_baron_pack":["red baron 1","red baron 3d"],
                "ishar_compilation":["ishar crystals","ishar legend","ishar 2","ishar 3"],
                "gobliiins_pack":["goblins 1","gobliins 2","gobliiins 3"],
                "robinsons_requiem_collection":["robinsons requiem","deus"],
                "masters_of_orion_1_2":["masters of orion 1","masters of orion 2"],
                "patrician_1_2":["patrician 1","patrician 2"],
                "the_incredible_machine_mega_pack":["the incredible machine 1","the incredible machine 3","the incredible machine contraptions","the incredible machine even more contraptions"],
                "betrayal_at_krondor":["betrayal at krondor","betrayal at antara"],
                "dracula_trilogy":["dracula 1","dracula 2","dracula 3"],
                "kings_quest_4_5_6":["king's quest 4","king's quest 5","king's quest 6"],
                "kings_quest_1_2_3":["king's quest 1","king's quest 2","king's quest 3"],
                "police_quest_swat_1_2":["police quest: swat 1","police quest: swat 2"],
                "kings_quest_7_8":["king's quest 7","king's quest 8"],
                "blackwell_bundle":["blackwell legacy","blackwell unbound","blackwell convergence","blackwell deception"],
                "police_quest_1_2_3_4":["police quest 1","police quest 2","police quest 3","police quest 4"],
                "megarace_1_2":["megarace 1","megarace 2"],
                "wizardry_6_7":["wizardry 6","wizardry 7"],
                "the_zork_anthology":["zork 1","zork 2","zork 3","beyond zork","zork zero","planetfall"],
                "tex_murphy_1_2":["tex murphy mean streets","tex murphy martian memorandum"],
                "alone_in_the_dark":["alone in the dark 1","alone in the dark 2","alone in the dark 3"],
                "cultures_34":["cultures 3","cultures 4"]
}
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
def import_gog():
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
            game = data.Game(name=name,source="gog",gogid=id,icon_url="http://www.gog.com"+g["icon"])
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
      #          '--load-images=no',
                '--ignore-ssl-errors=true'
            ]
            super(NewService, self).__init__(*args, **kwargs)
    webdriver.phantomjs.webdriver.Service = NewService
    #browser = webdriver.PhantomJS("phantomjs/phantomjs.exe",desired_capabilities={"phantomjs.page.settings.resourceTimeout":"1000"})
    browser = webdriver.Firefox()
    #browser.set_window_size(1024,768)
    #browser.set_page_load_timeout(20)
    #browser.set_script_timeout(20)
    browser.get("http://127.0.0.1")
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
        browser.find_element_by_id("log_email").send_keys("saluk64007@gmail.com")
        browser.find_element_by_id("log_password").send_keys("wan3bane")
        browser.find_element_by_id("submitForLoginForm").click()
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
        browser.get("http://www.gog.com/account/games/shelf")
        print("shelf open, waiting for full game list")
        acct = WebDriverWait(browser,20).until(EC.presence_of_element_located((By.CSS_SELECTOR,"span.all")))
        print("saving screenshot")
        browser.save_screenshot("phantomshot_shelf.jpg")
    browser.quit()

if __name__ == "__main__":
    for game in import_gog():
        print (game.name)
