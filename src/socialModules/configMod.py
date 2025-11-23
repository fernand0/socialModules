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
WWWADDRESS = "https://elmundoesimperfecto.com/img/"
NAMEIMG = "instagram.jpg"

FAIL = "Fail!"
OK = "OK"


# import logging
# import inspect
# import os
#
# # 1. Configurar el formato del log para incluir el nuevo atributo
# logging.basicConfig(
#     format="%(asctime)s [%(filename)s -> %(caller_file)s] %(levelname)s: %(message)s",
#     level=logging.INFO
# )
#
# logger = logging.getLogger(__name__)
#
# # 2. Función de log mejorada para obtener el origen de forma automática
# def log_con_origen(logger_obj, mensaje):
#     """
#     Función de log que obtiene automáticamente el nombre del archivo
#     que la invocó, usando el módulo 'inspect'.
#     """
#     # Obtiene la pila de llamadas. La posición [1] es la función que nos llamó
#     # (en este caso, 'mi_funcion_en_main').
#     # La posición [0] sería la pila de 'log_con_origen'.
#     caller_frame = inspect.stack()[1]
#
#     # 'caller_frame.filename' contiene la ruta completa del archivo de origen.
#     # 'os.path.basename' extrae solo el nombre del archivo.
#     caller_file = os.path.basename(caller_frame.filename)
#
#     # Realiza la llamada al logger, pasando el nombre del archivo como 'extra'
#     logger_obj.info(mensaje, extra={'caller_file': caller_file})
#
# # 3. Archivo 'mi_modulo.py'
# def mi_funcion_en_modulo():
#     log_con_origen(logger, "Este mensaje se llama desde mi_modulo.")
#
# # 4. Archivo 'main.py'
# if __name__ == "__main__":
#     from mi_modulo import mi_funcion_en_modulo
#     mi_funcion_en_modulo()
#      mi_funcion_en_modulo()
#
# __name__

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
        myNetloc = url
    if ("twitter" in myNetloc) or ("reddit" in myNetloc):
        myNetloc = f"{myNetloc}_{urlParsed.path[1:]}"
    if myNetloc.endswith("/"):
        myNetloc = myNetloc[:-1]
    myNetloc = myNetloc.replace("/", "_")
    if not socialNetwork:
        theName = f"{DATADIR}/{myNetloc}"
    else:
        myFile = f"{DATADIR}/{myNetloc}_" f"{socialNetwork[0]}_{socialNetwork[1]}"
        theName = os.path.expanduser(myFile)
    return theName

def checkFile(fileName, indent=""):
    msgLog = f"{indent} Start checkFile"
    logMsg(msgLog, 2, 0)
    msgLog = f"{indent}  File: {fileName}"
    logMsg(msgLog, 2, 0)
    dirName = os.path.dirname(fileName)

    msgRes = f" File OK"
    if not os.path.isdir(dirName):
        msgRes = f"Directory {dirName} does not exist."
    elif not os.path.isfile(fileName):
        msgRes = f"File {fileName} does not exist."

    logMsg(f"{indent}  {msgRes}", 2, 0)
    msgLog = f"{indent} End checkFile"
    logMsg(msgLog, 2, 0)
    return msgRes


def getLastLink(fileName, indent=""):
    msgLog = f"fileName: {fileName}"
    logMsg(msgLog, 2, 0)
    linkLast = ""
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
        return (linkLast[0], timeLast)
    else:
        return (linkLast, timeLast)


def checkLastLink(url, socialNetwork=()):
    # Redundant with moduleCache
    fileNameL = fileNamePath(url, socialNetwork) + ".last"
    msgLog = f"Checking last link: {fileNameL}"
    logMsg(msgLog, 2, 0)
    # print("Checking last link: %s" % fileNameL)
    (linkLast, timeLast) = getLastLink(fileNameL)
    return (linkLast, timeLast)


def newUpdateLastLink(url, link, lastLink, socialNetwork=()):
    if isinstance(lastLink, list):
        link = "\n".join(["{}".format(post[1]) for post in listPosts])
        link = link + "\n" + "\n".join(lastLink)

    fileName = fileNamePath(url, socialNetwork) + ".last"

    msgLog = checkFile(fileName)
    if "OK" in msgLog:
        with open(fileName, "w") as f:
            if isinstance(link, bytes):
                f.write(link.decode())
            elif isinstance(link, str):
                f.write(link)
            else:
                f.write(link[0])


