#!/usr/bin/env python

import configparser
import pickle
import os
import urllib
import logging
import gitterpy
import gitterpy.client

import sys
import time
import click
import logging
import requests

from bs4 import BeautifulSoup

from moduleContent import *
from moduleQueue import *


class moduleGitter(Content,Queue):

    def __init__(self):
        super().__init__()
        self.service = None
        self.client = None
        self.channel = None
        self.keys = []
        self.service = 'Gitter'

    def getKeys(self, config):
        token = config.get(self.service, "token")
        oauth_key = config.get(self.service, "oauth_key")
        oauth_secret = config.get(self.service, "oauth_secret")

        return (token, oauth_key, oauth_secret)

    def initApi(self, keys):
        self.token = keys[0]
        # https://api.slack.com/authentication/basics
        logging.info("     Connecting {}".format(self.service))
        try:
            client = gitterpy.client.GitterClient(self.token)
        except:
            logging.warning("Account not configured")
            if sys.exc_info()[0]:
                logging.warning("Unexpected error: {}".format(
                    sys.exc_info()[0]))
                logging.info(self.report(self.service, "", "", sys.exc_info()))
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)
            logging.info(self.report('Slack', text, sys.exc_info()))
            client = slack.WebClient(token=self.slack_token)
        return client

    def setChannel(self, channel="links"):
        # setPage in Facebook
        self.channel = channel

    def getChannel(self):
        return self.channel

    def setApiPosts(self):
        if not self.channel:
            # FIXME
            self.setChannel('fernand0errbot/links')
        posts = []
        try:
            if self.getClient():
                history = self.getClient().messages.list(self.getChannel())
                posts = history
        except:
            logging.warning(self.report(self.service, "", "", sys.exc_info()))

        return posts

    def getIdPosition(self, idPost):
        posts = self.getPosts()
        if posts:
            for i, entry in enumerate(posts):
                idS = idPost
                myIdPost = self.getPostId(entry)
                if idS == myIdPost:
                    pos = i
            return (pos)
        else:
            return -1

    def getPostContentHtml(self, post):
        return post.get('html', '')

    def setPostTitle(self, post, newTitle):
        if 'text' in post:
            pos = post['text'].rfind('http')
            title = newTitle 
            if pos>=0:
                title = title + ' ' + post['text'][pos:]
            post['text'] = title

    def getPostTitle(self, post):
        title = ''
        if 'text' in post:
            title = post['text']
            pos = title.rfind('http')
            if pos>=0:
                title = title[:pos]
            return title

    def getPostLink(self, post):
        link = ''
        if 'text' in post:
            text = post['text']
            pos = text.rfind('http')
            if pos>=0:
                link = text[pos:]
        return link

    # def getPostUrl(self, post):
    #     return (f"https://api.gitter.im/v1/rooms/{roomId}/chatMessages/"
    #             f"{self.getPostId(post)}")
    #     # https://developer.gitter.im/docs/messages-resource
    #     #idChannel

    def getPostId(self, post):
        logging.info(f"Id: {post}")
        idPost = -1
        if 'id' in post:
            idPost = post['id']
        return (idPost)

    def deleteGitter(self, idPost, idChannel):
        # This does not belong here
        # '/v1/rooms/:roomId/chatMessages/:chatMessageId"
        api_meth  = self.getClient().get_and_update_msg_url(idChannel, idPost)
        # call = f"https://api.gitter.im/v1/{api_meth}"
        #api_meth = 'rooms/{}/chatMessages/{}'.format(room_id, idPost)
        logging.info(f"api {api_meth}")
        #result = self.getClient().put(api_meth,data={'text':''})
        result = self.getClient().messages.get_message(idChannel, idPost)
        logging.info(f"Result1: {result}")
        result = self.getClient().get(api_meth)
        logging.info(f"Result1: {result}")
        result = self.getClient().delete(api_meth)
        logging.info(f"Result: {result}")
        logging.info("Result: {}".format(str(result)))
        return result

    def deleteApiPosts(self, idPost):
        theChan = self.getChannel()
        # idChannel = self.getChanId(theChan)
        logging.info(f"Chan: {theChan}")
        idChannel = theChan
        res = self.deletePost(idPost, idChannel)
        return res

    def deletePost(self, idPost, idChannel):
        #theChannel or the name of the channel?
        logging.info("Deleting id %s from %s" % (idPost, idChannel))

        logging.info(f"Chan: {idChannel}")
        # idChannel = self.getChanId(idChannel)
        # logging.info(f"Chan: {idChannel}")

        try:
            result = self.deleteGitter(idPost, idChannel)
        except:
            logging.info(self.report('Gitter',
                            "Error deleting", "", sys.exc_info()))
            result= ""
        logging.debug(result)
        return(result)

    def getChanId(self, name):
        logging.debug("getChanId %s"% self.service)

        chanList = self.getClient().rooms.rooms_list
        for channel in chanList:
            if channel['name'].endswith(name):
                return(channel['id'])
        return(None)

    def extractDataMessage(self, i):
        logging.info(f"extract gitt {i}")
        logging.info("Extract Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None)

        if i < len(self.getPosts()):
            post = self.getPosts()[i]
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLink(post)
            print("The title: {theTitle}")

            theLinks = ''
            content = ''
            theContent = ''
            firstLink = theLink
            theImage = ''
            theSummary = ''

            theSummaryLinks = ''
            comment = ''

        print (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)
        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    
    def processReply(self, reply):
        logging.info(reply)
        if 'id' in reply:
           logging.info(reply['id'])
           reply = reply['id']
        return reply

    def publishApiPost(self, *args, **kwargs):
        title, link, comment = args
        more = kwargs
        chan = self.getChannel()
        logging.info(f"Chan: {chan}")
        result = self.getClient().messages.send(chan, f"{title} {link}")
        return(result)

    def getBots(self, channel='tavern-of-the-bots'):
        if not self.posts:
            self.setPosts(channel)
        msgs = {}
        for msg in self.getPosts():
            if msg['text'].find('Hello')>=0:
                posN = msg['text'].find('Name:')+6
                posFN = msg['text'].find('"',posN)
                posI = msg['text'].find('IP:')+4
                posFI = msg['text'].find(' ',posI+1)-1
                posC = msg['text'].find('[')
                name = msg['text'][posN:posFN]
                ip = msg['text'][posI:posFI]
                command = msg['text'][posC+1:posC+2]
                if name not in msgs:
                    theTime = msg['sent'][:10]
                    msgs[name] = (ip, command, theTime)
        theBots = []
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a,b,c,name))
        return(theBots)

