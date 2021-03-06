#!/usr/bin/env python
import logging
import os
import pickle
import requests
import shutil
import urllib
from PIL import Image
import sys

HOME = os.path.expanduser("~")
LOGDIR = HOME + "/usr/var/log"
APPDIR = HOME + "/.mySocial"
CONFIGDIR = APPDIR + "/config"
DATADIR = APPDIR + "/data"
TMPDIR = "/tmp"
WWWDIR = "/var/www/html/img/"
WWWADDRESS = 'https://elmundoesimperfecto.com/img/'
NAMEIMG = 'instagram.jpg'

FAIL = 'Fail!'
OK = 'OK'

def logMsg(msgLog, log=1, output=1):
    if log == 1:
        logging.info(msgLog)
    elif log == 2:
        logging.debug(msgLog)

    if output == 1:
        print(msgLog)
    elif output == 2: 
        print("") 
        print("====================================") 
        print("{}".format(msgLog)) 
        print("====================================") 
 
def fileNamePath(url, socialNetwork=()):
    if not socialNetwork: 
        theName = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc)
    else: 
        myFile = (f"{DATADIR}/{urllib.parse.urlparse(url).netloc}_"
                  f"{socialNetwork[0]}_{socialNetwork[1]}")
        theName = os.path.expanduser(myFile)
    return(theName)

def setNextTime(blog, socialNetwork, tNow, tSleep):        
    fileNameNext = fileNamePath(blog.getUrl(), socialNetwork)+'.timeNext' 
    with open(fileNameNext,'wb') as f:
        pickle.dump((tNow, tSleep), f)
    return fileNameNext

def getNextTime(blog, socialNetwork):        
    fileNameNext = fileNamePath(blog.getUrl(), socialNetwork)+'.timeNext' 
    logging.debug(f"fileNameNext {fileNameNext}")
    try:
        with open(fileNameNext,'rb') as f:
            tNow, tSleep = pickle.load(f)
        return tNow, tSleep
    except:
        # File does not exist, we need to create it.
        with open(fileNameNext, "wb") as f:
            logging.warning("File %s does not exist. Creating it."
                    % fileNameNext) 
            # None published, or non-existent file
            return 0, 0
 
def getLastLink(fileName):        
    logging.debug(f"fileName: {fileName}")
    if not os.path.isdir(os.path.dirname(fileName)):
        sys.exit("No directory {} exists".format(os.path.dirname(fileName)))
    if os.path.isfile(fileName):
        with open(fileName, "rb") as f: 
            linkLast = f.read().decode().split()  # Last published
    else:
        # File does not exist, we need to create it.
        # Should we create it here? It is a reading function!!
        with open(fileName, "wb") as f:
            logging.warning("File %s does not exist. Creating it."
                    % fileName) 
            linkLast = ''  
            # None published, or non-existent file
    if len(linkLast) == 1: 
        return(linkLast[0], os.path.getmtime(fileName))
    else:
        return(linkLast, os.path.getmtime(fileName))

def checkLastLink(url, socialNetwork=()):
    # Redundant with moduleCache
    fileNameL = fileNamePath(url, socialNetwork)+".last"
    logging.debug("Checking last link: %s" % fileNameL)
    #print("Checking last link: %s" % fileNameL)
    (linkLast, timeLast) = getLastLink(fileNameL)
    return(linkLast, timeLast)

def newUpdateLastLink(url, link, lastLink, socialNetwork=()): 
    if isinstance(lastLink, list): 
        link = '\n'.join([ "{}".format (post[1]) for post in listPosts]) 
        link = link + '\n' + '\n'.join(lastLink)

    fileName = fileNamePath(url, socialNetwork) + ".last"

    print(fileName)
    with open(fileName, "w") as f: 
        if isinstance(link, bytes): 
            f.write(link.decode())
        elif isinstance(link, str): 
            f.write(link)
        else:
            f.write(link[0])

def updateLastLink(url, link, socialNetwork=()):
    logging.debug(f"Url: {url} Link: {link} SocialNetwork: {socialNetwork}")
    fileName = fileNamePath(url, socialNetwork) + ".last"

    logging.debug(f"fileName: {fileName}")
    with open(fileName, "w") as f: 
        if isinstance(link, bytes): 
            f.write(link.decode())
        elif isinstance(link, str): 
            f.write(link)
        else:
            f.write(link[0])

def resizeImage(imgUrl):
    print(imgUrl)
    response = requests.get(imgUrl, stream=True)

    fileName = '{}/{}'.format(TMPDIR,
            urllib.parse.urlparse(response.url)[2].split('/')[-1])
    with open(fileName,'wb') as f: 
        shutil.copyfileobj(response.raw, f)

    im = Image.open(fileName)
    size = im.size

    if size[0] < size[1]: 
       dif = size[1]-size[0]
       box = (0, dif/2 , size[0], dif/2+size[0])
    else:
       dif = size[0]-size[1]
       box = (dif/2, 0 , dif/2 + size[1], size[1])
    region = im.crop(box)
    fileNameOutput = WWWDIR + NAMEIMG
    print("f",fileNameOutput)
    try: 
        region.save(fileNameOutput)
    except: 
        fileNameOutput = '/tmp/' + NAMEIMG
        region.save(fileNameOutput)
    address = '{}{}'.format(WWWADDRESS,NAMEIMG)
    return(address)

def getModule(profile):
    # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
    import importlib
    serviceName = profile.capitalize()
    logging.debug(f"Module {serviceName}")
    mod = importlib.import_module('module' + serviceName) 
    cls = getattr(mod, 'module' + serviceName)
    api = cls()
    return api

def getApi(profile, nick):
    api = getModule(profile)
    api.setClient(nick)

    return api
