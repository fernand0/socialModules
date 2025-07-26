import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Union

import argparse
import click
import socialModules
from socialModules.configMod import logMsg, getApi, getModule, CONFIGDIR, LOGDIR

fileName = socialModules.__file__
path = f"{os.path.dirname(os.path.dirname(fileName))}"

sys.path.append(path)

hasSet = {}
hasPublish = {}
myModuleList = {}


@dataclass(frozen=True)
class Rule:
    service: str
    method: str
    profile: str
    post_type: str


class moduleRules:
    def indentPlus(self):
        if not hasattr(self, "indent"):
            self.indent = " "
        else:
            self.indent = f"{self.indent} "

    def indentLess(self):
        self.indent = self.indent[:-1]

    def _load_configuration(self, configFile):
        config = configparser.ConfigParser()
        if not configFile:
            configFile = ".rssBlogs"
        configFile = f"{CONFIGDIR}/{configFile}"
        config.read(configFile)
        return config

    def _process_source(self, section_config, services, srcs, srcsA, more, moreS):
        toAppend = ""
        url = section_config.get("url")
        api = None
        theService = ""

        for service in services["regular"]:
            if ("service" in section_config) and (service == section_config["service"]):
                msgLog = f"{self.indent} Service: {service}"
                logMsg(msgLog, 1, 1)
                theService = service
                api = getModule(service, self.indent)
                api.setUrl(url)
                if service in section_config:
                    serviceData = section_config.get(service)
                    api.setService(service, serviceData)

                if service in section_config:
                    api.setNick(section_config[service])
                else:
                    api.setNick()

                self.indentPlus()
                msgLog = f"{self.indent} Nick: {api.getNick()}"
                logMsg(msgLog, 2, 0)

                methods = self.hasSetMethods(service)
                msgLog = (f"{self.indent} Service {service} has " f"set {methods}")
                logMsg(msgLog, 2, 0)
                for method in methods:
                    if "posts" in moreS:
                        if moreS["posts"] == method[1]:
                            toAppend = Rule(theService, "set", api.getNick(), method[1])
                    else:
                        toAppend = Rule(theService, "set", api.getNick(), method[1])
                    if toAppend not in srcs:
                        if ("posts" in moreS) and (moreS["posts"] == method[1]):
                            srcs.append(toAppend)
                            more.append(moreS)
                        else:
                            # Available, but with no rules
                            srcsA.append(toAppend)
        fromSrv = toAppend
        return fromSrv, api, theService

    def _process_destinations(self, section_config, services, fromSrv, api, theService, mor, ruls, dsts, moreS):
        hasSpecial = False
        if "posts" in section_config:
            postsType = section_config["posts"]
        else:
            postsType = "posts"
        msgLog = f"{self.indent} Type {postsType}"
        logMsg(msgLog, 2, 0)
        if fromSrv:
            fromSrv = (
                fromSrv.service,
                fromSrv.method,
                fromSrv.profile,
                postsType,
            )
            for serviceS in services["special"]:
                toAppend = ""
                if serviceS in section_config:
                    valueE = section_config.get(serviceS).split("\n")
                    for val in valueE:
                        url = ""
                        if val in section_config:
                            nick = section_config.get(val)
                        else:
                            nick = api.getNick()
                        if serviceS == "direct":
                            url = "posts"
                        toAppend = Rule(serviceS, url, val, nick)
                        if toAppend not in dsts:
                            if not hasattr(toAppend, "service"):
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
        return hasSpecial

    def _process_actions(self, section_config, services, fromSrv, theService, hasSpecial, mor, ruls, dsts, impRuls, moreS):
        if fromSrv:
            msgLog = f"{self.indent} Checking actions for {fromSrv.service}"
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
                if serviceD in section_config:
                    msgLog = (
                        f"{self.indent} Service {fromSrv.service} -> {serviceD} checking "
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
                        toAppend = Rule("direct", mmethod, serviceD, section_config.get(serviceD))

                        if toAppend not in dsts:
                            dsts.append(toAppend)
                        if toAppend:
                            if hasSpecial:
                                nickSn = f"{toAppend.profile}@{toAppend.service}"
                                fromSrvSp = Rule(
                                    "cache",
                                    (fromSrv.service, fromSrv.profile),
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
                                    fromSrv.profile != toAppend.profile
                                    and fromSrv.post_type[:-1] != toAppend.method
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

    def _create_rules_from_section(self, moreS, services, fromSrv, rulesNew, mor):
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
                            destRule = Rule(dest, "post", key, moreS[key])
                        else:
                            destRule = Rule(dest, moreS["url"], key, moreS[key])
                            destRuleNew = Rule(
                                dest,
                                moreS["service"],
                                Rule("direct", "post", key, moreS[key]),
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
                            fromCacheNew = Rule(
                                "cache",
                                moreS["service"],
                                Rule("direct", "post", key, moreS[key]),
                                moreS["url"],
                            )  # , 'posts'),
                            # f"{key}@{moreS[key]}")
                            # FIXME: It is needed for imgur, in the other
                            # cases is OK
                            destRuleCache = Rule("direct", "post", key, moreS[key])
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
                                fromSrvN = Rule(
                                    fromSrv.service,
                                    chan,
                                    fromSrv.profile,
                                    fromSrv.post_type,
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
        logging.debug(f"{self.indent}rulesNew after section processing: {rulesNew}")
        logging.debug(f"{self.indent}mor after section processing: {mor}")

    def _process_section(self, section, config, services, srcs, srcsA, more, dsts):

        rulesNew = {}
        mor = {}
        impRuls = []
        ruls = {}
        url = config.get(section, "url")
        msgLog = f" Section: {section} Url: {url}"
        logMsg(msgLog, 1, 1)
        self.indent = f"  {section}>"
        # Sources
        moreS = dict(config.items(section))
        fromSrv, api, theService = self._process_source(config[section], services, srcs, srcsA, more, moreS)

        msgLog = f"{self.indent} We will append: {fromSrv}"
        logMsg(msgLog, 2, 0)
        if fromSrv:
            service = fromSrv.service

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
        hasSpecial = self._process_destinations(config[section], services, fromSrv, api, theService, mor, ruls, dsts, moreS)

        self._process_actions(config[section], services, fromSrv, theService, hasSpecial, mor, ruls, dsts, impRuls, moreS)

        self._create_rules_from_section(moreS, services, fromSrv, rulesNew, mor)

        return rulesNew, mor

    def _process_srcs_not_added(self, srcs, srcsA, rulesNew, more):
        for src in srcsA:
            if src:
                if src not in rulesNew:
                    rulesNew[src] = []
                if src not in srcs:
                    srcs.append(src)
                    more.append({})

    def _process_destinations_as_sources(self, dsts, srcs, more):
        self.indent = f"{self.indent} Destinations:"
        for dst in dsts:
            msgLog = f"{self.indent} Dest: {dst}"
            logMsg(msgLog, 2, 0)
            if isinstance(dst, Rule) and dst.service == "direct":
                service = dst.profile
                account = dst.post_type
                # FIXME
                methods = self.hasSetMethods(service)
                for method in methods:
                    toAppend = Rule(service, "set", account, method[1])
                    if toAppend not in srcs:
                        srcs.append(toAppend)
                        more.append({})
            elif self.getRuleComponent(dst, 0) == "direct":
                service = self.getRuleComponent(dst, 2)
                # FIXME
                methods = self.hasSetMethods(service)
                for method in methods:
                    toAppend = Rule(service, "set", self.getRuleComponent(dst, 3), method[1])
                    if toAppend not in srcs:
                        srcs.append(toAppend)
                        more.append({})
            elif self.getRuleComponent(dst, 0) == "cache":
                # This part is more complex and will be handled later.
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

    def _initialize_rule_data(self):
        srcs = []
        srcsA = []
        more = []
        dsts = []
        return srcs, srcsA, more, dsts

    def checkRules(self, configFile=None, select=None):
        msgLog = "Checking rules"
        logMsg(msgLog, 1, 2)
        config = self._load_configuration(configFile)

        self.indentPlus()
        services = self.getServices()
        logging.debug(f"{self.indent}Services: {services}")


        srcs, srcsA, more, dsts = self._initialize_rule_data()
        rulesNew = {}
        mor = {}
        for section in config.sections():
            if select and (section != select):
                continue
            rulesNew_section, mor_section = self._process_section(section, config, services, srcs, srcsA, more, dsts)
            rulesNew.update(rulesNew_section)
            mor.update(mor_section)

        logging.info(f"RRules: {rulesNew}")

        # Now we can add the sources not added.
        self._process_srcs_not_added(srcs, srcsA, rulesNew, more)

        self._process_destinations_as_sources(dsts, srcs, more)

        self._finalize_rules_data(rulesNew, srcs, more, mor)

        self.indentLess()
        msgLog = "End Checking rules"
        logMsg(msgLog, 1, 2)

    def _finalize_rules_data(self, rulesNew, srcs, more, mor):
        available = {}
        myKeys = {}
        myIniKeys = []
        for i, src in enumerate(rulesNew.keys()):
            if not src:
                continue
            iniK, nameK = self.getIniKey(
                self.getNameRule(src).upper(), myKeys, myIniKeys
            )
            if iniK not in available:
                available[iniK] = {
                    "name": self.getNameRule(src),
                    "data": [],
                    "social": [],
                }
                available[iniK]["data"] = []
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
            if rulesNew[key]:
                self.rules[key] = rulesNew[key]

        msgLog = f"More: {mor}"
        logMsg(msgLog, 2, 0)
        if hasattr(self, "args") and self.args.rules:
            self.printDict(rulesNew, "Rules")

        msgLog = f"Available: {self.available}"
        logMsg(msgLog, 2, 0)
        msgLog = f"Rules: {self.rules}"
        logMsg(msgLog, 2, 0)
        msgLog = f"Rules keys: {list(self.rules.keys())}"
        logMsg(msgLog, 2, 0)
        self.more = mor

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

        logging.info(f"Selected rule: {iRul}. Rule {src} ")
        print(f" Selected rule: {iRul}. Rule {src} ")
        logging.debug(f" Selected more: {self.more} ")
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
        service = [name] if not isinstance(name, list) else name

        for name_ser in service:
            logging.debug(f"Name: {name_ser}, Selectors: {selector2}, {selector3}")
            for src in self.rules.keys():
                # Primary filter: rule name must match the service name
                if name_ser.capitalize() not in self.getNameRule(src).capitalize():
                    continue

                # If we are here, the name matches. Now evaluate selectors.
                if not selector2:
                    # No second selector, so we add the rule
                    rules.append(src)
                    continue

                # A second selector is present, it must match
                # FIXME: ??
                if selector2 in self.getProfileAction(src):
                    # The second selector matches. Now check the third.
                    if not selector3 or selector3 in self.getTypeRule(src):
                        # No third selector, or the third selector also matches.
                        rules.append(src)

        # Fallback: if no rules were found, search by action name
        if not rules:
            for name_ser in service:
                for src in self.rules.keys():
                    for action in self.rules[src]:
                        if self.getNameAction(action).capitalize() == name_ser.capitalize():
                            if src not in rules:
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
        modulesFiles = os.listdir(f"{path}/socialModules")
        logging.debug(f"{self.indent}modulesFiles: {modulesFiles}")
        modules = {"special": ["cache", "direct"], "regular": [], "other": ["service"]}
        # Initialized with some special services
        name = "module"
        for module in modulesFiles:
            if module.startswith(name) and module.endswith(".py") and module not in ["moduleRules.py", "configMod.py", "testingSrcDst.py"]:
                moduleName = module[len(name) : -3].lower()
                logging.debug(f"{self.indent}moduleName: {moduleName}")
                if moduleName not in modules["special"]:
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

    def getNickSrc(self, src: Union[Rule, tuple]):
        if isinstance(src, Rule):
            return src.profile
        elif isinstance(src[2], tuple):
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

    def getRuleComponent(self, rule: Union[Rule, tuple], pos: int) -> str:
        res = ""
        if isinstance(rule, Rule):
            if pos == 0:
                res = rule.service
            elif pos == 1:
                res = rule.method
            elif pos == 2:
                res = rule.profile
            elif pos == 3:
                res = rule.post_type
        elif isinstance(rule, tuple):
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
        if isinstance(rule, Rule) and "rss" not in rule.service:
            msgLog = (
                f"{indent} {typeC} Error. " f"No client for {rule} ({action}). End."
            )
        elif not isinstance(rule, Rule) and "rss" not in rule:
            msgLog = (
                f"{indent} {typeC} Error. " f"No client for {rule} ({action}). End."
            )
        return f"{msgLog}"

    def readConfigSrc(self, indent, src, more):
        msgLog = f"{indent} Start readConfigSrc {src}"
        logMsg(msgLog, 2, 0)
        indent = f"{indent} "

        profile = self.getNameRule(src)
        msgLog = f"{indent} profile {profile}"
        logMsg(msgLog, 2, 0)
        account = self.getProfileRule(src)
        msgLog = f"{indent} account {account}"
        logMsg(msgLog, 2, 0)
        if "channel" in more:
            apiSrc = getApi(profile, account, indent, more["channel"])
        else:
            apiSrc = getApi(profile, account, indent)
        msgLog = f"{indent} readConfigSrc clientttt {apiSrc.getClient()}"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        apiSrc.src = src
        apiSrc.setPostsType(src.post_type)
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
        if isinstance(action, Rule):
            if pos == 0:
                res = action.service
            elif pos == 1:
                res = action.method
            elif pos == 2:
                res = action.profile
            elif pos == 3:
                res = action.post_type
        elif isinstance(action, tuple) and (len(action) == 4):
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
                    f"{len(listPosts2[0])}:"
                )
                for i, post in enumerate(listPosts):
                    for j, line in enumerate(listPosts[i]):
                        if line:
                            if listPosts[i][j] != listPosts2[i][j]:
                                print(
                                    f"{j}) *{listPosts[i][j]}* "
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

            cmd_method = None
            cmd_args = []

            if nextPost:
                cmd_method = getattr(apiSrc, f"{postaction}NextPost", None)
                # Heuristic: if method takes more than 'self', assume it needs apiDst
                if cmd_method and hasattr(cmd_method, '__code__') and cmd_method.__code__.co_argcount > 1:
                    cmd_args = [apiDst]
            else:
                cmd_method = getattr(apiSrc, f"{postaction}", None)
                # Heuristic: if method takes more than 'self', assume it needs pos
                if cmd_method and hasattr(cmd_method, '__code__') and cmd_method.__code__.co_argcount > 1:
                    cmd_args = [pos]

            if cmd_method:
                try:
                    resPost = cmd_method(*cmd_args)
                except TypeError as e:
                    logMsg(f"{indent}Error calling {postaction} with args {cmd_args}: {e}", 3, 1)
                    resPost = f"Error: {e}"
                except Exception as e:
                    logMsg(f"{indent}Unexpected error calling {postaction} with args {cmd_args}: {e}", 3, 1)
                    resPost = f"Unexpected Error: {e}"

                msgLog = f"{indent}End {postaction}, reply: {resPost} "
                logMsg(msgLog, 1, 1)
                resMsg += f" Post Action: {resPost}"
            else:
                msgLog = f"{indent}No callable method found for post action {postaction}"
                logMsg(msgLog, 1, 1)
                resMsg += f" No callable method for {postaction}"
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

            for src in sorted(self.rules.keys(), key=lambda rule: rule.service):
                logging.debug(f"{self.indent}Rules to process: {self.rules.keys()}")
                logging.debug(f"{self.indent}Select filter: {select}")
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
                    textEnd = f"{textEnd} {msgLog}"
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
                        messages.append(f"  Published in: {future} {res} ")
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
                text_sel = f"{text_sel} {i}) {elem}"
            try:
                columns, rows = shutil.get_terminal_size()
            except OSError:
                columns, rows = 80, 24
            logging.info(f"Rows: {rows} Columns: {columns}")
            if text_sel.count(' ') > int(rows) -2:
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

    def readArgs(self):

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
        # filename=f"{LOGDIR}/rssSocial.log",
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
