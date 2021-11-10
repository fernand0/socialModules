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

    def readConfigSrc(self, indent, src, more):
        msgLog = f"Src: Src {src}"
        logMsg(msgLog, 2, 0)
        msgLog = f"More: Src {more}"
        logMsg(msgLog, 1, 0)
        if src[0] == 'cache':
            if src[2].count('@')>1:
                parts = src[2].split('@')
                sN = parts[0]
                nick = '@'.join(parts[1:])
            else:
                sN, nick = src[2].split('@')
            apiSrc = getApi(src[0], (sN, nick))
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

        return apiSrc

    def readConfigDst(self, indent, action, more):
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
            apiDst = getApi("cache", (action[1], socialNetwork))
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

    def executeAction(self, src, more, action, 
                    noWait, timeSlots, simmulate, name=""): 

        sys.path.append(path)
        from configMod import logMsg

        indent = f" {name}"+" "

        msgLog = (f"{indent}Sleeping to launch all processes")
        logMsg(msgLog, 1, 0)
        # 'Cometic' waiting to allow all the processes to be launched.
        time.sleep(1)

        msgAction = (f"{action[0]} {action[3]}@{action[2]} "
                     f"({action[1]})")
        msgLog = (f"{indent}Source: {src[2]} ({src[3]}) -> "
                f"Action: {msgAction})")

        logMsg(msgLog, 1, 0)
        textEnd = (f"{msgLog}")

        # Destination

        apiSrc = self.readConfigSrc(indent, src, more)
        apiDst = self.readConfigDst(indent, action, more)
        apiDst.setUrl(apiSrc.getUrl())

        # getSocialNetwork() ?
        profile = action[2]
        nick = action[3]
        socialNetwork = (profile, nick)
        msgLog = (f"{indent}socialNetwork: {socialNetwork}")
        logMsg(msgLog, 2, 0)

        indent = f"{indent} "

        num = apiDst.getMax()
        msgLog = (f"{indent}num: {num}")
        logMsg(msgLog, 1, 1)

        apiSrc.setLastLink(apiDst)

        myLastLink = apiDst.getLastLinkPublished()
        lastTime = apiSrc.getLastTimePublished()
        if not myLastLink:
            logMsg("{indent}lllllastLink not available", 1, 1)
            myLastLink, lastTime = apiDst.getLastTime()
            # Maybe this should be in moduleContent ?
            lastLink = myLastLink
            if isinstance(lastLink, list):
                if len(lastLink) > 0:
                    myLastLink = lastLink[0]
                else:
                    myLastLink = ""
            else:
                myLastLink = lastLink

        # if myLastLink != mmyLastLink: 
        #     msgLog = (f"{indent}Differ ll: "
        #               f"lastLink {myLastLink} mlastLink {mmyLastLink}")
        #     logMsg(msgLog, 1, 1)

        myTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lastTime))

        lastLink = myLastLink
        
        apiSrc.setPosts()

        if ((src[0] in ['gmail', 'cache'])
                or (src[3] == 'favs')):
            i = 1
            myLastLink = ''
        else:
            numAvailable = len(apiSrc.getPosts())
            i = apiSrc.getLinkPosition(myLastLink)
        indent = f"{indent}  "
        nextPost = (f"{indent}getNextPost: {apiSrc.getNextPost()}")
        msgLog = nextPost
        logMsg(msgLog, 2, 0)


        msgLog = (f"{indent}Last time: {myTime}")
        logMsg(msgLog, 1, 1)

        if myLastLink:
            msgLog = (f"{indent}Last link: {myLastLink}")
            logMsg(msgLog, 1, 1)

        msgLog = (f"{indent}DstMax: {apiDst.getMax()}"
                f" num: {num} i: {i}"
                #f" Available: {numAvailable}"
                f" Max: {apiDst.getMax()}")
        logMsg(msgLog, 1, 0)

        msgLog = (f"apiSrc: {apiSrc}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"apiDst: {apiDst}")
        logMsg(msgLog, 2, 0)

        listPosts = []
        
        testDiffer = False
        if testDiffer:
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

            return
 
        if num>0:
            diffTime = time.time() - lastTime
            msgLog = (f"{indent}Src time: {apiSrc.getTime()} "
                    f"Dst time: {apiDst.getTime()}")
            logMsg(msgLog, 2, 0)
            hours = float(apiDst.getTime())*60*60

        numAvailable = 0
        if (num > 0) and (noWait or (diffTime>hours)): 
            tSleep = random.random()*float(timeSlots)*60
            tNow = time.time()

            if ((i>0) and (action[0] not in ['cache'])):
                #and (src[2] != f"{action[2]}@{action[3]}")): 
                fileNameNext = setNextTime(apiDst, socialNetwork, 
                        tNow, tSleep)
                msgLog = (f"{indent}apiSrc: {apiSrc} apiDst: {apiDst}")
                logMsg(msgLog, 1, 0)

                text = (f"{indent}Source: {more['url']} ({src[3]}) -> " 
                        f"\n{indent}Source: {src[2]} ({src[3]}) -> " 
                        f"Action: {msgAction})")
                if numAvailable: 
                    msgLog = (f"{msgLog}\n{indent}Available: "
                            f"{numAvailable}")
                    logMsg(text, 1, 0)
                msgLog = (f"{indent}{fileNameNext}")
                logMsg(text, 1, 0)
                with open(fileNameNext,'wb') as f: 
                    pickle.dump((tNow,tSleep), f)

            if (tSleep>0.0):
                msgLog= f"{indent}Waiting {tSleep/60:2.2f} minutes" 
            else:
                tSleep = 2.0
                msgLog= f"{indent}No Waiting"
            msgLog = f"{msgLog} for action: {msgAction}"
            logMsg(msgLog, 1, 1)

            time.sleep(tSleep)

            msgLog = (f"{indent}Go!\n"
                      f"{indent}└-> Action: {msgAction}")
            logMsg(msgLog, 1, 1)

            # The source of data can have changes while we were waiting
            apiSrc.setPosts()

            listPosts = apiSrc.getNumPostsData(num, i, lastLink)
            listPosts2 = apiSrc.getNumNextPost(num)

            if listPosts and listPosts[0][1]: 
                if listPosts2:
                    if (listPosts == listPosts2):
                        print("{indent}Equal listPosts")
                    else:
                        print(f"{indent}Differ listPosts:\n"
                              f"{listPosts}\n"
                              f"{listPosts2}\n")
                else:
                    print(f"{indent}No listPosts2")
                msgLog = f"{indent}Would schedule in {msgAction} ..."
                logMsg(msgLog, 1, 1)
                indent = f"{indent} "
                msgLog = (f"{indent}listPosts: {listPosts}")
                logMsg(msgLog, 2, 0)
                [ logMsg(f"{indent}- {post[0][:200]}", 1, 1) 
                            for post in listPosts 
                ]
                logMsg(f"{indent}Next post: {nextPost}", 2, 0)
                npost = apiSrc.getNextPost()[0]
                #logMsg(f"npost {npost}")
                if npost:
                    ntitle = apiSrc.getPostTitle(npost)
                    logMsg(f"{indent}Title Next post: {ntitle}", 1, 1)
                    nlink = apiSrc.getPostLink(npost)
                    logMsg(f"{indent}Link Next post: {nlink}", 1, 1)
                    try:
                        extract = apiSrc.extractPostLinks(npost)
                    except:
                        logMsg(f"{indent}Fail extract!")
                        extract = ('','')
                    nsummary = f"{extract[0]}\n{extract[1]} "
                    #logMsg(f"First link Next post: {apiSrc.getPostContentLink(apiSrc.getNextPost())}", 1, 1)
                else:
                    ntitle = ''
                    nsummary = ''
                    nlink = ''
                    extract = ('','')

                indent = f"{indent[:-1]}"

                # Only the last one.
                title = listPosts[-1][0]
                if (title != ntitle):
                    print(f"{indent}Differ: t {title} - {ntitle}")
                link = listPosts[-1][1]
                if (link != nlink):
                    print(f"{indent}Differ: l {link} - {nlink}")
                llink = ''
                firstLink = listPosts[-1][2]
                summaryLinks = listPosts[-1][6]
                if (summaryLinks != extract[0]):
                    print(f"{indent}Differ: s {summaryLinks} - {extract[0]}")
                if (firstLink != extract[1]):
                    print(f"{indent}Differ: f {firstLink} - {extract[1]}")
                comment = listPosts[-1][-1]
                tags = listPosts[-1][-2]
                ntags = apiSrc.getPostImagesTags(npost)
                if (tags != ntags):
                    print(f"{indent}Differ: ta {tags} - {ntags}")

                if profile in ['telegram', 'facebook']: 
                    comment = summaryLinks 
                elif profile not in 'wordpress':
                    comment = ''
                if profile == 'pocket': 
                    if firstLink: 
                        link, llink = firstLink, link

                msgLog = (f"{indent}title: {title}")
                logMsg(msgLog, 2, 0)
                msgLog = (f"{indent}link: {link}")
                logMsg(msgLog, 2, 0)
                msgLog = (f"{indent}i: {i}")
                logMsg(msgLog, 2, 0)

                if tags: 
                    msgLog = (f"{indent}Tags {tags}")
                    logMsg(msgLog, 2, 0)

                msgLog = (f"{indent}I'll publish: {title} - {link}")
                logMsg(msgLog, 1, 1)

                if not simmulate:
                    if action[0] == "cache": 
                        apiDst.setPosts()
                        res = apiDst.addPosts(listPosts)
                        res = apiDst.publishPost('', '', '', 
                                more = (apiSrc, listPosts2))
                    elif ((action[2] == "twitter") 
                            and (src[0] == 'twitter')): 
                        # Is this the correct place?
                        idPost = link.split('/')[-1]
                        msgLog = (f"{indent}I'll publish: {title} "
                                  "- {link}")
                        logMsg(msgLog, 1, 1)
                        msgLog = (f"{indent}I'll publish: {title} "
                                  f"- {link} - {idPost}")
                        logMsg(msgLog, 1, 1)
                        res = apiDst.publishApiRT((title, link, 
                                                   comment, 
                                                   {'idPost' : idPost}))
                        link =  listPosts[-1][1]
                    elif ((action[2] == "twitter") 
                            and (action[1] == 'rt')): 
                        msgLog = (f"{indent}Fail! Nothing to be done")
                        logMsg(msgLog, 1, 1)
                        res = "Fail! Nothing to be done"
                    else: 
                        res = None
                        if hasattr(apiDst, 'service'):
                            clsService = getModule(apiDst.service)
                            if hasattr(apiDst, "publishPost"):
                                if profile in ['tumblr']: 
                                    # For the cache we use the origin's
                                    # url but sometimes we need the url
                                    # of the service
                                    apiDst.setUrl(
                                        f"https://{apiDst.user}.tumblr.com/")
                                    res = apiDst.publishPost(title, 
                                            link, comment)
                                elif profile in ['wordpress']: 
                                    res = apiDst.publishPost(title, 
                                                             link, 
                                                             comment, 
                                                             tags=tags)
                                    if '401' in res:
                                        res = f"Fail! {res}"
                                else: 
                                    if not tags: 
                                        tags = (apiSrc, listPosts2)
                                    res = apiDst.publishPost(title, 
                                                             link, 
                                                             comment, 
                                                             tags=tags)
                            else: 
                                res = apiDst.publish(i) 
                    indent = f"{indent[:-1]}"

                    if ((not res) or (res and 
                        (('You have already retweeted' in res) or 
                         ('Status is a duplicate.' in res) or 
                            not ('Fail!' in res)))):
                        msgLog = (f"{indent}End publish, reply: {res}")
                        logMsg(msgLog, 1, 1)

                        if llink:
                            link = llink
                        if link and (src[0] not in ['cache']):  
                            if isinstance(lastLink, list):
                                link = "\n".join(
                                    [
                                        "{}".format(post[1])
                                        for post in reversed(listPosts)
                                    ]
                                )
                                link = link + "\n" + "\n".join(lastLink)
                            logging.info(f"Link: {link}")
                            try:
                                logging.info(f"self Link: {apiDst.lastLink}")
                            except:
                                logging.info(f"self Link: ")
                            updateLastLink(apiDst.getUrl(), 
                                            link, socialNetwork)
                            apiSrc.updateLastLink(apiDst, link)
                    else:
                        if res.find('Status is a duplicate')>=0:
                            msgLog = (f"{indent}End publish, "
                                      f"reply: {res}")
                        else:
                            msgLog = (f"{indent}End publish, "
                                      f"reply: {res}")
                        logMsg(msgLog, 1, 1)
                else:
                    msgLog = (f"{indent}This is a simmulation")
                    logMsg(msgLog, 1, 1)
                    msgLog = (f"{indent}I'd record link: {link}")
                    logMsg(msgLog, 1, 1)
                    fN = fileNamePath(apiDst.getUrl(), socialNetwork)
                    msgLog = (f"{indent}in file ", f"{fN}.last")
                    logMsg(msgLog, 1, 1)
                    # apiSrc.updateLastLink(apiDst, link)

                postaction = apiSrc.getPostAction()
                if (not postaction) and (src[0] in ["cache"]):
                    postaction = "delete"
                if postaction:
                    msgLog = (f"{indent} Post Action {postaction}")
                    logMsg(msgLog, 1, 1)

                if ((not simmulate) 
                    and (not res or res 
                             and ('Status is a duplicate.' in res) 
                             and ('You have already retweeted' in res) 
                             or not ('Fail!' in res))):
                    try:
                        cmdPost = getattr(apiSrc, postaction)
                        msgLog = (f"[indent]Post Action {postaction} "
                                  f"command {cmdPost}")
                        logMsg(msgLog, 1, 0)
                        res = cmdPost(i - 1)
                        msgLog = (f"{indent}End {postaction}, reply: {res}")
                        logMsg(msgLog, 1, 1)
                    except:
                        msgLog = (f"{indent}No postaction or wrong one")
                        logMsg(msgLog, 1, 1)
                
                msgLog = (f"{indent}Available {len(apiSrc.getPosts())-1}")
                logMsg(msgLog, 1, 1)
            else:
                msgLog = f"{indent}Empty listPosts or some problem {listPosts}"
                # Sometimes the module (moduleGmail) returns a list of None
                # values
                logMsg(msgLog, 1, 1)
        else:
            if (num<=0):
                msgLog = (f"{indent}No posts available")
                logMsg(msgLog, 1, 1)
            elif (diffTime<=hours):
                msgLog = (f"{indent}Not enough time passed")
                logMsg(msgLog, 1, 1)
 
        return textEnd

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
                            toAppend = (service, url, val, nick, timeW, bufferMax)
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
                                    config.get(section, service),
                                    timeW,
                                    bufferMax,
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
                                            "set",
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
                    toAppend = (service, "set", dst[3], method[1], dst[4])
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
        for i, src in enumerate(srcs):
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
                name = f"{src[0]}[{i}]"
                if src in self.more:
                    # f"  More: {self.more[src]}")
                    more = self.more[src]
                else:
                    # f"  More: empty")
                    more = None

                if src[0] in ['cache']:
                    text = (f"Source: {more['url']} ({src[3]})")
                else:
                    text = (f"Source: {src[2]} ({src[3]})")
                textEnd = (f"Source: {name} {src[2]} {src[3]}")
                # print(text)
                actions = self.rules[src]
                for k, action in enumerate(actions): 
                    if (select and (select.lower() != f"{src[0].lower()}{i}")):
                        actionMsg = f"Skip."
                    else:
                        actionMsg = (f"Scheduling...")
                    nameA = f"{name} {actionMsg} ({action[1]})"
                    msgLog = (f"{nameA} {text} Action {k}:"
                              f" {action[3]}@{action[2]} ({action[1]})")
                    textEnd = f"{textEnd}\n{msgLog}"
                    logMsg(msgLog, 1, 1)
                    nameA = f"{name} ({action[1]})"
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
        filename=LOGDIR + "/rssSocial.log",
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

    # return

    # rules.printList(impRuls, "Implicit rules")

    # print("===========================================================")
    # for i,rul in enumerate(rules.available):
    #     print(f"{rul.upper()}({len( rules.available[rul]['data'])}) "
    #           f"{rules.available[rul]['name']}\n"
    #           f"{rules.available[rul]['data']}")


if __name__ == "__main__":
    main()
