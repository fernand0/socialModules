# This module provides infrastructure for reading content from different places
# It stores in a convenient and consistent way the content in order to be used
# in other programs

import configparser
import html
import re
import sys
from html.parser import HTMLParser

from bs4 import BeautifulSoup, Tag

from socialModules.configMod import *


class Content:

    def __init__(self, indent=''):
        self.url = ""
        self.name = ""
        self.nick = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.posts = None
        self.postsFormatted = None
        self.nextPosts = {}
        self.time = 0
        self.bufferapp = None
        self.program = None
        self.buffer = None
        self.cache = None
        self.xmlrpc = None
        self.search = None
        self.api = {}
        self.lastLinkPublished = None
        self.numPosts = 0
        self.user = None
        self.client = None
        ser = self.__class__.__name__
        self.service = self.__class__.__name__[6:]
        self.indent = indent
        # msgLog = (f"{self.indent} Service {self.service} initializing")
        # logMsg(msgLog, 1, 0)
        # They start with module
        self.hold = None

    def setClient(self, account):
        msgLog = (f"{self.indent} Connecting {self.service}: {account}")
        logMsg(msgLog, 1, 0)
        # print(f"acc: {account}")
        # print(f"tt: {type(account[1])}")
        client = None

        if isinstance(account, str):
            logging.info(f"{self.indent} Service {self.service} setClient str")
            #FIXME We should not need these ifs
            self.user = account
        # elif isinstance(account[1], str) and (account[1].find('@') > 0):
        #     logging.info(f"{self.indent} setClient account[1] str with @")
        #     # Grrrr
        #     self.user = account[1]
        # elif isinstance(account[0], str):
        #     logging.info(f"{self.indent} setClient account[1] str without @")
        #     self.user = account[0]
        else:
            msgLog = f"{self.indent} setClient else. This shouldn't happen"
            logMsg(msgLog, 3, 0)
            logging.info(f"{self.indent} setClient else")
            # Deprecated
            self.user = account[1][1]

        msgLog = f"{self.indent} Service config: {self.service}"
        logMsg(msgLog, 2, 0)

        configFile = f"{CONFIGDIR}/.rss{self.service}"
        try:
            config = configparser.RawConfigParser()
            config.read(f"{configFile}")
        except:
            msgLog = (f"Does file {configFile} exist?")
            self.report({self.indent}, msgLog, 0, '')

        keys = ''
        try:
            keys = self.getKeys(config)
            logging.debug(f"{self.indent} user {self.user}")
        except:
            if not config.sections():
                # FIXME: Are you sure?
                msgLog = (f"{self.indent} Do the adequate keys exist "
                          f"in {configFile}")
                logMsg(msgLog, 3, 0)

        if keys:
            try:
                client = self.initApi(keys)
            except:
                msgLog(f"{self.indent} Exception")
                logMsg(msgLog, 2, 0)
                if not config.sections and not keys:
                    self.report({self.service}, "No keys", "", '')
                else:
                    self.report({self.service}, "Some problem", "", '')

            self.client = client
        else:
            self.report(self.service, "No keys", "", '')
            self.client = None

    def getService(self):
        if hasattr(self, 'auxClass'):
            return self.auxClass
        else:
            return self.service

    def getService(self):
        if hasattr(self, "service"):
            return self.service
        else:
            return ""

    def setUser(self, nick):
        self.user = nick

    def getUser(self):
        user = ""
        if hasattr(self, "user"):
            user = self.user
        return user

    def getNick(self):
        if hasattr(self, 'nick'):
            nick = getattr(self, 'nick')#, '')
        else:
            nick = ''
        return nick

    def getAttribute(self, post, selector):
        try:
            return post.get(selector, '')
        except:
            print(f"Attribute: {post}")
            return ""
        # result = ""
        # try:
        #     result = post[selector]
        # except:
        #     result = ""

        # return result

    def setApiPosts(self):
        pass

    def setPosts(self):
        msgLog = f"{self.indent} service {self.service} Start setPosts"
        logMsg(msgLog, 2, 0)
        nick = self.getNick()
        if nick:
            identifier = nick
        else:
            identifier = self.getUrl()

        typePosts = self.getPostsType()
        msgLog = (f"{self.indent} Service {self.service} setting "
                  f"{self.getPostsType()}")
        logMsg(msgLog, 1, 0)
        if hasattr(self, "getPostsType") and self.getPostsType():
            typePosts = self.getPostsType()
            if typePosts == "cache":
                # FIXME: cache??
                cmd = getattr(self, "setApiCache")
            else:
                cmd = getattr(
                    self, f"setApi{self.getPostsType().capitalize()}"
                )
        else:
            cmd = getattr(self, "setApiPosts")

        # msgLog = (f"{self.indent} Cmd: {cmd}")
        # logMsg(msgLog, 2, 0)
        posts = cmd()
        msgLog = (f"{self.indent} Posts: {posts}")
        logMsg(msgLog, 2, 0)
        self.assignPosts(posts)
        msgLog = f"{self.indent} service {self.service} End setPosts"
        logMsg(msgLog, 2, 0)

    def getClient(self):
        client = None
        if hasattr(self, "client"):
            client = self.client
        return client

    def getUrl(self):
        url = ""
        if hasattr(self, "url"):
            url = self.url
        return url

    def fileNameBase(self, dst):
        msgLog = (f"{self.indent} fileNameBase src: {self}")
        logMsg(msgLog, 2, 0)
        src = self
        nameSrc = type(src).__name__
        if 'module' in nameSrc:
            nameSrc = nameSrc[len('module'):]
            msgLog = (f"{self.indent} fileNameBase module Src: {nameSrc}")
            logMsg(msgLog, 2, 0)
        nameDst = type(dst).__name__
        if 'module' in nameDst:
            nameDst = nameDst[len('module'):]
            msgLog = (f"{self.indent} fileNameBase module Dst: {nameDst}")
            logMsg(msgLog, 2, 0)
            userD = dst.getUser()
            if hasattr(dst, 'socialNetwork'):
                serviceD = dst.socialNetwork
            else:
                serviceD = nameDst
            logging.debug(f"{self.indent} user... {dst.user}")
            user = src.getUser()
            service = src.getService()
            msgLog = (f"{self.indent} fileNameBase userD: {userD}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"{self.indent} fileNameBase serviceD: {serviceD}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"{self.indent} fileNameBase user: {user}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"{self.indent} fileNameBase service: {service}")
            logMsg(msgLog, 2, 0)
        else:
            user = src.getUrl()
            service = self.service
            # userD = dst[0]
            serviceD = dst[1]
            nameDst = serviceD.capitalize()

        if hasattr(src, 'getPostsType'):
            typeSrc = src.getPostsType()
        else:
            typeSrc = 'posts'

        if hasattr(dst, 'getPostsType'):
            typeDst = dst.getPostsType()
        else:
            typeDst = 'posts'

        msgLog = (f"{self.indent} fileNameBase typeSrc: {typeSrc}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} fileNameBase typeDst: {typeDst}")
        logMsg(msgLog, 2, 0)
        # print(f"user: {user}")
        # if not user:
        #     user = dst.getUrl()
        # print(f"user: {user}")
        fileName = (f"{nameSrc}_{typeSrc}_"
                    f"{user}_{service}__"
                    f"{nameDst}_{typeDst}_"
                    f"{userD}_{serviceD}")
        fileName = (f"{DATADIR}/{fileName.replace('/','-').replace(':','-')}")
        msgLog = (f"{self.indent} End fileNameBase fileName: {fileName}")
        logMsg(msgLog, 2, 0)

        return fileName

    def updateLastLink(self, dst, link):
        if link and isinstance(link, list):
            #FIXME: This will be removed
            link = self.getPostLink(link[-1])
        elif not link:
            post = self.getNextPost()
            msgLog = f"{self.indent} nextPost {post}"
            logMsg(msgLog, 2, 0)
            link = self.getPostLink(post)
        msgUpdate = f"last link {link} in {self.service}"
        msgLog = f"{self.indent} Updating {msgUpdate}"
        logMsg(msgLog, 1, 0)

        fileName = f"{self.fileNameBase(dst)}.last"
        msgLog = f"{self.indent} fileName {fileName}"
        logMsg(msgLog, 2, 0)
        msgLog = checkFile(fileName)
        if 'OK' in msgLog:
            with open(fileName, "w") as f:
                if link:
                    if isinstance(link, bytes):
                        f.write(link.decode())
                    elif isinstance(link, str):
                        f.write(link)
                    else:
                        f.write(link[0])

            self.setLastLink(dst)
        else:
            logMsg(msgLog, 3, 0)

        return f"Updated {msgUpdate}"

    def getLastLinkNew(self, dst):
        return self.lastLinkPublished

    def getLastLink(self):
        url = self.getUrl()
        service = self.service.lower()
        nick = self.getUser()
        fileName = (f"{fileNamePath(url, (service, nick))}.last")

        # logging.debug(f"Urll: {url}")
        # logging.debug(f"Nickl: {nick}")
        # logging.debug(f"Servicel: {service}")
        # logging.debug(f"fileName: {fileName}")
        msgLog = checkFile(fileName)
        # dirName = os.path.dirname(fileName)
        # if not os.path.isdir(dirName):
        #     return ""
        #     sys.exit("No directory {dirName} exists")
        if service in ['html']:
            #FIXME: Not here
            linkLast = ''
        elif "OK" in msgLog:
            with open(fileName, "rb") as f:
                linkLast = f.read().decode().split()  # Last published
        else:
            logMsg(msgLog, 3, 0)
        lastLink = ''
        if len(linkLast) == 1:
            lastLink = linkLast[0]
        else:
            lastLink = linkLast

        msgLog = f"{self.indent} {linkLast}"
        logMsg(msgLog, 1, 0)

        self.lastLink = lastLink
        return lastLink

    def setLastLink(self, dst = None):
        if hasattr(self, 'fileName') and self.fileName:
            fileName = f"{self.fileName}.last"
        else:
            if dst:
                self.fileName = self.fileNameBase(dst)
                fileName = f"{self.fileName}.last"
            else:
                url = self.getUrl()
                service = self.service.lower()
                nick = self.getUser()
                fileName = (f"{fileNamePath(url, (service, nick))}.last")

        lastTime = ''
        linkLast = ''
        msgLog = checkFile(fileName)
        if 'OK' in msgLog:
            with open(fileName, "rb") as f:
                linkLast = f.read().decode().split()  # Last published
            lastTime = os.path.getctime(fileName)
        else:
            lastTime = 0
            self.report(self.service, msgLog, '', '')

        self.lastLinkPublished = linkLast
        self.lastTimePublished = lastTime

    def getLastTime(self, other = None):
        lastTime = 0.0
        myLastLink = ""
        # You always need to check lastLink?
        # Example: gmail, Twitter
        if other:
            fileName = self.fileNameBase(other)
            lastTime2 = ""
            if os.path.isfile(fileName):
                lastTime2 = os.path.getctime(fileName)
            myLastLink2 = self.getLastLinkNew(other)
            print(f"myLastLink2: {myLastLink2} {lastTime2}")
            return myLastLink2, lastTime2
        try:
                url = self.getUrl()
                service = self.service.lower()
                nick = self.getUser()
                fN = (f"{fileNamePath(url, (service, nick))}.last")
                lastTime = os.path.getctime(fN)
                myLastLink = self.getLastLink()
        except:
                fN = ""
                msgLog = (f"No last link")
                logMsg(msgLog, 2, 0)

        self.lastLinkPublished = myLastLink
        self.lastTimePublished = lastTime

        logMsg(f"myLastLink: {myLastLink} {lastTime}",2 , 0)
        return myLastLink, lastTime

    def setNextAvailableTime(self, tNow, tSleep, dst = None):
        fileNameNext = ''
        if dst:
            fileNameNext = f"{self.fileNameBase(dst)}.timeAvailable"
            msgLog = checkFile(fileNameNext)
            if "OK" in msgLog:
                with open(fileNameNext,'wb') as f:
                    pickle.dump((tNow, tSleep), f)
            else:
                self.report(self.service, msgLog, '', '')
        else:
            print(f"Not implemented!")

    def setNextTime(self, tNow, tSleep, dst = None):
        fileNameNext = ''
        if dst:
            fileNameNext = f"{self.fileNameBase(dst)}.timeNext"
            msgLog = checkFile(fileNameNext)
            logMsg(f"{self.indent} fileNameNext: {msgLog}", 2, 0)
            if 'OK' in msgLog:
                logging.debug(f"{self.indent} OK fileNext")
                with open(fileNameNext,'wb') as f:
                    pickle.dump((tNow, tSleep), f)
            else:
                logging.debug(f"{self.indent} not OK fileNext")
                self.report('', msgLog, '', '')
        else:
            msgLog = (f"Not implemented!")
            logMsg(msgLog, 3, 0)

    def setNumPosts(self, numPosts):
        self.numPosts = numPosts

    def getNumPosts(self):
        return self.numPosts

    def setUrl(self, url):
        self.url = url

    def setSearch(self, term):
        self.search = term

    def getSearch(self):
        name = ""
        if hasattr(self, "search"):
            name = self.search
        return name

    def getName(self):
        name = ""
        if hasattr(self, "name"):
            name = self.name
        return name

    def setName(self, name):
        self.name = name

    def setPostAction(self, action):
        self.postaction = action


    def getSiteTitle(self):
        return self.getName()

    def getPostAction(self):
        postaction = "delete"
        if hasattr(self, "postaction"):
            postaction = self.postaction
        return postaction

    def getPostContentHtml(self, post):
        return ""

    def getPostContentLink(self, post):
        return self.getPostLink(post)

    def getSocialNetwork(self):
        socialNetwork = (self.service, self.nick)
        return socialNetwork


    def getSocialNetworks(self):
        socialNetworks = None
        if hasattr(self, "socialNetworks"):
            socialNetworks = self.socialNetworks
        return socialNetworks

    # Old ? To eliminate
    def setSocialNetworks(self, socialNetworksConfig):
        socialNetworksOpt = [
            "twitter",
            "facebook",
            "telegram",
            "wordpress",
            "medium",
            "linkedin",
            "pocket",
            "mastodon",
            "instagram",
            "imgur",
            "tumblr",
            "slack",
            "refind",
            "file",
            "kindle",
        ]
        msgLog =("  sNC {socialNetworksConfig}")
        logMsg(msgLog, 2, 0)
        for sN in socialNetworksConfig:
            if sN in socialNetworksOpt:
                self.addSocialNetwork((sN, socialNetworksConfig[sN]))
        msgLog = ("  sNN {self.getSocialNetworks()}")
        logMsg(msgLog, 2, 0)

    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def assignPosts(self, posts):
        self.posts = []
        if posts:
            for post in posts:
                self.posts.append(post)

    def getPosts2(self):
        posts = None
        if hasattr(self, 'posts2'):
            posts = self.posts2
        return posts

    def getPosts(self):
        posts = None
        if hasattr(self, 'posts'):
            posts = self.posts
        return posts

    def getPost(self, i):
        post = None
        posts = self.getPosts()
        if posts and (i >= 0) and (i < len(posts)):
            post = posts[i]
        return post

    def getPostImages(self, post):
        return self.extractImages(post)

    def getImagesTags(self, i):
        res = self.getImages(i)
        tags = []
        for iimg in res:
            for tag in iimg[3]:
                if tag not in tags:
                    tags.append(tag)

        return tags

    def getPostImagesCode(self, post):
        # Needs work
        url = self.getPostLink(post)
        res = self.getPostImages(post)
        text = ""
        if res:
            for iimg in res:
                print(iimg)

                if iimg[2]:
                    description = iimg[2]
                else:
                    description = ""

                if description:
                    import string

                    if (iimg[1] and iimg[1].endswith(" ")
                            or iimg[1].endswith("\xa0")):
                        # \xa0 is actually non-breaking space in Latin1 (ISO
                        # 8859-1), also chr(160).
                        # https://stackoverflow.com/questions/10993612/how-to-remove-xa0-from-string-in-python
                        title = iimg[1][:-1]
                    else:
                        if iimg[1]:
                            title = iimg[1]
                        else:
                            title = "No title"
                    if iimg[0].endswith('mp4'):
                        srcTxt = (f"<video width='640' height='360' controls "#"class='alignnone size-full "
                                  #f"wp-image-3306'>
                                  f'src="{iimg[0]}" '
                                  f'type="video/mp4"></video>')
                    else:
                        srcTxt = (f"<img class='alignnone size-full "
                                  f"wp-image-3306' src='{iimg[0]}' "
                                  f"alt='{title} {description}' "
                                  f"width='776' height='1035' />")

                    if title[-1] in string.punctuation:
                        text = (
                            '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                            #'<img class="alignnone size-full '
                            #'wp-image-3306" src="{}"
                            '{} </a></p>'.format( text, description, url, srcTxt)
                            )
                    else:
                        text = (
                            '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                            #'<img class="alignnone size-full '
                            #'wp-image-3306" src="{}"
                            '{} /></a></p>'.format( text, description, url, srcTxt)
                            )
                else:
                    title = iimg[1]
                    if iimg[0].endswith('mp4'):
                        srcTxt = (f"<video width='640' height='360' controls " #class='alignnone size-full "
                                  #f"wp-image-3306'>
                                  f" src='{iimg[0]}' "
                                  f"type='video/mp4'></video>")
                    else:
                        srcTxt = (f"<a href='{url}'><img class='alignnone size-full "
                                  f"wp-image-3306' src='{iimg[0]}' "
                                  f"alt='{title} {description}' "
                                  f"width='776' height='1035' /></a>")
                    text = (
                        '{}\n<p>'#<img class="alignnone '
                        #'size-full wp-image-3306" src="{}"
                        '{} '
                        #'alt="{} {}"'
                        #'width="776" height="1035" />
                        '</p>'.format(text, srcTxt )
                        )
        return text


    def getImagesCode(self, i):
        # FIXME: use some template system.
        res = self.getImages(i)
        # print(self.getPosts()[i])
        print(f"imagesCode: {res}")
        url = self.getPostLink(self.getPosts()[i])
        text = ""
        for iimg in res:
            print(iimg)

            if iimg[2]:
                description = iimg[2]
            else:
                description = ""

            if description:
                import string

                if (iimg[1] and iimg[1].endswith(" ")
                        or iimg[1].endswith("\xa0")):
                    # \xa0 is actually non-breaking space in Latin1 (ISO
                    # 8859-1), also chr(160).
                    # https://stackoverflow.com/questions/10993612/how-to-remove-xa0-from-string-in-python
                    title = iimg[1][:-1]
                else:
                    if iimg[1]:
                        title = iimg[1]
                    else:
                        title = "No title"
                if iimg[0].endswith('mp4'):
                    srcTxt = (f"<video width='640' height='360' controls "#"class='alignnone size-full "
                              #f"wp-image-3306'>
                              f'src="{iimg[0]}" '
                              f'type="video/mp4"></video>')
                else:
                    srcTxt = (f"<img class='alignnone size-full "
                              f"wp-image-3306' src='{iimg[0]}' "
                              f"alt='{title} {description}' "
                              f"width='776' height='1035' />")

                if title[-1] in string.punctuation:
                    text = (
                        '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                        #'<img class="alignnone size-full '
                        #'wp-image-3306" src="{}"
                        '{} </a></p>'.format( text, description, url, srcTxt)
                        )
                else:
                    text = (
                        '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                        #'<img class="alignnone size-full '
                        #'wp-image-3306" src="{}"
                        '{} /></a></p>'.format( text, description, url, srcTxt)
                        )
            else:
                title = iimg[1]
                if iimg[0].endswith('mp4'):
                    srcTxt = (f"<video width='640' height='360' controls " #class='alignnone size-full "
                              #f"wp-image-3306'>
                              f" src='{iimg[0]}' "
                              f"type='video/mp4'></video>")
                else:
                    srcTxt = (f"<a href='{url}'><img class='alignnone size-full "
                              f"wp-image-3306' src='{iimg[0]}' "
                              f"alt='{title} {description}' "
                              f"width='776' height='1035' /></a>")
                text = (
                    '{}\n<p>'#<img class="alignnone '
                    #'size-full wp-image-3306" src="{}"
                    '{} '
                    #'alt="{} {}"'
                    #'width="776" height="1035" />
                    '</p>'.format(text, srcTxt )
                    )
        return text

    def getPosNextPost(self):
        posts = self.getPosts()
        posLast = -1

        if posts and (len(posts) > 0):
            if self.getPostsType() in ['favs', 'queue']:
                # This is not the correct condition, it should be independent
                # of social network
                posLast = 1
            else:
                lastLink = self.getLastLinkPublished()
                # print(f"lastLink: {lastLink}")
                if lastLink:
                    posLast = self.getLinkPosition(lastLink)
                else:
                    posLast = len(posts)

        return posLast

    def getNumNextPosts(self, num):
        listPosts = []
        posLast = self.getPosNextPost()
        i = posLast
        # print(f"iiii: {i}")
        for j in range(num, 0, -1):
            i = i - 1
            if i < 0:
                break
            post = self.getPost(i)
            if post:
                listPosts.append(post)

        return listPosts

    def getNumNextPost(self, num):
        # To be abandonded? TODO
        listPosts = []
        posLast = self.getPosNextPost()
        i = posLast
        # print(f"iiii: {i}")
        for j in range(num, 0, -1):
            i = i - 1
            if i < 0:
                break
            post = self.getPost(i)
            # print("p",post)
            if post:
                contentHtml = self.getPostContentHtml(post)
                if contentHtml.startswith('http'):
                    (theContent, theSummaryLinks) = ("", "")
                else:
                    soup = BeautifulSoup(contentHtml,'lxml')
                    if hasattr(self, 'getLinksToAvoid') and self.getLinksToAvoid():
                        (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinksToAvoid())
                        #logging.debug("theC %s" % theContent)
                        if theContent.startswith('Anuncios'):
                            theContent = ''
                            # logging.debug("theC %s"% theContent)
                    else:
                        (theContent, theSummaryLinks) = self.extractLinks(soup, "")
                        # logging.debug("theC %s"% theContent)
                        if theContent.startswith('Anuncios'):
                            theContent = ''
                        # logging.debug("theC %s"% theContent)
                    # theSummaryLinks = theContent + '\n' + theSummaryLinks

                field0 =self.getPostTitle(post)
                field1 = self.getPostLink(post)
                field2 = self.getPostContentLink(post)
                field3 = self.getPostImage(post)
                field4 =self.getPostContent(post)
                field5 = self.getPostContentHtml(post)
                field6 =f"{theContent}\n{theSummaryLinks}"
                field7 = self.getPostImagesTags(post)
                field8 = self.getPostImagesCode(post)
                postData = (
                    field0,            #0
                    field1,             #1
                    field2,      #2
                    field3,            #3
                    field4,          #4
                    field5,      #5
                    field6, #6
                    field7,       #7
                    field8        #8
                    )
                if postData:
                    listPosts.append(postData)

        return listPosts

    def getNextPost(self):
        posLast = self.getPosNextPost()
        post = self.getPost(posLast - 1)

        return post

    def getTitle(self, i):
        title = ""
        if i < len(self.getPosts()):
            post = self.getPost(i)
            title = self.getPostTitle(post)
        return title

    def getLink(self, i):
        link = ""
        if i < len(self.getPosts()):
            post = self.getPost(i)
            link = self.getPostLink(post)
        return link

    def getId(self, j):
        idPost = -1
        if j < len(self.getPosts()):
            post = self.getPost(j)
            msgLog = (f"{self.indent} Post: {post}")
            logMsg(msgLog, 2, 0)
            idPost = self.getPostId(post)
        return idPost

    def splitPost(self, post):
        splitListPosts = []
        for imgL in post[3]:
            myPost = list(post)
            # logging.info("mP", myPost)
            myPost[3] = imgL
            splitListPosts.append(tuple(myPost))

        return splitListPosts

    def getNumPostsData(self, num, i, lastLink=None):
        listPosts = []
        for j in range(num, 0, -1):
            # logging.debug("j, i %d - %d" % (j, i))
            i = i - 1
            if i < 0:
                break
            post = self.obtainPostData(i, False)
            if post:
                listPosts.append(post)
        return listPosts

    def getDrafts(self):
        if hasattr(self, "drafts"):
            return self.drafts
        else:
            if hasattr(self, "getPostsType"):
                return self.getPosts()

    def setPostsType(self, postsType):
        self.postsType = postsType

    def getPostsType(self):
        postsType = 'posts'
        if hasattr(self, "postsType"):
            postsType = self.postsType
        return postsType

    def addComment(self, post, comment):
        if comment:
            post = comment + " " + post
        try:
            h = HTMLParser()
            post = h.unescape(post)
        except:
            post = html.unescape(post)

        return post

    def publishImage(self, *args, **kwargs):
        post, image = args
        more = kwargs
        msgLog = (f"{self.indent} Service {self.service} publishing image "                       f"{image}: {post}")
        logMsg(msgLog, 2, 0)
        try:
            reply = self.publishApiImage(post, image, **more)
            return self.processReply(reply)
        except:
            return self.report(self.service, post, image, sys.exc_info())

    def deleteApiNextPost(self):
        pass

    def deleteNextPost(self):
        reply = ''
        msgLog = (f"{self.indent} Service {self.service} deleting next post")
        logMsg(msgLog, 2, 0)
        try:
            post = self.getNextPost()
            if post:
                msgLog = (f"{self.indent} Service {self.service} deleting "
                          f"post {post}")
                logMsg(msgLog, 2, 0)
                idPost = self.getPostId(post)
                msgLog = (f"{self.indent} Service {self.service} post Id "
                          f"post {idPost}")
                logMsg(msgLog, 2, 0)
                if (hasattr(self, 'getPostsType')
                    and (self.getPostsType())
                    and (hasattr(self,
                            f"deleteApi{self.getPostsType().capitalize()}"))):
                    nameMethod = self.getPostsType().capitalize()

                    method = getattr(self, f"deleteApi{nameMethod}")
                    res = method(idPost)
                    reply = self.processReply(res)
            else:
                reply = "Fail! No posts available"
        except:
            reply = self.report(self.service, post, idPost, sys.exc_info())
        return reply

    def publishPosPost(self, apiSrc, pos):
        msgLog = (f"{self.indent} Service {self.service} publishing post in "
                  f"pos {pos} from {apiSrc}")
        logMsg(msgLog, 2, 0)
        reply = ''
        try:
            post = apiSrc.getPost(pos)
            if post:
                msgLog = (f"{self.indent} Service {self.service} publishing "
                          f"post {post}")
                logMsg(msgLog, 2, 0)

                nameMethod = 'Post'

                method = getattr(self, f"publishApi{nameMethod}")
                msgLog = (f"{self.indent} Service {self.service} "
                          f"method: {method}")
                logMsg(msgLog, 2, 0)
                res = method(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "Fail! No posts available"
        except:
            reply = self.report(self.service, apiSrc, '', sys.exc_info())

        return reply

    def publishNextPost(self, apiSrc):
        reply = ''
        msgLog = (f"{self.indent} Service {self.service} publishing next post")
        logMsg(msgLog, 2, 0)
        try:
            post = apiSrc.getNextPost()
            if post:
                msgLog = (f"{self.indent} Post {post}")
                logMsg(msgLog, 2, 0)

                title = apiSrc.getPostTitle(post)
                link = apiSrc.getPostLink(post)
                comment= ''
                if hasattr(apiSrc, 'getPostApiDate'):
                    # FIXME we should use the more general method for calling
                    # publishing methods
                    comment = apiSrc.getPostApiDate(post)
                nameMethod = 'Post'
                if (hasattr(apiSrc, 'getPostsType')
                    and (apiSrc.getPostsType())
                    and (hasattr(self,
                        f"publishApi{apiSrc.getPostsType().capitalize()}"))):
                    nameMethod = self.getPostsType().capitalize()

                method = getattr(self, f"publishApi{nameMethod}")
                res = method(title, link, comment)
                reply = self.processReply(res)
            else:
                msgLog = (f"{self.indent} No posts available")
                logMsg(msgLog, 2, 0)
                reply = "No posts available"
        except:
            reply = self.report(self.service, apiSrc, post, sys.exc_info())

        return reply

    def publishPost(self, *args, **more):
        api = ''
        post = ''
        nameMethod = 'Post'
        listPosts = []
        if len(args) == 3:
            title = args[0]
            link = args[1]
            comment = args[2]
            msgLog = (f"{self.indent} Service {self.service} publishing post "
                      f"{title}, {link} with comment: {comment}")
            logMsg(msgLog, 2, 0)
        elif len(args) == 1:
            # apiSrc= args[0]
            listPosts = args#[1]
            msgLog = (f"{self.indent} Service {self.service} publishing post "
                      f"{listPosts}")
            logMsg(msgLog, 2, 0)
            print(f"    Publishing in {self.service}: posts {listPosts}")
            for post in listPosts:
                title = self.getPostTitle(post)
                link = self.getPostLink(post)
                comment = ''
                #more = {'api': apiSrc, 'post': post}
                print(f"Title: {title}\nLink: {link}")
            return
        else:
            title = ''
            link = ''
            comment = ''
        if more:
            print(f"    Publishing in {self.service}: {more}")
            # if 'tags' in more:
            #     print(f"    Publishing in {self.service}: {type(more['tags'])}")

            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)

        print(f"    Publishing in {self.service}: {title}")
        print(f"    Publishing in {self.service}:  {link}")
        print(f"    Publishing in {self.service}: {comment}")
        reply = 'Fail!'
        try:
            nameMethod = 'Post'
            if (hasattr(self, 'getPostsType')
                    and (self.getPostsType())
                    and (hasattr(self,
                        f"publishApi{self.getPostsType().capitalize()}"))):
                nameMethod = self.getPostsType().capitalize()

            method = getattr(self, f"publishApi{nameMethod}")

            if listPosts:
                for post in listPosts:
                    reply = method(title, link, comment, api=api, post=post)
            else:
                if api and post:
                    reply = method(title, link, comment, api=api, post=post)
                else:
                    reply = method(title, link, comment)

            reply = self.processReply(reply)
        except:
            reply = self.report(self.service, title, link, sys.exc_info())

        return reply

    def deletePostId(self, idPost):
        msgLog = (f"{self.indent} Service {self.service} deleting post "
                  f"id {idPost}")
        logMsg(msgLog, 2, 0)
        typePosts = self.getPostsType()
        if typePosts:
            if typePosts == "cache":
                cmd = getattr(self, "deleteApi")
            else:
                cmd = getattr(
                    self, "deleteApi" + self.getPostsType().capitalize()
                )
        else:
            cmd = getattr(self, "deleteApiPosts")
        reply = cmd(idPost)
        return self.processReply(reply)

    def deletePost(self, post):
        msgLog = (f"{self.indent} Service {self.service} deleting post "
                  f" {post}")
        logMsg(msgLog, 2, 0)
        idPost = self.getPostId(post)
        msgLog = (f"{self.indent} Service {self.service} deleting post "
                  f"id {idPost}")
        logMsg(msgLog, 2, 0)
        result = self.deletePostId(idPost)
        return result

    def delete(self, j):
        msgLog = (f"{self.indent} Service {self.service} deleting post "
                  f"pos: {j}")
        logMsg(msgLog, 2, 0)
        post = self.getPost(j)
        idPost = self.getPostId(self.getPost(j))
        result = self.deletePostId(idPost)
        return result

    def processReply(self, reply):
        msgLog = (f"{self.indent} Service {self.service} res "
                  f"{reply}")
        logMsg(msgLog, 2, 0)
        return reply

    def do_edit(self, j, **kwargs):
        update = ""
        if j < len(self.getPosts()):
            post = self.getPost(j)
            if ("newTitle" in kwargs) and kwargs["newTitle"]:
                oldTitle = self.getPostTitle(post)
                newTitle = kwargs["newTitle"]
                msgLog = (f"{self.indent} Service {self.service} "
                          f"new title {newTitle}")
                logMsg(msgLog, 1, 0)
                res = self.editApiTitle(post, newTitle)
                res = self.processReply(res)
                update = f"Changed {oldTitle} with {newTitle} Id {str(res)}"
            if ("newState" in kwargs) and kwargs["newState"]:
                oldState = self.getPostState(post)
                newState = kwargs["newState"]
                msgLog = (f"{self.indent} Service {self.service} "
                          f"new state {newState}")
                logMsg(msgLog, 2, 0)
                res = self.editApiState(post, newState)
                res = self.processReply(res)
                update = f"Changed {oldState} to {newState} Id {str(res)}"
            if ("newLink" in kwargs) and kwargs["newLink"]:
                oldLink = self.getPostLink(post)
                newLink = kwargs["newLink"]
                msgLog = (f"{self.indent} Service {self.service} "
                          f"new link {newLink}")
                logMsg(msgLog, 2, 0)
                res = self.editApiLink(post, newLink)
                res = self.processReply(res)
                update = f"Changed {oldLink} with {newLink} Id {str(res)}"
            return update

    def edit(self, j, newTitle):
        msgLog = (f"{self.indent} Service {self.service} "
                  f"do edit {j} - {newTitle}")
        logMsg(msgLog, 2, 0)
        update = self.do_edit(j, newTitle=newTitle)
        return update

    def editl(self, j, newLink):
        update = self.do_edit(j, newLink=newLink)
        return update

    def updatePostsCachee(self, socialNetwork):
        service = socialNetwork[0]
        nick = socialNetwork[1]
        fileNameQ = fileNamePath(self.url, (service, nick)) + ".queue"

        with open(fileNameQ, "wb") as f:
            pickle.dump(self.nextPosts, f)
        msgLog = ("{self.indent} Writing in {fileNameQ}")
        logMsg(msgLog, 2, 0)

        return "Ok"

    def getNextPosts(self, socialNetwork):
        if socialNetwork in self.nextPosts:
            return self.nextPosts[socialNetwork]
        else:
            return None

    def addNextPosts(self, listPosts, socialNetwork):
        link = ""
        if listPosts:
            self.nextPosts[socialNetwork] = listPosts
            link = listPosts[len(listPosts) - 1][1]
        return link

    def addLastLinkPublished(self, socialNetwork, lastLink, lastTime):
        self.lastLinkPublished[socialNetwork] = (lastLink, lastTime)

    def getLastLinkPublished(self):
        lastLink = ''
        if self.lastLinkPublished and (len(self.lastLinkPublished) == 1):
            lastLink = self.lastLinkPublished[0]
            msgLog = (f"{self.indent} Last link (len 1) ")
        else:
            msgLog = (f"{self.indent} Last link (len >1) ")
            lastLink = self.lastLinkPublished
        if lastLink:
            msgLog = f"{msgLog} {lastLink}"
        else:
            msgLog = f"{msgLog} No lastLink"
        logMsg(msgLog, 1, 1)
        return lastLink

    def getLastTimePublished(self, indent=''):
        lastTime = ''
        msgLog = (f"{indent} No lastTimePublished")
        if hasattr(self, 'lastTimePublished'):
            lastTime = self.lastTimePublished
            msgLog = (f"{indent} lastTime {lastTime}")
            if lastTime:
                import time
                myTime = time.strftime("%Y-%m-%d %H:%M:%S",
                                        time.localtime(lastTime))
            else:
                myTime = "No time"
            msgLog = (f"{indent} Last time: {myTime}")
        logMsg(msgLog, 1, 1)
        return lastTime

    def getLinksToAvoid(self):
        return self.linksToAvoid

    def setLinksToAvoid(self, linksToAvoid):
        self.linksToAvoid = linksToAvoid

    def setTime(self, time):
        self.time = time

    def getTime(self):
        return self.time

    def setHold(self, hold):
        self.hold = hold

    def getHold(self):
        return self.hold

    # def getBuffer(self):
    #    return(self.buffer)

    # def setBuffer(self):
    #    import moduleBuffer
    #    # https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
    #    self.buffer = {}
    #    for service in self.getSocialNetworks():
    #        if service[0] in self.getBufferapp():
    #            nick = self.getSocialNetworks()[service]
    #            buf = moduleBuffer.moduleBuffer()
    #            buf.setClient(self.url, (service, nick))
    #            buf.setPosts()
    #            self.buffer[(service, nick)] = buf

    # def getBufferapp(self):
    #    return(self.bufferapp)

    # def setBufferapp(self, bufferapp):
    #    self.bufferapp = bufferapp
    #    self.setBuffer()

    def setMax(self, maxVal):
        self.max = maxVal

    def getMax(self):
        maxVal = 1
        return maxVal

    # def getCache(self):
    #     return self.cache

    # def setCache(self):
    #     import moduleCache

    #     # https://github.com/fernand0/scripts/blob/master/moduleCache.py
    #     self.cache = {}
    #     for service in self.getSocialNetworks():
    #         if (
    #             self.getProgram()
    #             and isinstance(self.getProgram(), list)
    #             and service in self.getProgram()
    #         ) or (
    #             self.getProgram()
    #             and isinstance(self.getProgram(), str)
    #             and (service[0] in self.getProgram())
    #         ):

    #             nick = self.getSocialNetworks()[service]
    #             cache = moduleCache.moduleCache()
    #             param = (self.url, (service, nick))
    #             cache.setClient(param)
    #             cache.setUrl(self.getUrl())
    #             cache.setPosts()
    #             self.cache[(service, nick)] = cache

    def getProgram(self):
        return self.program

    def setProgram(self, program):
        program = program.split("\n")
        self.program = program
        self.setCache()

    def setBufMax(self, bufMax):
        self.bufMax = bufMax

    def getBufMax(self):
        bufMax = 1
        if hasattr(self, "bufMax") and self.bufMax:
            bufMax = int(self.bufMax)
        return bufMax

    def len(self, profile):
        service = profile
        nick = self.getSocialNetworks()[profile]
        posts = []
        if self.cache and (service, nick) in self.cache:
            posts = self.cache[(service, nick)].getPosts()
        # elif self.buffer and (service, nick) in self.buffer:
        #    posts = self.buffer[(service, nick)].getPosts()

        return len(posts)

    def getPostByLink(self, link):
        pos = self.getLinkPosition(link)
        if pos >= 0:
            return self.getPosts()[pos]
        else:
            return None

    def getIdPosition(self, idPost):
        #FIXME equal to getLinkPosition?
        posts = self.getPosts()
        if posts:
            pos = len(posts)
            if not idPost:
                #logging.debug(self.getPosts())
                return len(self.getPosts())
            for i, entry in enumerate(posts):
                idEntry = self.getPostId(entry)
                if idPost == idEntry:
                    # When there are duplicates (there shouldn't be) it
                    # returns the last one
                    pos = i
                    # print(url[:lenCmp],linkS[:lenCmp])
        else:
            pos = -1
        return pos

    def getLinkPosition(self, link):
        posts = self.getPosts()
        if posts:
            pos = len(posts)
            if not link:
                #logging.debug(self.getPosts())
                return len(self.getPosts())
            for i, entry in enumerate(posts):
                linkS = link
                if isinstance(link, bytes):
                    linkS = linkS.decode()
                url = self.getPostLink(entry)
                # msgLog = (f"{self.indent} Url: {url}"
                # logMsg(msgLog, 2, 0)
                # msgLog = (f"{self.indent} Link:{linkS}"
                # logMsg(msgLog, 2, 0)
                lenCmp = min(len(url), len(linkS))
                # if url[:lenCmp] == linkS[:lenCmp]:
                if url == linkS:
                    # When there are duplicates (there shouldn't be) it returns
                    # the last one
                    pos = i
                    # print(url[:lenCmp],linkS[:lenCmp])
        else:
            pos = -1
        return pos

    def datePost(self, pos):
        # print(self.getPosts())
        if "entries" in self.getPosts():
            return self.getPosts().entries[pos]["published_parsed"]
        else:
            return self.getPosts()[pos]["published_parsed"]

    def extractImage(self, soup):
        # This should go to the moduleHtml
        imageLink = ""
        pageImage = soup.findAll("img")
        #  Only the first one
        if len(pageImage) > 0:
            imageLink = pageImage[0]["src"]

        if imageLink.find("?") > 0:
            return imageLink[: imageLink.find("?")]
        else:
            return imageLink

    def extractPostLinks(self, post, linksToAvoid=""):
        links = []
        if post:
            content = self.getPostContentHtml(post)
            if content.startswith('http'):
                links = []
            else:
                soup = BeautifulSoup(content, 'lxml')
                links = self.extractLinks(soup, linksToAvoid)
        return  links

    def extractLinks(self, soup, linksToAvoid=""):
        # This should go to the moduleHtml
        j = 0
        linksTxt = ""

        for node in soup.find_all('blockquote'):
            nodeT = node.get_text()
            node.parent.insert(node.parent.index(node)+1, f'"{nodeT[1:-1]}"')
            # We need to delete before and after \n

        links = soup.find_all(["a", "iframe"])
        for link in links:
            theLink = ""
            if len(link.contents) > 0:
                if not isinstance(link.contents[0], Tag):
                    # We want to avoid embdeded tags (mainly <img ... )
                    if link.has_attr("href"):
                        theLink = link["href"]
                    else:
                        if "src" in link:
                            theLink = link["src"]
                        else:
                            continue
            else:
                if "src" in link:
                    theLink = link["src"]
                else:
                    continue

            if (linksToAvoid == "") or (not re.search(linksToAvoid, theLink)):
                if theLink:
                    link.append(" [" + str(j) + "]")
                    linksTxt = f"{linksTxt} [{str(j)}] {link.contents[0]}\n"
                    linksTxt = f"{linksTxt}     {theLink}\n"
                    j = j + 1

        if linksTxt != "":
            theSummaryLinks = linksTxt
        else:
            theSummaryLinks = ""

        # print("post")#.strip('\n'))#, theSummaryLinks)
        # print("post",soup.get_text())#.strip('\n'))#, theSummaryLinks)
        return (soup.get_text().strip("\n"), theSummaryLinks)

    def report(self, profile, post, link, data):
        msg = (f"{profile} failed! ",
               f"Post: {post} "
               f"Link: {link} ")
        if data:
               msg = (f"{msg} "
                      f"Data error: {data} ",
                      f"Unexpected error: {data[0]} ",
                      f"Unexpected error: {data[1]}")
        res = ""
        for line in msg:
            msgLog = (f"{self.indent} Service {self.service} "
                      f"{line}")
            logMsg(msgLog, 3, 1)
            res = f"{res}{line}\n"
            sys.stderr.write(line)
        return f"Fail! {res}"
        # print("----Unexpected error: %s"% data[2])

    def getPostComment(self, post):
        return ""

    def getPostTitle(self, post):
        return ""

    def getPostDate(self, post):
        return ""

    def getPostLink(self, post):
        return ""

    def getPostUrl(self, post):
        return ""

    def getPostId(self, post):
        return ""

    def getPostContent(self, post):
        res = ''
        summary = self.getPostContentHtml(post)
        if not summary.startswith('http'):
            soup = BeautifulSoup(summary, 'lxml')
            res = soup.get_text()
        return  res

    def extractImages(self, post):
        return None

    def getImages(self, i):
        posts = self.getPosts()
        res = None
        if i < len(posts):
            post = posts[i]
            # logging.debug("Post: %s" % post)
            res = self.extractImages(post)
        return res

    def getTags(self, images):
        # Is this the correct place?
        tags = []
        if images:
            for iimg in images:
                for tag in iimg[3]:
                    if tag not in tags:
                        tags.append(tag)

        return tags

    def getPostImage(self, post):
        return ""

    def getPostImagesTags(self, post):
        res = self.extractImages(post)
        tags = self.getTags(res)
        return tags

    def getPostImagesTags(self, post):
        # Dirty trick. This whould not be here. Needs work
        x = Content()
        res = x.getPostImages(post)
        tags = []
        if res:
            for iimg in res:
                for tag in iimg[3]:
                    if tag not in tags:
                        tags.append(tag)

        return tags



def main():

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )


if __name__ == "__main__":
    main()
