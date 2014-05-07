import sys
import difflib
import requests
import xml.etree.cElementTree as etree

gamelistep = "http://thegamesdb.net/api/GetGamesList.php"
gameep = "http://thegamesdb.net/api/GetGame.php"

as_list = ["Genres","Images"]
def get_value(child):
    v = {}
    if child.attrib:
        v = dict(child.attrib)
    if len(child):
        v.update(to_dict(child))
    if child.text:
        if child.text.replace("\\n","\n").strip():
            v["_value"] = child.text.replace("\\n","\n").strip()
    if len(v.keys())==1:
        if "_value" in v:
            return v["_value"]
        elif "_children" in v:
            return v["_children"]
    return v

def to_dict(tree):
    d = {}
    lists = {}
    for child in tree:
        v = get_value(child)
        if child.tag in d:
            if child.tag not in lists:
                lists[child.tag] = [d[child.tag]]
            lists[child.tag].append(v)
        else:
            d[child.tag] = v
    d.update(lists)
    return d

def find_game(name):
    r = requests.get(gamelistep,params={"name":'"'+name+'"',"platform":"pc"})
    xml = r.text
    root = etree.XML(xml)
    list = [to_dict(game) for game in root]
    #find best match
    def match(n1,n2):
        n1=n1.lower()
        n2=n2.lower()
        score = difflib.SequenceMatcher(None,n1,n2).ratio()
        if n2.startswith(n1):
            score += 0.1
        return score
    print [(li["GameTitle"],match(name,li["GameTitle"])) for li in list]
    list.sort(key=lambda li: -match(name,li["GameTitle"]))
    return list[0]

def get_game_info(game_id):
    r = requests.get(gameep,params={"id":game_id})
    xml = r.text
    print xml
    root = etree.XML(xml)
    return to_dict(root)

print get_game_info(find_game(sys.argv[1])["id"])
