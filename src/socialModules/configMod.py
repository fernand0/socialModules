#!/usr/bin/env python
import importlib
import logging
import os
import pickle
import shutil
import sys
import urllib

import requests
# from PIL import Image

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
    elif log == 3:
        logging.warning(msgLog)

    if output == 1:
        print(f"{msgLog}")
    elif output == 2:
        print("")
        print("====================================")
        print("{}".format(msgLog))
        print("====================================")

def fileNamePath(url, socialNetwork=()):
    urlParsed = urllib.parse.urlparse(url)
    myNetloc = urlParsed.netloc
    if not myNetloc:
        myNetloc=url
    if 'twitter' in myNetloc:
        myNetloc = f"{myNetloc}_{urlParsed.path[1:]}"
    if myNetloc.endswith('/'):
        myNetloc = myNetloc[:-1]
    if not socialNetwork:
        theName = (f"{DATADIR}/{myNetloc}")
    else:
        myFile = (f"{DATADIR}/{myNetloc}_"
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
    msgLog = (f"fileNameNext {fileNameNext}")
    logMsg(msgLog, 2, 0)
    msgLog = checkFile(fileNameNext)
    if 'OK' in msgLog:
        with open(fileNameNext,'rb') as f:
            tNow, tSleep = pickle.load(f)
        return tNow, tSleep
    else:
        self.report(self.service, msgLog, '', '')
        return 0, 0

def checkFile(fileName, indent=""):
    msgLog = f"{indent} Start Checking {fileName} "
    logMsg(msgLog, 2, 0)
    dirName = os.path.dirname(fileName)

    msgRes = f"OK {fileName}"
    if not os.path.isdir(dirName):
        msgRes = f"Directory {dirName} does not exist."
    elif not os.path.isfile(fileName):
        msgRes = f"File {fileName} does not exist."

    msgLog = f"{indent} End Checking"
    logMsg(msgLog, 2, 0)
    return msgRes

def getLastLink(fileName, indent=''):
    msgLog = (f"fileName: {fileName}")
    logMsg(msgLog, 2, 0)
    linkLast = ''
    timeLast = 0
    msgLog = checkFile(fileName)
    if not "OK" in msgLog:
        logging.info(msgLog)
    else:
        with open(fileName, "rb") as f:
            linkLast = f.read().decode().split()  # Last published
        timeLast = os.path.getmtime(fileName)
    # else:
    #     # File does not exist, we need to create it.
    #     # Should we create it here? It is a reading function!!
    #     with open(fileName, "wb") as f:
    #         msgLog = f"File {fileName} does not exist. Creating it."
    #         logMsg(msgLog, 3, 0)
    #         linkLast = ''
    #         # None published, or non-existent file
    if len(linkLast) == 1:
        return(linkLast[0], timeLast)
    else:
        return(linkLast, timeLast)

def checkLastLink(url, socialNetwork=()):
    # Redundant with moduleCache
    fileNameL = fileNamePath(url, socialNetwork)+".last"
    msgLog = (f"Checking last link: {fileNameL}")
    logMsg(msgLog, 2, 0)
    #print("Checking last link: %s" % fileNameL)
    (linkLast, timeLast) = getLastLink(fileNameL)
    return(linkLast, timeLast)

def newUpdateLastLink(url, link, lastLink, socialNetwork=()):
    if isinstance(lastLink, list):
        link = '\n'.join([ "{}".format (post[1]) for post in listPosts])
        link = link + '\n' + '\n'.join(lastLink)

    fileName = fileNamePath(url, socialNetwork) + ".last"

    msgLog = checkFile(fileName)
    if 'OK' in msgLog:
        with open(fileName, "w") as f:
            if isinstance(link, bytes):
                f.write(link.decode())
            elif isinstance(link, str):
                f.write(link)
            else:
                f.write(link[0])

def updateLastLink(url, link, socialNetwork=()):
    try:
        #FIXME: not self here
        indent = self.indent
    except:
        indent = ''
    msgLog = (f"{indent} updateLastLink {socialNetwork}")
    logMsg(msgLog, 1, 0)
    msgLog = (f"{indent} Url: {url} Link: {link} "
              f"SocialNetwork: {socialNetwork}")
    logMsg(msgLog, 2, 0)
    fileName = fileNamePath(url, socialNetwork) + ".last"


    msgLog = (f"fileName: {fileName}")
    logMsg(msgLog, 2, 0)
    msgLog = checkFile(fileName)
    logMsg(msgLog, 2, 0)
    if not 'OK' in msgLog:
        msgLog = (f"fileName: {fileName} does not exist, I'll create it")
        logMsg(msgLog, 2, 0)
    with open(fileName, "w") as f:
        if isinstance(link, bytes):
            f.write(link.decode())
        elif isinstance(link, str):
            f.write(link)
        else:
            f.write(link[0])

# def resizeImage(imgUrl):
#     print(imgUrl)
#     response = requests.get(imgUrl, stream=True)
#
#     fileName = '{}/{}'.format(TMPDIR,
#             urllib.parse.urlparse(response.url)[2].split('/')[-1])
#     with open(fileName,'wb') as f:
#         shutil.copyfileobj(response.raw, f)
#
#     im = Image.open(fileName)
#     size = im.size
#
#     if size[0] < size[1]:
#        dif = size[1]-size[0]
#        box = (0, dif/2 , size[0], dif/2+size[0])
#     else:
#        dif = size[0]-size[1]
#        box = (dif/2, 0 , dif/2 + size[1], size[1])
#     region = im.crop(box)
#     fileNameOutput = WWWDIR + NAMEIMG
#     print("f",fileNameOutput)
#     try:
#         region.save(fileNameOutput)
#     except:
#         fileNameOutput = '/tmp/' + NAMEIMG
#         region.save(fileNameOutput)
#     address = '{}{}'.format(WWWADDRESS,NAMEIMG)
#     return(address)

def getModule(profile, indent=''):
    # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
    indent = f"{indent} "
    msgLog = (f"{indent} Start getModule")
    logMsg(msgLog, 2, 0)
    serviceName = profile.capitalize()

    mod = importlib.import_module('socialModules.module' + serviceName)
    cls = getattr(mod, 'module' + serviceName)
    # logging.debug(f"Class: {cls}")
    api = cls(indent)
    msgLog = (f"{indent} End getModule")
    logMsg(msgLog, 2, 0)
    indent = indent[:-1]
    return api

def getApi(profile, nick, indent=""):
    msgLog = (f"{indent} Start getApi")
    logMsg(msgLog, 2, 0)

    #indent = f"{indent} "

    msgLog = (f"{indent}  Profile {profile}")
    logMsg(msgLog, 2, 0)
    msgLog = (f"{indent}  Nick {nick}")
    logMsg(msgLog, 2, 0)
    api = getModule(profile, indent)
    api.indent = indent
    api.setClient(nick)
    api.setPostsType('posts')

    #indent = indent[:-1]
    msgLog = (f"{indent} End getApi")
    logMsg(msgLog, 2, 0)
    return api

def nameModule():
    import inspect
    stack = inspect.stack()
    info = stack[1]
    name = info.filename
    pos = name.rfind('module')
    name = name[pos+len('module'):-3]
    return name

