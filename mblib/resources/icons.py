import os
import requests
import textwrap

from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon,QPixmap,QImageReader
except:
    pass
    
try:
    import pygame
except:
    pass

from mblib.resources import extract_icons

headers = {
    'User-Agent': 'MyBacklog Game tracker and launcher v1.0',
    'From': 'saluk64007@gmail.com'
}

def generate_icon(fpath,game,filecache_root,from_image = None):
    if not from_image:
        im = Image.new('RGB',[460,265])
        print("generate new image for",fpath)
    else:
        print("LOADED IMAGE",from_image)
        im = Image.open(from_image).resize([460,265],Image.BILINEAR)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join("data","Muli-Light.ttf"),25)
    wt = "wwww"
    ww = draw.textsize(wt,font=font)
    print(ww)
    ws = int((460/ww[0])*4)
    print(ws)
    y = 25
    for line in textwrap.wrap(game.name,ws):
        draw.text((5, y), line, font=font)
        y += ww[1]+5
    im.save(fpath)

def urlclean(url):
    return url.replace("http", "").replace("https", "").replace(
        ":", "").replace("/", "").replace("=", "_").replace(
        "\\", "").replace("?","q").replace("&","aa")

def path_to_icon(game,filecache_root,category="icon",url=""):
    if url:
        pass
    elif category=="icon": 
        url = game.icon_url
    elif category=="logo": 
        url = game.logo_url
    if url:
        return filecache_root+"/cache/icons/"+urlclean(url)+".png","download",url
    elif game.get_exe():
        exe_path = game.get_exe()
        return filecache_root+"/cache/icons/"+urlclean(exe_path)+".png","extract",exe_path
    elif game.get_gba():
        gba_path = game.get_gba()
        return filecache_root+"/cache/icons/"+urlclean(gba_path)+".png","gba",gba_path
    else:
        name = "custom_"+str(game.gameid)+"_icon.png"
        return filecache_root+"/cache/icons/"+name,"generate",name

def icon_in_cache(game,size,cache,filecache_root,category="icon",imode="qt",url=""):
    fpath,mode,url = path_to_icon(game,filecache_root,category,url)
    if (fpath,size) in cache:
        if imode=="qt":
            return QIcon(cache[(fpath,size)])
        return cache[(fpath,size)]
    return None

def icon_for_game(game,size,icon_cache,filecache_root,category="icon",imode="qt",url=""):
    cur = icon_in_cache(game,size,icon_cache,filecache_root,category,imode)
    if cur:
        return cur
        
    fpath,mode,url = path_to_icon(game,filecache_root,category,url=url)
    if not os.path.exists(fpath):
        p = None #p == image bytes or a local file path that Image can .open()
        if mode == "download":
            print("2.Download icon:",url)
            r = requests.get(url,headers=headers)
            p = BytesIO(r.content)
        elif mode == "extract":
            print("3.Extract icon:",url.encode("ascii","backslashreplace"))
            extracted_path = extract_icons.get_icon(url,filecache_root)
            #Add text on top of icon - usually has no title
            generate_icon(fpath,game,filecache_root,from_image=extracted_path)
        elif mode == "gba":
            print("4.Download gba icon:",url)
            p = extract_icons.get_gba(url)
        elif mode == "5.generate":
            print("Generate custom icon:",url)
            generate_icon(fpath,game,filecache_root)
        #Save all images as .png
        if p:
            try:
                pil_image = Image.open(p)
            except OSError:
                print("None image provided, no icon loaded:",url)
            else:
                print("6.save")
                pil_image.save(fpath)
    if os.path.exists(fpath) and not (fpath,size) in icon_cache:
        if imode=="path":
            return fpath.replace("/",os.path.sep)
        elif imode=="qt":
            mode = ""
            with open(fpath.replace("/",os.path.sep),"rb") as f:
                head = str(f.read(20))
                if "JFIF" in head:
                    mode = "JPG"
            img = QImageReader(fpath.replace("/",os.path.sep))
            qp = QPixmap.fromImageReader(img)
            if not qp.isNull():
                if category == "icon": mode = Qt.IgnoreAspectRatio
                if category == "logo": mode = Qt.KeepAspectRatio
                qp = qp.scaled(size,size,mode,Qt.SmoothTransformation)
            else:
                print("error loading",repr(fpath),mode)
            icon_cache[(fpath,size)] = qp
        else:
            try:
                icon_cache[(fpath,size)] = pygame.transform.scale(pygame.image.load(fpath),[size,size])
            except:
                pass
    return icon_in_cache(game,size,icon_cache,filecache_root,category,imode,url)
