import concurrent.futures
import configparser
import inspect
import logging
import os
import random
import sys
import time

import socialModules
from socialModules.configMod import (
    CONFIGDIR,
    DATADIR,
    extract_nick_from_url,
    getApi,
    getModule,
    logMsg,
    select_from_list,
    thread_local,
)

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
    def __init__(self, args=None):
        class _DummyArgs:
            def __init__(self):
                self.verbose = False
                self.timeSlots = 0
                self.noWait = False
                self.checkBlog = None
                self.simmulate = False

        if args is None:
            self.args = _DummyArgs()
        else:
            self.args = args

    def indentPlus(self):
        if not hasattr(self, "indent"):
            self.indent = " "
        else:
            self.indent = f"{self.indent} "

    def indentLess(self):
        self.indent = self.indent[:-1]

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
            # If it's an absolute path and exists, use it directly
            if os.path.isabs(configFile) and os.path.exists(configFile):
                config.read(configFile)
            else:
                configFile = f"{CONFIGDIR}/{configFile}"
                config.read(configFile)
        except Exception as e:
            logMsg(
                f"ERROR: Could not read configuration file: {e}", 3, self.args.verbose
            )
            raise ConfigError(f"Could not read configuration file: {e}")

        self.indentPlus()
        services = self.getServices()
        logging.debug(f"{self.indent}Services: {services}")
        services["regular"].append("cache")

        # Use sets to avoid duplicates and improve efficiency
        sources, sources_available, destinations = set(), set(), set()
        more, temp_rules, rulesNew, rule_metadata, implicit_rules = [], {}, {}, {}, []

        for section in config.sections():
            if select and section != select:
                continue
            msgLog = f" Section: {section}"
            self.indentPlus()
            logMsg(msgLog, 1, self.args.verbose)
            self.indent = f"{self.indent}{section}>"

            try:
                self._process_section(
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
                logMsg(f"ERROR in section [{section}]: {ce}", 3, self.args.verbose)
                raise  # Reraise the exception so tests can catch it
            except Exception as e:
                logMsg(
                    f"UNEXPECTED ERROR in section [{section}]: {e}",
                    3,
                    self.args.verbose,
                )
                continue

            self.indent = f"{self.indent[:-(len(section)+2)]}"

        self._finalize_rules(
            config, services, sources, sources_available, more, destinations, rulesNew
        )
        msgLog = f"Rules: {rulesNew} after _finalize_rules"
        logMsg(msgLog, 2, False)
        self.more = rule_metadata
        self._set_available_and_rules(rulesNew, more)
        msgLog = f"Rules: {rulesNew} after _set_available_and_rules"
        logMsg(msgLog, 2, False)
        self.indentLess()
        msgLog = "End Checking rules"
        logMsg(msgLog, 1, 2)
        msgLog = f"Rules: {rulesNew}"
        logMsg(msgLog, 2, False)

    def _process_section(
        self,
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
        """
        Processes a section of the configuration file, identifying sources and
        destinations.  Validates the presence of required keys and data types.
        """
        # Robustly validate required keys and ensure they are not empty
        required_keys = ["url", "service"]
        section_dict = dict(config.items(section))
        for key in required_keys:
            if key not in section_dict or not section_dict[key].strip():
                raise ConfigError(
                    f"Missing required key '{key}' or it is empty in section [{section}]"
                )
        url = section_dict["url"]
        msgLog = f"{self.indent} Url: {url}"
        logMsg(msgLog, 1, self.args.verbose)
        section_metadata = dict(config.items(section))
        # Save the section name in section_metadata for traceability
        section_metadata["section_name"] = section
        toAppend, theService, api = self._process_sources(
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
        msgLog = f"{self.indent} We will append: {toAppend}"
        logMsg(msgLog, 2, False)
        if toAppend:
            service = toAppend[0]
        postsType = section_dict.get("posts", "posts")
        self.indentPlus()
        msgLog = f"{self.indent} Type: {postsType}"
        logMsg(msgLog, 2, False)
        if fromSrv:
            fromSrv = (fromSrv[0], fromSrv[1], fromSrv[2], postsType)
            if fromSrv not in rule_metadata:
                rule_metadata[fromSrv] = section_metadata

            # This is the fix:
            # Ensure held rules are added to rulesNew even with no actions
            if section_metadata.get("hold") == "yes":
                if fromSrv not in rulesNew:
                    rulesNew[fromSrv] = []

            msgLog = f"{self.indent} Checking actions for {service}"
            logMsg(msgLog, 1, False)
            self._process_destinations(
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
            section_metadata, services, fromSrv, rulesNew, rule_metadata
        )
        self.indentLess()

    def _process_sources(
        self,
        section,
        config,
        services,
        url,
        section_metadata,
        sources,
        sources_available,
        more,
    ):
        source_tuple = None
        theService = None
        api = None

        # Determine the service name for this section
        section_service_name = config[section].get("service")
        if not section_service_name:
            logMsg(
                f"ERROR: No 'service' defined in section [{section}]",
                3,
                self.args.verbose,
            )
            return None, None, None

        # Process regular services
        if section_service_name in services["regular"]:
            theService = section_service_name
            api = getModule(theService, self.indent)
            api.setUrl(url)
            if theService in config[section]:
                api.setService(theService, config.get(section, theService))
            if theService in config[section]:
                api.setNick(config[section][theService])
            else:
                api.setNick()

            self.indentPlus()
            methods = self.hasSetMethods(theService)
            desired_posts_type = section_metadata.get("posts")

            for method_action, method_target in methods:
                if not isinstance(method_action, str) or not isinstance(
                    method_target, str
                ):
                    logMsg(
                        f"WARNING: Unexpected method in {theService}: {method_action, method_target}",
                        2,
                        self.args.verbose,
                    )
                    continue

                if (
                    desired_posts_type
                ):  # If 'posts' is specified, find that specific method
                    if desired_posts_type == method_target:
                        source_tuple = (
                            theService,
                            method_action,
                            api.getNick(),
                            method_target,
                        )
                        break
                else:  # if method_target == "post": # If no 'posts' specified, default to 'post' method
                    source_tuple = (
                        theService,
                        method_action,
                        api.getNick(),
                        method_target,
                    )
                    break

            if source_tuple:
                if source_tuple not in sources:
                    sources.add(source_tuple)
                    more.append(section_metadata)  # Add metadata for the found source
            else:
                # If no source_tuple was created, it means no suitable method was found
                logMsg(
                    f"WARNING: No suitable source method found for service '{theService}' "
                    f"with posts type '{desired_posts_type}' in section [{section}]",
                    2,
                    self.args.verbose,
                )
                # Add None to sources_available, to reflect that a source could not be formed
                # This might need further refinement depending on desired behavior for missing sources
                sources_available.add(None)

            self.indentLess()
            msgLog = f"{self.indent} Service: {theService}"
            logMsg(msgLog, 1, self.args.verbose)

        return source_tuple, theService, api

    def _process_destinations(
        self,
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
        self.indentPlus()
        for serviceD in services["regular"]:
            if (
                (serviceD == "cache")
                or (serviceD == "xmlrpc")
                or (fromSrv and serviceD == fromSrv[0])
            ):
                continue
            toAppend = ""
            if serviceD in config.options(section):
                msgLog = f"{self.indent} Service {service} -> {serviceD} checking "
                logMsg(msgLog, 2, False)

                methods = self.hasPublishMethod(serviceD)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(
                            f"WARNING: Unexpected method in {serviceD}: {method}",
                            2,
                            self.args.verbose,
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
        self.indentLess()

    def _process_rule_keys(
        self, section_metadata, services, fromSrv, rulesNew, rule_metadata
    ):
        """
        Processes the section keys to build additional rules.
        Validates the presence and type of required values.
        """
        msgLog = f"{self.indent} Processing services in more"
        logMsg(msgLog, 2, False)
        self.indentPlus()
        msgLog = f"{self.indent} section_metadata: {section_metadata}"
        logMsg(msgLog, 2, False)
        self.indentPlus()
        orig = None
        dest = None
        for key in section_metadata.keys():
            service = section_metadata[key] if key == "service" else key
            if not orig:
                if service in services["special"]:
                    msgLog = f"{self.indent} Service {service} special"
                    logMsg(msgLog, 2, False)
                    orig = service
                elif service in services["regular"]:
                    msgLog = f"{self.indent} Service {service} regular"
                    logMsg(msgLog, 2, False)
                    orig = service
                else:
                    msgLog = f"{self.indent} Service {service} not interesting"
                    logMsg(msgLog, 2, False)
            else:
                msgLog = f"{self.indent} Service {service} not orig"
                logMsg(msgLog, 2, False)
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
                        self.indentPlus()
                        msgLog = f"{self.indent} Rule: {orig} -> {key}({dest})"
                        logMsg(msgLog, 2, False)
                        self.indentPlus()
                        msgLog = f"{self.indent} from Srv: {fromSrv}"
                        logMsg(msgLog, 2, False)
                        msgLog = f"{self.indent} dest Rule: {destRule}"
                        logMsg(msgLog, 2, False)
                        self.indentLess()
                        self.indentLess()

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

        self.indentLess()
        self.indentLess()

    def _finalize_rules(
        self, config, services, sources, sources_available, more, destinations, rulesNew
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
        self.indent = f"{self.indent} Destinations:"
        for dst in destinations:
            if not isinstance(dst, tuple) or len(dst) < 4:
                logMsg(f"WARNING: Unexpected destination: {dst}", 2, self.args.verbose)
                continue
            if dst[0] == "direct":
                service = dst[2]
                methods = self.hasSetMethods(service)
                for method in methods:
                    if not isinstance(method, tuple) or len(method) != 2:
                        logMsg(
                            f"WARNING: Unexpected method in {service}: {method}",
                            2,
                            self.args.verbose,
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

        # Convert sets to lists for compatibility with the rest of the code
        self._srcs = list(sources)
        self._srcsA = list(sources_available)
        self._dsts = list(destinations)

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
        # Modified line: include rules if they have actions OR if they are on hold
        final_rules = {}
        for key in rulesNew:
            if rulesNew.get(key):  # If there are actions, include it
                final_rules[key] = rulesNew[key]
            else:  # No actions, check if it's on hold
                rule_metadata = self.more.get(key)
                if rule_metadata and rule_metadata.get("hold") == "yes":
                    final_rules[key] = (
                        []
                    )  # Keep the held rule with an empty action list
        self.rules = final_rules

    def selectActionInteractive(self, apiSrc=None):
        selActions = None
        if apiSrc:
            rule = apiSrc.src
            selActions = self.rules[rule]

        print("Actions:")
        for i, act in enumerate(selActions):
            print(f"{i}) {act}")
        iAct = input("Which action? ")
        # apiDst = self.readConfigDst("", selActions[int(iAct)], None, apiSrc)
        # apiDst = self.readConfigDst(nameR_action, rule_action, rule_metadata, apiSrc)

        return selActions[int(iAct)]

    def selectServiceInteractive(self):
        """
        Lists the available services and prompts the user to select one.
        """
        print("\n--- Select a Service ---")
        services = self.getServices()["regular"]
        for i, service in enumerate(services):
            print(f"{i}) {service}")
        iService = input("Which service? ")
        try:
            selected_service = services[int(iService)]
            return selected_service
        except (ValueError, IndexError):
            print("Invalid selection. Aborting.")
            return None

    def interactive_publish_with_rule(self):
        """
        Allows interactive selection of a rule and an action, then prompts for
        a title and a link to publish using the selected destination.
        """
        print("\n--- Interactive Publishing ---")

        # 1. Select a service
        selected_service = self.selectServiceInteractive()
        if not selected_service:
            print("No service selected. Aborting.")
            return

        # 2. Select a rule (source)
        apiSrc = self.selectRuleInteractive(service=selected_service)
        if not apiSrc:
            print("No rule selected or API source not found. Aborting.")
            return

        # 3. Select an action (destination)
        action = self.selectActionInteractive(apiSrc=apiSrc)
        if not action:
            print("No action selected or API destination not found. Aborting.")
            return

        # 4. Prompt for title and link
        title = input("Enter title for publication: ")
        link = input("Enter link for publication (optional): ")
        content = input("Enter content for publication (optional): ")

        if not title and not content:
            print("Title or content must be provided for publication. Aborting.")
            return

        print(
            f"\nPublishing '{title}' "
        )  # to {self.getNameAction(apiDst.action)}@{self.getProfileAction(apiDst.action)}...")

        # 5. Call the publish method
        try:
            # Assuming publishPost can take title, url, content directly
            # The apiDst.action is a tuple like ('direct', 'post', 'service', 'account')
            # We need to extract the actual destination service and account from it
            # destination_service = self.getNameAction(apiDst.action)
            # destination_account = self.getDestAction(apiDst.action)

            apiDst = self.readConfigDst("", action, self.more[apiSrc.src], apiSrc)
            result_dict = self._initialize_result_dict(error_message="No post found", include_total=True)
            post = {"title": title, "link": link, "content": content}
            publication_res = apiDst.publishPost(api=apiSrc, post=post)
            logging.info(f"Pub Res: {publication_res}")
            is_success = "Fail!" not in str(publication_res) and "failed!" not in str(
                publication_res
            )
            result_dict["success"] = is_success
            # results = (action,res)
            if is_success:
                result_dict["error"] = None
                result_dict["successful"] = 1
                result_dict["response_links"] = {
                    "item": publication_res,
                }
            resUpdate = apiDst.updateLastLink(apiSrc, link)

            # Use the unified publishing method
            # results = self.publish_to_multiple_destinations(
            #     destinations={destination_service: destination_account},
            #     title=title,
            #     url=link,
            #     content=content
            # )
            print(f"Res: {resUpdate}")
            summary = result_dict  # self.get_publication_summary(results)
            summary["failed"] = 0
            print(f"Summary: {summary}")
            print("\n--- Publication Summary ---")
            print(f"Total attempts: {summary['total']}")
            print(f"Successful publications: {summary['successful']}")
            for service, res_link in summary["response_links"].items():
                print(f"  - {service}: {res_link}")
            if summary["failed"] > 0:
                print(f"Failed publications: {summary['failed']}")
                for service, error in summary["errors"].items():
                    print(f"  - {service}: {error}")
            print("---------------------------\n")

        except Exception as e:
            print(f"An error occurred during publication: {e}")

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
        # selRules = []
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
        logMsg(msgLog, 2, False)
        methods = []
        if service != "social":
            if service in hasSet:
                msgLog = f"{self.indent} Service {service} cached"
                logMsg(msgLog, 2, False)
                listMethods = hasSet[service]
            else:
                clsService = getModule(service, self.indent)
                listMethods = clsService.__dir__()
                hasSet[service] = listMethods

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
        logMsg(msgLog, 2, False)
        if service in hasPublish:
            msgLog = f"{self.indent}  Service {service} cached"
            logMsg(msgLog, 2, False)
            listMethods = hasPublish[service]
        else:
            clsService = getModule(service, self.indent)
            # msgLog = f"{self.indent} Service cls: {clsService}"

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
                    logMsg(msgLog, 2, False)
                    toAppend = (action, target)
                    if toAppend not in methods:
                        methods.append(toAppend)
        self.indentLess()
        return methods

    def getServices(self):
        msgLog = f"{self.indent} Start getServices"
        logMsg(msgLog, 2, False)
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
        logMsg(msgLog, 2, False)
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

    # def cleanUrlRule(self, url, service=""):
    #     # FIXME: does it belong here?
    #     if service:
    #         url = url.replace(service, "")
    #     url = url.replace("https", "").replace("http", "")
    #     url = url.replace("---", "").replace(".com", "")
    #     url = url.replace("-(", "(").replace("- ", " ")
    #     url = url.replace(":", "").replace("/", "")
    #     return url

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
        # Check if this is a cache action and handle accordingly
        if self.getNameAction(action) == "cache":
            # For cache actions, extract the actual destination from the nested action
            inner_action = action[2]  # This is the actual destination rule tuple
            # Use getDestAction to get the raw destination and extract nickname
            dest_raw = self.getDestAction(inner_action)
            if dest_raw and (dest_raw.startswith("http://") or dest_raw.startswith("https://")):
                # Extract hostname from URL if it's a URL
                nick = dest_raw.split("//", 1)[1]
            else:
                # For non-URL destinations, use the original getNickAction logic on the inner action
                if isinstance(self.getActionComponent(inner_action, 2), tuple):
                    nick = self.getActionComponent(self.getActionComponent(inner_action, 2), 1)
                else:
                    nick = self.getActionComponent(inner_action, 3)
        else:
            # Original logic for non-cache actions
            if isinstance(self.getActionComponent(action, 2), tuple):
                nick = self.getActionComponent(self.getActionComponent(action, 2), 1)
            else:
                nick = self.getActionComponent(action, 3)
                # FIXME: Problem with slack?
        return nick

    def getNameAction(self, action):
        res = self.getActionComponent(action, 0)
        if res == "direct":
            res = self.getActionComponent(action, 2)
        return res

    def getServiceNameAction(self, action):
        """Get the service name for an action, handling cache actions internally.

        For cache actions, extracts the actual destination service name from the nested action.
        For non-cache actions, returns the action's service name directly.

        Args:
            action: The action to extract service name from

        Returns:
            str: The service name for the action
        """
        # Check if this is a cache action and handle accordingly
        if self.getNameAction(action) == "cache":
            # For cache actions, extract the actual destination from the nested action
            inner_action = action[2]  # This is the actual destination rule tuple
            res = self.getActionComponent(inner_action, 0)
            if res == "direct":
                res = self.getActionComponent(inner_action, 2)
        else:
            # Original logic for non-cache actions
            res = self.getActionComponent(action, 0)
            if res == "direct":
                res = self.getActionComponent(action, 2)
        return res.capitalize()

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
            idR = f"{self.getRuleComponent(subC, 3)}@{self.getRuleComponent(subC, 2)}@{self.getRuleComponent(rule, 0)}[{self.getRuleComponent(rule, 3)}]".format(
                self.getRuleComponent(rule, 0)
            )
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

    def getOrigString(self, obj):
        """Generate the orig string for a rule object.

        Args:
            obj: The rule object to extract information from
        """
        # Use consistent rule-based methods (fixing original inconsistency)
        return (
                f"{self.getNickRule(obj)}@{self.getNameRule(obj)}"
                f" ({self.getTypeRule(obj)})"
                )


    def getActionString(self, action):
        """Generate the action string for an action object (compact format).

        Args:
            action: The action object to extract information from
        """
        # Use consistent action-based methods for compact representation
        return (
                f"{self.getNickAction(action)}@{self.getServiceNameAction(action)} "
                f"({self.getTypeAction(action)})"
                )

    def clientErrorMsg(self, indent, api, typeC, rule, action):
        return f"{indent} {typeC} Error. " f"No client for {rule} in ({action}). End."

    def readConfigSrc(self, indent, src, more, fileName=None):
        if not fileName:
            fileName = self._get_filename_base(src, None)
        msgLog = f"{indent} Start readConfigSrc {src}"
        logMsg(msgLog, 2, self.args.verbose)
        child_indent = f"{indent} "
        profile = self.getNameRule(src)
        account = self.getProfileRule(src)
        if more and "channel" in more:
            apiSrc = getApi(profile, account, child_indent, more["channel"])
        else:
            apiSrc = getApi(profile, account, child_indent)

        if apiSrc is not None:
            apiSrc.src = src
            apiSrc.setPostsType(src[-1])
            apiSrc.setMoreValues(more)
            apiSrc.indent = indent
            if fileName:
                apiSrc.fileName = fileName
        else:
            msgLog = f"{indent} Failed to get API for source: {src}"
            logMsg(msgLog, 3, self.args.verbose)

        msgLog = f"{indent} End readConfigSrc"  #: {src[1:]}"
        logMsg(msgLog, 2, self.args.verbose)
        return apiSrc

    def getActionComponent(self, action, pos):
        res = ""
        if isinstance(action, tuple) and (len(action) == 4):
            res = action[pos]
        return res

    def readConfigDst(self, indent, action, more, apiSrc=None, fileName=None):
        msgLog = f"{indent} Start readConfigDst {action}"  #: {src[1:]}"
        logMsg(msgLog, 2, self.args.verbose)
        child_indent = f"{indent} "
        profile = self.getNameAction(action)
        account = self.getDestAction(action)
        apiDst = getApi(profile, account, child_indent)

        if apiDst is not None:
            if apiSrc:
                apiDst.src = apiSrc.src
            apiDst.action = action
            apiDst.setMoreValues(more)
            apiDst.indent = child_indent
            if fileName:
                apiDst.fileName = fileName
            if isinstance(action[2], tuple):
                apiDst.dst_fileName = self._get_filename_base(action, action[2])
            if apiSrc:
                apiDst.setUrl(apiSrc.getUrl())
            else:
                apiDst.setUrl(None)
            if apiSrc:
                apiDst.setLastLink(apiSrc)
            else:
                apiDst.setLastLink(apiDst)
        else:
            logMsg(
                f"{indent} Failed to get API for destination: {action}",
                3,
                self.args.verbose,
            )

        msgLog = f"{indent} End readConfigDst"  #: {src[1:]}"
        logMsg(msgLog, 2, False)
        return apiDst

    def _initialize_result_dict(self, error_message="No post found", include_total=False):
        """
        Initializes a standard result dictionary with default values.

        Args:
            error_message: The error message to set in the dictionary
            include_total: Whether to include the 'total' field (for interactive publishing)

        Returns:
            Dictionary with default result values
        """
        result = {
            "success": False,
            "publication_result": None,
            "link_updated": False,
            "post_action_result": None,
            "error": error_message
        }
        if include_total:
            result["total"] = 0
        return result

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
        self,
        indent,
        msgAction,
        apiSrc,
        apiDst,
        simmulate,
        nextPost,
        pos,
        publication_res,
    ):
        resPost = apiSrc.get_empty_res_dict()
        resMsg = ""
        msgLog = f"{indent}Trying to execute Post Action"
        logMsg(msgLog, 1, self.args.verbose)
        postaction = apiSrc.getPostAction()
        resPost['action'] = postaction
        if postaction:
            msgLog = f"{indent}Post Action {postaction} " f"(nextPost = {nextPost})"
            logMsg(msgLog, 1, self.args.verbose)

            if (('success' in publication_res and publication_res['success'])
                or ("OK. Published!" in publication_res)):
                msgLog = f"{indent} Res {publication_res} is OK"
                logMsg(msgLog, 1, False)
                if nextPost:
                    msgLog = f"{indent}Post Action next post"
                    logMsg(msgLog, 2, False)
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resCmd = cmdPost(apiDst)
                else:
                    msgLog = f"{indent}Post Action pos post"
                    logMsg(msgLog, 2, False)
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resCmd = cmdPost(pos)
                    # FIXME inconsistent
                if 'OK' in resCmd:
                    resPost['success'] = True
                resPost['cmd'] = cmdPost
                resPost['raw_response'] = resCmd
            # when the publishMethod does not return the adequate values: FIXME?
            elif (
                (publication_res and ("failed!" not in publication_res) and ("Fail!" not in publication_res))
                or (publication_res and ("abusive!" in publication_res))
                or (
                    ((not publication_res) and ("OK. Published!" not in publication_res))
                    or ("duplicate" in publication_res)
                )
            ):
                msgLog = f"{indent} Res {publication_res} is not OK"
                # FIXME Some OK publishing follows this path (mastodon, linkedin, ...)
                logMsg(msgLog, 1, False)

                if nextPost:
                    cmdPost = getattr(apiSrc, f"{postaction}NextPost")
                    resCmd = cmdPost(apiDst)
                else:
                    cmdPost = getattr(apiSrc, f"{postaction}")
                    resCmd = cmdPost(pos)
                if 'success' in resCmd:
                    resPost['success'] = resCmd['success']
                elif 'OK' in resCmd:
                    resPost['success'] = True
                else:
                    resPost['success'] = resCmd
                resPost['cmd'] = cmdPost
                resPost['raw_response'] = resCmd
                # FIXME inconsistent
                msgLog = f"{indent}Post Action command {cmdPost}"
                logMsg(msgLog, 1, self.args.verbose)
                msgLog = f"{indent}End {postaction}, reply: {resPost} "
                logMsg(msgLog, 1, self.args.verbose)
                resMsg += f"Post Action: {resPost}"
            else:
                msgLog = f"{indent}Something went wrong"
                logMsg(msgLog, 1, self.args.verbose)
            msgLog = f"{indent}End {postaction}, reply: {resPost} "
            logMsg(msgLog, 1, self.args.verbose)
            resMsg += f" Post Action: {resPost}"

            # when the publishMethod does not return the adequate values: FIXME?
        else:
            resPost['success'] = True
            msgLog = f"{indent}No Post Action"
            logMsg(msgLog, 1, self.args.verbose)

        return resPost

    def executePublishAction(
        self,
        indent,
        action,
        apiSrc,
        apiDst,
        simmulate,
        nextPost=True,
        pos=-1,
    ):
        """
        Executes a publishing action for a single post.

        Args:
            indent: Indentation string for logging
            action: The action to execute
            apiSrc: Source API object
            apiDst: Destination API object
            simmulate: Whether to simulate the action
            nextPost: Whether to get the next post or a specific one
            pos: Position of the post to get if nextPost is False

        Returns:
            Dictionary with result information
        """
        postaction = ""
        apiSrc.setPosts()

        # Initialize result dictionary with default values
        result_dict = self._initialize_result_dict()

        post = apiSrc.getNextPost(apiDst) if nextPost else apiSrc.getPost(pos)
        # Handle case when no post is available
        if not post:
            msgAction = self.getActionString(action)
            msgLog = f"{indent}No post to schedule in {msgAction}"
            logMsg(msgLog, 1, self.args.verbose)
            result_dict["success"] = True
            result_dict["publication_result"] = "No posts available"
            result_dict["error"] = None
        else:
            # Process the post
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            msgLog = f"Title: {title}."
            if link:
                msgLog = (
                    f"{msgLog} Recording Link: {link} "
                    # f"in file {apiSrc.fileNameBase(apiDst)}.last"
                    f"in file {DATADIR}/{apiSrc.fileName}.last"
                )
            logMsg(f"{indent}{msgLog}", 1, self.args.verbose)

            # Handle simulation mode
            if simmulate:
                msgAction = self.getActionString(action)
                msgLog = f"{indent}Would schedule in {msgAction} {msgLog}"
                logMsg(msgLog, 1, self.args.verbose)
                result_dict["success"] = True
                result_dict["publication_result"] = f"No posting (simmulation).{msgLog}"
                result_dict["error"] = "Simulation"
            else:
                # Perform actual publication
                publication_res = apiDst.publishPost(api=apiSrc, post=post)
                result_dict["publication_result"] = publication_res
                msgLog = f"{indent}Reply: {publication_res}"
                logMsg(msgLog, 1, self.args.verbose)

                # Determine success based on publication result
                if isinstance(publication_res, dict) and "success" in publication_res:
                    is_success = publication_res["success"]
                else:
                    #FIXME: this needs to be eliminated. It deals with string replies
                    is_success = "Fail!" not in str(publication_res) and "failed!" not in str(publication_res)

                result_dict["success"] = is_success
                result_dict["error"] = None if is_success else f"Publication failed: {publication_res}"
                #FIXME: This can be improved. The whole reply will be available, anyway

                if is_success:
                    # Update link if needed
                    result_dict["link_updated"] = None
                    if nextPost:
                        resUpdate = apiDst.updateLastLink(apiSrc, link)
                        result_dict["link_updated"] = resUpdate

                    msgLog = f"{indent}Reply Update: {result_dict}"
                    logMsg(msgLog, 1, self.args.verbose)

                    # Execute post-action
                    # msgAction = self.getActionString(action)
                    post_action_res = self.executePostAction(
                        indent,
                        action,
                        apiSrc,
                        apiDst,
                        simmulate,
                        nextPost,
                        pos,
                        publication_res,
                    )
                    result_dict["post_action_result"] = post_action_res

        # Log final result
        msgLog = f"{indent}Reply Post: {result_dict}"
        logMsg(msgLog, 1, self.args.verbose)

        if postaction == "delete":
            msgLog = f"{indent}Available {len(apiSrc.getPosts())-1}"
        else:
            msgLog = f"{indent}Available {len(apiSrc.getPosts())}"
        logMsg(msgLog, 1, self.args.verbose)

        return result_dict

    def executeAction(
        self,
        src,
        more,
        action,
        # apiSrc,
        noWait,
        timeSlots,
        simmulate,
        name="",
        action_index=1,
        nextPost=True,
        pos=-1,
        delete=False,
    ):
        indent = ""
        if name:
            indent = f"{name}"
        textEnd = ""
        logMsg(f"{indent} Start executeAction {textEnd}", 2, False)
        res = {"success": False, "error": "No execution"}

        # Destination
        orig = self.getOrigString(src)
        dest = self.getActionString(action)
        msgLog = f"{indent} Scheduling {orig} -> {dest}"
        logMsg(msgLog, 1, self.args.verbose)
        base_name = self._get_filename_base(src, action)

        # Backup the current next-run time before making changes
        backup_time = self.getNextTime(src, action)

        tL = random.random() * action_index  # 'Progressive' delay
        indent = f"{indent} "
        msgLog = (
            f"{indent} Sleeping {tL:.2f} seconds ({action_index} actions) "
            f"to launch all processes"
        )
        logMsg(msgLog, 1, False)
        numAct = max(3, action_index)  # Less than 3 is too small
        time.sleep(tL)

        msgLog = f"{indent} Go!"
        logMsg(msgLog, 1, False)
        indent = f"{indent} "

        textEnd = f"{msgLog}"

        time.sleep(1)

        msgLog = ""

        # Get scheduling data without full API instantiation
        rule_metadata = more
        max_val, time_val, last_time_val = self._get_publication_check_data(
            src, action, rule_metadata
        )

        if nextPost:
            num = max_val
        else:
            num = 1

        if num > 0:
            tNow = time.time()
            # hours = float(time_val) * 60 * 60
            # lastTime = last_time_val

            # if lastTime:
            #     diffTime = tNow - lastTime
            # else:
            #     diffTime = hours + 1

            tSleep = random.random() * float(timeSlots) * 60

            # Reserve the time slot by setting the new time
            self.setNextTime(src, action, tNow, tSleep)

            if tSleep > 0.0:
                msgLog = f"{indent} Waiting {tSleep/60:2.2f} minutes"
            else:
                tSleep = 2.0
                msgLog = f"{indent} No Waiting"

            theAction = self.getTypeAction(action)
            # msgLog = f"{msgLog} for {orig} in " f"{dest}"            
            logMsg(msgLog, 1, self.args.verbose)

            # Wait BEFORE instantiation
            if not simmulate:
                time.sleep(tSleep)
                if "minutes" in msgLog:
                    logMsg(f"{indent} End Waiting", 1, self.args.verbose)

            # Instantiate APIs ONCE, after the wait
            apiSrc = self.readConfigSrc(indent, src, more, fileName=base_name)
            if not apiSrc:
                client_error_msg = self.clientErrorMsg(
                    indent, apiSrc, "Source", f"{orig}", f"{dest}",
                )
                logMsg(client_error_msg, 3, self.args.verbose)
                sys.stderr.write(f"Error: {client_error_msg}\n")
                res = {"success": False, "error": f"End: {client_error_msg}"}
                return res

            apiDst = self.readConfigDst(
                indent, action, more, apiSrc, fileName=base_name
            )

            if not apiDst.getClient():
                client_error_msg = self.clientErrorMsg(
                    indent, apiDst, "Destination", f"{orig}", f"{dest}",
                )
                logMsg(client_error_msg, 3, self.args.verbose)
                sys.stderr.write(f"Error: {client_error_msg}\n")
                res = {"success": False, "error": f"End: {client_error_msg}"}
                return res

            # Calculate numAct correctly using the instantiated apiDst
            if nextPost:
                num = apiDst.getMax()
            else:
                num = 1
            numAct = num

            msgLog = (
                f"{indent}I'll publish {numAct} from {orig} in {dest}"
            )
            logMsg(msgLog, 1, self.args.verbose)

            if numAct > 0:
                for i in range(numAct):
                    res = self.executePublishAction(
                        indent,
                        action,
                        apiSrc,
                        apiDst,
                        simmulate,
                        nextPost,
                        pos,
                    )
            else:
                res = {
                    "success": True,
                    "publication_result": "Limit for publications reached",
                    "link_updated": False,
                    "post_action_result": None,
                }

            # If no publication occurred, restore the previous time
            if not res.get("success") and backup_time[0] is not None:
                logMsg(
                    f"{indent} No publication occurred. Restoring previous next-run time.",
                    1,
                    self.args.verbose,
                )
                self.setNextTime(src, action, backup_time[0], backup_time[1])

        else:
            msgLog = f"{indent} No posts available"
            logMsg(msgLog, 1, self.args.verbose)

        indent = f"{indent[:-1]}"
        logMsg(f"{indent} End executeAction {textEnd}", 2, False)
        return res

    def executeRules(self, max_workers=None):
        """
        Executes all generated rules using concurrency.
        Refactored to delegate to helper functions.
        Allows configuring the number of threads (max_workers) by argument,
        environment variable SOCIALMODULES_MAX_WORKERS, or automatically
        according to the number of actions to execute
        (one per action, minimum 1, maximum 100).
        """
        import os

        msgLog = "Start Executing rules"
        logMsg(msgLog, 1, 2)
        self.indent = ""
        args = self.args
        select = args.checkBlog
        # simmulate = args.simmulate
        # Prepare actions to execute
        scheduled_actions, held_actions, skipped_actions = self._prepare_actions(
            args, select
        )
        # Determine number of threads
        if max_workers is not None:
            pass  # use the explicit value
        elif "SOCIALMODULES_MAX_WORKERS" in os.environ:
            max_workers = int(os.environ["SOCIALMODULES_MAX_WORKERS"])
        else:
            num_actions = max(1, len(scheduled_actions))
            max_workers = min(num_actions, 100)  # reasonable maximum
        # Execute actions concurrently
        action_results, action_errors = self._run_actions_concurrently(
            scheduled_actions, max_workers=max_workers
        )
        # Report results and errors
        self._report_results(
            action_results, action_errors, held_actions, skipped_actions
        )
        msgLog = f"End Executing rules with {len(scheduled_actions)} actions."
        logMsg(msgLog, 1, 2)
        return

    def _get_filename_base(self, rule_key, rule_action):
        nameSrc = self.getNameRule(rule_key).capitalize()
        typeSrc = self.getTypeRule(rule_key)
        user_src_raw = self.getNickRule(rule_key)
        if user_src_raw.startswith("http"):
            user_src = extract_nick_from_url(user_src_raw)
        else:
            user_src = user_src_raw

        service_src = self.getNameRule(rule_key).capitalize()

        nameDst = self.getNameAction(rule_action).capitalize()
        typeDst = "posts"  # Always 'posts' for consistency
        user_dst = self.getNickAction(rule_action)  # Handles cache internally
        service_dst = self.getServiceNameAction(rule_action)  # Handles cache internally
        if user_src.endswith("/"):
            user_src = user_src[:-1]
        if nameSrc == "Cache":
            typeSrc = "posts"
            service_src = self.getSecondNameRule(rule_key).capitalize()

        base_name = (
            f"{nameSrc}_{typeSrc}_"
            f"{user_src}_{service_src}__"
            f"{nameDst}_{typeDst}_"
            f"{user_dst}_{service_dst}"
        )
        base_name = base_name.replace("/", "-").replace(":", "-")
        return base_name

    def getNextTime(self, src, action):
        # We need to import pickle here because it's used only in this specific context
        import pickle

        tNow, tSleep = None, None
        base_name = self._get_filename_base(src, action)
        fileNameNext = os.path.join(DATADIR, f"{base_name}.timeNext")

        if os.path.exists(fileNameNext):
            with open(fileNameNext, "rb") as f:
                tNow, tSleep = pickle.load(f)

        return (tNow, tSleep)

    def setNextTime(self, src, action, tNow, tSleep):
        import pickle

        base_name = self._get_filename_base(src, action)
        fileNameNext = os.path.join(DATADIR, f"{base_name}.timeNext")

        try:
            with open(fileNameNext, "wb") as f:
                pickle.dump((tNow, tSleep), f)
        except (IOError, pickle.PicklingError) as e:
            logMsg(
                f"Failed to write to time file {fileNameNext}: {e}",
                3,
                self.args.verbose,
            )

    def _get_publication_check_data(self, rule_key, rule_action, rule_metadata):
        max_val = rule_metadata.get("max", 1) if rule_metadata else 1
        time_val = rule_metadata.get("time", 0) if rule_metadata else 0

        base_name = self._get_filename_base(rule_key, rule_action)
        last_time_file = f"{DATADIR}/{base_name}.last"

        last_time_val = 0
        if os.path.exists(last_time_file):
            last_time_val = os.path.getctime(last_time_file)

        return int(max_val), float(time_val), last_time_val

    def _should_skip_publication_early(
        self, rule_key, rule_action, rule_metadata, noWait, nameA
    ):
        max_val, time_val, last_time_val = self._get_publication_check_data(
            rule_key, rule_action, rule_metadata
        )

        should_skip = False
        indent = ""  # nameA
        num = max_val
        skip_reason = ""
        if num <= 0:
            msgLog = f"{indent} Max number of posts does not allow publishing"
            logMsg(msgLog, 1, self.args.verbose)
            should_skip = True

        tNow = time.time()
        hours = float(time_val) * 60 * 60
        lastTime = last_time_val

        if not should_skip:  # Only check if not already skipping
            if lastTime:
                diffTime = tNow - lastTime
            else:
                diffTime = hours + 1

            if not noWait and (diffTime <= hours):
                thread_local.nameA = nameA
                skip_reason = (
                    f"Not enough time passed. "
                    f"We will wait at least "
                    f"{(hours-diffTime)/(60*60):2.2f} hours."
                )
                msgLog = f"{indent} {skip_reason}"
                logMsg(msgLog, 1, self.args.verbose)
                should_skip = True
        return should_skip, skip_reason

    def _prepare_actions(self, args, select):
        """
        Prepares the list of actions to execute, filtering and collecting all
        necessary information.  Returns a list of dictionaries with data for
        each action.
        """
        scheduled_actions = []
        held_actions = []
        skipped_actions = []
        previous = ""
        i = 0  # Initialize i outside the loop to avoid UnboundLocalError
        for rule_index, rule_key in enumerate(sorted(self.rules.keys())):
            # Repetition control by action name
            rule_metadata = self.more.get(rule_key)
            rule_actions = self.rules[rule_key]
            if self.getNameAction(rule_key) != previous:
                i = 0
            else:
                i = i + 1
            name_action = f"[{self.getNameAction(rule_key)}{i}]"
            name_action = f"{name_action:->12}>"
            rule_name = self.getOrigString(rule_key)
            msgLog = f"Preparing actions for rule: {rule_name}"
            try:
                thread_local.nameA = name_action
                logMsg(msgLog, 1, self.args.verbose)
            finally:
                thread_local.nameA = None
            previous = self.getNameAction(rule_key)
            if rule_metadata and rule_metadata.get("hold") == "yes":
                msgHold = (
                    f"[HOLD] {rule_name} "
                )
                try:
                    thread_local.nameA = name_action
                    logMsg(msgHold, 1, False)
                finally:
                    thread_local.nameA = None
                held_actions.append(
                    {
                        "rule_key": rule_key,
                        "rule_metadata": rule_metadata,
                        "rule_action": None,
                        "rule_index": i,
                        "action_index": -1,
                        "name_action": name_action,
                    }
                )
                continue

            for action_index, rule_action in enumerate(rule_actions):
                # Rule selection if --checkBlog is used
                nameA = f"{name_action} Action {action_index}:"
                nameRule = f"{self.getNameRule(rule_key).lower()}{i}"

                if select and (select.lower() != nameRule):
                    continue

                # section_name = (
                #     rule_metadata.get("section_name", "") if rule_metadata else ""
                # )

                #if select and (select.lower() != section_name.lower()):
                #    continue

                timeSlots, noWait = self._get_action_properties(
                    rule_action, rule_metadata, args
                )

                should_skip, skip_reason_msg = self._should_skip_publication_early(
                    rule_key, rule_action, rule_metadata, noWait, f"{nameA}"
                )
                if should_skip:
                    skipped_actions.append(
                        {
                            "rule_key": rule_key,
                            "rule_metadata": rule_metadata,
                            "rule_action": rule_action,
                            "rule_index": i,
                            "action_index": action_index,
                            "name_action": name_action,
                            "nameA": nameA,
                            "skip_reason": skip_reason_msg,
                        }
                    )
                    continue

                # base_name = self._get_filename_base(rule_key, rule_action)

                scheduled_actions.append(
                    {
                        "rule_key": rule_key,
                        "rule_metadata": rule_metadata,
                        "rule_action": rule_action,
                        "rule_index": i,
                        "action_index": action_index,
                        "args": args,
                        "simmulate": args.simmulate,
                        "name_action": name_action,
                        "nameA": nameA,
                        "timeSlots": timeSlots,  # Add timeSlots to scheduled_actions
                        "noWait": noWait,  # Add noWait to scheduled_actions
                    }
                )
        return scheduled_actions, held_actions, skipped_actions

    def _get_action_properties(self, rule_action, rule_metadata, args):
        timeSlots = args.timeSlots
        noWait = args.noWait

        if (self.getNameAction(rule_action) in "cache") or (
            (self.getNameAction(rule_action) == "direct")
            and (self.getProfileAction(rule_action) == "pocket")
        ):
            timeSlots = 0
            noWait = True
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
                    self._execute_single_action, scheduled_action
                ): scheduled_action
                for scheduled_action in scheduled_actions
            }
            for future in concurrent.futures.as_completed(future_to_action):
                scheduled_action = future_to_action[future]
                res = ""
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
        # args = scheduled_action["args"]
        simmulate = scheduled_action["simmulate"]
        # apiSrc = scheduled_action["apiSrc"]
        timeSlots = scheduled_action["timeSlots"]
        noWait = scheduled_action["noWait"]

        # Prepare arguments for executeAction
        rule_index = scheduled_action.get("rule_index", 0)
        action_index = scheduled_action.get("action_index", 0)
        name_action = f"[{self.getNameAction(rule_key)}{rule_index}]"
        nameA = f"{name_action:->12}> Action {action_index}:"
        try:
            thread_local.nameA = nameA
            return self.executeAction(
                rule_key,
                rule_metadata,
                rule_action,
                # apiSrc,
                noWait,
                timeSlots,
                simmulate,
                "",  # Previously nameA
                action_index,
            )
        finally:
            thread_local.nameA = None

    def _report_results(
        self, action_results, action_errors, held_actions=None, skipped_actions=None
    ):
        """
        Reports the results and errors of action execution.
        """
        if held_actions:
            for held_action in held_actions:
                # rule_key = held_action["rule_key"]
                # rule_index = held_action.get("rule_index", "")
                name_action = held_action["name_action"]
                # rule_summary = (
                #     f"{name_action} Rule {rule_index}: {rule_key}" if rule_index != "" else str(rule_key)
                # )
                summary_msg = "Rule on hold."
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f" Actions: [OK] (Held) {summary_msg}",
                        1,
                        # self.args.verbose,
                        True,
                    )
                finally:
                    thread_local.nameA = None

        if skipped_actions:
            for skipped_action in skipped_actions:
                # rule_key = skipped_action["rule_key"]
                # rule_action = skipped_action["rule_action"]
                # rule_index = skipped_action.get("rule_index", "")
                name_action = skipped_action["name_action"]
                skip_reason = skipped_action["skip_reason"]

                summary_msg = f"{skip_reason.strip()}"
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f" Actions: [WARN] (Skipped). {summary_msg}",
                        2,
                        True,
                    )
                finally:
                    thread_local.nameA = None
        for scheduled_action, res_dict in action_results:
            # rule_key = scheduled_action["rule_key"]
            # rule_index = scheduled_action.get("rule_index", "")
            name_action = scheduled_action["nameA"]
            # rule_summary = (
            #     f"{name_action} Rule {rule_index}: {rule_key}"
            #     if rule_index != ""
            #     else str(rule_key)
            # )

            if res_dict == "ok":
                summary_msg = "Success. Action completed."
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f" [OK] {summary_msg}",
                        1,
                        True,
                    )
                finally:
                    thread_local.nameA = None
            elif isinstance(res_dict, dict) and res_dict.get("success"):
                pub_res = res_dict.get("publication_result", "N/A")
                post_act = res_dict.get("post_action_result")
                if 'post_url' in pub_res:
                    summary_msg = f"Success. {pub_res['post_url']}"
                else:
                    summary_msg = f"Success. {pub_res}"
                if post_act:
                    summary_msg += f". Post-Action: '{post_act}'"
                summary_msg += "."
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f"[OK] {summary_msg}",
                        1,
                        True,
                    )
                finally:
                    thread_local.nameA = None
            elif isinstance(res_dict, dict):
                error_msg = res_dict.get("error", "Unknown error")
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f"[ERROR] {error_msg}",
                        3,
                        True,
                    )
                finally:
                    thread_local.nameA = None
            else:
                # Fallback for empty or non-dict results
                try:
                    thread_local.nameA = name_action
                    logMsg(
                        f"[WARN] Action produced an invalid result: {res_dict}",
                        2,
                        True,
                    )
                finally:
                    thread_local.nameA = None

        for scheduled_action, exc in action_errors:
            # rule_key = scheduled_action["rule_key"]
            # rule_index = scheduled_action.get("rule_index", "")
            name_action = scheduled_action["nameA"]
            # rule_summary = (
            #     f"{name_action} Rule {rule_index}: {rule_key}"
            #     if rule_index != ""
            #     else str(rule_key)
            # )
            try:
                thread_local.nameA = name_action
                logMsg(
                    f"[ERROR] {exc}",
                    3,
                    True,
                )
            finally:
                thread_local.nameA = None

    def _configure_service_api(
        self,
        api,
        destination,
        channel=None,
        from_email=None,
        to_email=None,
        account=None,
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
                logging.debug(f"Channel set to '{channel}' for {destination}")

            # Configure SMTP-specific settings
            if "smtp" in destination.lower():
                if hasattr(api, "fromaddr"):
                    api.fromaddr = from_email or "default@example.com"
                    logging.debug(f"SMTP fromaddr set to {api.fromaddr}")

                if hasattr(api, "to"):
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
                    for url_field in [
                        "url",
                        "image_url",
                        "media_url",
                        "attachment_url",
                    ]:
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
        result_dict = {}

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
                        logging.info(
                            f"Image published to {destination}: {image_result}"
                        )
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
                (service, account)
                for service, account in destinations.items()
                if account
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
        results = {}
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
            url=kwargs.get("url", ""),
            content=kwargs.get("content", ""),
            image_path=kwargs.get("image_path"),
            alt_text=kwargs.get("alt_text", ""),
            channel=kwargs.get("channel"),
            from_email=kwargs.get("from_email"),
            to_email=kwargs.get("to_email"),
        )

    def get_publication_summary(self, results):
        """
        Generate a summary of publication results

        Args:
            results: Results dict from publish_to_multiple_destinations

        Returns:
            dict: Summary with statistics and details
        """
        summary = {}
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
            "--interactive",
            "-i",
            default=False,
            action="store_true",
            help="interactive publishing mode",
        )
        parser.add_argument(
            "--rules",
            "-r",
            default=False,
            action="store_true",
            help="Show the list of rules and actions",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            default=False,
            action="store_true",
            help="Enable verbose output (print to console)",
        )
        self.args = parser.parse_args()


def main():
    rules = moduleRules()

    rules.readArgs()
    rules.indent = ""
    rules.checkRules()

    if rules.args.interactive:
        rules.interactive_publish_with_rule()
    else:
        rules.executeRules()

    return


if __name__ == "__main__":
    main()
