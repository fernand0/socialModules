import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import sys
import time

import socialModules
from socialModules.configMod import logMsg, getApi, getModule, CONFIGDIR, LOGDIR, select_from_list

fileName = socialModules.__file__
path = f"{os.path.dirname(fileName)}"

sys.path.append(path)

hasSet = {}
hasPublish = {}
myModuleList = {}


class moduleRules:
    def indentPlus(self):
        if not hasattr(self, "indent"):
            self.indent = " "
        else:
            self.indent = f"{self.indent} "

    def indentLess(self):
        self.indent = self.indent[:-1]

    def checkRules(self, configFile=None, select=None):
        msgLog = "Checking rules"
        logMsg(msgLog, 1, 2)
        config = configparser.ConfigParser()
        if not configFile:
            configFile = ".rssBlogs"
        configFile = f"{CONFIGDIR}/{configFile}"
        config.read(configFile)

        self.indentPlus()
        services = self.getServices()
        logging.debug(f"{self.indent}Services: {services}")
        services["regular"].append("cache")
        # cache objects can be considered as regular for publishing elements
        # stored there

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
            msgLog = f" Section: {section} Url: {url}"
            logMsg(msgLog, 1, 1)
            self.indent = f"  {section}>"
            toAppend = ""
            # Sources
            moreS = dict(config.items(section))
            # moreSS = None
            # FIXME Could we avoid the last part for rules,
            # selecting services here?
            for service in services["regular"]:
                if ("service" in config[section]) and (
                    service == config[section]["service"]
                ):
                    msgLog = f"{self.indent} Service: {service}"
                    logMsg(msgLog, 1, 1)
                    theService = service
                    api = getModule(service, self.indent)
                    api.setUrl(url)
                    if service in config[section]:
                        serviceData = config.get(section, service)
                        api.setService(service, serviceData)
                        # nameGet = f"get{service.capitalize()}"
                        # if nameGet in api.__dir__():
                        #     cmd = getattr(api, nameGet)

                    if service in config[section]:
                        api.setNick(config[section][service])
                    else:
                        api.setNick()

                    self.indentPlus()
                    msgLog = f"{self.indent} Nick: {api.getNick()}"
                    logMsg(msgLog, 2, 0)

                    methods = self.hasSetMethods(service)
                    msgLog = (f"{self.indent} Service {service} has " 
                              f"set {methods}")
                    logMsg(msgLog, 2, 0)
                    for method in methods:
                        if "posts" in moreS:
                            if moreS["posts"] == method[1]:
                                toAppend = (theService, "set", api.getNick(), method[1])
                        else:
                            toAppend = (theService, "set", api.getNick(), method[1])
                        if toAppend not in srcs:
                            if ("posts" in moreS) and (moreS["posts"] == method[1]):
                                srcs.append(toAppend)
                                more.append(moreS)
                            else:
                                # Available, but with no rules
                                srcsA.append(toAppend)
            fromSrv = toAppend
            msgLog = f"{self.indent} We will append: {toAppend}"
            logMsg(msgLog, 2, 0)
            if toAppend:
                service = toAppend[0]

            # if "time" in config.options(section):
            #     timeW = config.get(section, "time")
            # else:
            #     timeW = 0
            # if "buffermax" in config.options(section):
            #     bufferMax = config.get(section, "buffermax")
            # else:
            #     bufferMax = 0
            # if "max" in config.options(section):
            #     bufferMax = config.get(section, "max")

            # Destinations
            hasSpecial = False
            if "posts" in config[section]:
                postsType = config[section]["posts"]
            else:
                postsType = "posts"
            msgLog = f"{self.indent} Type {postsType}"
            logMsg(msgLog, 2, 0)
            if fromSrv:
                fromSrv = (
                    fromSrv[0],
                    fromSrv[1],
                    fromSrv[2],
                    postsType,
                )
                for serviceS in services["special"]:
                    toAppend = ""
                    if serviceS in config.options(section):
                        valueE = config.get(section, serviceS).split("\n")
                        for val in valueE:
                            if val in config[section]:
                                nick = config.get(section, val)
                            else:
                                nick = api.getNick()
                            if serviceS == "direct":
                                url = "posts"
                            toAppend = (serviceS, url, val, nick)  # , timeW, bufferMax)
                            if toAppend not in dsts:
                                if "service" not in toAppend:
                                    dsts.append(toAppend)
                            if toAppend:
                                if fromSrv not in mor:
                                    mor[fromSrv] = moreS
                                if fromSrv in ruls:
                                    if toAppend not in ruls[fromSrv]:
                                        ruls[fromSrv].append(toAppend)
                                else:
                                    ruls[fromSrv] = []
                                    ruls[fromSrv].append(toAppend)

                                if serviceS == "cache":
                                    hasSpecial = True

                msgLog = f"{self.indent} Checking actions for {service}"
                logMsg(msgLog, 2, 0)
                self.indentPlus()
                for serviceD in services["regular"]:
                    if (
                        (serviceD == "cache")
                        or (serviceD == "xmlrpc")
                        or (serviceD == theService)
                    ):
                        continue
                    toAppend = ""
                    if serviceD in config.options(section):
                        msgLog = (
                            f"{self.indent} Service {service} -> {serviceD} checking "
                        )
                        logMsg(msgLog, 2, 0)
                        self.indentPlus()
                        methods = self.hasPublishMethod(serviceD)
                        msgLog = (
                            f"{self.indent} Service {serviceD} has "
                            f"publish {methods}"
                        )
                        logMsg(msgLog, 2, 0)
                        self.indentLess()
                        for method in methods:
                            if not method[1]:
                                mmethod = "post"
                            else:
                                mmethod = method[1]
                            toAppend = (
                                "direct",
                                mmethod,
                                serviceD,
                                config.get(section, serviceD),
                            )

                            if toAppend not in dsts:
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
                                        if toAppend not in ruls[fromSrvSp]:
                                            ruls[fromSrvSp].append(toAppend)
                                    else:
                                        ruls[fromSrvSp] = []
                                        ruls[fromSrvSp].append(toAppend)
                                else:
                                    if not (
                                        fromSrv[2] != toAppend[3]
                                        and fromSrv[3][:-1] != toAppend[1]
                                    ):
                                        # We do not want to add the origin as
                                        # destination
                                        if fromSrv not in mor:
                                            mor[fromSrv] = moreS
                                        if fromSrv in ruls:
                                            if toAppend not in ruls[fromSrv]:
                                                ruls[fromSrv].append(toAppend)
                                        else:
                                            ruls[fromSrv] = []
                                            ruls[fromSrv].append(toAppend)

            orig = None
            dest = None
            for key in moreS.keys():
                if key == "service":
                    service = moreS[key]
                else:
                    service = key

                if not orig:
                    if service in services["special"]:
                        msgLog = f"{self.indent} Service {service} special"
                        logMsg(msgLog, 2, 0)
                        orig = service
                    elif service in services["regular"]:
                        msgLog = f"{self.indent} Service {service} regular"
                        logMsg(msgLog, 2, 0)
                        orig = service
                    else:
                        msgLog = f"{self.indent} Service {service} not interesting"
                        logMsg(msgLog, 2, 0)
                else:
                    if (key in services["special"]) or (key in services["regular"]):
                        if key == "cache":
                            msgLog = f"{self.indent} Rules: {key}"
                            logMsg(msgLog, 2, 0)
                            dest = key
                        elif key == "direct":
                            msgLog = f"{self.indent} Rules: {key}"
                            logMsg(msgLog, 2, 0)
                            dest = key
                        elif self.hasPublishMethod(key):
                            # If it has no publish methods it can not be a
                            # destination
                            if not dest:
                                dest = "direct"
                            destRuleNew = ""
                            destRuleCache = ""
                            fromCacheNew = ""
                            if dest == "direct":
                                destRule = (dest, "post", key, moreS[key])
                            else:
                                destRule = (dest, moreS["url"], key, moreS[key])
                                destRuleNew = (
                                    dest,
                                    moreS["service"],
                                    ("direct", "post", key, moreS[key]),
                                    moreS["url"],
                                )
                                # Rule cache:
                                #if "posts" in moreS:
                                #    myPosts = moreS["posts"]
                                #else:
                                #    myPosts = "posts"
                                # fromCache = (
                                #     "cache",
                                #     (moreS["service"], moreS["url"]),
                                #     f"{key}@{moreS[key]}",
                                #     "posts",
                                # )
                                fromCacheNew = (
                                    "cache",
                                    moreS["service"],
                                    ("direct", "post", key, moreS[key]),
                                    moreS["url"],
                                )  # , 'posts'),
                                # f"{key}@{moreS[key]}")
                                # FIXME: It is needed for imgur, in the other
                                # cases is OK
                                destRuleCache = ("direct", "post", key, moreS[key])
                                if fromCacheNew and destRuleCache:
                                    if fromCacheNew not in rulesNew:
                                        rulesNew[fromCacheNew] = []
                                    rulesNew[fromCacheNew].append(destRuleCache)
                                    mor[fromCacheNew] = moreS
                                # print(f"fromCache: {fromCache}")
                                # print(f"fromCacheNew: {fromCacheNew}")
                                # print(f"destRule: {destRule}")
                                # print(f"destRuleCache: {destRuleCache}")
                                # print(f"destRuleNew: {destRuleNew}")

                            # FIXME. Can this be done before?
                            # Look at previous arrow " -> "
                            msgLog = f"{self.indent} Rule: {orig} -> " f"{key}({dest})"
                            logMsg(msgLog, 2, 0)
                            msgLog = f"{self.indent}  from Srv: {fromSrv}"
                            logMsg(msgLog, 2, 0)
                            msgLog = f"{self.indent}  dest Rule: {destRule}"
                            logMsg(msgLog, 2, 0)
                            msgLog = f"{self.indent}  moreS: {moreS}"
                            logMsg(msgLog, 2, 0)
                            if "channel" in moreS:
                                msgLog = f"{self.indent}  moreSC: {moreS['channel']}"
                                logMsg(msgLog, 2, 0)
                                channels = moreS["channel"].split(",")
                            else:
                                msgLog = f"{self.indent}  moreSC: No"
                                logMsg(msgLog, 2, 0)
                                channels = ["set"]
                            for chan in channels:
                                if fromSrv and (destRuleNew or destRule):
                                    fromSrvN = (
                                        fromSrv[0],
                                        chan,
                                        fromSrv[2],
                                        fromSrv[3],
                                    )
                                    if fromSrvN not in rulesNew:
                                        rulesNew[fromSrvN] = []
                                    # print(f".fromSrv: {fromSrv}")
                                    if destRuleNew:
                                        # print(f".destRuleNew: {destRuleNew}")
                                        rulesNew[fromSrvN].append(destRuleNew)
                                    else:
                                        # print(f"destRule: {destRule}")
                                        rulesNew[fromSrvN].append(destRule)

                                    msgLog = f"{self.indent}  moreS: {moreS}"
                                    logMsg(msgLog, 2, 0)
                                    mor[fromSrvN] = dict(moreS)
                                    msgLog = f"{self.indent}  chan: {chan}"
                                    logMsg(msgLog, 2, 0)
                                    if (chan != "set") and not 'imap' in moreS:
                                        mor[fromSrvN].update(
                                            {"posts": chan, "channel": chan}
                                        )

        # logging.info(f"Rules: {rulesNew}")

        # Now we can add the sources not added.

        for src in srcsA:
            # logging.info(f"-> {src}")
            if src:
                if src not in rulesNew:
                    # Adding more rules
                    rulesNew[src] = []
                if src not in srcs:
                    # msgLog = (f"Adding implicit {src}")
                    # logMsg(msgLog, 2, 0)
                    srcs.append(src)
                    more.append({})

        # Now we can see which destinations can be also sources
        # msgLog = f"Dsts: {dsts}"
        # logMsg(msgLog, 2, 0)
        # logging.info(f"Srcs: {srcs}")
        # logging.info(f"SrcsA: {srcsA}")

        self.indent = f"{self.indent} Destinations:"
        for dst in dsts:
            msgLog = f"{self.indent} Dest: {dst}"
            logMsg(msgLog, 2, 0)
            if dst[0] == "direct":
                service = dst[2]
                # FIXME
                methods = self.hasSetMethods(service)
                for method in methods:
                    # msgLog = (f"cache dst {dst}")
                    # logMsg(msgLog, 2, 0)
                    toAppend = (service, "set", dst[3], method[1])  # , dst[4])
                    # msgLog = (f"toAppend src {toAppend}")
                    # logMsg(msgLog, 2, 0)
                    if toAppend[:4] not in srcs:
                        srcs.append(toAppend[:4])
                        more.append({})
            elif dst[0] == "cache":
                if len(dst) > 4:
                    toAppend = (
                        dst[0],
                        "set",
                        (dst[1], (dst[2], dst[3])),
                        "posts",
                        dst[4],
                        1,
                    )
                else:
                    toAppend = (
                        dst[0],
                        "set",
                        (dst[1], (dst[2], dst[3])),
                        "posts",
                        0,
                        1,
                    )
                if toAppend[:4] not in srcs:
                    srcs.append(toAppend[:4])
                    more.append({})

        available = {}
        myKeys = {}
        myIniKeys = []
        # for i, src in enumerate(srcs):
        for i, src in enumerate(rulesNew.keys()):
            if not src:
                continue
            iniK, nameK = self.getIniKey(
                self.getNameRule(src).upper(), myKeys, myIniKeys
            )
            # logging.info(f"iniK: {iniK}")
            if iniK not in available:
                available[iniK] = {
                    "name": self.getNameRule(src),
                    "data": [],
                    "social": [],
                }
                available[iniK]["data"] = []  # {'src': src, 'more': more[i]}]
            available[iniK]["data"].append({"src": src, "more": more[i]})

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

        self.rules = {}
        for key in rulesNew:
            # FIXME Is this ok?
            if rulesNew[key]:
                self.rules[key] = rulesNew[key]

        # msgLog = (f"RulesNew: {rulesNew}")
        # logMsg(msgLog, 2, 0)
        msgLog = f"More: {mor}"
        logMsg(msgLog, 2, 0)
        if hasattr(self, "args") and self.args.rules:
            self.printDict(rulesNew, "Rules")

        # self.rules = rulesNew
        msgLog = f"Available: {self.available}"
        logMsg(msgLog, 2, 0)
        msgLog = f"Rules: {self.rules}"
        logMsg(msgLog, 2, 0)
        self.more = mor

        self.indentLess()
        msgLog = "End Checking rules"
        logMsg(msgLog, 1, 2)

    def selectActionInteractive(self, service=None):
        if not service:
            nameModule = os.path.basename(inspect.stack()[1].filename)
            service = nameModule.split(".")[0][6:].casefold()
        selActions = self.selectAction(service)

        print("Actions:")
        for i, act in enumerate(selActions):
            print(f"{i}) {act}")
        iAct = input("Which action? ")
        apiDst = self.readConfigDst("", iAct, None, None)

        return apiDst

    def selectRuleInteractive(self, service=None):
        if not service:
            nameModule = os.path.basename(inspect.stack()[1].filename)
            service = nameModule.split(".")[0][6:].casefold()
        if not isinstance(service, list):
            service = [service, ]
        selRules = []
        logging.info(f"Services: {service}")
        for ser in service:
            logging.info(f"Service: {ser}")
            selRules = selRules + self.selectRule(ser, "")

        # selRules = self.selectRule(service, "")
        logging.info(f"Rules: {selRules}")
        iRul, src = select_from_list(selRules)

        logging.info(f"Selected rule: {iRul}. Rule {src}\n")
        print(f"\nSelected rule: {iRul}. Rule {src}\n")
        logging.debug(f"\nSelected more: {self.more}\n")
        more = None
        if src in self.more:
            more = self.more[src]
        apiSrc = self.readConfigSrc("", src, more)

        return apiSrc

    def selectAction(self, name="", selector2="", selector3=""):
        actions = []
        for src in self.rules.keys():
            for act in self.rules[src]:
                if self.getNameAction(act).capitalize() == name.capitalize():
                    logging.debug(f"Action: {act}")
                    actions.append(act)

        return actions

    def selectRule(self, name="", selector2="", selector3=""):
        rules = []
        service = name
        if not isinstance(name, list):
            service = [name, ]
        selRules = []
        for name_ser in service:
            logging.debug(f"Name: {name_ser}, Selectors: {selector2}, {selector3}")
            for src in self.rules.keys():
                if name_ser.capitalize() in self.getNameRule(src).capitalize():
                    logging.debug(f"profileR: {self.getProfileRule(src)}")
                    logging.debug(f"profileR: {self.getProfileAction(src)}")
                    if not selector2:
                        rules.append(src)
                    else:
                        if selector2 in self.getProfileAction(src):
                            # FIXME: ??
                            logging.debug(f"Second Selector: {selector2}")
                            if not selector3:
                                rules.append(src)
                            elif selector3 in self.getTypeRule(src):
                                rules.append(src)
        if not rules:
            for src in self.rules.keys():
                for action in self.rules[src]:
                    print(f"Action: {action}")
                    if self.getNameAction(action).capitalize() == name_ser.capitalize():
                        rules.append(src)

        return rules

    def hasSetMethods(self, service):
        self.indentPlus()
        msgLog = f"{self.indent} Service {service} checking set methods"
        logMsg(msgLog, 2, 0)
        if service == "social":
            return []

        if service in hasSet:
            msgLog = f"{self.indent} Service {service} cached"
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
                # FIXME: indenting inside modules?
                try:
                    myModule = eval(f"clsService.{method}.__module__")
                    myModuleList[(service, method)] = myModule
                except:
                    myModule = myModuleList[(service, method)]

                if method.find("Api") >= 0:
                    target = method[len("setApi") :].lower()
                # elif (clsService.setPosts.__module__
                elif myModule == f"module{service.capitalize()}":
                    target = method[len("set") :].lower()
                if target and (
                    target.lower()
                    in ["posts", "drafts", "favs", "messages", "queue", "search"]
                ):
                    toAppend = (action, target)
                    if toAppend not in methods:
                        methods.append(toAppend)
        self.indentLess()
        return methods

    def hasPublishMethod(self, service):
        self.indentPlus()
        msgLog = f"{self.indent} Start " f"Checking service publish methods"
        logMsg(msgLog, 2, 0)
        if service in hasPublish:
            msgLog = f"{self.indent}  Service {service} cached"
            logMsg(msgLog, 2, 0)
            listMethods = hasPublish[service]
        else:
            clsService = getModule(service, self.indent)
            # msgLog = f"{self.indent} Service cls: {clsService}"
            # logMsg(msgLog, 2, 0)

            listMethods = clsService.__dir__()
            hasPublish[service] = listMethods

        methods = []
        target = None
        for method in listMethods:
            if method.find("publish") >= 0:
                action = "publish"
                target = ""
                if method.find("Api") >= 0:
                    target = method[len("publishApi") :].lower()

                if target and (target != "image"):
                    msgLog = f"{self.indent} Service target: {target}"
                    logMsg(msgLog, 2, 0)
                    toAppend = (action, target)
                    if toAppend not in methods:
                        methods.append(toAppend)
        self.indentLess()
        return methods

    def getServices(self):
        msgLog = f"{self.indent} Start getServices"
        logMsg(msgLog, 2, 0)
        modulesFiles = os.listdir(path)
        modules = {"special": ["cache", "direct"], "regular": [], "other": ["service"]}
        # Initialized with some special services
        name = "module"
        for module in modulesFiles:
            if module.startswith(name):
                moduleName = module[len(name) : -3].lower()
                if moduleName not in modules["special"]:
                    # We drop the 'module' and the '.py' parts
                    modules["regular"].append(moduleName)

        msgLog = f"{self.indent} End getServices"
        logMsg(msgLog, 2, 0)
        return modules

    def printDict(self, myList, title):
        print(f"{title}:")
        for i, element in enumerate(myList):
            if isinstance(myList[element], list):
                self.printList(myList[element], element)
            else:
                print(f"  {i}) {element} {myList[element]}")

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
                    iniK = "J"
                    while iniK in myIniKeys:
                        iniK = chr(ord(iniK) + 1)
            myKeys[key] = iniK
        else:
            iniK = myKeys[key]
        myIniKeys.append(iniK)
        pos = key.find(iniK)
        if pos >= 0:
            nKey = key[:pos] + iniK.upper() + key[pos + 1 :]
        else:
            nKey = iniK + key
        nKey = key + "-{}".format(iniK)

        return iniK, nKey

    def cleanUrlRule(self, url, service=""):
        # FIXME: does it belong here?
        if service:
            url = url.replace(service, "")
        url = url.replace("https", "").replace("http", "")
        url = url.replace("---", "").replace(".com", "")
        url = url.replace("-(", "(").replace("- ", " ")
        url = url.replace(":", "").replace("/", "")
        return url

    def getNickSrc(self, src):
        if isinstance(src[2], tuple):
            res = src[-1]
        else:
            res = src[2]
        return res

    def getDestAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            destAction = action[1:]
        else:
            destAction = self.getActionComponent(action, 3)
        return destAction

    def getNickAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            nick = self.getActionComponent(self.getActionComponent(action, 2), 1)
        else:
            nick = self.getActionComponent(action, 3)
        return nick

    def getNameAction(self, action):
        res = self.getActionComponent(action, 0)
        if res == "direct":
            res = self.getActionComponent(action, 2)
        return res

    def getTypeAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            action = self.getActionComponent(action, 0)
        else:
            action = self.getActionComponent(action, 1)
        return action

    def getProfileAction(self, action):
        if isinstance(self.getActionComponent(action, 2), tuple):
            profile = self.getActionComponent(self.getActionComponent(action, 2), 2)
        else:
            profile = self.getActionComponent(action, 2)
        return profile

    def getRuleComponent(self, rule, pos):
        res = ""
        if isinstance(rule, tuple):
            res = rule[pos]
        return res

    def getNameRule(self, rule):
        return self.getRuleComponent(rule, 0)

    def getSecondNameRule(self, rule):
        res = ""
        if self.getNameRule(rule) == "cache":
            res = self.getRuleComponent(rule, 1)
        else:
            res = self.getRuleComponent(rule, 0)
        return res

    def getTypeRule(self, rule):
        res = "post"
        if self.getNameRule(rule) == "cache":
            res = "cache"
        else:
            res = self.getRuleComponent(rule, 3)
        return res

    def getIdRule(self, rule):
        idR = ""
        if isinstance(self.getRuleComponent(rule, 2), tuple):
            subC = self.getRuleComponent(rule, 2)
            idR = f"{self.getRuleComponent(subC, 3)}@{self.getRuleComponent(subC, 2)}@{self.getRuleComponent(rule, 0)}[{self.getRuleComponent(rule, 3)}]"  # @{self.getRuleComponent(rule, 0)}]"
        else:
            idR = f"{self.getRuleComponent(rule, 2)}@{self.getNameRule(rule)}"
        return idR

    def getProfileRule(self, rule):
        profileR = ""
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
        if "rss" not in rule:
            msgLog = (
                f"{indent} {typeC} Error. " f"No client for {rule} ({action}). End."
            )
        return f"{msgLog}"

    def readConfigSrc(self, indent, src, more):
        msgLog = f"{indent} Start readConfigSrc {src}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent} "

        profile = self.getNameRule(src)
        account = self.getProfileRule(src)
        if "channel" in more:
            apiSrc = getApi(profile, account, indent, more["channel"])
        else:
            apiSrc = getApi(profile, account, indent)
        msgLog = f"{indent} readConfigSrc clientttt {apiSrc.getClient()}"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        apiSrc.src = src
        apiSrc.setPostsType(src[-1])
        apiSrc.setMoreValues(more)

        # msgLog = f"{indent} Url: {apiSrc.getUrl()}" #: {src[1:]}"
        # logMsg(msgLog, 2, 0)
        indent = f"{indent[:-1]}"
        msgLog = f"{indent} End readConfigSrc"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        apiSrc.indent = indent
        return apiSrc

    def getActionComponent(self, action, pos):
        res = ""
        if isinstance(action, tuple) and (len(action) == 4):
            res = action[pos]
        return res

    def readConfigDst(self, indent, action, more, apiSrc):
        msgLog = f"{indent} Start readConfigDst"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent} "

        profile = self.getNameAction(action)
        account = self.getDestAction(action)
        apiDst = getApi(profile, account, indent)
        apiDst.setMoreValues(more)

        if apiSrc:
            apiDst.setUrl(apiSrc.getUrl())
        else:
            apiDst.setUrl(None)

        if apiSrc:
            apiDst.setLastLink(apiSrc)
        else:
            # FIXME. Do we need this? 
            apiDst.setLastLink(apiDst)

        # FIXME: best in readConfigSrc (readConfigDst, since we need it)?
        # PROBLEMS -> the same lastLink for each action ????
        # apiDst.lastLinkSrc = apiSrc.getLastLink()

        indent = f"{indent[:-1]}"
        msgLog = f"{indent} End readConfigDst"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        apiDst.indent = indent
        return apiDst

    def testDifferPosts(self, apiSrc, lastLink, listPosts):
        indent = ""
        i = 1
        num = 1
        listPosts = apiSrc.getNumPostsData(num, i, lastLink)
        if len(apiSrc.getPosts()) > 0:
            try:
                apiSrc.lastLinkPublished = apiSrc.getPostLink(apiSrc.getPosts()[1])
            except:
                apiSrc.lastLinkPublished = ""

        listPosts2 = apiSrc.getNumNextPost(num)
        # print(f"{indent} {listPosts}")
        if listPosts2:
            if listPosts == listPosts2:
                print("{indent} Equal listPosts")
            else:
                print(
                    f"{indent} Differ listPosts (len {len(listPosts[0])}, "
                    f"{len(listPosts2[0])}:\n"
                )
                for i, post in enumerate(listPosts):
                    for j, line in enumerate(listPosts[i]):
                        if line:
                            if listPosts[i][j] != listPosts2[i][j]:
                                print(
                                    f"{j}) *{listPosts[i][j]}*\n"
                                    f"{j}) *{listPosts2[i][j]}*"
                                )
                        else:
                            print(f"{j})")
        else:
            print(f"{indent}No listPosts2")

    def executePostAction(
        self, indent, msgAction, apiSrc, apiDst, simmulate, nextPost, pos, res
    ):
        resPost = ""
        resMsg = ""
        msgLog = f"{indent}Trying to execute Post Action"
        logMsg(msgLog, 1, 1)
        postaction = apiSrc.getPostAction()
        if postaction:
            msgLog = f"{indent}Post Action {postaction} " f"(nextPost = {nextPost})"
            logMsg(msgLog, 1, 1)

            if "OK. Published!" in res:
                msgLog = f"{indent} Res {res} is OK"
                logMsg(msgLog, 1, 0)
                if nextPost:
                    msgLog = f"{indent}Post Action next post"
                    logMsg(msgLog, 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost()
                else:
                    msgLog = f"{indent}Post Action pos post"
                    logMsg(msgLog, 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
                    # FIXME inconsistent
            msgLog = f"{indent}End {postaction}, reply: {resPost} "
            logMsg(msgLog, 1, 1)
            resMsg += f" Post Action: {resPost}"
            if (
                (res and ("failed!" not in res) and ("Fail!" not in res))
                or (res and ("abusive!" in res))
                or (
                    ((not res) and ("OK. Published!" not in res))
                    or ("duplicate" in res)
                )
            ):
                msgLog = f"{indent} Res {res} is not OK"
                # FIXME Some OK publishing follows this path (mastodon, linkedin, ...)
                logMsg(msgLog, 1, 0)

                if nextPost:
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost(apiDst)
                else:
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
                # FIXME inconsistent
                msgLog = f"{indent}Post Action command {cmdPost}"
                logMsg(msgLog, 1, 1)
                msgLog = f"{indent}End {postaction}, reply: {resPost} "
                logMsg(msgLog, 1, 1)
                resMsg += f"Post Action: {resPost}"
            else:
                msgLog = f"{indent}Something went wrong"
                logMsg(msgLog, 1, 1)
        else:
            msgLog = f"{indent}No Post Action"
            logMsg(msgLog, 1, 1)

        return resMsg

    def executePublishAction(
        self, indent, msgAction, apiSrc, apiDst, simmulate, nextPost=True, pos=-1
    ):
        res = ""

        resMsg = ""
        postaction = ""
        apiSrc.setPosts()
        if nextPost:
            post = apiSrc.getNextPost(apiDst)
        else:
            post = apiSrc.getPost(pos)
        link = ""
        if post:
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            resMsg = f"Publish result: {res}"
            msgLog = f"Title: {title}."
            if link:
                msgLog = (
                    f"{msgLog} Recording Link: {link} "
                    f"in file {apiDst.fileNameBase(apiSrc)}.last"
                )
        else:
            msgLog = f"{indent}No post to schedule in " f" {msgAction}"
            # f"from {apiSrc.getUrl()} "
            # f"in {self.getNickAction(action)}@"
            # f"{self.getProfileAction(action)}")

        if simmulate:
            if post:
                msgLog = f"{indent}Would schedule in " f" {msgAction} " f"{msgLog}"
            logMsg(msgLog, 1, 1)

            indent = f"{indent[:-1]}"
            resMsg = ""
        else:
            res = ""
            if post:
                res = apiDst.publishPost(api=apiSrc, post=post)
                msgLog = f"{indent}Reply: {res}"
                msgLog = f"{indent}Trying to publish {msgLog} "
                # print(f"{indent}res: {res}")
                if nextPost and (
                    res and ("Fail!" not in res) and ("failed!" not in res)
                ):
                    # ((not res) or ('SAVELINK' in res) or
                    #              (('Fail!' not in res)) or
                    #              (('failed!' not in res)))):
                    resUpdate = apiDst.updateLastLink(apiSrc, link)
                    resMsg += f" Update: {resUpdate}"

            logMsg(msgLog, 1, 1)
            # msgLog = (f"{indent} Res enddddd: {res}")
            # logMsg(msgLog, 2, 0)
            if res:
                msgLog = f"{indent}Res: {res} "
                logMsg(msgLog, 2, 0)
            if post:
                resMsg = self.executePostAction(
                    indent, msgAction, apiSrc, apiDst, simmulate, nextPost, pos, res
                )
            msgLog = f"{indent}End publish"
            if resMsg:
                msgLog = f"{msgLog}, reply: {resMsg}"
            logMsg(msgLog, 1, 1)
        if postaction == "delete":
            # FIXME: not always len is the available number. We should
            # consider the last published and so on.
            msgLog = f"{indent}Available {len(apiSrc.getPosts())-1}"
        else:
            msgLog = f"{indent}Available {len(apiSrc.getPosts())}"
        logMsg(msgLog, 1, 1)

        return resMsg

    def executeAction(
        self,
        src,
        more,
        action,
        msgAction,
        apiSrc,
        noWait,
        timeSlots,
        simmulate,
        name="",
        numAct=1,
        nextPost=True,
        pos=-1,
        delete=False,
    ):
        indent = f"{name}"

        # FIXME. What happens when src and dst are the same service (drafts, mainly)?
        # Destination
        apiDst = self.readConfigDst(indent, action, more, apiSrc)
        if not apiDst.getClient():
            msgLog = self.clientErrorMsg(
                indent,
                apiDst,
                "Destination",
                (f"{self.getNameRule(src)}@" f"{self.getProfileRule(src)}"),
                self.getNickAction(src),
            )
            if msgLog:
                logMsg(msgLog, 3, 1)
                sys.stderr.write(f"Error: {msgLog}\n")
            return f"End: {msgLog}"

        tL = random.random() * numAct
        indent = f"{indent} "
        msgLog = (
            f"{indent} Sleeping {tL:.2f} seconds ({numAct} actions) "
            f"to launch all processes"
        )
        logMsg(msgLog, 1, 0)
        numAct = max(3, numAct)  # Less than 3 is too small
        # 'Cosmetic' waiting to allow all the processes to be launched.
        # Randomization is a way to avoid calling several times the same
        # service (almost) as the same time.
        time.sleep(tL)

        msgLog = f"{indent} Go!"
        logMsg(msgLog, 1, 0)
        indent = f"{indent} "

        res = ""
        textEnd = f"{msgLog}"

        time.sleep(1)

        msgLog = ""
        if nextPost:
            num = apiDst.getMax()
        else:
            num = 1

        theAction = self.getTypeAction(action)
        msgLog = (
            f"{indent} I'll publish {num} {theAction} "
            f"from {apiSrc.getUrl()} "
            f"in {self.getNickAction(action)}@"
            f"{self.getProfileAction(action)}"
        )
        logMsg(msgLog, 1, 1)

        if num > 0:
            tNow = time.time()
            hours = float(apiDst.getTime()) * 60 * 60

            lastTime = apiDst.getLastTimePublished(f"{indent} ")

            if lastTime:
                diffTime = tNow - lastTime
            else:
                # If there is no lasTime, we will publish
                diffTime = hours + 1

            if noWait or (diffTime > hours):
                tSleep = random.random() * float(timeSlots) * 60

                apiDst.fileName = ""
                apiDst.setNextTime(tNow, tSleep, apiSrc)
                apiDst.fileName = ""

                if tSleep > 0.0:
                    msgLog = f"{indent} Waiting {tSleep/60:2.2f} minutes"
                else:
                    tSleep = 2.0
                    msgLog = f"{indent} No Waiting"

                msgLog = (
                    f"{msgLog} for {theAction} "
                    f"from {apiSrc.getUrl()} "
                    f"in {self.getNickAction(action)}@"
                    f"{self.getProfileAction(action)}"
                )
                logMsg(msgLog, 1, 1)

                for i in range(num):
                    time.sleep(tSleep)
                    msgLog = (
                        f"{indent} End Waiting {theAction} "
                        f"from {apiSrc.getUrl()} "
                        f"in {self.getNickAction(action)}@"
                        f"{self.getProfileAction(action)}"
                    )
                    logMsg(msgLog, 1, 1)
                    res = self.executePublishAction(
                        indent, msgAction, apiSrc, apiDst, simmulate, nextPost, pos
                    )
            elif diffTime <= hours:
                msgLog = (
                    f"{indent} Not enough time passed. "
                    f"We will wait at least "
                    f"{(hours-diffTime)/(60*60):2.2f} hours."
                )
                logMsg(msgLog, 1, 1)
                textEnd = ""

        else:
            if num <= 0:
                msgLog = f"{indent} No posts available"
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
                if self.getNameAction(src) != previous:
                    i = 0
                else:
                    i = i + 1
                previous = self.getNameAction(src)

                nameAction = f"[{self.getNameAction(src)}{i}]"
                indent = f"{nameAction:->12}>"
                msgIni = f"{self.getNickSrc(src)} ({self.getNickAction(src)})"

                if src in self.more:
                    if ("hold" in self.more[src]) and (self.more[src]["hold"] == "yes"):
                        msgHold = f"{indent} On hold. {msgIni}"
                        logMsg(msgHold, 1, 0)
                        continue

                if src in self.more:
                    more = self.more[src]
                else:
                    more = None

                msgIni = f"{self.getNickSrc(src)} ({self.getNickAction(src)})"

                actions = self.rules[src]

                if select and (select.lower() != f"{self.getNameRule(src).lower()}{i}"):
                    actionMsg = f"Skip {msgIni}"
                else:
                    actionMsg = f"Scheduling {msgIni}"
                msgLog = f"{indent} {actionMsg}"
                logMsg(msgLog, 1, 1)
                if actionMsg == "Skip.":
                    # FIXME ?
                    continue
                # Source
                apiSrc = self.readConfigSrc(indent, src, more)
                logging.info(f"{indent} Clientttt: {apiSrc.getClient()}")
                if not apiSrc.getClient():
                    msgLog = self.clientErrorMsg(
                        indent,
                        apiSrc,
                        "Source",
                        self.getProfileRule(src),
                        self.getNickAction(src),
                    )
                    if msgLog:
                        logMsg(msgLog, 3, 1)
                    # return f"{msgLog} End."

                if apiSrc.getName():
                    theName = apiSrc.getName()
                else:
                    theName = self.getProfileAction(src)

                for k, action in enumerate(actions):
                    name = f"{self.getNameRule(src)}{i}>"
                    theAction = "posts"
                    if not self.getTypeAction(action).startswith("http"):
                        theAction = self.getTypeAction(action)

                    indent = f"{indent} "
                    msgLog = (
                        f"{indent} Action {k}:"
                        f" {self.getNickAction(action)}@"
                        f"{self.getProfileAction(action)} ({theAction})"
                    )
                    name = f"Action {k}:"  # [({theAction})"
                    nameA = f"{actionMsg} "
                    textEnd = (
                        f"Source: {nameA} {self.getProfileRule(src)} "
                        f"{self.getNickRule(src)}"
                    )
                    logMsg(msgLog, 1, 1)
                    textEnd = f"{textEnd}\n{msgLog}"
                    nameA = f"{indent} {name}"
                    if "Skip" not in actionMsg:
                        timeSlots = args.timeSlots
                        noWait = args.noWait

                        # Is this the correct place?
                        if (self.getNameAction(action) in "cache") or (
                            (self.getNameAction(action) == "direct")
                            and (self.getProfileAction(action) == "pocket")
                        ):
                            # We will always load new items in the cache
                            timeSlots = 0
                            noWait = True
                        msgAction = (
                            f"{self.getNameAction(action)} "
                            f"{self.getNickAction(action)}@"
                            f"{self.getProfileAction(action)} "
                            f"({self.getTypeAction(action)})"
                        )

                        msgLog = (
                            f"Source: {theName}-{self.getNickAction(src)}"
                            f" -> Action: {msgAction}"
                        )

                        threads = threads + 1
                        delayedPosts.append(
                            pool.submit(
                                self.executeAction,
                                src,
                                more,
                                action,
                                msgAction,
                                apiSrc,  # apiDst[-1],
                                noWait,
                                timeSlots,
                                simmulate,
                                nameA,
                                threads,
                            )
                        )
                    indent = f"{indent[:-1]}"
                indent = f"{indent[:-1]}"

            messages = []
            for future in concurrent.futures.as_completed(delayedPosts):
                try:
                    res = future.result()
                    if res:
                        messages.append(f"  Published in: {future}\n{res} ")
                except Exception as exc:
                    # else:
                    msgLog = (
                        f"{future} generated an exception: {exc} "
                        f"Src: {src}. Action: {action}"
                    )
                    logMsg(msgLog, 1, 1)
                    msgLog = f"{sys.exc_info()}"
                    logMsg(msgLog, 1, 1)
                    import traceback

                    msgLog = f"{traceback.print_exc()}"
                    logMsg(msgLog, 1, 1)

        # FIXME: We are not using messages
        msgLog = f"End Executing rules with {threads} threads."
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
            help=("How many time slots we will have for publishing (in minutes)"),
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
    mode = logging.INFO
    logging.basicConfig(
        filename=f"{LOGDIR}/rssSocial.log",
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