def updateLastLink(url, link, socialNetwork=(), indent=""):
    try:
        # FIXME: not self here
        indent = self.indent
    except:
        indent = ""
    msgLog = f"{indent} updateLastLink {socialNetwork}"
    logMsg(msgLog, 1, 0)
    msgLog = f"{indent} Url: {url} Link: {link} " f"SocialNetwork: {socialNetwork}"
    logMsg(msgLog, 2, 0)
    fileName = fileNamePath(url, socialNetwork) + ".last"

    msgLog = f"fileName: {fileName}"
    logMsg(msgLog, 2, 0)
    msgLog = checkFile(fileName, indent)
    logMsg(msgLog, 2, 0)
    if not "OK" in msgLog:
        msgLog = f"fileName: {fileName} does not exist, I'll create it"
        logMsg(msgLog, 2, 0)
    with open(fileName, "w") as f:
        if isinstance(link, bytes):
            f.write(link.decode())
        elif isinstance(link, str):
            f.write(link)
        else:
            f.write(link[0])


def getModule(profile, indent=""):
    # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
    indent = f"{indent} "
    msgLog = f"{indent} Start getModule {profile}"
    logMsg(msgLog, 2, 0)
    serviceName = profile.capitalize()
    module_name = f"socialModules.module{serviceName}"
    class_name = f"module{serviceName}"

    api = None  # Initialize api to None

    try:
        logging.info("1")
        mod = importlib.import_module(module_name)
        logging.info(f"2 {mod}")
        cls = getattr(mod, class_name)
        logging.info(f"3 {cls}")
        api = cls(indent)
        logging.info("4")
        msgLog = f"{indent} End getModule"
        logMsg(msgLog, 2, 0)
        indent = indent[:-1]
    except ImportError:
        logMsg(f"{indent} Module {module_name} not found.", 3, 1)
    except AttributeError:
        logMsg(f"{indent} Class {class_name} not found in module {module_name}.", 3, 1)

    return api

def getApi(profile, nick, indent="", channel=None):
    msgLog = f"{indent} Start getApi with channel {channel}"
    logMsg(msgLog, 2, 0)

    api = getModule(profile, indent)

    result_api = None

    if api is None:
        logMsg(f"{indent} Failed to get API module for profile: {profile}", 3, 1)
    else:
        api.profile = profile
        api.nick = nick
        api.indent = f"{indent} "
        api.setClient(nick)
        if channel:
            api.setPage(channel)
        api.indent = f"{indent[:-1]}"
        api.setPostsType("posts")
        result_api = api

    msgLog = f"{indent} End getApi"
    logMsg(msgLog, 2, 0)
    return result_api

def nameModule():
    import inspect

    stack = inspect.stack()
    info = stack[1]
    name = info.filename
    pos = name.rfind("module")
    name = name[pos + len("module") : -3]
    return name


def safe_get(data, keys, default=""):
    """Safely retrieves nested values from a dictionary."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


def select_from_list(
    options,
    identifier="",
    selector="",
    negation_selector="",
    default="",
    more_options=[],
):
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
        names_sel = [opt for opt in names if selector in opt]  # + more_options
    if negation_selector:
        names_sel = [opt for opt in names if not (negation_selector in opt)]
    names_sel = names_sel + more_options
    options_sel = names_sel.copy()
    while options_sel and len(options_sel) > 1:
        text_sel = ""
        for i, elem in enumerate(options_sel):
            text_sel = f"{text_sel}\n{i}) {elem}"
        resPopen = os.popen("stty size", "r").read()
        rows, columns = resPopen.split()
        logging.info(f"Rows: {rows} Columns: {columns}")
        if text_sel.count("\n") > int(rows) - 2:
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

def extract_nick_from_url(url):
    result = url
    url_parsed = urllib.parse.urlparse(url)
    #if url and (url.startswith("http")):
    #    result = url.split("//", 1)[1]
    if (((url_parsed.netloc.count('.')>1)
         and (url_parsed.netloc.split('.')[0] in ['www']))
        or (url_parsed.netloc.count('.') == 1)):
            result = f"{url_parsed.netloc}{url_parsed.path}"
    else:
        result = f"{url_parsed.netloc}"
    if url_parsed.query:
        result = f"{result}?{url_parsed.query}"

    return result
