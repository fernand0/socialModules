import configparser
import inspect
import logging
import os
import random
import sys
import time
import urllib.parse


path = f"{os.path.expanduser('~')}/usr/src/socialModules"
sys.path.append(path)

from configMod import *

class moduleRules:

    def hasSetMethods(self, service):
        if service == "social":
            return []
        clsService = getModule(service)
        listMethods = clsService.__dir__()

        methods = []
        for method in listMethods:
            if (not method.startswith("__")) and (method.find("set") >= 0):
                action = "set"
                target = ""
                myModule = eval(f"clsService.{method}.__module__")

                if method.find("Api") >= 0:
                    target = method[len("setApi"):].lower()
                # elif (clsService.setPosts.__module__
                elif myModule == f"module{service.capitalize()}":
                    target = method[len("set"):].lower()
                if target and (
                    target.lower() in ["posts", "drafts", "favs",
                                       "messages", "queue", "search"]
                              ):
                    toAppend = (action, target)
                    if not (toAppend in methods):
                        methods.append(toAppend)
        return methods

    def hasPublishMethod(self, service):
        clsService = getModule(service)
        listMethods = clsService.__dir__()

        methods = []
        target = None
        for method in listMethods:
            if method.find("publish") >= 0:
                action = "publish"
                target = ""
                moduleService = clsService.publishPost.__module__
                if method.find("Api") >= 0:
                    target = method[len("publishApi"):].lower()
                    msgLog = (f"Target api {target}")
                    logMsg(msgLog, 2, 0)
                elif moduleService == f"module{service.capitalize()}":
                    target = method[len("publish"):].lower()
                    msgLog = (f"Target mod {target}")
                    logMsg(msgLog, 2, 0)
                if target and (target!='image'):
                    toAppend = (action, target)
                    if not (toAppend in methods):
                        methods.append(toAppend)
        return methods

    def getServices(self):
        modulesFiles = os.listdir(path)
        modules = {"special": ["cache", "direct"], "regular": []}
        # Initialized with some special services
        name = "module"
        for module in modulesFiles:
            if module.startswith(name):
                moduleName = module[len(name): -3].lower()
                if not (moduleName in modules["special"]):
                    # We drop the 'module' and the '.py' parts
                    modules["regular"].append(moduleName)

        return modules

    def checkRules(self):
        msgLog = "Checking rules"
        logMsg(msgLog, 1, 2)
        config = configparser.ConfigParser()
        config.read(CONFIGDIR + "/.rssBlogs")

        services = self.getServices()
        services['regular'].append('cache')
        # cache objects can be considered as regular for publishing elements
        # stored there
        indent = 3*"  "+4*" "

        srcs = []
        srcsA = []
        more = []
        dsts = []
        ruls = {}
        mor = {}
        impRuls = []
        for section in config.sections():
            url = config.get(section, "url")
            msgLog = f"Section: {section} Url: {url}"
            logMsg(msgLog, 1, 1)
            # Sources
            moreS = dict(config.items(section))
            moreSS = None
            if "rss" in config.options(section):
                rss = config.get(section, "rss")
                msgLog = (f"Service: rss -> {rss}")
                logMsg(msgLog, 2, 0)
                toAppend = ("rss", "set",
                            urllib.parse.urljoin(url, rss), "posts")
                srcs.append(toAppend)
                more.append(moreS)
            else:
                msgLog = (f"url {url}")
                logMsg(msgLog, 2, 0)

                for service in services["regular"]:
                    if (
                        ("service" in config[section])
                        and (service == config[section]["service"])
                    ) or (url.find(service) >= 0):
                        methods = self.hasSetMethods(service)
                        logging.debug(f"Service: {service} has set {methods}")
                        for method in methods:
                            msgLog = (f"Method: {method}")
                            logMsg(msgLog, 2, 0)
                            msgLog = (f"moreS: {moreS}")
                            logMsg(msgLog, 2, 0)
                            # If it has a method for setting, we can set
                            # directly using this
                            if service in config[section]:
                                nick = config[section][service]
                            else:
                                nick = url
                                if ((nick.find("slack") < 0)
                                        and (nick.find("gitter") < 0)):
                                    nick = nick.split("/")[-1]
                            if (service == 'imdb') or (service == 'imgur'):
                                nick = url
                            elif ('twitter' in url):
                                nick = url.split("/")[-1]

                            if 'posts' in moreS:
                                if moreS['posts'] == method[1]:
                                   toAppend = (service, "set", nick, method[1])
                            else:
                               toAppend = (service, "set", nick, method[1])
                            msgLog = (f"toAppend: {toAppend}")
                            logMsg(msgLog, 2, 0)
                            if not (toAppend in srcs):
                                if (('posts' in moreS)
                                    and (moreS['posts'] == method[1])):
                                    srcs.append(toAppend)
                                    more.append(moreS)
                                else:
                                    # Available, but with no rules
                                    srcsA.append(toAppend)
            fromSrv = toAppend
            msgLog = (f"fromSrv toAppend: {toAppend}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"fromSrv moreS: {moreS}")
            logMsg(msgLog, 2, 0)

            if "time" in config.options(section):
                timeW = config.get(section, "time")
            else:
                timeW = 0
            if "buffermax" in config.options(section):
                bufferMax = config.get(section, "buffermax")
            else:
                bufferMax = 0
            if "max" in config.options(section):
                bufferMax = config.get(section, "max")

            # Destinations
            hasSpecial = False
            if "posts" in config[section]:
                postsType = config[section]["posts"]
            else:
                postsType = "posts"
            if fromSrv:
                fromSrv = ( fromSrv[0], fromSrv[1], fromSrv[2], postsType,)
                for service in services["special"]:
                    toAppend = ""
                    msgLog = (f"Service: {service}")
                    logMsg(msgLog, 2, 0)
                    if service in config.options(section):
                        valueE = config.get(section, service).split("\n")
                        for val in valueE:
                            nick = config.get(section, val)
                            msgLog = (f"Service special: {service} "
                                      f"({val}, {nick})")
                            logMsg(msgLog, 2, 0)
                            if service == "direct":
                                url = "posts"
                            toAppend = (service, url, val, nick) #, timeW, bufferMax)
                            msgLog = (f"Service special toAppend: {toAppend} ")
                            logMsg(msgLog, 2, 0)
                            msgLog = (f"Service special from: {fromSrv} ")
                            logMsg(msgLog, 2, 0)
                            if toAppend not in dsts:
                                dsts.append(toAppend)
                            if toAppend:
                                if fromSrv not in mor:
                                    mor[fromSrv] = moreS
                                if fromSrv in ruls:
                                    if not toAppend in ruls[fromSrv]:
                                        ruls[fromSrv].append(toAppend)
                                        msgLog = (f"1 added: {toAppend} "
                                                  f"in {fromSrv} ")
                                        logMsg(msgLog, 2, 0)
                                else:
                                    ruls[fromSrv] = []
                                    ruls[fromSrv].append(toAppend)
                                    msgLog = (f"1.1 added: {toAppend} "
                                              f"in {fromSrv} ")
                                    logMsg(msgLog, 2, 0)

                                hasSpecial = True

                for service in services["regular"]:
                    if (service == 'cache'):
                        continue
                    toAppend = ""
                    if service in config.options(section):
                        methods = self.hasPublishMethod(service)
                        msgLog = (f"Service: {service} ({section}) has "
                                  f"{methods}")
                        logMsg(msgLog, 2, 0)
                        for method in methods:
                            msgLog = (f"Method: {method}")
                            logMsg(msgLog, 2, 0)
                            # If it has a method for publishing, we can
                            # publish directly using this

                            if not method[1]:
                                mmethod = 'post'
                            else:
                                mmethod = method[1]
                            toAppend = (
                                    "direct",
                                    mmethod,
                                    service,
                                    config.get(section, service) #,
                                    # timeW,
                                    # bufferMax,
                                    )

                            if not (toAppend in dsts):
                                dsts.append(toAppend)
                            if toAppend:
                                if hasSpecial:
                                    msgLog = (f"hasSpecial: {fromSrv}---")
                                    logMsg(msgLog, 2, 0)
                                    msgLog = (f"hasSpecial: {toAppend}---")
                                    logMsg(msgLog, 2, 0)
                                    nickSn = f"{toAppend[2]}@{toAppend[3]}"
                                    fromSrvSp = (
                                            "cache",
                                            (fromSrv[0], fromSrv[2]),
                                            nickSn,
                                            "posts",
                                            )
                                    impRuls.append((fromSrvSp, toAppend))
                                    if fromSrvSp not in mor:
                                        mor[fromSrvSp] = moreS
                                    if fromSrvSp in ruls:
                                        if not toAppend in ruls[fromSrvSp]:
                                            ruls[fromSrvSp].append(toAppend)
                                            msgLog = (f"2 added: {toAppend} "
                                                      f"in {fromSrvSp} ")
                                            logMsg(msgLog, 1, 0)
                                    else:
                                        ruls[fromSrvSp] = []
                                        ruls[fromSrvSp].append(toAppend)
                                        if url:
                                            msgLog = (f"2.1 added: {toAppend} "
                                                      f"in {fromSrvSp} "
                                                      f"with {url}")
                                        else:
                                            msgLog = (f"2.1 added: {toAppend} "
                                                      f"in {fromSrvSp} "
                                                      f"with no url")
                                        logMsg(msgLog, 1, 0)
                                else:
                                    msgLog = (f"From {fromSrv}")
                                    logMsg(msgLog, 2, 0)
                                    msgLog = (f"direct: {dsts}---")
                                    logMsg(msgLog, 2, 0)

                                    if fromSrv not in mor:
                                        msgLog = (f"Adding {moreS}")
                                        logMsg(msgLog, 2, 0)
                                        mor[fromSrv] = moreS
                                    if fromSrv in ruls:
                                        if not toAppend in ruls[fromSrv]:
                                            ruls[fromSrv].append(toAppend)
                                            msgLog = (f"3 added: {toAppend} in "
                                                      f"{fromSrv} ")
                                            logMsg(msgLog, 2, 0)
                                    else:
                                        ruls[fromSrv] = []
                                        ruls[fromSrv].append(toAppend)
                                        msgLog = (f"3.1 added: {toAppend} in "
                                                  f"{fromSrv} ")
                                        logMsg(msgLog, 2, 0)

        # Now we can add the sources not added.

        for src in srcsA:
            if not src in srcs:
                msgLog = (f"Adding implicit {src}")
                logMsg(msgLog, 2, 0)
                srcs.append(src)
                more.append({})

        # Now we can see which destinations can be also sources
        for dst in dsts:
            if dst[0] == "direct":
                service = dst[2]
                methods = self.hasSetMethods(service)
                for method in methods:
                    msgLog = (f"cache dst {dst}")
                    logMsg(msgLog, 2, 0)
                    toAppend = (service, "set", dst[3], method[1])#, dst[4])
                    msgLog = (f"toAppend src {toAppend}")
                    logMsg(msgLog, 2, 0)
                    if not (toAppend[:4] in srcs):
                        srcs.append(toAppend[:4])
                        more.append({})
            elif dst[0] == "cache":
                if len(dst)>4 :
                    toAppend = (dst[0], "set", (dst[1], (dst[2], dst[3])),
                                "posts", dst[4], 1)
                else:
                    toAppend = (dst[0], "set", (dst[1], (dst[2], dst[3])),
                                "posts", 0, 1)
                if not (toAppend[:4] in srcs):
                        srcs.append(toAppend[:4])
                        more.append({})

        available = {}
        myKeys = {}
        myIniKeys = []
        # for i, src in enumerate(srcs):
        for i, src in enumerate(ruls.keys()):
            if not src:
                continue
            iniK, nameK = self.getIniKey(src[0], myKeys, myIniKeys)
            if not (iniK in available):
                available[iniK] = {"name": src[0], "data": [], "social": []}
                available[iniK]["data"] = [{'src': src[1:], 'more': more[i]}]
            else:
                available[iniK]["data"].append({'src': src[1:],
                                                'more': more[i]})
            # srcC = (src[0], "set", src[1], src[2])
            # if srcC not in ruls:
            #     ruls[srcC] =

        myList = []
        for elem in available:
            component = (
                f"{elem}) "
                f"{available[elem]['name']}: "
                f"{len(available[elem]['data'])}"
            )
            myList.append(component)

        if myList:
            availableList = myList
        else:
            availableList = []

        self.available = available
        self.availableList = availableList

        msgLog = (f"Avail: {self.available}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"Ruls: {ruls}")
        logMsg(msgLog, 2, 0)
        self.rules = ruls
        self.more = mor

        return (srcs, dsts, ruls, impRuls)

<<<<<<< Updated upstream
=======
    def selectRule(self, selector, selector2 = "", selector3 = ""):
        indent = ""
        srcR = None

        for src in self.rules.keys():
            if src[0] == selector:
                logging.debug(f"- Src: {src}")
                logging.debug(f"Selectors: {selector} {selector2} {selector3}")
                more = self.more[src]
                srcR = src
                if not selector2:
                    break
                else:
                    if (selector2 == src[2]):
                        if not selector3:
                            break
                        elif  (selector3 in src[3]):
                            break
        return (srcR, more)

>>>>>>> Stashed changes
    def printList(self, myList, title):
        print(f"{title}:")
        for i, element in enumerate(myList):
            print(f"  {i}) {element}")

    def getIniKey(self, key, myKeys, myIniKeys):
        if key not in myKeys:
            if key[0] not in myIniKeys:
                iniK = key[0]
            else:
                i = 1
                while (i < len(key)) and (key[i] in myIniKeys):
                    i = i + 1
                if i < len(key):
                    iniK = key[i]
                else:
                    iniK = "j"
                    while iniK in myIniKeys:
                        iniK = chr(ord(iniK) + 1)
            myKeys[key] = iniK
        else:
            iniK = myKeys[key]
        myIniKeys.append(iniK)
        pos = key.find(iniK)
        if pos >= 0:
            nKey = key[:pos] + iniK.upper() + key[pos + 1:]
        else:
            nKey = iniK + key
        nKey = key + "-{}".format(iniK)

        return iniK, nKey

    def readConfigSrc(self, indent, src, more):
        msgLog = f"Src: Src {src}"
        logMsg(msgLog, 2, 0)
        msgLog = f"More: Src {more}"
        logMsg(msgLog, 1, 0)
        if src[0] == 'cache':
            apiSrc = getApi(src[0], src[1:])
            apiSrc.fileName = apiSrc.fileNameBase(src[1:])
            apiSrc.postaction = 'delete'
        else:
            apiSrc = getApi(src[0], src[2])

        for option in more:
            if option == 'posts':
                nameMethod = f"setPostsType"
            else:
                nameMethod = f"set{option.capitalize()}"

            if  nameMethod in apiSrc.__dir__():
                # setCache ¿?
                # url, time, max, posts,
                cmd = getattr(apiSrc, nameMethod)
                if inspect.ismethod(cmd):
                    cmd(more[option])
            else:
                for name in apiSrc.__dir__():
                    if name.lower() == nameMethod.lower():
                        cmd = getattr(apiSrc, name)
                        if inspect.ismethod(cmd):
                            cmd(more[option])
                            break

        if not apiSrc.getPostsType():
            apiSrc.setPostsType('posts')

        # apiSrc.setPosts()
        # print(f"Postsss: {apiSrc.getPosts()}")
        return apiSrc

    def readConfigDst(self, indent, action, more, apiSrc):
        profile = action[2]
        nick = action[3]
        socialNetwork = (profile, nick)
        msgLog = (f"{indent}socialNetwork: {socialNetwork}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{indent}Action: {action}")
        logMsg(msgLog, 1, 0)
        msgLog = (f"{indent}More: Dst {more}")
        logMsg(msgLog, 1, 0)

        if action[0] == "cache":
            print(f"Dst: {action}")
            apiDst = getApi("cache", ((more['service'],  action[1]), 
                f"{action[2]}@{action[3]}", 'posts'))
            apiDst.socialNetwork = action[2]
            apiDst.nick = action[3]
            apiDst.fileName = apiDst.fileNameBase(apiSrc)
        else:
            apiDst = getApi(profile, nick)

        apiDst.setUser(nick)
        apiDst.setPostsType('posts')

        msgLog = (f"{indent}Api dst: {apiDst}")
        logMsg(msgLog, 2, 0)

        if 'max' in more:
            mmax = more['max']
        elif 'buffermax' in more:
            mmax = more['buffermax']
        else:
            mmax = 0

        apiDst.setMax(mmax)

        if 'time' in more:
            apiDst.setTime(more['time'])

        return apiDst

    def testDifferPosts(self, apiSrc, lastLink, listPosts):
        i = 1
        num = 1
        listPosts = apiSrc.getNumPostsData(num, i, lastLink)
        if len(apiSrc.getPosts()) > 0:
            try:
                apiSrc.lastLinkPublished = apiSrc.getPostLink(apiSrc.getPosts()[1])
            except:
                apiSrc.lastLinkPublished = ''

        listPosts2 = apiSrc.getNumNextPost(num)
        print(f"{listPosts}")
        if listPosts2:
            if (listPosts == listPosts2):
                print("{indent}Equal listPosts")
            else:
                print(f"Differ listPosts (len {len(listPosts[0])}, "
                      f"{len(listPosts2[0])}:\n")
                for i, post in enumerate(listPosts):
                    for j, line in enumerate(listPosts[i]):
                        if line:
                            if (listPosts[i][j] != listPosts2[i][j]):
                                print(f"{j}) *{listPosts[i][j]}*\n"
                                      f"{j}) *{listPosts2[i][j]}*")
                        else:
                            print(f"{j})")
        else:
            print(f"{indent}No listPosts2")

    def executePublishAction(self, indent, msgAction, apiSrc, apiDst, 
                            simmulate, nextPost=True, pos=-1):
        res = ''

        msgLog = (f"{indent}Go! Action: {msgAction}")
        logMsg(msgLog, 1, 1)

        # The source of data can have changes while we were waiting
        apiSrc.setPosts()
        if nextPost:
            # FIXME is  this needed?
            post = apiSrc.getNextPost()
        else:
            post = apiSrc.getPost(pos)

        if post:
            msgLog = f"{indent}Would schedule in {msgAction} ..."
            logMsg(msgLog, 1, 1)
            indent = f"{indent} "
            logMsg(msgLog, 2, 0)
            logMsg(f"{indent}- {apiSrc.getPostTitle(post)}", 1, 1)
        else:
            msgLog = f"{indent}No post to schedule in {msgAction}"
            logMsg(msgLog, 1, 1)

        indent = f"{indent[:-1]}"

        resMsg = ''
        postaction = ''
        if not simmulate:
            if nextPost:
                res = apiDst.publishNextPost(apiSrc)
            else:
                res = apiDst.publishPosPost(apiSrc, pos)
            resMsg = f"Publish: {res}. "
            # print(f"{indent}res: {res}")
            if (nextPost and 
                    ((not res) or ('SAVELINK' in res) or not ('Fail!' in res))):
                resUpdate = apiSrc.updateLastLink(apiDst, '')
                resMsg += f"Update: {resUpdate}"
            if ((not res) or ('SAVELINK' in res) or not ('Fail!' in res)
                    or not( 'Duplicate' in res)):
                postaction = apiSrc.getPostAction()
                if postaction:
                    msgLog = (f"{indent}Post Action {postaction}")
                    logMsg(msgLog, 1, 1)

                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    msgLog = (f"{indent}Post Action command {cmdPost}")
                    logMsg(msgLog, 1, 1)
                    resPost = cmdPost()
                    msgLog = (f"{indent}End {postaction}, reply: {resPost} ")
                    logMsg(msgLog, 1, 1)
                    resMsg += f"Post Action: {resPost}"
                else:
                    msgLog = (f"{indent}No Post Action")
                    logMsg(msgLog, 1, 1)

            msgLog = (f"{indent}End publish, reply: {resMsg}")
            logMsg(msgLog, 1, 1)
        else:
            msgLog = (f"{indent}This is a simmulation")
            logMsg(msgLog, 1, 1)
            resMsg = f"Simulate: {msgLog}\n"
            post = apiSrc.getNextPost()
            if post:
                link = apiSrc.getPostLink(post)
                if link:
                    msgLog = (f"{indent}I'd record link: {link}")
                    logMsg(msgLog, 1, 1)
                    resMsg += f"{msgLog}\n"
                    # fN = fileNamePath(apiDst.getUrl(), socialNetwork)
                    # msgLog = (f"{indent}in file ", f"{fN}.last")
                    # logMsg(msgLog, 1, 1)
                    msgLog = (f"{indent}in file "
                              f"{apiSrc.fileNameBase(apiDst)}.last")
                    logMsg(msgLog, 1, 1)
                    resMsg += f"{msgLog}\n"
        if postaction == 'delete':
            msgLog = (f"{indent}Available {len(apiSrc.getPosts())-1}")
        else:
            msgLog = (f"{indent}Available {len(apiSrc.getPosts())}")
        logMsg(msgLog, 1, 1)

        return resMsg

    def executeAction(self, src, more, action,
                    noWait, timeSlots, simmulate, name="",
                    nextPost = True, pos = -1, delete=False):

        sys.path.append(path)
        from configMod import logMsg

        indent = f"    {name}->({action[3]}@{action[2]})] -> "+" "
        # The ']' is opened in executeRules FIXME

        msgLog = (f"{indent}Sleeping to launch all processes")
        logMsg(msgLog, 1, 0)
        # 'Cometic' waiting to allow all the processes to be launched.
        time.sleep(1)

        msgAction = (f"{action[0]} {action[3]}@{action[2]} "
                     f"({action[1]})")
        # Destination

        apiSrc = self.readConfigSrc(indent, src, more)

        if apiSrc.getName(): 
            msgLog = (f"{indent}Source: {apiSrc.getName()} ({src[3]}) -> "
                f"Action: {msgAction})")
        else:
            msgLog = (f"{indent}Source: {src[2]} ({src[3]}) -> "
                f"Action: {msgAction})")

        logMsg(msgLog, 1, 0)
        textEnd = (f"{msgLog}")

        # print(f"Srcccc: {src}")
        # print(f"Srcccc: {apiSrc.getNick()}")
        # return
        if (apiSrc.getHold() == 'yes'):
            time.sleep(1)
            msgHold = f"{indent} In hold"
            logging.info(msgHold)
            return msgHold
        if not apiSrc.getClient():
            msgLog = (f"{indent}Error. No client for {src[2]} ({src[3]})")
            logMsg(msgLog, 1, 1)
            return f"End: {msgLog}"

        apiSrc.setPosts()

        # print(f"apiSrc: {apiSrc}")
        # print(f"action: {action}")
        # print(f"more {more}")
        apiDst = self.readConfigDst(indent, action, more, apiSrc)
        if not apiDst.getClient():
            msgLog = (f"{indent}Error. No client for {action[2]}")
            logMsg(msgLog, 1, 1)
            return f"End: {msgLog}"

        apiDst.setUrl(apiSrc.getUrl())

        # print(f"{indent}action: {action}")
        # print(f"-->{indent}apiDst: {apiDst.getPostsType()} {action[1]}")
        # print(f"-->{indent}apiDst: {apiDst.getPostsType()[:-1]} {action[1]}")

        # print(f"-->{indent}apiDst: {apiDst.getPostsType()} {action[1]}")
        if ((apiDst.getPostsType() != action[1])
            and (apiDst.getPostsType()[:-1] != action[1])
            and (action[0] != 'cache')):
            # FIXME: Can we do better?
            return f"{indent}{action}"

        apiDst.setPosts()
        # print(f"Posttttts: {apiDst.getPosts()}")
        #FIXME: Is it always needed? Only in caches?

        indent = f"{indent} "

        apiSrc.setLastLink(apiDst)

        lastLink = apiSrc.getLastLinkPublished()
        lastTime = apiSrc.getLastTimePublished()

        time.sleep(1)
        if lastLink:
            msgLog = (f"Last link: {lastLink} ")
            logMsg(f"{indent}{msgLog}", 1, 1)

        msgLog = ''
        if lastTime:
            myTime = time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(lastTime))

            msgLog = (f"{msgLog}Last time: {myTime}")

        if nextPost:
            num = apiDst.getMax()
        else:
            num = 1

        msgLog = (f"{indent}{msgLog} Num: {num}")
        logMsg(msgLog, 1, 1)

        listPosts = []
        link = ''

        testDiffer = False

        if testDiffer:
            self.testDifferPosts(apiSrc, lastLink, listPosts)
            return

        if (num > 0):
            tNow = time.time()
            hours = float(apiDst.getTime())*60*60

            if lastTime:
                diffTime = tNow - lastTime
            else:
                # If there is no lasTime, we will publish
                diffTime = hours + 1

            msgLog = (f"{indent}Src time: {apiSrc.getTime()} "
                      f"Dst time: {apiDst.getTime()}")
            logMsg(msgLog, 2, 0)

            numAvailable = 0

            if (noWait or (diffTime>hours)):
                tSleep = random.random()*float(timeSlots)*60

                if nextPost:
                    post = apiSrc.getNextPost()
                else:
                    post = apiSrc.getPost(pos)

                if post:
                    apiSrc.setNextTime(tNow, tSleep, apiDst)
                else:
                    apiSrc.setNextAvailableTime(tNow, tSleep, apiDst)

                if (tSleep>0.0):
                    msgLog= f"{indent}Waiting {tSleep/60:2.2f} minutes"
                else:
                    tSleep = 2.0
                    msgLog= f"{indent}No Waiting"

                msgLog = f"{msgLog} for action: {msgAction}"
                logMsg(msgLog, 1, 1)

                for i in range(num):
                    time.sleep(tSleep)
                    if nextPost:
                        self.executePublishAction(indent, msgAction, apiSrc,
                                                apiDst, simmulate)
                    else:
                        self.executePublishAction(indent, msgAction, apiSrc,
                                                apiDst, simmulate, 
                                                nextPost, pos)

            elif (diffTime<=hours):
                msgLog = (f"Not enough time passed. "
                          f"We will wait at least "
                          f"{(hours-diffTime)/(60*60):2.2f} hours.")
                # logMsg(msgLog, 1, 1)
                textEnd = f"{textEnd} {msgLog}"

        else:
            if (num<=0):
                msgLog = (f"{indent}No posts available")
                logMsg(msgLog, 1, 1)

        return textEnd

    def executeRules(self, args):
        msgLog = "Execute rules"
        logMsg(msgLog, 1, 2)

        # print(args)
        select = args.checkBlog
        simmulate = args.simmulate

        import concurrent.futures

        delayedPosts = []
        # import pprint
        # pprint.pprint(self.rules)
        # textEnd = ""

        threads = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=75) as pool:
            i = 0
            previous = ""

            for src in sorted(self.rules.keys()):
                if src[0] != previous:
                    i = 0
                previous = src[0]
                name = f"{src[0]}{i}>"
                if src in self.more:
                    # f"  More: {self.more[src]}")
                    more = self.more[src]
                else:
                    # f"  More: empty")
                    more = None

                if src[0] in ['cache', 'gitter', 'gmail']:
                    srcName = more['url']
                    # FIXME 
                    if 'slack' in srcName:
                        srcName = f"Slack({srcName.split('/')[2].split('.')[0]})"
                    elif 'gitter' in srcName:
                        srcName = f"Gitter({srcName.split('/')[-2]})"
                    elif 'imgur' in srcName:
                        srcName = f"Imgur({srcName.split('/')[-1]})"
                    elif '.com' in srcName:
                        srcName = f"Gmail({srcName.split('.')[0]})"
                    text = (f"Source: {srcName} ({src[3]})")
                else:
                    text = (f"Source: {src[2]} ({src[3]})")
                textEnd = (f"Source: {name} {src[2]} {src[3]}")

                actions = self.rules[src]

                for k, action in enumerate(actions):
                    if (select and (select.lower() != f"{src[0].lower()}{i}")):
                        actionMsg = f"Skip."
                    else:
                        actionMsg = (f"Scheduling...")
                    nameA = f"{name} {actionMsg} "
                    if action[1].startswith('http'):
                        # FIXME
                        theAction = 'posts'
                    else:
                        theAction = action[1]

                    msgLog = (f"{nameA} {text} Action {k}:"
                              f" {action[3]}@{action[2]} ({theAction})")
                    textEnd = f"{textEnd}\n{msgLog}"
                    logMsg(msgLog, 1, 1)
                    nameA = f"{name} [({theAction})"
                    # The '[' is closed in executeAction TODO
                    if actionMsg == "Skip.":
                        continue
                    timeSlots = args.timeSlots
                    noWait = args.noWait

                    # Is this the correct place?
                    if ((action[0] in 'cache') or
                        ((action[0] == 'direct') and (action[2] == 'pocket'))
                        ):
                        # We will always load new items in the cache
                        timeSlots = 0
                        noWait=True

                    threads = threads + 1
                    delayedPosts.append(pool.submit(self.executeAction,
                                        src, more, action,
                                        noWait,
                                        timeSlots,
                                        args.simmulate,
                                        nameA))
                i = i + 1

            messages = []
            for future in concurrent.futures.as_completed(delayedPosts):
                try:
                    res = future.result()
                    msgLog = (f"End Delay: {res}")
                    logMsg(msgLog, 1, 1)
                    if res:
                        messages.append(
                                f"  Published in: {future}\n{res} "
                                )
                except Exception as exc:
                #else:
                    msgLog = (f"{future} generated an exception: {exc} "
                                 f"Src: {src}. Action: {action}")
                    logMsg(msgLog, 1, 1)
                    msgLog = (f"{sys.exc_info()}")
                    logMsg(msgLog, 1, 1)
                    import traceback
                    msgLog = (f"{traceback.print_exc()}")
                    logMsg(msgLog, 1, 1)


        msgLog = (f"End Execute rules with {threads} threads.")
        logMsg(msgLog, 1, 2)

        return


def main():

    logging.basicConfig(
        #filename=LOGDIR + "/rssSocial.log",
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s [%(filename).12s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    msgLog = "Launched at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    rules = moduleRules()
    srcs, dsts, ruls, impRuls = rules.checkRules()

    rules.printList(srcs, "Sources")
    rules.printList(dsts, "Destinations")
    print("Rules")
    for i,rul in enumerate(sorted(ruls)):
        print(f"{i}) {rul}")
        for j, action in enumerate(ruls[rul]):
                print(f"   └---->{j}) {action}")

    return

    # rules.printList(impRuls, "Implicit rules")

    # print("===========================================================")
    # for i,rul in enumerate(rules.available):
    #     print(f"{rul.upper()}({len( rules.available[rul]['data'])}) "
    #           f"{rules.available[rul]['name']}\n"
    #           f"{rules.available[rul]['data']}")


if __name__ == "__main__":
    main()
