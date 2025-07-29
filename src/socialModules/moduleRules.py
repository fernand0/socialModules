import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import sys
import time

import socialModules
from socialModules.configMod import logMsg, getApi, getModule, CONFIGDIR, LOGDIR

fileName = socialModules.__file__
path = f"{os.path.dirname(fileName)}"

sys.path.append(path)

hasSet = {}
hasPublish = {}
myModuleList = {}


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class moduleRules:
    def indentPlus(self):
        if not hasattr(self, "indent"):
            self.indent = " "
        else:
            self.indent = f"{self.indent} "

    def indentLess(self):
        self.indent = self.indent[:-1]

    def checkRules(self, configFile=None, select=None):
        """
        Reads the configuration file, processes each section, and builds the publishing rules.
        Includes exhaustive validation and error handling.
        Optimized for efficiency using sets and efficient access.
        Allows absolute path for the configuration file.
        """
        import os
        msgLog = "Checking rules"
        logMsg(msgLog, 1, 2)
        config = configparser.ConfigParser()
        try:
            if not configFile:
                configFile = ".rssBlogs"
            # If it's an absolute path and exists, use it directly
            if os.path.isabs(configFile) and os.path.exists(configFile):
                config.read(configFile)
            else:
                configFile = f"{CONFIGDIR}/{configFile}"
                config.read(configFile)
        except Exception as e:
            logMsg(f"ERROR: Could not read configuration file: {e}", 3, 1)
            raise ConfigError(f"Could not read configuration file: {e}")

        self.indentPlus()
        services = self.getServices()
        logging.debug(f"{self.indent}Services: {services}")
        services["regular"].append("cache")

        # Use sets to avoid duplicates and improve efficiency
        srcs, srcsA, dsts = set(), set(), set()
        more, ruls, rulesNew, mor, impRuls = [], {}, {}, {}, []

        for section in config.sections():
            msgLog = f" Section: {section}"
            logMsg(msgLog, 1, 1)
            self.indent = f"{self.indent}{section}>"
            try:
                self._process_section(section, config, services, srcs, srcsA, more, dsts, ruls, rulesNew, mor, impRuls, select)
            except ConfigError as ce:
                logMsg(f"ERROR in section [{section}]: {ce}", 3, 1)
                raise  # Reraise the exception so tests can catch it
            except Exception as e:
                logMsg(f"UNEXPECTED ERROR in section [{section}]: {e}", 3, 1)
                continue
            self.indent = f"{self.indent[:-(len(section)+2)]}"

        self._finalize_rules(config, services, srcs, srcsA, more, dsts, rulesNew)
        self._set_available_and_rules(rulesNew, more)
        self.more = mor
        self.indentLess()
        msgLog = "End Checking rules"
        logMsg(msgLog, 1, 2)
        msgLog = f"Rules: {rulesNew}"
        logMsg(msgLog, 2, 0)

    def _process_section(self, section, config, services, srcs, srcsA, more, dsts, ruls, rulesNew, mor, impRuls, select=None):
        """
        Processes a section of the configuration file, identifying sources and destinations.
        Validates the presence of required keys and data types.
        """
        # Robustly validate required keys and ensure they are not empty
        required_keys = ["url", "service"]
        section_dict = dict(config.items(section))
        for key in required_keys:
            if key not in section_dict or not section_dict[key].strip():
                raise ConfigError(f"Missing required key '{key}' or it is empty in section [{section}]")
        url = section_dict["url"]
        msgLog = f"{self.indent} Url: {url}"
        logMsg(msgLog, 1, 1)
        moreS = dict(config.items(section))
        toAppend, theService, api = self._process_sources(section, config, services, url, moreS, srcs, srcsA, more)
        fromSrv = toAppend
        msgLog = f"{self.indent} We will append: {toAppend}"
        logMsg(msgLog, 2, 0)
        if toAppend:
            service = toAppend[0]
        postsType = section_dict.get("posts", "posts")
        self.indentPlus()
        msgLog = f"{self.indent} Type: {postsType}"
        logMsg(msgLog, 2, 0)
        if fromSrv:
            fromSrv = (fromSrv[0], fromSrv[1], fromSrv[2], postsType)
            msgLog = f"{self.indent} Checking actions for {service}"
            logMsg(msgLog, 1, 0)
            self._process_destinations(section, config, service, services, fromSrv, moreS, api, dsts, ruls, mor, impRuls)
        self._process_rule_keys(moreS, services, fromSrv, rulesNew, mor)
        # Save the section name in moreS for traceability
        moreS['section_name'] = section

    def _process_sources(self, section, config, services, url, moreS, srcs, srcsA, more):
        """
        Identifies and registers the source services of a section.
        Validates the presence and type of required values.
        Optimized for efficiency using sets.
        """
        toAppend = ""
        theService = None
        api = None
        for service in services["regular"]:
            if ("service" in config[section]) and (service == config[section]["service"]):
                theService = service
                api = getModule(service, self.indent)
                api.setUrl(url)
                if service in config[section]:
                    serviceData = config.get(section, service)
                    api.setService(service, serviceData)
                if service in config[section]:
                    api.setNick(config[section][service])
                else:
                    api.setNick()
                self.indentPlus()
                methods = self.hasSetMethods(service)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(f"WARNING: Unexpected method in {service}: {method}", 2, 1)
                        continue
                    if "posts" in moreS:
                        if moreS["posts"] == method[1]:
                            toAppend = (theService, "set", api.getNick(), method[1])
                    else:
                        toAppend = (theService, "set", api.getNick(), method[1])
                    if toAppend not in srcs:
                        if ("posts" in moreS) and (moreS["posts"] == method[1]):
                            srcs.add(toAppend)
                            more.append(moreS)
                        else:
                            srcsA.add(toAppend)

                self.indentLess()
                msgLog = f"{self.indent} Service: {service}"
                logMsg(msgLog, 1, 1)
        return toAppend, theService, api

    def _process_destinations(self, section, config, service, services, fromSrv, moreS, api, dsts, ruls, mor, impRuls):
        """
        Identifies and registers the destination services of a section.
        Validates the presence of keys and types in the destinations.
        Optimized for efficiency using sets.
        """
        hasSpecial = False
        for serviceS in services["special"]:
            toAppend = ""
            if serviceS in config.options(section):
                valueE = config.get(section, serviceS).split("\n")
                for val in valueE:
                    if val in config[section]:
                        nick = config.get(section, val)
                    else:
                        nick = api.getNick() if api else ""
                    url = "posts" if serviceS == "direct" else None
                    toAppend = (serviceS, url, val, nick)
                    if toAppend not in dsts:
                        if "service" not in toAppend:
                            dsts.add(toAppend)
                    if toAppend:
                        if fromSrv not in mor:
                            mor[fromSrv] = moreS
                        if fromSrv in ruls:
                            if toAppend not in ruls[fromSrv]:
                                ruls[fromSrv].append(toAppend)
                        else:
                            ruls[fromSrv] = [toAppend]
                        if serviceS == "cache":
                            hasSpecial = True
        self.indentPlus()
        for serviceD in services["regular"]:
            if (serviceD == "cache") or (serviceD == "xmlrpc") or (fromSrv and serviceD == fromSrv[0]):
                continue
            toAppend = ""
            if serviceD in config.options(section):
                msgLog = ( 
                          f"{self.indent} Service {service} -> {serviceD} checking "
                          )
                logMsg(msgLog, 2, 0)

                methods = self.hasPublishMethod(serviceD)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(f"WARNING: Unexpected method in {serviceD}: {method}", 2, 1)
                        continue
                    mmethod = method[1] if method[1] else "post"
                    toAppend = ("direct", mmethod, serviceD, config.get(section, serviceD))
                    if toAppend not in dsts:
                        dsts.add(toAppend)
                    if toAppend:
                        if hasSpecial:
                            nickSn = f"{toAppend[2]}@{toAppend[3]}"
                            fromSrvSp = ("cache", (fromSrv[0], fromSrv[2]), nickSn, "posts")
                            impRuls.append((fromSrvSp, toAppend))
                            if fromSrvSp not in mor:
                                mor[fromSrvSp] = moreS
                            if fromSrvSp in ruls:
                                if toAppend not in ruls[fromSrvSp]:
                                    ruls[fromSrvSp].append(toAppend)
                            else:
                                ruls[fromSrvSp] = [toAppend]
                        else:
                            if not (fromSrv[2] != toAppend[3] and fromSrv[3][:-1] != toAppend[1]):
                                if fromSrv not in mor:
                                    mor[fromSrv] = moreS
                                if fromSrv in ruls:
                                    if toAppend not in ruls[fromSrv]:
                                        ruls[fromSrv].append(toAppend)
                                else:
                                    ruls[fromSrv] = [toAppend]
        self.indentLess()

    def _process_rule_keys(self, moreS, services, fromSrv, rulesNew, mor):
        """
        Processes the section keys to build additional rules.
        Validates the presence and type of required values.
        """
        msgLog = f"{self.indent} Processing services in more"
        logMsg(msgLog, 2, 0)
        self.indentPlus()
        msgLog = f"{self.indent} moreS: {moreS}"
        logMsg(msgLog, 2, 0)
        self.indentPlus()
        orig = None
        dest = None
        for key in moreS.keys():
            service = moreS[key] if key == "service" else key
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
                msgLog = f"{self.indent} Service {service} not orig"
                logMsg(msgLog, 2, 0)
                if (key in services["special"]) or (key in services["regular"]):
                    if key == "cache":
                        dest = key
                    elif key == "direct":
                        dest = key
                    elif self.hasPublishMethod(key):
                        if not dest:
                            dest = "direct"
                        destRuleNew = ""
                        destRuleCache = ""
                        fromCacheNew = ""
                        if dest == "direct":
                            destRule = (dest, "post", key, moreS.get(key, ""))
                        else:
                            destRule = (dest, moreS.get("url", ""), key, moreS.get(key, ""))
                            destRuleNew = (
                                dest,
                                moreS.get("service", ""),
                                ("direct", "post", key, moreS.get(key, "")),
                                moreS.get("url", ""),
                            )
                            fromCacheNew = (
                                "cache",
                                moreS.get("service", ""),
                                ("direct", "post", key, moreS.get(key, "")),
                                moreS.get("url", ""),
                            )
                            destRuleCache = ("direct", "post", key, moreS.get(key, ""))
                            if fromCacheNew and destRuleCache:
                                if fromCacheNew not in rulesNew:
                                    rulesNew[fromCacheNew] = []
                                rulesNew[fromCacheNew].append(destRuleCache)
                                mor[fromCacheNew] = moreS
                        self.indentPlus()
                        msgLog = f"{self.indent} Rule: {orig} -> {key}({dest})"
                        logMsg(msgLog, 2, 0)
                        self.indentPlus()
                        msgLog = f"{self.indent} from Srv: {fromSrv}"
                        logMsg(msgLog, 2, 0)
                        msgLog = f"{self.indent} dest Rule: {destRule}"
                        logMsg(msgLog, 2, 0)
                        self.indentLess()
                        self.indentLess()
                        channels = moreS["channel"].split(",") if "channel" in moreS else ["set"]
                        for chan in channels: 
                            if fromSrv and (destRuleNew or destRule):
                                fromSrvN = (fromSrv[0], chan, fromSrv[2], fromSrv[3])
                                if fromSrvN not in rulesNew:
                                    rulesNew[fromSrvN] = []
                                if destRuleNew:
                                    rulesNew[fromSrvN].append(destRuleNew)
                                else:
                                    rulesNew[fromSrvN].append(destRule)
                                mor[fromSrvN] = dict(moreS)
                                if chan != "set":
                                    mor[fromSrvN].update({"posts": chan, "channel": chan})
        self.indentLess()
        self.indentLess()

    def _finalize_rules(self, config, services, srcs, srcsA, more, dsts, rulesNew):
        """
        Adds implicit sources and destinations that can be sources.
        Validates the structure of the data before adding them.
        Optimized for efficiency using sets.
        """
        for src in srcsA:
            if src:
                if src not in rulesNew:
                    rulesNew[src] = []
                if src not in srcs:
                    srcs.add(src)
                    more.append({})
        logging.info(f"Srcs: {list(srcs)}")
        logging.info(f"SrcsA: {list(srcsA)}")
        self.indent = f"{self.indent} Destinations:"
        for dst in dsts:
            if not isinstance(dst, tuple) or len(dst) < 4:
                logMsg(f"WARNING: Unexpected destination: {dst}", 2, 1)
                continue
            if dst[0] == "direct":
                service = dst[2]
                methods = self.hasSetMethods(service)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(f"WARNING: Unexpected method in {service}: {method}", 2, 1)
                        continue
                    toAppend = (service, "set", dst[3], method[1])
                    if toAppend[:4] not in srcs:
                        srcs.add(toAppend[:4])
                        more.append({})
            elif dst[0] == "cache":
                if len(dst) > 4:
                    toAppend = (dst[0], "set", (dst[1], (dst[2], dst[3])), "posts", dst[4], 1)
                else:
                    toAppend = (dst[0], "set", (dst[1], (dst[2], dst[3])), "posts", 0, 1)
                if toAppend[:4] not in srcs:
                    srcs.add(toAppend[:4])
                    more.append({})

        # Convert sets to lists for compatibility with the rest of the code
        self._srcs = list(srcs)
        self._srcsA = list(srcsA)
        self._dsts = list(dsts)

    def _set_available_and_rules(self, rulesNew, more):
        """
        Builds self.available, self.availableList and self.rules.
        Validates the integrity of the data before adding them.
        """
        available = {}
        myKeys = {}
        myIniKeys = []
        for i, src in enumerate(rulesNew.keys()):
            if not src:
                continue
            # Use the section name if available
            section_name = more[i].get('section_name', self.getNameRule(src)) if i < len(more) and isinstance(more[i], dict) else self.getNameRule(src)
            iniK, nameK = self.getIniKey(section_name.upper(), myKeys, myIniKeys)
            if iniK not in available:
                available[iniK] = {"name": section_name, "data": [], "social": []}
            more_i = more[i] if i < len(more) and isinstance(more[i], dict) else {}
            available[iniK]["data"].append({"src": src, "more": more_i})
        myList = [f"{elem}) {available[elem]['name']}: {len(available[elem]['data'])}" for elem in available]
        self.available = available
        self.availableList = myList if myList else []
        self.rules = {key: rulesNew[key] for key in rulesNew if rulesNew[key]}

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
        selRules = self.selectRule(service, "")
        print("Rules:")
        iRul = 0
        if len(selRules) > 1:
            for i, rul in enumerate(selRules):
                print(f"{i}) {rul}")
            iRul = input("Which rule? ")
        src = selRules[int(iRul)]
        print(f"\nSelected rule: {iRul}. Rule {src}")
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
        for src in self.rules.keys():
            if self.getNameRule(src).capitalize() == name.capitalize():
                logging.debug(f"profileR: {self.getProfileRule(src)}")
                logging.debug(f"profileR: {self.getProfileAction(src)}")
                if not selector2:
                    rules.append(src)
                else:
                    if selector2 == self.getProfileAction(src):
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
                    if self.getNameAction(action).capitalize() == name.capitalize():
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
        orig = f"{self.getNameAction(src)} ({self.getNickRule(src)}) {self.getTypeRule(src)}"
        dest = f"{self.getNameAction(action)} ({self.getNickAction(action)}) {self.getTypeAction(action)}"
        msgLog = f"{indent} Scheduling {orig} -> {dest}"
        logMsg(msgLog, 1, 1)
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

    def executeRules(self, max_workers=None):
        """
        Executes all generated rules using concurrency.
        Refactored to delegate to helper functions.
        Allows configuring the number of threads (max_workers) by argument, environment variable SOCIALMODULES_MAX_WORKERS,
        or automatically according to the number of actions to execute (one per action, minimum 1, maximum 100).
        """
        import os
        msgLog = "Start Executing rules"
        logMsg(msgLog, 1, 2)
        args = self.args
        select = args.checkBlog
        simmulate = args.simmulate
        # Prepare actions to execute
        scheduled_actions = self._prepare_actions(args, select)
        # Determine number of threads
        if max_workers is not None:
            pass  # use the explicit value
        elif "SOCIALMODULES_MAX_WORKERS" in os.environ:
            max_workers = int(os.environ["SOCIALMODULES_MAX_WORKERS"])
        else:
            num_actions = max(1, len(scheduled_actions))
            max_workers = min(num_actions, 100)  # reasonable maximum
        # Execute actions concurrently
        action_results, action_errors = self._run_actions_concurrently(scheduled_actions, max_workers=max_workers)
        # Report results and errors
        self._report_results(action_results, action_errors)
        msgLog = f"End Executing rules with {len(scheduled_actions)} actions."
        logMsg(msgLog, 1, 2)
        return

    def _prepare_actions(self, args, select):
        """
        Prepares the list of actions to execute, filtering and collecting all necessary information.
        Returns a list of dictionaries with data for each action.
        """
        scheduled_actions = []
        previous = ""
        for rule_index, rule_key in enumerate(sorted(self.rules.keys())):
            # Repetition control by action name
            rule_metadata = self.more[rule_key] if rule_key in self.more else None
            if rule_metadata and rule_metadata.get("hold") == "yes":
                msgHold = f"[HOLD] {self.getNickSrc(rule_key)} ({self.getNickAction(rule_key)})"
                logMsg(msgHold, 1, 0)
                continue
            rule_actions = self.rules[rule_key]
            if self.getNameAction(rule_key) != previous:
                i = 0
            else:
                i = i + 1
            previous = self.getNameAction(rule_key)

            for action_index, rule_action in enumerate(rule_actions):
                # Rule selection if --checkBlog is used

                if select and (select.lower() != f"{self.getNameRule(rule_key).lower()}{i}"):
                    continue
                scheduled_actions.append({
                    "rule_key": rule_key,
                    "rule_metadata": rule_metadata,
                    "rule_action": rule_action,
                    "rule_index": i,
                    "action_index": action_index,
                    "args": args,
                    "simmulate": args.simmulate,
                })
        return scheduled_actions

    def _run_actions_concurrently(self, scheduled_actions, max_workers=75):
        """
        Executes actions in parallel using ThreadPoolExecutor.
        Returns two lists: results and errors.
        """
        import concurrent.futures
        action_results = []
        action_errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_action = {
                pool.submit(
                    self._execute_single_action,
                    scheduled_action
                ): scheduled_action for scheduled_action in scheduled_actions
            }
            for future in concurrent.futures.as_completed(future_to_action):
                scheduled_action = future_to_action[future]
                try:
                    res = future.result()
                    action_results.append((scheduled_action, res))
                except Exception as exc:
                    action_errors.append((scheduled_action, exc))
        return action_results, action_errors

    def _execute_single_action(self, scheduled_action):
        """
        Executes a single action (wrapper for executeAction).
        """
        rule_key = scheduled_action["rule_key"]
        rule_metadata = scheduled_action["rule_metadata"]
        rule_action = scheduled_action["rule_action"]
        args = scheduled_action["args"]
        simmulate = scheduled_action["simmulate"]
        # Prepare arguments for executeAction
        apiSrc = self.readConfigSrc("", rule_key, rule_metadata)
        msgAction = (
            f"{self.getNameAction(rule_action)} "
            f"{self.getNickAction(rule_action)}@"
            f"{self.getProfileAction(rule_action)} "
            f"({self.getTypeAction(rule_action)})"
        )
        rule_index = scheduled_action.get('rule_index', 0)
        action_index = scheduled_action.get('action_index', 0)
        name_action = f"[{self.getNameAction(rule_key)}{rule_index}]"
        nameA =  f"{name_action:->12}> Action {action_index}:"
        return self.executeAction(
            rule_key,
            rule_metadata,
            rule_action,
            msgAction,
            apiSrc,
            args.noWait,
            args.timeSlots,
            simmulate,
            nameA,
            action_index,
        )

    def _report_results(self, action_results, action_errors):
        """
        Reports the results and errors of action execution.
        """
        for scheduled_action, res in action_results:
            if res:
                rule_key = scheduled_action['rule_key']
                rule_index = scheduled_action.get('rule_index', '')
                rule_summary = f"Rule {rule_index}: {rule_key}" if rule_index != '' else str(rule_key)
                logMsg(f"[OK] Action executed for {rule_summary} -> {scheduled_action['rule_action']}: {res}", 1, 1)
        for scheduled_action, exc in action_errors:
            rule_key = scheduled_action['rule_key']
            rule_index = scheduled_action.get('rule_index', '')
            rule_summary = f"Rule {rule_index}: {rule_key}" if rule_index != '' else str(rule_key)
            logMsg(f"[ERROR] Action failed for {rule_summary} -> {scheduled_action['rule_action']}: {exc}", 3, 1)

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
    mode = logging.DEBUG
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
