import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import sys
import time
import urllib.parse

import socialModules
from socialModules.configMod import *

fileName = socialModules.__file__
path = f"{os.path.dirname(fileName)}"

sys.path.append(path)

hasSet = {}
hasPublish = {}
myModuleList = {}

class moduleRules:

    def checkRules(self, configFile = None, select=None):
        operation = "Checking Rules"
        msgLog = f"Start {operation}"
        logMsg(msgLog, 1, 2)
        config = configparser.ConfigParser()
        if not configFile:
            configFile = ".rssBlogs"
        configFile = f"{CONFIGDIR}/{configFile}"
        res = config.read(configFile)

        services = self.getServices()
        logging.debug(f" Services: {services}")
        indent = 3*"  "+4*" "

        srcs = []
        srcsA = []
        more = []
        dsts = []
        ruls = {}
        rulesNew = {}
        mor = {}
        impRuls = []
        for section in config.sections():
            if select and (section != select):
                continue
            url = config.get(section, "url")
            msgLog = f"  Section: {section} Url: {url}"
            logMsg(msgLog, 1, 1)
            self.indent = f"  {section}>"
            # Sources
            moreS = dict(config.items(section))
            moreSS = None
            # FIXME Could we avoid the last part for rules, 
            # selecting services here?
            if "rss" in config.options(section):
                #FIXME: Why is it managed separately?
                rss = config.get(section, "rss")
                msgLog = (f"{self.indent} Service rss -> {rss}")
                logMsg(msgLog, 2, 0)
                toAppend = ("rss", "set",
                            urllib.parse.urljoin(url, rss), "posts")
                srcs.append(toAppend)
                more.append(moreS)
            else:
                for service in services["regular"]:
                    if (
                        ("service" in config[section])
                        and (service == config[section]["service"])
                    ) or (url.find(service) >= 0):
                        methods = self.hasSetMethods(service)
                        for method in methods:
                            if service in config[section]:
                                nick = config[section][service]
                            else:
                                nick = url
                                if ((nick.find("slack") < 0)
                                        and (nick.find("gitter") < 0)):
                                    nick = nick.split("/")[-1]
                            if (service == 'imdb') or (service == 'imgur'):
                                nick = url
                            elif ('twitter' in url) or ('flickr' in url):
                                nick = url.split("/")[-1]
                            elif ('blsk' in url):
                                nick = url.split(".")[0]

                            if 'posts' in moreS:
                                if moreS['posts'] == method[1]:
                                   toAppend = (service, "set",
                                               nick, method[1])
                            else:
                               toAppend = (service, "set", nick, method[1])
                            if not (toAppend in srcs):
                                if (('posts' in moreS)
                                    and (moreS['posts'] == method[1])):
                                    srcs.append(toAppend)
                                    more.append(moreS)
                                else:
                                    # Available, but with no rules
                                    srcsA.append(toAppend)
            fromSrv = toAppend

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
            msgLog = f"{self.indent} Type posts [{postsType}]"
            logMsg(msgLog, 2, 0)
            if fromSrv:
                fromSrv = ( fromSrv[0], fromSrv[1], fromSrv[2], postsType,)
                for service in services["special"]:
                    toAppend = ""
                    if service in config.options(section):
                        valueE = config.get(section, service).split("\n")
                        for val in valueE:
                            nick = config.get(section, val)
                            if service == "direct":
                                url = "posts"
                            toAppend = (service, url, val, nick)
                            if toAppend not in dsts:
                                dsts.append(toAppend)
                            if toAppend:
                                if fromSrv not in mor:
                                    mor[fromSrv] = moreS
                                if fromSrv in ruls:
                                    if not toAppend in ruls[fromSrv]:
                                        ruls[fromSrv].append(toAppend)
                                else:
                                    ruls[fromSrv] = []
                                    ruls[fromSrv].append(toAppend)
                                if service == 'cache':
                                    hasSpecial = True

                self.indent = f"{self.indent}"
                for service in services["regular"]:
                    if (service == 'cache'):
                        continue
                    toAppend = ""
                    if service in config.options(section):
                        msgLog = (f"{self.indent} [{service}] "
                                  f"Checking service ")
                        logMsg(msgLog, 2, 0)
                        methods = self.hasPublishMethod(service)
                        msgLog = (f"{self.indent} [{service}] "
                                  f"Checking service methods")
                        logMsg(msgLog, 2, 0)
                        for method in methods:
                            if not method[1]:
                                mmethod = 'post'
                            else:
                                mmethod = method[1]
                            toAppend = (
                                    "direct",
                                    mmethod,
                                    service,
                                    config.get(section, service)
                                    )

                            if not (toAppend in dsts):
                                dsts.append(toAppend)
                            if toAppend:
                                if hasSpecial:
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
                                    else:
                                        ruls[fromSrvSp] = []
                                        ruls[fromSrvSp].append(toAppend)
                                else:
                                    if fromSrv not in mor:
                                        mor[fromSrv] = moreS
                                    if fromSrv in ruls:
                                        if not toAppend in ruls[fromSrv]:
                                            ruls[fromSrv].append(toAppend)
                                    else:
                                        ruls[fromSrv] = []
                                        ruls[fromSrv].append(toAppend)

            orig = None
            dest = None
            for key in moreS.keys():
                if key == 'service':
                    service = moreS[key]
                else:
                    service = key

                if not orig:
                    msgLog = (f"{self.indent} [{service}]")
                    if service in services['special']:
                        msgLog = (f"{msgLog} special") 
                        logMsg(msgLog, 2, 0)
                        orig = service
                    elif service in services['regular']:
                        msgLog = (f"{msgLog} regular") 
                        logMsg(msgLog, 2, 0)
                        orig = service
                    else:
                        msgLog = (f"{msgLog} not interesting") 
                        logMsg(msgLog, 2, 0)
                else:
                    if ((key in services['special'])
                        or (key in services['regular'])):
                        msgIni = (f"{self.indent} [{orig}]  ")
                        if key in ['cache', 'direct']:
                            dest = key
                        else:
                            if not dest:
                                dest = 'direct'
                            destRuleNew = ''
                            destRuleCache = ''
                            fromCacheNew = ''
                            if dest == 'direct':
                                destRule = (dest, 'post', key, moreS[key])
                            else:
                                destRule = (dest, moreS['url'],
                                            key, moreS[key])
                                destRuleNew = (dest, moreS['service'],
                                               ('direct', 'post',
                                            key, moreS[key]), moreS['url'])
                                # Rule cache:
                                if 'posts' in moreS:
                                    myPosts = moreS['posts']
                                else:
                                    myPosts = 'posts'
                                fromCache = ('cache', (moreS['service'],
                                                       moreS['url']),
                                             f"{key}@{moreS[key]}", 'posts')
                                fromCacheNew = ('cache', moreS['service'],
                                                ('direct', 'post',
                                                    key, moreS[key]),
                                                       moreS['url'])#, 'posts'),
                                                #f"{key}@{moreS[key]}")
                                #FIXME: It is needed for imgur, in the other
                                # cases is OK
                                destRuleCache = ('direct', 'post',
                                                 key, moreS[key])
                                if fromCacheNew:
                                    if not (fromCacheNew in rulesNew):
                                        rulesNew[fromCacheNew] = []
                                    rulesNew[fromCacheNew].append(destRuleCache)
                                    mor[fromCacheNew] = moreS

                            if fromSrv:
                                # msgLog = (f"{msgIni} Action: -> {key}"
                                #           f"({fromSrv[3]})")
                                # logMsg(msgLog, 2, 0)
                                msgLog = (f"{msgIni} Source: {fromSrv[2]} "
                                          f"({fromSrv[3]}) ({fromSrv})")
                                logMsg(msgLog, 2, 0)
                                msgLog = (f"{msgIni}  Action: {destRule[3]}@"
                                          f"{destRule[2]} {destRule[1]} "
                                          f"({destRule})")
                                logMsg(msgLog, 2, 0)
                            # msgLog = (f"{msgIni}  from Srv: {fromSrv}")
                            # logMsg(msgLog, 2, 0)
                            # msgLog = (f"{msgIni}  dest Rule: {destRule}")
                            # logMsg(msgLog, 2, 0)
                            if fromSrv:
                                if not (fromSrv in rulesNew):
                                    rulesNew[fromSrv] = []
                                if destRuleNew:
                                    rulesNew[fromSrv].append(destRuleNew)
                                else:
                                    rulesNew[fromSrv].append(destRule)

        # Now we can add the sources not added.

        for src in srcsA:
            if not src in srcs:
                srcs.append(src)
                more.append({})

        # Now we can see which destinations can be also sources

        self.indent = f" Destinations:"
        for dst in dsts:
            if dst[0] == "direct":
                service = dst[2]
                #FIXME 
                methods = self.hasSetMethods(service)
                for method in methods:
                    toAppend = (service, "set", dst[3], method[1])#, dst[4])
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
        for i, src in enumerate(rulesNew.keys()):
            if not src:
                continue
            iniK, nameK = self.getIniKey(self.getNameRule(src).upper(),
                                         myKeys, myIniKeys)
            if not (iniK in available):
                available[iniK] = {"name": self.getNameRule(src),
                                   "data": [], "social": []}
                available[iniK]["data"] = [{'src': src, 'more': more[i]}]
            else:
                available[iniK]["data"].append({'src': src,
                                                'more': more[i]})

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

        msgLog = f"End {operation}"
        logMsg(msgLog, 1, 2)

        msgLog = (f"RulesNew: {rulesNew}")
        logMsg(msgLog, 2, 0)

        if hasattr(self, 'args') and self.args.rules:
            self.printDict(rulesNew, "Rules")
        sys.exit

        self.rules = rulesNew
        self.more = mor


    def selectActionInteractive(self, service = None):
        if not service:
            nameModule = os.path.basename(inspect.stack()[1].filename)
            service = nameModule.split('.')[0][6:].casefold()
        indent = ""
        selActions = self.selectAction(service)

        print(f"Actions:")
        for i, act in enumerate(selActions):
            print(f"{i}) {act}")
        iAct = input("Which action? ")
        src = selActions[int(iAct)]
        apiDst = self.readConfigDst(indent, act, None, None)

        return apiDst

    def selectRuleInteractive(self, service = None):
        if not service:
            nameModule = os.path.basename(inspect.stack()[1].filename)
            service = nameModule.split('.')[0][6:].casefold()
        indent = ""
        selRules = self.selectRule(service, '')
        print(f"Rules:")
        if len(selRules)>1:
            for i, rul in enumerate(selRules):
                print(f"{i}) {rul}")
            iRul = input("Which rule? ")
        else:
            iRul = 0
        src = selRules[int(iRul)]
        apiSrc = self.readConfigSrc("", src, self.more[src])

        return apiSrc

    def selectAction(self, name = "", selector2 = "", selector3 = ""):
        if hasattr(self, 'indent'):
            indent = self.indent
        else:
            indent = ""
        srcR = None

        actions = []
        for src in self.rules.keys():
            for act in self.rules[src]:
                if (self.getNameAction(act).capitalize() == name.capitalize()):
                    logging.debug(f"Action: {act}")
                    actions.append(act)

        return actions

    def selectRule(self, name = "", selector2 = "", selector3 = ""):
        if hasattr(self, 'indent'):
            indent = self.indent
        else:
            indent = ""
        srcR = None

        rules = []
        for src in self.rules.keys():
            if self.getNameRule(src).capitalize() == name.capitalize():
                more = self.more[src]
                srcR = src
                logging.debug(f"profileR: {self.getProfileRule(src)}")
                logging.debug(f"profileR: {self.getProfileAction(src)}")
                if not selector2:
                    rules.append(src)
                else:
                    if (selector2 == self.getProfileAction(src)):
                        #FIXME: ??
                        logging.debug(f"Second Selector: {selector2}")
                        if not selector3:
                            rules.append(src)
                        elif  (selector3 in self.getTypeRule(src)):
                            rules.append(src)
        return rules

    def hasSetMethods(self, service):
        msgIni = f"{self.indent} [{service}] service"
        msgLog = f"{msgIni} checking set methods"
        logMsg(msgLog, 2, 0)
        if service == "social":
            return []

        if service in hasSet:
            msgLog = f"{msgIni} cached"
            logMsg(msgLog, 2, 0)
            listMethods = hasSet[service]
        else:
            clsService = getModule(service, self.indent)
            listMethods = clsService.__dir__()
            hasSet[service] = listMethods

        methods = []
        for method in listMethods:
            if (not method.startswith("__")) and (method.find("set") >= 0):
                action = "set"
                target = ""
                #FIXME: indenting inside modules?
                try:
                    myModule = eval(f"clsService.{method}.__module__")
                    myModuleList[(service, method)] = myModule
                except:
                    myModule = myModuleList[(service, method)]


                if method.find("Api") >= 0:
                    target = method[len("setApi"):].lower()
                # elif (clsService.setPosts.__module__
                elif myModule == f"module{service.capitalize()}":
                    target = method[len("set"):].lower()
                if target and (target.lower()
                               in ["posts", "drafts", "favs",
                                   "messages", "queue", "search"]
                              ):
                    toAppend = (action, target)
                    if not (toAppend in methods):
                        methods.append(toAppend)

        msgLog = (f"{self.indent} [{service}] service has set {methods}")
        logMsg(msgLog, 2, 0)

        return methods

    def hasPublishMethod(self, service):
        msgLog = (f"{self.indent} [{service}] " 
                  f"Checking service publish methods")
        logMsg(msgLog, 2, 0)
        if service in hasPublish:
            msgLog = f"{self.indent} [{service}] service cached"
            logMsg(msgLog, 2, 0)
            listMethods = hasPublish[service]
        else:
            clsService = getModule(service, self.indent)
            listMethods = clsService.__dir__()
            hasPublish[service] = listMethods

        methods = []
        target = None
        for method in listMethods:
            if method.find("publish") >= 0:
                action = "publish"
                target = ""
                if method.find("Api") >= 0:
                    target = method[len("publishApi"):].lower()
                else: 
                    target = method[len("publish"):].lower()
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

        modules['regular'].append('cache')
        # cache objects can be considered as regular for publishing elements
        # stored there

        return modules

    def printDict(self, myList, title):
        print(f"{title}:")
        for i, element in enumerate(myList):
            if type(myList[element]) == list:
                self.printList(myList[element], element)
            else:
                print(f"  {i}) {element} {myList[element]}")
        print(f"End {title}")

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

    def cleanUrlRule(self, url, service=''):
        #FIXME: does it belong here?
        if service:
            url = url.replace(service, '')
        url = url.replace('https', '').replace('http','')
        url = url.replace('---','').replace('.com','')
        url = url.replace('-(','(').replace('- ',' ')
        url = url.replace(':','').replace('/','')
        return url

    def getNickSrc(self, action):
        src = self.getActionComponent(action, 0)
        return src

    def getNickAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            nick = self.getActionComponent(self.getActionComponent(action, 2),
                                           3)
        else:
            nick = self.getActionComponent(action, 3)
        return nick

    def getNameAction(self, action):
        res = self.getActionComponent(action, 0)
        if res == 'direct':
            res = self.getActionComponent(action, 2)
        return res

    def getTypeAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            action = self.getActionComponent(action, 0)
        else:
            action = self.getActionComponent(action, 1)
        return action

    def getDestAction(self, action):
        profile = ''
        if isinstance(self.getActionComponent(action, 2), tuple):
            profile = action[1:]
        else:
            profile = self.getActionComponent(action, 3)

        return profile

    def getProfileAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            profile = self.getActionComponent(self.getActionComponent(action, 2), 2)
        else:
            profile =self.getActionComponent(action, 2)
        return profile

    def getRuleComponent(self, rule, pos):
        res = ''
        if isinstance(rule, tuple) :
            res = rule[pos]
        return res

    def getNameRule(self, rule):
        return self.getRuleComponent(rule, 0)

    def getSecondNameRule(self, rule):
        res = ''
        if self.getNameRule(rule) == 'cache':
            res = self.getRuleComponent(rule, 1)
        else:
            res = self.getRuleComponent(rule, 0)
        return res

    def getTypeRule(self, rule):
        res = 'post'
        if self.getNameRule(rule) == 'cache':
            res = 'cache'
        else:
            res = self.getRuleComponent(rule, 3)
        return res

    def getIdRule(self, rule):
        idR = ''
        if isinstance(self.getRuleComponent(rule, 2), tuple):
            subC = self.getRuleComponent(rule, 2)
            idR = f"{self.getRuleComponent(subC, 3)}@{self.getRuleComponent(subC, 2)}@{self.getRuleComponent(rule, 0)}[{self.getRuleComponent(rule, 3)}]" #@{self.getRuleComponent(rule, 0)}]"
        else:
            idR = f"{self.getRuleComponent(rule, 2)}@{self.getNameRule(rule)}"
        return idR

    def getProfileRule(self, rule):
        profileR = ''
        if isinstance(self.getRuleComponent(rule, 2), tuple):
            profileR = rule[1:]
        else:
            profileR = self.getRuleComponent(rule, 2)
        return profileR

    def getNickRule(self, rule):
        if isinstance(self.getRuleComponent(rule, 2), tuple):
            res = self.getRuleComponent(rule, 3)
        else:
            res = self.getRuleComponent(rule, 2)
        return res

    def clientErrorMsg(self, indent, api, typeC, rule, action):
        msgLog = ""
        if not 'rss' in rule:
            msgLog = (f"{indent} {typeC} Error. "
                      f"No client for {rule} ({action}). End.")
        return f"{msgLog}"

    def readConfigSrc(self, indent, src, more):
        msgLog = f"{indent} Start readConfigSrc" #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent} "

        apiSrc = getApi(self.getNameRule(src), 
                        self.getProfileRule(src), indent)
        if self.getNameRule(src) == 'cache':
            apiSrc.fileName = apiSrc.fileNameBase(src[1:])
            apiSrc.postaction = 'delete'
        else:
            apiSrc.setPostsType('posts')

        apiSrc.setMoreValues(more)

        indent = indent[:-1]
        msgLog = f"{indent} End readConfigSrc" #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent[:-1]}"
        return apiSrc

    def getActionComponent(self, action, pos):
        res = ''
        if isinstance(action, tuple) and (len(action)==4):
            res = action[pos]
        return res

    def readConfigDst(self, indent, action, more, apiSrc):
        msgLog = f"{indent} Start readConfigDst" #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent} "
        
        apiDst = getApi(self.getNameAction(action),
                        self.getDestAction(action), indent)
        if self.getNameAction(action) == 'cache':
            apiDst.fileName = apiDst.fileNameBase(action[1:])
            apiDst.postaction = 'delete'
        else:
            apiDst.setPostsType('posts')

        apiDst.setMoreValues(more)

        if apiSrc:
            apiDst.setUrl(apiSrc.getUrl())
        else:
            apiDst.setUrl(None)

        indent = indent[:-1]
        msgLog = f"{indent} End readConfigDst" #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent[:-1]}"
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
        # print(f"{indent} {listPosts}")
        if listPosts2:
            if (listPosts == listPosts2):
                print("{indent} Equal listPosts")
            else:
                print(f"{indent} Differ listPosts (len {len(listPosts[0])}, "
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

    def executePostAction(self, indent, msgAction, apiSrc, apiDst,
                            simmulate, nextPost, pos, res):
        resPost = ''
        resMsg = ''
        msgLog = (f"{indent}Trying to excecute Post Action")
        logMsg(msgLog, 1, 1)
        postaction = apiSrc.getPostAction()
        if postaction:
            msgLog = (f"{indent}Post Action {postaction} "
                      f"(nextPost = {nextPost})")
            logMsg(msgLog, 1, 1)

            if 'OK. Published!' in res:
                msgLog = (f"{indent} Res {res} is OK")
                logMsg(msgLog, 1, 0)
                if nextPost:
                    msgLog = (f"{indent}Post Action next post")
                    logMsg(msgLog, 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost()
                else:
                    msgLog = (f"{indent}Post Action pos post")
                    logMsg(msgLog, 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
                    # FIXME inconsistent
            msgLog = (f"{indent}End {postaction}, reply: {resPost} ")
            logMsg(msgLog, 1, 1)
            resMsg += f" Post Action: {resPost}"
            if ((res and (not 'failed!' in res) and (not 'Fail!' in res))
                or (res and ('abusive!' in res))
                or (((not res) and (not 'OK. Published!' in res))
                    or ('duplicate' in res))):
                msgLog = (f"{indent} Res {res} is not OK")
                #FIXME Some OK publishing follows this path (mastodon, linkedin, ...)
                logMsg(msgLog, 1, 0)

                if nextPost:
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost()
                else:
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
                # FIXME inconsistent
                msgLog = (f"{indent}Post Action command {cmdPost}")
                logMsg(msgLog, 1, 1)
                msgLog = (f"{indent}End {postaction}, reply: {resPost} ")
                logMsg(msgLog, 1, 1)
                resMsg += f"Post Action: {resPost}"
            else:
                msgLog = (f"{indent}No Post Action")
                logMsg(msgLog, 1, 1)

            return resMsg

    def executePublishAction(self, indent, msgAction, apiSrc, apiDst,
                            simmulate, nextPost=True, pos=-1):
        res = ''

        msgLog = (f"{indent} End Waiting.")
        logMsg(msgLog, 1, 1)

        # The source of data can have changes while we were waiting
        resMsg = ''
        postaction = ''
        apiSrc.setPosts()
        if nextPost:
            msgLog = (f"next post in service {apiDst.service}")
            post = apiSrc.getNextPost()
        else:
            msgLog = (f"post in pos {pos} in service {apiDst.service}")
            post = apiSrc.getPost(pos)
        if post:
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            resMsg = f"Publish result: {res}"
            msgLog = f"Title: {title}."
            if link:
                msgLog = (f"{msgLog} Recording Link: {link} "
                          f"in file {apiSrc.fileNameBase(apiDst)}.last")
        else:
            msgLog = f"{indent}No post to schedule with {msgLog}."

        if simmulate:
            if post:
                msgLog = f"{indent}Would schedule {msgLog} "
            logMsg(msgLog, 1, 1)

            indent = f"{indent[:-1]}"
            resMsg = ""
        else:
            res = ''
            if post:
                res = apiDst.publishPost(api = apiSrc, post = post)
                msgLog = f"{indent}Reply: {res}"
                msgLog = f"{indent}Trying to publish {msgLog} "
                # print(f"{indent}res: {res}")
                if (nextPost
                    and (res
                    and not ('Fail!' in res)
                    and not ('failed!' in res))):
                    #((not res) or ('SAVELINK' in res) or
                    #              (not ('Fail!' in res)) or
                    #              (not ('failed!' in res)))):
                    resUpdate = apiSrc.updateLastLink(apiDst, '')
                    resMsg += f" Update: {resUpdate}"

            logMsg(msgLog, 1, 1)
            # msgLog = (f"{indent} Res enddddd: {res}")
            # logMsg(msgLog, 2, 0)
            if res:
                msgLog = f"{indent}Res: {res} "
                logMsg(msgLog, 2, 0)
            if post:
                resMsg = self.executePostAction(indent, msgAction,
                                                apiSrc, apiDst,
                                                simmulate, nextPost,
                                                pos, res)
            msgLog = (f"{indent}End publish, reply: {resMsg}")
            logMsg(msgLog, 1, 1)
        if postaction == 'delete':
            #FIXME: not always len is the available number. We should consider
            # the last published and so on.
            msgLog = (f"{indent}Available {len(apiSrc.getPosts())-1}")
        else:
            msgLog = (f"{indent}Available {len(apiSrc.getPosts())}")
        logMsg(msgLog, 1, 1)

        return resMsg

    def executeAction(self, src, more, action,
                    noWait, timeSlots, simmulate, name="",
                    numAct = 1, nextPost = True, pos = -1, delete=False):

        indent = f"{name}"

        numAct = max(3, numAct) # Less than 3 is too small
        tL = random.random()*numAct
        msgLog = (f"{indent}  Sleeping {tL:.2f} seconds ({numAct} actions) "
                  f"to launch all processes") 
        logMsg(msgLog, 1, 0)
        # 'Cosmetic' waiting to allow all the processes to be launched.
        # Randomization is a way to avoid calling several times the same
        # service (almost) as the same time.
        time.sleep(tL)

        msgLog = (f"{indent}  Go!")
        logMsg(msgLog, 1, 0)
        indent = f"{indent} "

        # Source
        apiSrc = self.readConfigSrc(indent, src, more)
        if not apiSrc.getClient():
            msgLog = self.clientErrorMsg(indent, apiSrc, "Source",
                                      self.getProfileRule(src),
                                      self.getNickAction(src))
            if msgLog:
                logMsg(msgLog, 3, 1)
            return f"{msgLog} End."

        if apiSrc.getName():
            theName = apiSrc.getName()
        else:
            theName = self.getProfileAction(src)

        msgAction = (f"{self.getNameAction(action)} "
                     f"{self.getNickAction(action)}@"
                     f"{self.getProfileAction(action)} "
                     f"({self.getTypeAction(action)})")
        msgLog = (f"Source: {theName}-{self.getNickAction(src)} "
                  f"-> Action: {msgAction}")

        res = ""
        textEnd = (f"{msgLog}")

        # Destination
        apiDst = self.readConfigDst(indent, action, more, apiSrc)
        if not apiDst.getClient():
            msgLog = self.clientErrorMsg(indent, apiDst, "Destination",
                                      (f"{self.getNameAction(action)}@"
                                       f"{self.getDestAction(action)}"),
                                      self.getNickAction(action))
            if msgLog:
                logMsg(msgLog, 3, 1)
                sys.stderr.write(f"Error: {msgLog}\n")
            return f"End: {msgLog}"

        indent = f"{indent} "

        apiSrc.setLastLink(apiDst)

        if apiSrc.getPostsType() == 'drafts':
            #FIXME
            apiDst.setPostsType('drafts')

        time.sleep(1)

        msgLog = ''
        if nextPost:
            num = apiDst.getMax()
        else:
            num = 1

        msgLog = (f"{indent} I'll publish {num} post in {apiDst.getService()}")
        logMsg(msgLog, 1, 1)

        if (num > 0):
            tNow = time.time()
            hours = float(apiDst.getTime())*60*60

            lastTime = apiSrc.getLastTimePublished(f"{indent} ")

            if lastTime:
                diffTime = tNow - lastTime
            else:
                # If there is no lasTime, we will publish
                diffTime = hours + 1

            numAvailable = 0

            if (noWait or (diffTime>hours)):
                tSleep = random.random()*float(timeSlots)*60

                apiSrc.setNextTime(tNow, tSleep, apiDst)

                if (tSleep>0.0):
                    msgLog= f"{indent} Waiting {tSleep/60:2.2f} minutes"
                else:
                    tSleep = 2.0
                    msgLog= f"{indent} No Waiting"

                msgLog = f"{msgLog} for action." #: {msgAction}"
                logMsg(msgLog, 1, 1)

                for i in range(num):
                    time.sleep(tSleep)
                    res = self.executePublishAction(indent, msgAction,
                                                    apiSrc, apiDst,
                                                    simmulate,
                                                    nextPost, pos)
            elif (diffTime<=hours):
                msgLog = (f"{indent} Not enough time passed. "
                          f"We will wait at least "
                          f"{(hours-diffTime)/(60*60):2.2f} hours.")
                logMsg(msgLog, 1, 1)
                textEnd = f""

        else:
            if (num<=0):
                msgLog = (f"{indent} No posts available")
                logMsg(msgLog, 1, 1)

        indent = f"{indent[:-1]}"
        logMsg(f"{indent} End executeAction {textEnd}", 2, 0)
        return f"{indent} {res} {textEnd}"


    def executeRules(self):
        msgLog = "Start Executing rules"
        logMsg(msgLog, 1, 2)
        indent = " "

        args = self.args
        select = args.checkBlog
        simmulate = args.simmulate

        delayedPosts = []

        threads = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=75) as pool:
            i = 0
            previous = ""

            for src in sorted(self.rules.keys()):
                if (self.getNameAction(src) != previous):
                    i = 0
                else:
                    i = i + 1
                previous = self.getNameAction(src)

                nameAction =f"[{self.getNameAction(src)}{i}]"
                indent = f"{nameAction:->12}>"

                if src in self.more:
                    if (('hold' in self.more[src])
                        and (self.more[src]['hold'] == 'yes')):
                        msgHold = f"{indent} On hold."
                        logMsg(msgHold,1, 0)
                        continue

                if src in self.more:
                    more = self.more[src]
                else:
                    more = None

                if self.getNameAction(src) in ['cache']:
                    srcName = src[2][2]
                    # FIXME Better access?

                    # FIXME Names?
                    if 'slack' in srcName:
                        srcName = (f"{srcName.split('/')[2].split('.')[0]}"
                                  f"@slack")
                    elif 'gitter' in srcName:
                        srcName = f"{srcName.split('/')[-2]}@gitter"
                    elif 'imgur' in srcName:
                        srcName = f"{srcName.split('/')[-1]}@imgur"
                    elif '.com' in srcName:
                        if 'gmail' in more:
                            srcName = more['gmail']
                        srcName = f"{srcName}@gmail"
                else:
                    #FIXME self.identifier
                    srcName = self.getProfileRule(src)
                    if 'slack' in srcName:
                        srcName = f"{srcName.split('/')[2].split('.')[0]}"
                    elif 'imgur' in srcName:
                        srcName = more['url']
                        srcName = f"{srcName.split('/')[-1]}"
                    elif 'gitter' in srcName:
                        srcName = f"{srcName.split('/')[-2]}"
                    elif ((not srcName)
                          and ('tumblr' in self.getNameAction(src))):
                        srcName = more['url']
                        srcName = f"{srcName.split('/')[2].split('.')[0]}"
                msgIni = (f"Source: {srcName} ({self.getNickAction(src)})")

                actions = self.rules[src]

                # print(f"Select: {select} - {src[0]}{i}")
                if (select and
                    (select.lower() !=
                     f"{self.getNameRule(src).lower()}{i}")):
                    actionMsg = f"Skip."
                else:
                    actionMsg = (f"Scheduling.")
                msgLog = f"{indent} {msgIni}"
                logMsg(msgLog, 1, 1)
                indent = f"{indent} "
                msgLog = f"{indent} {actionMsg}"
                logMsg(msgLog, 1, 1)
                if actionMsg == "Skip.":
                    #FIXME ?
                    continue
                for k, action in enumerate(actions):
                    name = f"{self.getNameRule(src)}{i}>"
                    theAction = 'posts'
                    if not self.getTypeAction(action).startswith('http'):
                        theAction = self.getTypeAction(action)

                    indent = f"{indent} "
                    msgLog = (f"{indent} Action {k}:"
                             f" {self.getNickAction(action)}@"
                             f"{self.getProfileAction(action)} ({theAction})")
                    name = f"Action {k}:" # [({theAction})"
                    nameA = f"{actionMsg} "
                    textEnd = (f"Source: {nameA} {self.getProfileRule(src)} "
                               f"{self.getNickRule(src)}")
                    logMsg(msgLog, 1, 1)
                    textEnd = f"{textEnd}\n{msgLog}"
                    nameA = f"{indent} {name}"
                    if actionMsg == "Skip.":
                        #FIXME "In hold"
                        continue
                    timeSlots = args.timeSlots
                    noWait = args.noWait

                    # Is this the correct place?
                    if ((self.getNameAction(action) in 'cache') or
                        ((self.getNameAction(action) == 'direct')
                         and (self.getProfileAction(action) == 'pocket'))
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
                                        name = nameA, numAct=len(actions)))
                    indent = f"{indent[:-1]}"
                indent = f"{indent[:-1]}"


            messages = []
            for future in concurrent.futures.as_completed(delayedPosts):
                try:
                    res = future.result()
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


        #FIXME: We are not using messages
        msgLog = (f"End Executing rules with {threads} threads.")
        logMsg(msgLog, 1, 2)

        return

    def readArgs(self):

        import argparse

        parser = argparse.ArgumentParser(
            description="Improving command line call", allow_abbrev=True
        )
        parser.add_argument(
            "--timeSlots",
            "-t",
            default=50,  # 50 minutes
            help=("How many time slots we will have for publishing "
                 f"(in minutes)"),
            )
        parser.add_argument(
            "checkBlog",
            default="",
            metavar="Blog",
            type=str,
            nargs="?",
            help="you can select just a blog",
        )
        parser.add_argument(
            "--simmulate",
            "-s",
            default=False,
            action="store_true",
            help="simulate which posts would be added",
        )
        parser.add_argument(
            "--noWait",
            "-n",
            default=False,
            action="store_true",
            help="no wait for time restrictions",
        )
        parser.add_argument(
            "--rules",
            "-r",
            default=False,
            action="store_true",
            help="Show the list of rules and actions",
        )
        self.args = parser.parse_args()

def main():

    mode = logging.DEBUG
    logging.basicConfig(filename=f"{LOGDIR}/rssSocial.log",
                        # stream=sys.stdout,
                        level=mode,
                        format="%(asctime)s [%(filename).12s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        )

    rules = moduleRules()

    rules.readArgs()
    rules.checkRules()
    rules.executeRules()

    return

if __name__ == "__main__":
    main()
