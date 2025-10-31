#!/usr/bin/env python

import configparser
import os
import pickle
import sys
import time
import urllib

import click
import gitterpy
import gitterpy.client
import requests
from bs4 import BeautifulSoup

from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class moduleGitter(Content):  # ,Queue):
    def getKeys(self, config):
        token = config.get(self.service, "token")
        oauth_key = config.get(self.service, "oauth_key")
        oauth_secret = config.get(self.service, "oauth_secret")

        return (token, oauth_key, oauth_secret)

    def initApi(self, keys):
        self.service = None
        self.client = None
        self.channel = None
        self.keys = []
        self.service = "Gitter"

        self.token = keys[0]
        # logging.info("     Connecting {}".format(self.service))
        try:
            client = gitterpy.client.GitterClient(self.token)
        except:
            msgLog = "Account not configured"
            logMsg(msgLog, 3, 0)
            if sys.exc_info()[0]:
                # logging.warning("Unexpected error: {}".format(
                #     sys.exc_info()[0]))
                self.report(self.service, "", "", sys.exc_info())
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)
            # logging.info(self.report('Slack', text, sys.exc_info()))
            client = slack.WebClient(token=self.slack_token)
        return client

    def getChannels(self):
        return self.getClient().rooms.rooms_list

    def setChannel(self, channel=""):
        if not channel:
            # The first one
            channel = self.getChannels()[0].get("name", "")
        # setPage in Facebook
        # We should follow more the model there
        self.channel = channel

    def getChannel(self):
        return self.channel

    def setApiPosts(self):
        if not self.channel:
            # It will set the owner channel by default
            msgLog = f"No channel defined, setting the first one (if any)"
            logMsg(msgLog, 3, 0)
            self.setChannel()
        posts = []
        try:
            if self.getClient():
                history = self.getClient().messages.list(self.getChannel())
                posts = history
        except:
            self.report(self.service, "", "", sys.exc_info())

        return posts

    # Duplicate code? Available in moduleContent
    # def getIdPosition(self, idPost):
    #     posts = self.getPosts()
    #     if posts:
    #         for i, entry in enumerate(posts):
    #             idS = idPost
    #             myIdPost = self.getPostId(entry)
    #             if idS == myIdPost:
    #                 pos = i
    #         return (pos)
    #     else:
    #         return -1

    def getPostContentHtml(self, post):
        return post.get("html", "")

    def editApiLink(self, post, newLink):
        # FIXME. To be done
        pass

    def setPostTitle(self, post, newTitle):
        # Only in local memory
        pos = post.get("text", "").rfind("http")
        title = newTitle
        if pos >= 0:
            title = f"{title} {post.get('text','')[pos:]}"
            post["text"] = title

    def getApiPostTitle(self, post):
        title = post.get("text", "")
        pos = title.rfind("http")
        if pos >= 0:
            title = title[:pos]
        return title

    def getApiPostLink(self, post):
        link = ''
        text = post.get('text','')
        pos = text.rfind('http')
        if pos>=0:
            link = text[pos:]
        return link

    def getPostId(self, post):
        idPost = post.get("id", "")
        return idPost

    def deleteApiPosts(self, idPost):
        result = self.deteleGitter(idPost, self.getChannel())
        # logging.info(f"Res: {result}")
        return result

    def deleteGitter(self, idPost, idChannel):
        # This does not belong here
        # '/v1/rooms/:roomId/chatMessages/:chatMessageId"
        # call = f"https://api.gitter.im/v1/{api_meth}"
        # api_meth = 'rooms/{}/chatMessages/{}'.format(room_id, idPost)
        api_meth = self.getClient().get_and_update_msg_url(idChannel, idPost)
        result = self.getClient().delete(api_meth)
        # logging.info("Result: {}".format(str(result)))
        return result

    def deleteApiPosts(self, idPost):
        theChan = self.getChannel()
        # idChannel = self.getChanId(theChan)
        # logging.info(f"Chan: {theChan}")
        idChannel = theChan
        res = self.deleteGitter(idPost, idChannel)
        return res

    # def deletePost(self, idPost, idChannel):
    #     #theChannel or the name of the channel?
    #     logging.info("Deleting id %s from %s" % (idPost, idChannel))
    #     logging.info(f"Chan: {idChannel}")
    #     # idChannel = self.getChanId(idChannel)
    #     # logging.info(f"Chan: {idChannel}")
    #     try:
    #         result = self.deleteGitter(idPost, idChannel)
    #     except:
    #         logging.info(self.report('Gitter',
    #                         "Error deleting", "", sys.exc_info()))
    #         result= ""
    #     logging.debug(result)
    #     return(result)

    def getChanId(self, name):
        msgLog = "{self.indent} getChanId {self.service}"
        logMsg(msgLog, 2, 0)

        chanList = self.getClient().rooms.rooms_list
        for channel in chanList:
            if channel.get("name", "").endswith(name):
                return channel["id"]
        return None

    # def extractDataMessage(self, i):
    #     logging.info(f"extract gitt {i}")
    #     logging.info("Extract Service %s"% self.service)
    #     (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         post = self.getPosts()[i]
    #         theTitle = self.getPostTitle(post)
    #         theLink = self.getPostLink(post)
    #         print("The title: {theTitle}")

    #         theLinks = ''
    #         content = ''
    #         theContent = ''
    #         firstLink = theLink
    #         theImage = ''
    #         theSummary = ''

    #         theSummaryLinks = ''
    #         comment = ''

    #     print (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)
    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def processReply(self, reply):
        # logging.info(reply)
        reply = reply.get("id", "")
        return reply

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, link, comment = args
        if kwargs:
            more = kwargs

            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        chan = self.getChannel()
        result = self.getClient().messages.send(chan, f"{title} {link}")
        return result

    def getBots(self, channel="tavern-of-the-bots"):
        # FIXME: this does not belong here
        if not self.posts:
            self.setPosts(channel)
        msgs = {}
        for msg in self.getPosts():
            if msg["text"].find("Hello") >= 0:
                posN = msg["text"].find("Name:") + 6
                posFN = msg["text"].find('"', posN)
                posI = msg["text"].find("IP:") + 4
                posFI = msg["text"].find(" ", posI + 1) - 1
                posC = msg["text"].find("[")
                name = msg["text"][posN:posFN]
                ip = msg["text"][posI:posFI]
                command = msg["text"][posC + 1 : posC + 2]
                if name not in msgs:
                    theTime = msg["sent"][:10]
                    msgs[name] = (ip, command, theTime)
        theBots = []
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a, b, c, name))
        return theBots


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    gitter_module = moduleGitter()
    tester = ModuleTester(gitter_module)
    tester.run()



if __name__ == "__main__":
    main()