def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.INFO,
            format='%(asctime)s %(message)s')

    import moduleGitter

    testingDelete = True

    if testingDelete:
        CHANNEL = 'Fernando Tricas García'
        CHANNEL = 'fernand0errbot/links'
        url = "https://gitter.im/fernand0errbot/fernand0"

        site = moduleGitter.moduleGitter()

        site.setUrl(url)
        site.setClient(url)
        site.setChannel(CHANNEL)

        print(site.getClient().check_auth())
        site.setPosts()

        [ print(f"{i}) {site.getPostTitle(post)}") 
                for i, post in enumerate(site.getPosts()) ]
        reply = input("Delete? ")
        if reply == 'y':
            posts = site.getPosts()
            posts.reverse()
            for post in posts:
                print(f"Deleting: {site.getPostTitle(post)}")
                site.deletePost(site.getPostId(post), site.getChannel())
                return

        return


    site = moduleGitter.moduleGitter()

    CHANNEL = 'fernand0errbot/tavern-of-the-bots'

    url = "https://gitter.im/fernand0errbot/tavern-of-the-bots"

    site.setUrl(url)
    site.setClient(url)

    print(site.getClient().check_auth()) #[0])
    # theChannel = site.getChanId(CHANNEL)  
    # print("the Channel %s" % theChannel)

    CHANNEL = 'fernand0errbot/links'
    site.setChannel(CHANNEL)

    print("Testing posts")
    site.setPostsType("posts")
    site.setPosts()

    print("Testing title and link")

    for i, post in enumerate(site.getPosts()):
        print(f"Post: {post}")
        title = site.getPostTitle(post)
        link = site.getPostLink(post)
        url = site.getPostUrl(post)
        theId = site.getPostId(post)
        summary = site.getPostContentHtml(post)
        image = site.getPostImage(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")
        print(f"{i}) Content: {summary} {image}\n")
    return


    testingSlack = False

    if testingSlack:
        import moduleSlack

        siteS = moduleSlack.moduleSlack()
        try:
            # My own config settings
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssBlogs")

            section = "Blog7"
            url = config.get(section, "url")
            siteS.setSocialNetworks(config)
            print(f"social: {siteS.getSocialNetworks()}")
        except:
            url = "http://fernand0-errbot.slack.com/"
        siteS.setClient(url)
        siteS.setChannel("links")
        siteS.setPosts()
        for post in reversed(siteS.getPosts()):
            link = siteS.getPostLink(post)
            title = siteS.getPostTitle(post)
            print(f"Link: {link} {title}")
            print(f"Reply: {site.publishPost(title, link, '')}")
            time.sleep(5)
        sys.exit()

    testingDeleteGitter = False
    if testingDeleteGitter:
        site.setPosts()
        for post in site.getPosts():
            print(f"Post: {post} {site.getChannel()}")
            input("Delete? ")
            site.deletePost(site.getPostId(post), site.getChannel())
        sys.exit()

    testingPostDelete = False
    if testingPostDelete:
        rep = site.publishPost(CHANNEL, 'helloo')

        site.setPosts()
        print(len(site.getPosts()))
        post = site.getPosts()[-1]
        print(post)
        print("----------------")
        print("title {}".format(site.getPostTitle(post)))
        link = site.getPostLink(post)
        print("link {}".format(link))
        print(site.getLinkPosition(link))
        input("Delete? ")
        site.deletePost(site.getPostId(post), CHANNEL)
        sys.exit()

    site.setPosts()
    post = site.getPosts()[-1]
    print("----------------")
    print("title {}".format(site.getPostTitle(post)))
    link = site.getPostLink(post)
    print("link {}".format(link))
    print(site.getLinkPosition(link))

    sys.exit()

    print(CHANNEL)
    site.deletePost(site.getPostId(post), site.getChanId(CHANNEL))
    rep = site.publishPost(CHANNEL, 'helloo')
    print(rep)

    print(site.extractDataMessage(4))

    sys.exit()
    res=site.search('links', 'https://www.pine64.org/2020/01/24/setting-the-record-straight-pinephone-misconceptions/a')
    print("res",res)
    print("res",res['messages']['total'])
    print(site.getPosts())
    post = site.getPosts()[0]
    print(site.getPostTitle(post))
    print(site.getPostLink(post))
    rep = site.publishPost('tavern-of-the-bots', 'hello')
    wait = input('Delete %s?' % rep)
    theChan = site.getChanId('tavern-of-the-bots')
    rep = site.deletePost(rep['ts'], theChan)

    sys.exit()

    site.setPosts('links')
    site.setPosts('tavern-of-the-bots')
    print(site.getPosts())
    print(site.getBots())
    print(site.getClient().api_call('channels.list'))
    sys.exit()
    rep = site.publishPost('tavern-of-the-bots', 'hello')
    site.deletePost(rep['ts'], theChan)
    sys.exit()

    site.setSocialNetworks(config)

    if ('buffer' in config.options(section)):
        site.setBufferapp(config.get(section, "buffer"))

    if ('cache' in config.options(section)):
        site.setProgram(config.get(section, "cache"))

    theChannel = site.getChanId("links")

    i = 0
    listLinks = ""

    lastUrl = ''
    for i, post in enumerate(site.getPosts()):
        url = site.getLink(i)
        if urllib.parse.urlparse(url).netloc == lastUrl:
            listLinks = listLinks + "%d>> %s\n" % (i, url)
        else:
            listLinks = listLinks + "%d) %s\n" % (i, url)
        lastUrl = urllib.parse.urlparse(url).netloc
        print(site.getTitle(i))
        print(site.getLink(i))
        print(site.getPostTitle(post))
        print(site.getPostLink(post))
        i = i + 1

    numEntries = i
    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == 'x':
        sys.exit()

    elem = int(i)
    print(site.getPosts()[elem])

    action = input("Delete [d], publish [p], exit [x] ")

    if action == 'x':
        sys.exit()
    elif action == 'p':
        if site.getBufferapp():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getBufferapp():
                    lenMax = site.len(profile)
                    print("   getBuffer %s" % profile)
                    socialNetwork = (profile,site.getSocialNetworks()[profile])
                    title = site.getTitle(elem)
                    url = site.getLink(elem)
                    listPosts = []
                    listPosts.append((title, url))
                    site.buffer[socialNetwork].addPosts(listPosts)

        if site.getProgram():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getProgram():
                    lenMax = site.len(profile)
                    print("   getProgram %s" % profile)

                    socialNetwork = (profile,site.getSocialNetworks()[profile])

                    listP = site.cache[socialNetwork].getPosts()
                    #site.cache[socialNetwork].posts = site.cache[socialNetwork].posts[:8]
                    #listP = site.cache[socialNetwork].getPosts()
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #site.cache[socialNetwork].updatePostsCache()
                    listPsts = site.obtainPostData(elem)
                    listP = listP + [listPsts]
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #sys.exit()
                    site.cache[socialNetwork].posts = listP
                    site.cache[socialNetwork].updatePostsCache()
        t = moduleTumblr.moduleTumblr()
        t.setClient('fernand0')
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        t.publishPost(title, url, '')

    site.deletePost(site.getId(j), theChannel)
    #print(outputData['Slack']['pending'][elem][8])

if __name__ == '__main__':
    main()
