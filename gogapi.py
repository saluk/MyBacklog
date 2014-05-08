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
}
"""
<div class="shelf_game" data-gameindex="dracula_trilogy" data-gameid="1207659251" data-orderid="3LKULVG353S" data-background="/upload/images/2013/07/50f3b525242c1a0129eabcbf5a6951c2e3f42194.jpg" data-title="dracula trilogy anuman interactive anuman interactive adventure pointandclick horror">
"""
def get_gog_games_html(html):
    gog_games = {}
    f = open(html)
    t = f.read()
    f.close()
    print (len(re.findall("data-gameindex",t)))
    games = re.findall('<div.*?data\-gameindex.*?>',t)
    for g in games:
        d = {}
        d["gameindex"] = re.findall('data-gameindex="(.*?)"',g)[0]
        d["gameid"] = re.findall('data-gameid="(.*?)"',g)[0]
        d["orderid"] = re.findall('data-orderid="(.*?)"',g)[0]
        d["background"] = re.findall('data-background="(.*?)"',g)[0]
        d["titlekeys"] = re.findall('data-title="(.*?)"',g)[0]
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
            game = data.Game(name=name,source="gog",gogid=id)
            games.append(game)
    return games

if __name__ == "__main__":
    for game in import_gog():
        print(game.dict())