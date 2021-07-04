import os
import shutil

upath = "/Applications/Ultima III™.app/Contents/Resources/game"
dpath = "/Users/patrickmullen/.ultima3"
files = ["PARTY.ULT", "ROSTER.ULT", "SOSARIA.ULT"]


def backup():
    for fn in files:
        shutil.copyfile(upath + "/" + fn, dpath + "/" + fn)


def restore():
    for fn in files:
        shutil.copyfile(dpath + "/" + fn, upath + "/" + fn)


while 1:
    inp = input("(B)ackup or (R)estore? ")
    if inp == "b":
        backup()
    elif inp == "r":
        restore()
