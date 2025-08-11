#!/usr/bin/env python
import click
import importlib
import logging
import os
import pickle
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
        print("====================================")
        print("{}".format(msgLog))
        print("====================================")

def fileNamePath(url, socialNetwork=()):
    logging.info(f" ----> Url: {url}")
    logging.info(f"socialNetwork: {socialNetwork}")
    urlParsed = urllib.parse.urlparse(url)
    myNetloc = urlParsed.netloc
    if not myNetloc:
        myNetloc=url
    if ('twitter' in myNetloc) or ('reddit' in myNetloc):
        myNetloc = f"{myNetloc}_{urlParsed.path[1:]}"
    if myNetloc.endswith('/'):
        myNetloc = myNetloc[:-1]
    myNetloc = myNetloc.replace('/','_')
    if not socialNetwork:
        theName = (f"{DATADIR}/{myNetloc}")
    else:
        myFile = (f"{DATADIR}/{myNetloc}_"
                  f"{socialNetwork[0]}_{socialNetwork[1]}")
        theName = os.path.expanduser(myFile)
    return(theName)

# def setNextTime(blog, socialNetwork, tNow, tSleep):
#     fileNameNext = fileNamePath(blog.getUrl(), socialNetwork)+'.timeNext'
#     with open(fileNameNext,'wb') as f:
#         pickle.dump((tNow, tSleep), f)
#     return fileNameNext

def getNextTime(blog, socialNetwork, indent=""):
    fileNameNext = fileNamePath(blog.getUrl(), socialNetwork)+'.timeNext'
    msgLog = (f"fileNameNext {fileNameNext}")
    logMsg(msgLog, 2, 0)
    msgLog = checkFile(fileNameNext, indent)
    if 'OK' in msgLog:
        with open(fileNameNext,'rb') as f:
            tNow, tSleep = pickle.load(f)
        return tNow, tSleep
    else:
        self.report(self.service, msgLog, '', '')
        return 0, 0

def checkFile(fileName, indent=""):
    msgLog = f"{indent} Start checkFile"
    logMsg(msgLog, 2, 0)
    msgLog = f"{indent}  File: {fileName}"
    logMsg(msgLog, 2, 0)
    dirName = os.path.dirname(fileName)

    msgRes = f"OK {fileName}"
    if not os.path.isdir(dirName):
        msgRes = f"Directory {dirName} does not exist."
    elif not os.path.isfile(fileName):
        msgRes = f"File {fileName} does not exist."

    logMsg(f"{indent}  {msgRes}", 2, 0)
    msgLog = f"{indent} End checkFile"
    logMsg(msgLog, 2, 0)
    return msgRes

def getLastLink(fileName, indent=''):
    msgLog = (f"fileName: {fileName}")
    logMsg(msgLog, 2, 0)
    linkLast = ''
    timeLast = 0
    msgLog = checkFile(fileName, indent)
    if not "OK" in msgLog:
        msgLog = f"{indent} {msgLog}"
        logMsg(msgLog, 3, 0)
    else:
        with open(fileName, "rb") as f:
            linkLast = f.read().decode().split()  # Last published
        timeLast = os.path.getmtime(fileName)
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

def updateLastLink(url, link, socialNetwork=(),indent=''):
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
    msgLog = checkFile(fileName, indent)
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

def getModule(profile, indent=''):
    # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
    indent = f"{indent} "
    msgLog = (f"{indent} Start getModule {profile}")
    logMsg(msgLog, 2, 0)
    serviceName = profile.capitalize()

    mod = importlib.import_module('socialModules.module' + serviceName)
    cls = getattr(mod, 'module' + serviceName)
    api = cls(indent)
    msgLog = (f"{indent} End getModule")
    logMsg(msgLog, 2, 0)
    indent = indent[:-1]
    return api

def getApi(profile, nick, indent="", channel = None):
    msgLog = (f"{indent} Start getApi with channel {channel}")
    logMsg(msgLog, 2, 0)

    # msgLog = (f"{indent}  Profile {profile} "
    #           f"Nick {nick}")
    # logMsg(msgLog, 2, 0)
    api = getModule(profile, indent)
    # msgLog = (f"{indent}  Api {api}")
    # logMsg(msgLog, 2, 0)

    api.profile = profile
    api.nick = nick
    api.indent = f"{indent} "
    api.setClient(nick)
    if channel:
        api.setPage(channel)
    api.indent = f"{indent[:-1]}"
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

def safe_get(data, keys, default=""):
    """Safely retrieves nested values from a dictionary."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


def select_from_list(options, identifier="", selector="", 
                     negation_selector="", default="", more_options=[]):
    """selects an option form an iterable element, based on some identifier

    we can make an initial selection of elements that contain 'selector'
    we can select based on numbers or in substrings of the elements
    of the list.
    """

    if options and (
        isinstance(options[0], dict)
        or (hasattr(options[0], "__slots__"))
        or hasattr(options[0], "name")
    ):
        names = [
            safe_get(
                el,
                [
                    identifier,
                ],
            )
            if isinstance(el, dict)
            else getattr(el, identifier)
            for el in options
        ]
    else:
        names = options
    sel = -1
    names_sel = names.copy()
    if selector:
        names_sel = [opt for opt in names if selector in opt]# + more_options
    if negation_selector:
        names_sel = [opt for opt in names if not (negation_selector in opt)] 
    names_sel = names_sel + more_options
    options_sel = names_sel.copy()
    while options_sel and len(options_sel)>1:
        text_sel = ""
        for i, elem in enumerate(options_sel):
            text_sel = f"{text_sel}\n{i}) {elem}"
        resPopen = os.popen('stty size', 'r').read()
        rows, columns = resPopen.split()
        logging.info(f"Rows: {rows} Columns: {columns}")
        if text_sel.count('\n') > int(rows) -2:
            click.echo_via_pager(text_sel) 
        else:
            click.echo(text_sel)
        msg = "Selection"
        # msg += f"({default}) " if default else ""
        sel = click.prompt(msg, default=default)
        if sel == "" and default:
            sel = names.index(default)
            options_sel = []
        elif not sel.isdigit():
            logging.debug(f"Opt: {sel}")
            options_sel = [opt for opt in options_sel if sel.lower() in opt.lower()]
            # if len(options_sel) == 1:
            #     if not options_sel[0] in more_options:
            #         sel = names.index(options_sel[0])
            #     options_sel = []
            # elif
            if len(options_sel) == 0:
                options_sel = names_sel.copy()
        else:
            # Now we select the original number
            if int(sel) < len(options_sel):
                sel = names.index(options_sel[int(sel)])
                options_sel = []
            else:
                options_sel = names_sel.copy()
    
    if len(options_sel) == 1:      
        if not options_sel[0] in more_options: 
            sel = names.index(options_sel[0])

    logging.info(f"Sel: {sel}")
    if isinstance(sel, int) and int(sel) < len(names): 
        logging.info(f"- {names[int(sel)]}")
        name = names[int(sel)]
    else:
        logging.info(f"- is an extra option")
        name = sel

    return sel, name
