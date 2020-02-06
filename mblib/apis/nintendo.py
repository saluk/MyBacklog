import requests
import re

DOMAIN = "https://%s-dsn.algolia.net/1/indexes/noa_aem_game_en_us"
ARGS = "?page=0&hitsPerPage=6&clickAnalytics=true&query=%s&getRankingInfo=true"
headers = {
        #"X-Algolia-API-Key": "9a20c93440cf63cf1a7008d75f7438bf",
        #"X-Algolia-Application-Id": "U3B6GR4UA3"
}

def find_screenshot(game_name):
    n = requests.get("https://www.nintendo.com")
    t = n.text
    algolia_config = re.findall("algoliaConfig.*?\{(.*?)\};.*?\<\/script", t, re.DOTALL)[0]
    values = re.findall("(\w*?): \"(.*?)\"", algolia_config)
    for (k,v) in values:
        if k == "appId":
            headers["X-Algolia-Application-Id"] = v
        elif k == "searchApiKey":
            headers["X-Algolia-API-Key"] = v

    url = (DOMAIN%headers["X-Algolia-Application-Id"].lower())+(ARGS%(game_name.replace(" ","+")))
    r = requests.get(url, headers=headers)
    print(r.text)
    j = r.json()
    data = j['hits'][0]
    return "https://www.nintendo.com"+data['boxArt']

print(find_screenshot("dragon quest xi"))