#!/usr/bin/env python
import logging
import os
import requests
import shutil
import urllib
from PIL import Image

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


def fileNamePath(url, socialNetwork=()):
    if not socialNetwork: 
        theName = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else: 
        theName = os.path.expanduser(DATADIR + '/' 
                    + urllib.parse.urlparse(url).netloc 
                    + '_' 
                    + socialNetwork[0] + '_' + socialNetwork[1])
    return(theName)

def getLastLink(fileName):        
    try: 
        with open(fileName, "rb") as f: 
            linkLast = f.read().decode().split()  # Last published
    except:
        # File does not exist, we need to create it.
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
    if not socialNetwork: 
        fileNameL = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else:
        fileNameL = fileNamePath(url, socialNetwork)+".last"
    logging.debug("Checking last link: %s" % fileNameL)
    (linkLast, timeLast) = getLastLink(fileNameL)
    return(linkLast, timeLast)

def newupdateLastLink(url, link, socialNetwork=()): 
    logging.info("    Updating link {} {}".format(profile, link))

    if isinstance(lastLink, list): 
        link = '\n'.join([ "{}".format (post[1]) for post in listPosts]) 
        link = link + '\n' + '\n'.join(lastLink)

    if not socialNetwork: 
        fileName = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else: 
        fileName = fileNamePath(url, socialNetwork) + ".last"

    with open(fileName, "w") as f: 
        if isinstance(link, bytes): 
            f.write(link.decode())
        elif isinstance(link, str): 
            f.write(link)
        else:
            f.write(link[0])


def updateLastLink(url, link, socialNetwork=()):
    if not socialNetwork: 
        fileName = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else: 
        fileName = fileNamePath(url, socialNetwork) + ".last"

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


