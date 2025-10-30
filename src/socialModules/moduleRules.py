import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import sys
import time
import datetime

import socialModules
from socialModules.configMod import (
    logMsg,
    getApi,
    getModule,
    CONFIGDIR,
    LOGDIR,
    select_from_list,
)

fileName = socialModules.__file__
path = f"{os.path.dirname(fileName)}"

hasSet = {}
hasPublish = {}
myModuleList = {}


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class moduleRules:
    def checkRules(self, configFile=None, select=None):
        """
        Reads the configuration file, processes each section, and builds the
        publishing rules.  Includes exhaustive validation and error handling.
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
            if os.path.isabs(configFile) and os.path.exists(configFile):
                config.read(configFile)
            else:
                configFile = f"{CONFIGDIR}/{configFile}"
                config.read(configFile)
        except Exception as e:
            logMsg(f"ERROR: Could not read configuration file: {e}", 3, 1)
            raise ConfigError(f"Could not read configuration file: {e}")

        indent = "  "
        services = self.getServices(indent)
        logging.debug(f"{indent}Services: {services}")
        services["regular"].append("cache")

        sources, sources_available, destinations = set(), set(), set()
        more, temp_rules, rulesNew, rule_metadata, implicit_rules = [], {}, {}, {}, []

        for section in config.sections():
            if select and section != select:
                continue
            msgLog = f" Section: {section}"
            logMsg(msgLog, 2, 0)
            section_indent = f"{indent}{section}>"
            try:
                self._process_section(
                    section_indent,
                    section,
                    config,
                    services,
                    sources,
                    sources_available,
                    more,
                    destinations,
                    temp_rules,
                    rulesNew,
                    rule_metadata,
                    implicit_rules,
                )
            except ConfigError as ce:
                logMsg(f"ERROR in section [{section}]: {ce}", 3, 1)
                raise
            except Exception as e:
                logMsg(f"UNEXPECTED ERROR in section [{section}]: {e}", 3, 1)
                continue

        self._finalize_rules(
            indent,
            config,
            services,
            sources,
            sources_available,
            more,
            destinations,
            rulesNew,
        )
        self._set_available_and_rules(rulesNew, more)
        self.more = rule_metadata
        msgLog = "End Checking rules"
        logMsg(msgLog, 1, 2)
        msgLog = f"Rules: {rulesNew}"
        logMsg(msgLog, 2, 0)

    def _process_section(
        self,
        indent,
        section,
        config,
        services,
        sources,
        sources_available,
        more,
        destinations,
        temp_rules,
        rulesNew,
        rule_metadata,
        implicit_rules,
    ):
        required_keys = ["url", "service"]
        section_dict = dict(config.items(section))
        for key in required_keys:
            if key not in section_dict or not section_dict[key].strip():
                raise ConfigError(
                    f"Missing required key '{key}' or it is empty in section [{section}]"
                )
        url = section_dict["url"]
        logMsg(f"{indent} Url: {url}", 1, 1)
        section_metadata = dict(config.items(section))
        toAppend, theService, api = self._process_sources(
            indent,
            section,
            config,
            services,
            url,
            section_metadata,
            sources,
            sources_available,
            more,
        )
        fromSrv = toAppend
        logMsg(f"{indent} We will append: {toAppend}", 2, 0)
        if toAppend:
            service = toAppend[0]
        postsType = section_dict.get("posts", "posts")
        child_indent = indent + "  "
        logMsg(f"{child_indent} Type: {postsType}", 2, 0)
        if fromSrv:
            fromSrv = (fromSrv[0], fromSrv[1], fromSrv[2], postsType)
            logMsg(f"{child_indent} Checking actions for {service}", 1, 0)
            self._process_destinations(
                child_indent,
                section,
                config,
                service,
                services,
                fromSrv,
                section_metadata,
                api,
                destinations,
                temp_rules,
                rule_metadata,
                implicit_rules,
            )
        self._process_rule_keys(
            child_indent, section_metadata, services, fromSrv, rulesNew, rule_metadata
        )
        section_metadata["section_name"] = section

    def _process_sources(
        self,
        indent,
        section,
        config,
        services,
        url,
        section_metadata,
        sources,
        sources_available,
        more,
    ):
        toAppend = ""
        theService = None
        api = None
        for service in services["regular"]:
            if (("service" in config[section]) and (
                service == config[section]["service"])
            ):
                theService = service
                api = getModule(service, indent)
                api.setUrl(url)
                if service in config[section]:
                    serviceData = config.get(section, service)
                    api.setService(service, serviceData)
                if service in config[section]:
                    api.setNick(config[section][service])
                else:
                    api.setNick()
                methods = self.hasSetMethods(indent + "  ", service)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(
                            f"WARNING: Unexpected method in {service}: {method}", 2, 1
                        )
                        continue
                    if "posts" in section_metadata:
                        if section_metadata["posts"] == method[1]:
                            toAppend = (theService, "set", api.getNick(), method[1])
                    else:
                        toAppend = (theService, "set", api.getNick(), method[1])
                    if toAppend not in sources:
                        if ("posts" in section_metadata) and (
                            section_metadata["posts"] == method[1]
                        ):
                            sources.add(toAppend)
                            more.append(section_metadata)
                        else:
                            sources_available.add(toAppend)
                logMsg(f"{indent} Service: {service}", 2, 0)
        return toAppend, theService, api

    def _process_destinations(
        self,
        indent,
        section,
        config,
        service,
        services,
        fromSrv,
        section_metadata,
        api,
        destinations,
        temp_rules,
        rule_metadata,
        implicit_rules,
    ):
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
                    if toAppend not in destinations:
                        if "service" not in toAppend:
                            destinations.add(toAppend)
                    if toAppend:
                        if fromSrv not in rule_metadata:
                            rule_metadata[fromSrv] = section_metadata
                        if fromSrv in temp_rules:
                            if toAppend not in temp_rules[fromSrv]:
                                temp_rules[fromSrv].append(toAppend)
                        else:
                            temp_rules[fromSrv] = [toAppend]
                        if serviceS == "cache":
                            hasSpecial = True
        child_indent = indent + "  "
        for serviceD in services["regular"]:
            if (
                (serviceD == "cache")
                or (serviceD == "xmlrpc")
                or (fromSrv and serviceD == fromSrv[0])
            ):
                continue
            toAppend = ""
            if serviceD in config.options(section):
                logMsg(
                    f"{child_indent} Service {service} -> {serviceD} checking ", 2, 0
                )
                methods = self.hasPublishMethod(child_indent + "  ", serviceD)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(
                            f"WARNING: Unexpected method in {serviceD}: {method}", 2, 1
                        )
                        continue
                    mmethod = method[1] if method[1] else "post"
                    toAppend = (
                        "direct",
                        mmethod,
                        serviceD,
                        config.get(section, serviceD),
                    )
                    if toAppend not in destinations:
                        destinations.add(toAppend)
                    if toAppend:
                        if hasSpecial:
                            nickSn = f"{toAppend[2]}@{toAppend[3]}"
                            fromSrvSp = (
                                "cache",
                                (fromSrv[0], fromSrv[2]),
                                nickSn,
                                "posts",
                            )
                            implicit_rules.append((fromSrvSp, toAppend))
                            if fromSrvSp not in rule_metadata:
                                rule_metadata[fromSrvSp] = section_metadata
                            if fromSrvSp in temp_rules:
                                if toAppend not in temp_rules[fromSrvSp]:
                                    temp_rules[fromSrvSp].append(toAppend)
                            else:
                                temp_rules[fromSrvSp] = [toAppend]
                        else:
                            if not (
                                fromSrv[2] != toAppend[3]
                                and fromSrv[3][:-1] != toAppend[1]
                            ):
                                if fromSrv not in rule_metadata:
                                    rule_metadata[fromSrv] = section_metadata
                                if fromSrv in temp_rules:
                                    if toAppend not in temp_rules[fromSrv]:
                                        temp_rules[fromSrv].append(toAppend)
                                else:
                                    temp_rules[fromSrv] = [toAppend]

    def _process_rule_keys(
        self, indent, section_metadata, services, fromSrv, rulesNew, rule_metadata
    ):
        logMsg(f"{indent} Processing services in more", 2, 0)
        child_indent = indent + "  "
        logMsg(f"{child_indent} section_metadata: {section_metadata}", 2, 0)
        grandchild_indent = child_indent + "  "
        orig = None
        dest = None
        for key in section_metadata.keys():
            service = section_metadata[key] if key == "service" else key
            if not orig:
                if service in services["special"]:
                    logMsg(f"{grandchild_indent} Service {service} special", 2, 0)
                    orig = service
                elif service in services["regular"]:
                    logMsg(f"{grandchild_indent} Service {service} regular", 2, 0)
                    orig = service
                else:
                    logMsg(
                        f"{grandchild_indent} Service {service} not interesting", 2, 0
                    )
            else:
                logMsg(f"{grandchild_indent} Service {service} not orig", 2, 0)
                if (key in services["special"]) or (key in services["regular"]):
                    if key == "cache":
                        dest = key
                    elif key == "direct":
                        dest = key
                    elif self.hasPublishMethod(grandchild_indent, key):
                        if not dest:
                            dest = "direct"
                        destRuleNew = ""
                        destRuleCache = ""
                        fromCacheNew = ""
                        if dest == "direct":
                            destRule = (
                                dest,
                                "post",
                                key,
                                section_metadata.get(key, ""),
                            )
                        else:
                            destRule = (
                                dest,
                                section_metadata.get("url", ""),
                                key,
                                section_metadata.get(key, ""),
                            )
                            destRuleNew = (
                                dest,
                                section_metadata.get("service", ""),
                                ("direct", "post", key, section_metadata.get(key, "")),
                                section_metadata.get("url", ""),
                            )
                            fromCacheNew = (
                                "cache",
                                section_metadata.get("service", ""),
                                ("direct", "post", key, section_metadata.get(key, "")),
                                section_metadata.get("url", ""),
                            )
                            destRuleCache = (
                                "direct",
                                "post",
                                key,
                                section_metadata.get(key, ""),
                            )
                            if fromCacheNew and destRuleCache:
                                if fromCacheNew not in rulesNew:
                                    rulesNew[fromCacheNew] = []
                                rulesNew[fromCacheNew].append(destRuleCache)
                                rule_metadata[fromCacheNew] = section_metadata
                        great_grandchild_indent = grandchild_indent + "  "
                        logMsg(
                            f"{great_grandchild_indent} Rule: {orig} -> {key}({dest})",
                            2,
                            0,
                        )
                        great_great_grandchild_indent = great_grandchild_indent + "  "
                        logMsg(
                            f"{great_great_grandchild_indent} from Srv: {fromSrv}", 2, 0
                        )
                        logMsg(
                            f"{great_great_grandchild_indent} dest Rule: {destRule}",
                            2,
                            0,
                        )
                        channels = (
                            section_metadata["channel"].split(",")
                            if "channel" in section_metadata
                            else ["set"]
                        )
                        for chan in channels:
                            if fromSrv and (destRuleNew or destRule):
                                fromSrvN = (fromSrv[0], chan, fromSrv[2], fromSrv[3])
                                if fromSrvN not in rulesNew:
                                    rulesNew[fromSrvN] = []
                                if destRuleNew:
                                    rulesNew[fromSrvN].append(destRuleNew)
                                else:
                                    rulesNew[fromSrvN].append(destRule)
                                rule_metadata[fromSrvN] = dict(section_metadata)
                                if chan != "set":
                                    rule_metadata[fromSrvN].update(
                                        {"posts": chan, "channel": chan}
                                    )

    def _finalize_rules(
        self,
        indent,
        config,
        services,
        sources,
        sources_available,
        more,
        destinations,
        rulesNew,
    ):
        for src in sources_available:
            if src:
                if src not in rulesNew:
                    rulesNew[src] = []
                if src not in sources:
                    sources.add(src)
                    more.append({})
        logging.info(f"Srcs: {list(sources)}")
        logging.info(f"SrcsA: {list(sources_available)}")
        logMsg(f"{indent}Destinations:", 1, 0)
        for dst in destinations:
            if not isinstance(dst, tuple) or len(dst) < 4:
                logMsg(f"WARNING: Unexpected destination: {dst}", 2, 1)
                continue
            if dst[0] == "direct":
                service = dst[2]
                methods = self.hasSetMethods(indent, service)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(
                            f"WARNING: Unexpected method in {service}: {method}", 2, 1
                        )
                        continue
                    toAppend = (service, "set", dst[3], method[1])
                    if toAppend[:4] not in sources:
                        sources.add(toAppend[:4])
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
                if toAppend[:4] not in sources:
                    sources.add(toAppend[:4])
                    more.append({})
        self._srcs = list(sources)
        self._srcsA = list(sources_available)
        self._dsts = list(destinations)

    def _set_available_and_rules(self, rulesNew, more):
        available = {}
        myKeys = {}
        myIniKeys = []
        for i, src in enumerate(rulesNew.keys()):
            if not src:
                continue
            section_name = self.getNameRule(src)
            iniK, nameK = self.getIniKey(section_name.upper(), myKeys, myIniKeys)
            if iniK not in available:
                available[iniK] = {"name": section_name, "data": [], "social": []}
            more_i = more[i] if i < len(more) and isinstance(more[i], dict) else {}
            available[iniK]["data"].append({"src": src, "more": more_i})
        myList = [
            f"{elem}) {available[elem]['name']}: {len(available[elem]['data'])}"
            for elem in available
        ]
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
        if not isinstance(service, list):
            service = [
                service,
            ]
        selRules = []
        logging.info(f"Services: {service}")
        for ser in service:
            logging.info(f"Service: {ser}")
            selRules = selRules + self.selectRule(ser, "")
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
            service = [
                name,
            ]
        for name_ser in service:
            logging.info(f"Name: {name_ser}, "
                         f"Selectors: {selector2}, "
                         f"{selector3}")
            for src in self.rules.keys():
                if name_ser.capitalize() in self.getNameRule(src).capitalize():
                    logging.debug(f"profileR: {self.getProfileRule(src)}")
                    logging.debug(f"profileR: {self.getProfileAction(src)}")
                    if not selector2:
                        rules.append(src)
                    else:
                        if selector2 in self.getProfileAction(src):
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

    def hasSetMethods(self, indent, service):
        msgLog = f"{indent} Service {service} checking set methods"
        logMsg(msgLog, 2, 0)
        if service == "social":
            return []
        if service in hasSet:
            msgLog = f"{indent} Service {service} cached"
            logMsg(msgLog, 2, 0)
            listMethods = hasSet[service]
        else:
            clsService = getModule(service, indent)
            listMethods = clsService.__dir__()
            hasSet[service] = listMethods
        methods = []
        for method in listMethods:
            if (not method.startswith("__")) and (method.find("set") >= 0):
                action = "set"
                target = ""
                try:
                    myModule = eval(f"clsService.{method}.__module__")
                    myModuleList[(service, method)] = myModule
                except:
                    myModule = myModuleList[(service, method)]
                if method.find("Api") >= 0:
                    target = method[len("setApi") :].lower()
                elif myModule == f"module{service.capitalize()}":
                    target = method[len("set") :].lower()
                if target and (
                    target.lower()
                    in ["posts", "drafts", "favs", "messages", "queue", "search"]
                ):
                    toAppend = (action, target)
                    if toAppend not in methods:
                        methods.append(toAppend)
        return methods

    def hasPublishMethod(self, indent, service):
        msgLog = f"{indent} Start Checking service publish methods"
        logMsg(msgLog, 2, 0)
        if service in hasPublish:
            msgLog = f"{indent}  Service {service} cached"
            logMsg(msgLog, 2, 0)
            listMethods = hasPublish[service]
        else:
            clsService = getModule(service, indent)
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
                    msgLog = f"{indent} Service target: {target}"
                    logMsg(msgLog, 2, 0)
                    toAppend = (action, target)
                    if toAppend not in methods:
                        methods.append(toAppend)
        return methods

    def getServices(self, indent=""):
        msgLog = f"{indent} Start getServices"
        logMsg(msgLog, 2, 0)
        modulesFiles = os.listdir(path)
        modules = {"special": ["cache", "direct"], "regular": [], "other": ["service"]}
        name = "module"
        for module in modulesFiles:
            if module.startswith(name):
                moduleName = module[len(name) : -3].lower()
                if moduleName not in modules["special"]:
                    modules["regular"].append(moduleName)
        msgLog = f"{indent} End getServices"
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
        if service:
            url = url.replace(service, "")
        url = url.replace("https", "").replace("http", "")
        url = url.replace("---", "").replace(".com", "")
        url = url.replace("-", "(").replace("- ", " ")
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
            nick = self.getActionComponent(action, 2)
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
            idR = f"{self.getRuleComponent(subC, 3)}@{self.getRuleComponent(subC, 2)}@{self.getRuleComponent(rule, 0)}[{self.getRuleComponent(rule, 3)}]"
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
        logMsg(msgLog, 2, 1)
        child_indent = f"{indent} "
        profile = self.getNameRule(src)
        account = self.getProfileRule(src)
        if more and "channel" in more:
            apiSrc = getApi(profile, account, child_indent, more["channel"])
        else:
            apiSrc = getApi(profile, account, child_indent)

        if apiSrc is not None:
            # msgLog = f"{child_indent} readConfigSrc clientttt {apiSrc.getClient()}"  #: {src[1:]}"
            # logMsg(msgLog, 2, 0)
            apiSrc.src = src
            apiSrc.setPostsType(src[-1])
            apiSrc.setMoreValues(more)
            apiSrc.indent = indent
        else:
            logMsg(f"{indent} Failed to get API for source: {src}", 3, 1)

        msgLog = f"{indent} End readConfigSrc"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
        return apiSrc

    def getActionComponent(self, action, pos):
        res = ""
        if isinstance(action, tuple) and (len(action) == 4):
            res = action[pos]
        return res

    def readConfigDst(self, indent, action, more, apiSrc):
        msgLog = f"{indent} Start readConfigDst {action}"  #: {src[1:]}"
        logMsg(msgLog, 2, 1)
        child_indent = f"{indent} "
        profile = self.getNameAction(action)
        account = self.getDestAction(action)
        apiDst = getApi(profile, account, child_indent)

        if apiDst is not None:
            apiDst.setMoreValues(more)
            apiDst.indent = child_indent
            # msgLog = f"{child_indent} apiDstt {apiDst}"  #: {src[1:]}"
            # logMsg(msgLog, 2, 0)
            # msgLog = f"{child_indent} apiDstt {apiDst.client}"  #: {src[1:]}"
            # logMsg(msgLog, 2, 0)
            if apiSrc:
                apiDst.setUrl(apiSrc.getUrl())
            else:
                apiDst.setUrl(None)
            if apiSrc:
                apiDst.setLastLink(apiSrc)
            else:
                apiDst.setLastLink(apiDst)
        else:
            logMsg(f"{indent} Failed to get API for destination: {action}", 3, 1)

        msgLog = f"{indent} End readConfigDst"  #: {src[1:]}"
        logMsg(msgLog, 2, 0)
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
        if listPosts2:
            if listPosts == listPosts2:
                print("{indent} Equal listPosts")
            else:
                print(
                    f"{indent} Differ listPosts (len {len(listPosts[0])}, {len(listPosts2[0])}:\n"
                )
                for i, post in enumerate(listPosts):
                    for j, line in enumerate(listPosts[i]):
                        if line:
                            if listPosts[i][j] != listPosts2[i][j]:
                                print(
                                    f"{j}) *{listPosts[i][j]}*\n{j}) *{listPosts2[i][j]}*"
                                )
                        else:
                            print(f"{j})")
        else:
            print(f"{indent}No listPosts2")

    def executePostAction(
        self, indent, msgAction, apiSrc, apiDst, simmulate, nextPost, pos, res
    ):
        resPost = f"{res}"
        resMsg = ""
        logMsg(f"{indent}Trying to execute Post Action", 1, 1)
        logMsg(f"{indent}Post Action ressss {res}", 1, 1)
        postaction = apiSrc.getPostAction()
        if postaction:
            logMsg(f"{indent}Post Action {postaction} (nextPost = {nextPost})", 1, 1)
            if "OK. Published!" in res:
                logMsg(f"{indent} Res {res} is OK", 1, 0)
                if nextPost:
                    logMsg(f"{indent}Post Action next post", 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost()
                else:
                    logMsg(f"{indent}Post Action pos post", 2, 0)
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
            logMsg(f"{indent}End {postaction}, reply: {resPost} ", 1, 1)
            resMsg += f" Post Action: {resPost}"
            if (
                (res and ("failed!" not in res) and ("Fail!" not in res))
                or (res and ("abusive!" in res))
                or (
                    ((not res) and ("OK. Published!" not in res))
                    or ("duplicate" in res)
                )
            ):
                logMsg(f"{indent} Res {res} is not OK", 1, 0)
                if nextPost:
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resPost = cmdPost(apiDst)
                else:
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resPost = cmdPost(pos)
                logMsg(f"{indent}Post Action command {cmdPost}", 1, 1)
                logMsg(f"{indent}End {postaction}, reply: {resPost} ", 1, 1)
                resMsg += f"Post Action: {resPost}"
            else:
                logMsg(f"{indent}Something went wrong", 1, 1)
        else:
            logMsg(f"{indent}No Post Action", 1, 1)
        return resMsg

    def executePublishAction(
        self,
        indent,
        msgAction,
        apiSrc,
        apiDst,
        simmulate,
        nextPost=True,
        pos=-1,
        src=None,
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
            msgLog = f"Title: {title}"
            if link:
                msgLog = f"{msgLog} Recording Link: {link} in file {apiDst.fileNameBase(apiSrc)}.last"
        else:
            msgLog = f"{indent}No post to schedule in {msgAction}"
        if simmulate:
            if post:
                logMsg(f"{indent}Would schedule in {msgAction} {msgLog}", 1, 1)
            resMsg = ""
        else:
            res = ""
            if post:
                logMsg(f"{indent}Will publish in {msgAction} {msgLog}", 1, 1)
                res = apiDst.publishPost(api=apiSrc, post=post)
                logMsg(f"{indent}Reply: {res}", 1, 1)
                logMsg(f"{indent}Trying to publish {msgLog} ", 1, 1)
                if nextPost and (
                    res and ("Fail!" not in res) and ("failed!" not in res)
                ):
                    link = apiSrc.getPostLink(post)
                    if (apiSrc
                        # and self.getNameRule(src) != "cache"
                        # and ('imgur' not in link or apiDst.profile != 'imgur')
                        ):
                        resUpdate = apiDst.updateLastLink(apiSrc, link)
                        resMsg += f" Update: {resUpdate}"
            if res:
                logMsg(f"{indent}Res: {res} ", 2, 0)
            if post:
                resMsg = self.executePostAction(
                    indent, msgAction, apiSrc, apiDst, simmulate, nextPost, pos, res
                )
            logMsg(f"{indent}End publish, reply: {resMsg}", 1, 1)
        # if postaction == "delete":
        #     msgLog = f"{indent}Available {len(apiSrc.getPosts())-1}"
        # else:
        #     msgLog = f"{indent}Available {len(apiSrc.getPosts())}"
        # logMsg(msgLog, 1, 1)
        return resMsg

    def executeAction(
        self,
        src,
        more,
        action,
        msgAction,
        apiSrc,
        apiDst,
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
        orig = (
                f"{self.getNickRule(src)}@{self.getNameAction(src)} "
                f"({self.getTypeRule(src)})"
                )
        dest = (
                f"{self.getNickAction(action)}@{self.getNameAction(action)} "
                f"({self.getTypeAction(action)})"
                )
        logMsg(f"{indent} Scheduling {orig} -> {dest}", 1, 1)
        if not apiDst.getClient():
            msgLog = self.clientErrorMsg(
                indent,
                apiDst,
                "Destination",
                (f"{self.getNameRule(src)}@{self.getProfileRule(src)}"),
                self.getNickAction(src),
            )
            if msgLog:
                logMsg(msgLog, 3, 1)
                sys.stderr.write(f"Error: {msgLog}\n")
            return f"End: {msgLog}"
        backup_time = apiDst.getNextTime(apiSrc)
        tL = random.random() * numAct
        child_indent = f"{indent} "
        logMsg(
            (f"{child_indent} Sleeping {tL:.2f} seconds ({numAct} "
            "actions) to launch all processes"),
            1,
            0,
        )
        numAct = max(3, numAct)
        time.sleep(tL)
        logMsg(f"{child_indent} Go!", 1, 0)
        grandchild_indent = f"{child_indent} "
        res = {}
        time.sleep(1)
        msgLog = ""
        if nextPost:
            num = apiDst.getMax()
        else:
            num = 1

        if num > 0:
            theAction = self.getTypeAction(action)
            msgFrom = (f"{theAction} from {apiSrc.getUrl()} in "
                       f"{self.getNickAction(action)}@"
                       f"{self.getProfileAction(action)}\n"
                       )
            logMsg(f"{grandchild_indent}I'll publish {num} {msgFrom}", 1, 1)

            tNow = time.time()
            hours = float(apiDst.getTime()) * 60 * 60
            lastTime = apiDst.getLastTimePublished(f"{grandchild_indent}")
            if lastTime:
                diffTime = tNow - lastTime
            else:
                diffTime = hours + 1

            tSleep = random.random() * float(timeSlots) * 60

            # Reserve the time slot by setting the new time
            apiDst.setNextTime(tNow, tSleep, apiSrc)

            if tSleep > 0.0:
                msgLog = f"{grandchild_indent} Waiting {tSleep/60:2.2f} minutes"
            else:
                tSleep = 2.0
                msgLog = f"{grandchild_indent} No Waiting"

            logMsg(f"{msgLog} for {msgFrom}", 1, 1)

            for i in range(num):
                time.sleep(tSleep)
                if "minutes" in msgLog:
                    logMsg(f"{grandchild_indent} End Waiting {msgFrom}", 1, 1)

                res = self.executePublishAction(
                    grandchild_indent,
                    msgAction,
                    apiSrc,
                    apiDst,
                    simmulate,
                    nextPost,
                    pos,
                )

            # If no publication happened, restore the previous time

            if isinstance(res, dict) and not res.get("success") and backup_time[0] is not None:
                logMsg(f"{grandchild_indent} No publication occurred. Restoring previous next-run time.", 1, 1)
                apiDst.setNextTime(backup_time[0], backup_time[1], apiSrc)

        else:
            msgLog = f"{grandchild_indent} No posts available"
            logMsg(msgLog, 1, 1)

        logMsg(f"{child_indent} End executeAction {msgLog}", 2, 0)
        return res


    def executeRules(self, max_workers=None):
        import os

        logMsg("Start Executing rules", 1, 2)
        self.indent = ""
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
        logMsg(f"End Executing rules with {len(scheduled_actions)} actions.", 1, 2)
        return

    def _should_skip_publication(self, apiDst, apiSrc, noWait, timeSlots, nameA):
        indent = nameA
        num = apiDst.getMax()
        if num <= 0:
            logMsg(f"{indent} No posts available", 1, 1)
            return True

        tNow = time.time()
        hours = float(apiDst.getTime()) * 60 * 60
        lastTime = apiDst.getLastTimePublished(f"{indent}")

        if lastTime:
            diffTime = tNow - lastTime
        else:
            diffTime = hours + 1

        if not noWait and (diffTime <= hours):
            msgLog = (
                f"{indent} Not enough time passed. "
                f"We will wait at least "
                f"{(hours-diffTime)/(60*60):2.2f} hours."
            )
            logMsg(msgLog, 1, 1)
            return True
        return False

    def _prepare_actions(self, args, select):
        """
        Prepares the list of actions to execute, filtering and collecting all
        necessary information.  Returns a list of dictionaries with data for
        each action.
        """
        scheduled_actions = []
        previous = ""
        i = 0  # Initialize i outside the loop to avoid UnboundLocalError
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
            nameR = f"[{self.getNameAction(rule_key)}{i}]"
            msgLog = (f"{nameR:->12}> "
                          f"Preparing actions for rule: "
                          f"{self.getNickSrc(rule_key)}@"
                          f"{self.getNameRule(rule_key)} "
                          f"({self.getNickAction(rule_key)})")
            logMsg(msgLog, 1, 1)
            previous = self.getNameAction(rule_key)

            for action_index, rule_action in enumerate(rule_actions):
                # Rule selection if --checkBlog is used
                name_action = f"[{self.getNameAction(rule_key)}{i}]"
                nameR_action = f"{name_action:->12}>"
                nameA =  f"{nameR_action} Action {action_index}:"

                if select and (select.lower() != f"{self.getNameRule(rule_key).lower()}{i}"):
                    continue

                apiSrc = self.readConfigSrc(nameR_action, rule_key, rule_metadata)
                if not apiSrc:
                    logMsg(f"ERROR: Could not create apiSrc for rule {rule_key}", 3, 1)
                    continue

                apiDst = self.readConfigDst(nameR_action, rule_action, rule_metadata, apiSrc)
                if not apiDst:
                    logMsg(f"ERROR: Could not create apiDst for rule {rule_action}", 3, 1)
                    continue

                timeSlots, noWait = self._get_action_properties(
                    rule_action, rule_metadata, args
                )

                if self._should_skip_publication(
                    apiDst, apiSrc, noWait, timeSlots, f"{nameA}"
                ):
                    continue
                scheduled_actions.append(
                    {
                        "rule_key": rule_key,
                        "rule_metadata": rule_metadata,
                        "rule_action": rule_action,
                        "rule_index": i,
                        "action_index": action_index,
                        "args": args,
                        "simmulate": args.simmulate,
                        "apiSrc": apiSrc,
                        "apiDst": apiDst,
                        "name_action": name_action,
                        "nameA": nameA,
                        "timeSlots": timeSlots, # Add timeSlots to scheduled_actions
                        "noWait": noWait,       # Add noWait to scheduled_actions
                    }
                )
        return scheduled_actions

    def _get_action_properties(self, rule_action, rule_metadata, args):
        timeSlots = args.timeSlots
        noWait = args.noWait

        action_name = self.getNameAction(rule_action)
        profile_action = self.getProfileAction(rule_action)

        # Hardcoded logic for specific services
        if (action_name == "cache") or (
            action_name == "direct" and profile_action == "pocket"
        ):
            timeSlots = 0
            noWait = True

        # Override with rule-specific metadata if present
        if rule_metadata and "timeSlots" in rule_metadata:
            try:
                timeSlots = float(rule_metadata["timeSlots"])
            except ValueError:
                logMsg(
                    (f"WARNING: Invalid timeSlots value in rule metadata: "
                     f"{rule_metadata['timeSlots']}"),
                    2, 1,)

        if rule_metadata and "noWait" in rule_metadata:
            noWait_str = str(rule_metadata["noWait"]).lower()
            noWait = noWait_str in ("true", "1", "t", "y", "yes")

        return timeSlots, noWait

    def _run_actions_concurrently(self, scheduled_actions, max_workers=75):
        """
        Executes actions in parallel using ThreadPoolExecutor.
        Returns two lists: results and errors.
        """
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
                res = ''
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
        apiSrc = scheduled_action["apiSrc"]
        apiDst = scheduled_action["apiDst"]
        timeSlots = scheduled_action["timeSlots"] # Get from scheduled_action
        noWait = scheduled_action["noWait"]       # Get from scheduled_action

        msgAction = (
            f"{self.getNameAction(rule_action)} "
            f"{self.getNickAction(rule_action)}@"
            f"{self.getProfileAction(rule_action)} "
            f"({self.getTypeAction(rule_action)})")
        rule_index = scheduled_action.get('rule_index', 0)
        action_index = scheduled_action.get('action_index', 0)
        name_action = f"[{self.getNameAction(rule_key)}{rule_index}]"
        nameR = f"{name_action:->12}>"
        nameA =  f"{nameR} Action {action_index}:"
        return self.executeAction(
            rule_key,
            rule_metadata,
            rule_action,
            msgAction,
            apiSrc,
            apiDst,
            noWait,
            timeSlots,
            simmulate,
            nameA,
            action_index,
        )

    def _report_results(self, action_results, action_errors):
        """
        Reports the results and errors of action execution.
        """
        for scheduled_action, res_dict in action_results:
            rule_key = scheduled_action["rule_key"]
            rule_index = scheduled_action.get("rule_index", "")
            rule_summary = (
                f"Rule {rule_index}: {rule_key}" if rule_index != "" else str(rule_key)
            )

            logging.info(f"Res_dict: {res_dict}")

            if isinstance(res_dict, str) and "OK" in res_dict:
                summary_msg = "Success. Action completed."
                logMsg(
                    f"[OK] Action for {rule_summary} -> {scheduled_action['rule_action']}: {summary_msg}",
                    1,
                    1,
                )
            elif isinstance(res_dict, dict) and res_dict.get("success"):
                pub_res = res_dict.get("publication_result", "N/A")
                post_act = res_dict.get("post_action_result", "N/A")
                summary_msg = f"Success. Pub: '{pub_res}'. Post-Action: '{post_act}'."
                logMsg(
                    f"[OK] Action for {rule_summary} -> {scheduled_action['rule_action']}: {summary_msg}",
                    1,
                    1,
                )
            elif isinstance(res_dict, dict):
                error_msg = res_dict.get("error", "Unknown error")
                logMsg(
                    f"[ERROR] Action failed for {rule_summary} -> "
                    f"{scheduled_action['rule_action']}: {error_msg}",
                    3,
                    1,
                )
            else:
                # Fallback for empty or non-dict results
                logMsg(
                    f"[WARN] Action for {rule_summary} -> {scheduled_action['rule_action']} produced an invalid result: {res_dict}",
                    2,
                    1,
                )

        for scheduled_action, exc in action_errors:
            rule_key = scheduled_action["rule_key"]
            rule_index = scheduled_action.get("rule_index", "")
            rule_summary = (
                f"Rule {rule_index}: {rule_key}" if rule_index != "" else str(rule_key)
            )
            logMsg(
                f"[ERROR] Action failed for {rule_summary} -> {scheduled_action['rule_action']}: {exc}",
                3,
                1,
            )

    def _configure_service_api(
        self, api, destination, channel=None, from_email=None, to_email=None, account=None
    ):
        """
        Configure service-specific API settings

        Args:
            api: Service API instance
            destination: Service name
            channel: Channel for services that support it
            from_email: Email origin for SMTP services
            to_email: Email destination for SMTP services
            account: Account name (fallback for email)
        """
        try:
            # Set channel if supported and provided
            if hasattr(api, "setChannel") and channel:
                api.setChannel(channel)
                logging.debug(f"Channel set to \n'{channel}' for {destination}")

            # Configure SMTP-specific settings
            if "smtp" in destination.lower():
                if hasattr(api, 'fromaddr'):
                    api.fromaddr = from_email or "default@example.com"
                    logging.debug(f"SMTP fromaddr set to {api.fromaddr}")

                if hasattr(api, 'to'):
                    api.to = to_email or account
                    logging.debug(f"SMTP to set to {api.to}")

        except Exception as e:
            logging.warning(f"Error configuring {destination} API: {e}")

    def _extract_image_url(self, api, destination):
        """
        Extract image URL from API response in a generic way

        Args:
            api: Service API instance
            destination: Service name

        Returns:
            str or None: Image URL if found
        """
        image_url = None
        try:
            if hasattr(api, "lastRes") and api.lastRes:
                response = api.lastRes

                # Try different response formats
                # Mastodon format
                if (
                    isinstance(response, dict)
                    and "media_attachments" in response
                    and response["media_attachments"]
                    and isinstance(response["media_attachments"], list)
                    and len(response["media_attachments"]) > 0
                    and "url" in response["media_attachments"][0]
                ):
                    image_url = response["media_attachments"][0]["url"]

                # Twitter format
                elif isinstance(response, dict) and "media" in response:
                    media = response["media"]
                    if isinstance(media, dict) and "media_url" in media:
                        image_url = media["media_url"]
                    elif (
                        isinstance(media, list)
                        and len(media) > 0
                        and "media_url" in media[0]
                    ):
                        image_url = media[0]["media_url"]

                # Generic URL field
                elif isinstance(response, dict):
                    for url_field in ["url", "image_url", "media_url", "attachment_url"]:
                        if url_field in response:
                            image_url = response[url_field]
                            break
                if not image_url:
                    logging.debug(f"No image URL found in {destination} response")

        except Exception as e:
            logging.warning(f"Error extracting image URL from {destination}: {e}")

        return image_url

    def _publish_to_single_destination(
        self,
        destination,
        account,
        title,
        url,
        content,
        image_path=None,
        alt_text="",
        channel=None,
        from_email=None,
        to_email=None,
    ):
        """
        Publish to a single destination

        Args:
            destination: Service name
            account: Account name
            title: Publication title
            url: Content URL
            content: Publication content
            image_path: Image path to publish
            alt_text: Alternative text for image
            channel: Channel for services that support it
            from_email: Email origin for SMTP
            to_email: Email destination for SMTP

        Returns:
            dict: Publication result
        """
        service_key = f"{destination}_{account}"
        result_dict = {{}}

        try:
            # Create key for readConfigDst
            key = ("direct", "post", destination, account)

            # Get service API
            api = self.readConfigDst("  ", key, None, None)

            if not api:
                result_dict = {
                    "success": False,
                    "error": f"Could not initialize API for {destination}",
                    "service": service_key,
                }
            else:
                # Configure service-specific settings
                self._configure_service_api(
                    api, destination, channel, from_email, to_email, account
                )

                # Publish image if provided
                image_url = None
                if image_path and hasattr(api, "publishImage"):
                    try:
                        image_result = api.publishImage(title, image_path, alt=alt_text)
                        image_url = self._extract_image_url(api, destination)
                        logging.info(f"Image published to {destination}: {image_result}")
                    except Exception as e:
                        logging.error(f"Error publishing image to {destination}: {e}")
                        # Continue with text post even if image fails

                # Publish main post
                result = api.publishPost(title, url, content)

                # Validate result
                if self._is_publication_successful(result):
                    logging.info(f"Successfully published to {destination}: {result}")
                    result_dict = {
                        "success": True,
                        "result": result,
                        "image_url": image_url,
                        "service": service_key,
                    }
                else:
                    result_dict = {
                        "success": False,
                        "error": f"Publication returned unsuccessful result: {result}",
                        "result": result,
                        "service": service_key,
                    }

        except Exception as e:
            error_msg = f"Error publishing to {destination}: {e}"
            logging.error(error_msg)
            result_dict = {"success": False, "error": str(e), "service": service_key}
        return result_dict

    def _is_publication_successful(self, result):
        """
        Determine if a publication result indicates success

        Args:
            result: Publication result from API

        Returns:
            bool: True if successful
        """
        successful = True
        if result is None:
            successful = False

        # String results starting with "Fail" are failures
        elif isinstance(result, str) and result.startswith("Fail"):
            successful = False

        # Dict results with explicit success/error indicators
        elif isinstance(result, dict):
            if "success" in result:
                successful = result["success"]
            elif "error" in result:
                successful = False
            else:
                successful = bool(result)
        else:
            successful = bool(result)

        return successful

    def _validate_destinations(self, destinations):
        """
        Validate and normalize destinations parameter

        Args:
            destinations: Dict or list of destinations

        Returns:
            list: Normalized list of (service, account) tuples

        Raises:
            ValueError: If destinations format is invalid
        """
        if not destinations:
            raise ValueError("Destinations cannot be empty")

        normalized = []
        if isinstance(destinations, dict):
            normalized = [
                (service, account) for service, account in destinations.items() if account
            ]
        elif isinstance(destinations, (list, tuple)):
            for item in destinations:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    service, account = item[0], item[1]
                    if account:  # Skip empty accounts
                        normalized.append((service, account))
                else:
                    raise ValueError(f"Invalid destination format: {item}")
        else:
            raise ValueError(
                f"Destinations must be dict or list, got {type(destinations)}"
            )
        return normalized

    def publish_to_multiple_destinations(
        self,
        destinations,
        title,
        url="",
        content="",
        image_path=None,
        alt_text="",
        channel=None,
        from_email=None,
        to_email=None,
    ):
        """
        Publishes content to multiple destinations using unified logic

        Args:
            destinations: Dict with {service: account} or list of tuples (service, account)
            title: Publication title
            url: Content URL (optional)
            content: Publication content (optional)
            image_path: Image path to publish (optional)
            alt_text: Alternative text for image (optional)
            channel: Specific channel for some services (optional)
            from_email: Origin email for SMTP (optional)
            to_email: Destination email for SMTP (optional)

        Returns:
            Dict with results from each publication

        Raises:
            ValueError: If parameters are invalid
        """
        results = {{}}
        # Validate inputs
        if not title and not content:
            raise ValueError("Either title or content must be provided")

        try:
            dest_items = self._validate_destinations(destinations)
            if not dest_items:
                logging.warning("No valid destinations found")
            else:
                logging.info(
                    f"Starting publication to {len(dest_items)} destinations: {title}"
                )

                # Publish to each destination
                for destination, account in dest_items:
                    logging.info(f"Publishing to: {destination} - {account}")

                    result = self._publish_to_single_destination(
                        destination=destination,
                        account=account,
                        title=title,
                        url=url,
                        content=content,
                        image_path=image_path,
                        alt_text=alt_text,
                        channel=channel,
                        from_email=from_email,
                        to_email=to_email,
                    )

                    results[result["service"]] = {
                        "success": result["success"],
                        "result": result.get("result"),
                        "error": result.get("error"),
                        "image_url": result.get("image_url"),
                    }

                # Log summary
                successful = sum(1 for r in results.values() if r.get("success"))
                total = len(results)
                logging.info(f"Publication completed: {successful}/{total} successful")

        except ValueError as e:
            logging.error(f"Invalid destinations: {e}")
            results = {"error": str(e)}

        return results

    def publish_message_to_destinations(self, destinations, message, **kwargs):
        """
        Simplified method to publish only a message

        Args:
            destinations: Dict with {service: account} or list of tuples
            message: Message to publish
            **kwargs: Additional parameters passed to publish_to_multiple_destinations

        Returns:
            Dict with results

        Raises:
            ValueError: If message is empty
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        return self.publish_to_multiple_destinations(
            destinations=destinations,
            title=message,
            url=kwargs.get('url', ''),
            content=kwargs.get('content', ''),
            image_path=kwargs.get('image_path'),
            alt_text=kwargs.get('alt_text', ''),
            channel=kwargs.get('channel'),
            from_email=kwargs.get('from_email'),
            to_email=kwargs.get('to_email')
        )

    def get_publication_summary(self, results):
        """
        Generate a summary of publication results

        Args:
            results: Results dict from publish_to_multiple_destinations

        Returns:
            dict: Summary with statistics and details
        """
        summary = {{}}
        if not results or "error" in results:
            summary = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "error": results.get("error") if results else "No results",
            }
        else:
            successful_services = [k for k, v in results.items() if v.get("success")]
            failed_services = [k for k, v in results.items() if not v.get("success")]

            total = len(results)
            successful_count = len(successful_services)

            summary = {
                "total": total,
                "successful": successful_count,
                "failed": len(failed_services),
                "success_rate": successful_count / total if total > 0 else 0.0,
                "successful_services": successful_services,
                "failed_services": failed_services,
                "response_links": {
                    k: v.get("image_url") or v.get("result")
                    for k, v in results.items()
                    if v.get("success") and (v.get("image_url") or v.get("result"))
                },
                "errors": {
                    k: v.get("error")
                    for k, v in results.items()
                    if not v.get("success") and v.get("error")
                },
            }
        return summary

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
        parser.add_argument(
            "--debug-filenames",
            default=False,
            action="store_true",
            help="Debug rules by showing generated filenames",
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
    rules.indent = ""
    rules.checkRules()

    rules.executeRules()

    return


if __name__ == "__main__":
    main()
