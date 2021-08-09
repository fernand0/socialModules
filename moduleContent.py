# This module provides infrastructure for reading content from different places
# It stores in a convenient and consistent way the content in order to be used
# in other programs

import configparser
import html
import logging
import pickle
import re
import sys

from bs4 import Tag
from html.parser import HTMLParser

from configMod import *


class Content:

    def __init__(self):
        self.url = ""
        self.name = ""
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
        self.lastLinkPublished = {}
        self.numPosts = 0
        self.user = None
        self.client = None
        ser = self.__class__.__name__
        self.service = self.__class__.__name__[6:]
        logging.debug(f"Setting service {self.service}")
        # They start with module
        self.hold = None

    def setClient(self, account):
        logging.info(f"    Connecting {self.service}: {account}")

        if isinstance(account, str):
            self.user = account
        elif isinstance(account[1], str) and (account[1].find('@') > 0):
            # Grrrr
            self.user = account[1]
        elif isinstance(account[0], str):
            self.user = account[0]
        else:
            # Deprecated
            self.user = account[1][1]

        logging.debug(f"Service: {self.service}")
        try:
            config = configparser.RawConfigParser()
            config.read(f"{CONFIGDIR}/.rss{self.service}")
            keys = self.getKeys(config)

            try:
                client = self.initApi(keys)
            except:
                logging.warning(f"{self.service} authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                client = None
        except:
            logging.warning("Account not configured")
            client = None

        self.client = client

    def getService(self):
        if hasattr(self, "service"):
            return self.service
        else:
            return ""

    def setUser(self, nick):
        self.user = nick

    def getUser(self):
        if hasattr(self, "user"):
            return self.user
        else:
            return ""

    def getNick(self):
        if hasattr(self, "nick"):
            return self.nick
        else:
            return ""

    def getAttribute(self, post, selector):
        result = ""
        try:
            result = post[selector]
        except:
            result = ""

        return result

    def setPosts(self):
        nick = self.getNick()
        logging.debug(f"nick: {nick}")
        if nick:
            identifier = nick
        else:
            identifier = self.getUrl()

        typePosts = self.getPostsType()
        logging.info(f"  Setting posts in {self.service} {identifier}"
                     f"  (type: {self.getPostsType()})")
        logging.debug(f"setApi {typePosts}")
        if hasattr(self, "getPostsType") and self.getPostsType():
            typePosts = self.getPostsType()
            logging.debug(f"setApi {typePosts}")
            if typePosts == "cache":
                cmd = getattr(self, "setApiCache")
            else:
                logging.debug(f"setApi{typePosts}")
                cmd = getattr(
                    self, f"setApi{self.getPostsType().capitalize()}"
                )
        else:
            cmd = getattr(self, "setApiPosts") 

        logging.debug(f"Cmd: {cmd}")
        posts = cmd()
        #logging.info(f"Posts: {posts}")
        self.assignPosts(posts)

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

    def getLastTime(self):
        # print(f"In lastTime")
        # import inspect
        # print(f"Object members: {inspect.getmembers(self)[3]}")
        # print(f"Object: {self}")
        # print(f"Social: {self.url} {self.service} {self.user}")

        lastTime = 0.0
        myLastLink = ""
        # You always need to check lastLink? 
        # Example: gmail, Twitter
        try:
            url = self.getUrl()
            service = self.service.lower()
            nick = self.user
            fN = (f"{fileNamePath(url, (service, nick))}.last")
            print(f"File: {fN}")
            myLastLink, lastTime = getLastLink(fN)
        except:
            fN = ""
            msgLog = (f"No last link")
            logMsg(msgLog, 2, 0)

        self.lastLinkPublished = myLastLink
        self.lastTimePublished = lastTime

        return myLastLink, lastTime

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

    def getPostAction(self):
        if hasattr(self, "postaction"):
            return self.postaction
        else:
            return ""

    def getSocialNetworks(self):
        socialNetworks = None
        if hasattr(self, "socialNetworks"):
            socialNetworks = self.socialNetworks
        return socialNetworks

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
        logging.debug("  sNC {}".format(socialNetworksConfig))
        for sN in socialNetworksConfig:
            if sN in socialNetworksOpt:
                self.addSocialNetwork((sN, socialNetworksConfig[sN]))
        logging.debug("  sNN {}".format(self.getSocialNetworks()))

    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def assignPosts(self, posts):
        self.posts = posts

    def getPosts(self):
        posts = self.posts
        return posts

    def getPost(self, i):
        post = None
        posts = self.getPosts()
        if i < len(posts):
            post = self.getPosts()[i]
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
        logging.info(f"Posts {self.getPosts()} j: {j}")
        if j < len(self.getPosts()):
            post = self.getPost(j)
            logging.info(f"Post: {post}")
            idPost = self.getPostId(post)
        return idPost

    def splitPost(self, post):
        splitListPosts = []
        for imgL in post[3]:
            myPost = list(post)
            logging.info("mP", myPost)
            myPost[3] = imgL
            splitListPosts.append(tuple(myPost))

        return splitListPosts

    def getNumPostsData(self, num, i, lastLink=None):
        listPosts = []
        for j in range(num, 0, -1):
            logging.debug("j, i %d - %d" % (j, i))
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
        postsType = None
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

    def publishImage(self, post, image, **more):
        logging.info(f"    Publishing image in {self.service}: {post}")
        try:
            reply = self.publishApiImage((post, image, more))
            return self.processReply(reply)
        except:
            return self.report(self.service, post, image, sys.exc_info())
       
    def publishPost(self, post, link="", comment="", **more):
        logging.info(f"    Publishing in {self.service}: {post}")
        try:
            reply = self.publishApiPost((post, link, comment, more))
            return self.processReply(reply)
        except:
            return self.report(self.service, post, link, sys.exc_info())

    def deletePostId(self, idPost):
        logging.debug(f"Deleting: {idPost}")
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
        logging.debug(f"Deleting post: {post}")
        idPost = self.getPostId(post)
        logging.debug(f"Deleting post: {idPost}")
        result = self.deletePostId(idPost)
        return result

    def delete(self, j):
        logging.debug(f"Deleting Pos: {j}")
        post = self.getPost(j)
        logging.debug(f"Deleting Pos Id: {post}")
        idPost = self.getPostId(self.getPost(j))
        logging.debug(f"Deleting Pos Id: {idPost}")
        result = self.deletePostId(idPost)
        return result

    def processReply(self, reply):
        logging.debug("Res: %s" % reply)
        return reply

    def do_edit(self, j, **kwargs):
        update = ""
        if j < len(self.getPosts()):
            post = self.getPost(j)
            if ("newTitle" in kwargs) and kwargs["newTitle"]:
                oldTitle = self.getPostTitle(post)
                newTitle = kwargs["newTitle"]
                logging.info(f"New title {newTitle}")
                res = self.editApiTitle(post, newTitle)
                res = self.processReply(res)
                update = f"Changed {oldTitle} with {newTitle} Id {str(res)}"
            if ("newState" in kwargs) and kwargs["newState"]:
                oldState = self.getPostState(post)
                newState = kwargs["newState"]
                logging.info("New state %s", newState)
                res = self.editApiState(post, newState)
                res = self.processReply(res)
                update = f"Changed {oldState} to {newState} Id {str(res)}"
            if ("newLink" in kwargs) and kwargs["newLink"]:
                oldLink = self.getPostLink(post)
                newLink = kwargs["newLink"]
                logging.info(f"New link {newLink}")
                res = self.editApiLink(post, newLink)
                res = self.processReply(res)
                update = f"Changed {oldLink} with {newLink} Id {str(res)}"
            return update

    def edit(self, j, newTitle):
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
        logging.debug("Writing in %s" % fileNameQ)

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
        return self.lastLinkPublished

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
        maxVal = None
        if hasattr(self, "max"): # and self.max:
            maxVal = int(self.max)
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

    def getLinkPosition(self, link):
        posts = self.getPosts()
        pos = len(posts)
        if posts:
            if not link:
                logging.debug(self.getPosts())
                return len(self.getPosts())
            for i, entry in enumerate(posts):
                linkS = link
                if isinstance(link, bytes):
                    linkS = linkS.decode()
                url = self.getPostLink(entry)
                # logging.debug("\n{}\n{}".format(url, linkS))
                # print("{} {}".format(url, linkS))
                lenCmp = min(len(url), len(linkS))
                if url[:lenCmp] == linkS[:lenCmp]:
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
        pageImage = soup.findAll("img")
        #  Only the first one
        if len(pageImage) > 0:
            imageLink = pageImage[0]["src"]
        else:
            imageLink = ""

        if imageLink.find("?") > 0:
            return imageLink[: imageLink.find("?")]
        else:
            return imageLink

    def extractLinks(self, soup, linksToAvoid=""):
        # This should go to the moduleHtml
        j = 0
        linksTxt = ""
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
        logging.warning("%s failed!" % profile)
        logging.warning("Post %s %s" % (post[:80], link))
        logging.warning("Unexpected error: %s" % data[0])
        logging.warning("Unexpected error: %s" % data[1])
        print("%s posting failed!" % profile)
        print("Post %s %s" % (post[:80], link))
        print("Unexpected error: %s" % data[0])
        print("Unexpected error: %s" % data[1])
        return "Fail! %s" % data[1]
        # print("----Unexpected error: %s"% data[2])

    def getPostTitle(self, post):
        return None

    def getPostDate(self, post):
        return None

    def getPostLink(self, post):
        return ""

    def getImages(self, i):
        posts = self.getPosts()
        res = None
        if i < len(posts):
            post = posts[i]
            logging.debug("Post: %s" % post)
            res = self.extractImages(post)
        return res

    def getImagesTags(self, i):
        res = self.getImages(i)
        tags = []
        for iimg in res:
            for tag in iimg[3]:
                if tag not in tags:
                    tags.append(tag)

        return tags

    def getImagesCode(self, i):
        res = self.getImages(i)
        # print(self.getPosts()[i])
        url = self.getPostLink(self.getPosts()[i])
        text = ""
        for iimg in res:
            if iimg[2]:
                description = iimg[2]
            else:
                description = ""
            if description:
                import string

                print(f"iimg {iimg}")
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
                if title[-1] in string.punctuation:
                    text = (
                        '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                        '<img class="alignnone size-full '
                        'wp-image-3306" src="{}" alt="{} {}" '
                        'width="776" height="1035" /></a></p>'.format(
                            text, description, url, iimg[0], title, description
                        )
                    )
                else:
                    text = (
                        '{}\n<p><h4>{}</h4></p><p><a href="{}">'
                        '<img class="alignnone size-full '
                        'wp-image-3306" src="{}" alt="{}. {}"'
                        'width="776" height="1035" /></a></p>'.format(
                            text, description, url, iimg[0], title, description
                        )
                    )
            else:
                title = iimg[1]
                text = (
                    '{}\n<p><a href="{}"><img class="alignnone '
                    'size-full wp-image-3306" src="{}" alt="{} {}"'
                    'width="776" height="1035" /></a></p>'.format(
                        text, url, iimg[0], title, description
                    )
                )
        return text


def main():

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )


if __name__ == "__main__":
    main()
