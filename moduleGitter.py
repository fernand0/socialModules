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

from moduleContent import *
from moduleQueue import *


class moduleGitter(Content,Queue):

    def __init__(self):
        super().__init__()
        self.service = None
        self.sc = None
        self.keys = []
        self.service = 'Gitter'

    def setClient(self):
        # https://api.slack.com/authentication/basics
        logging.info("     Connecting {}".format(self.service))
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssGitter')

            if config.sections(): 
                self.token = config.get('Gitter', 'token') 

                self.sc = gitterpy.client.GitterClient(self.token)
            else:
                logging.warning("Account not configured") 
                if sys.exc_info()[0]: 
                    logging.warning("Unexpected error: {}".format( 
                        sys.exc_info()[0])) 
                print("Please, configure a {} Account".format(self.service))
                sys.exit(-1)
        except:
            logging.warning("Account not configured") 
            if sys.exc_info()[0]: 
                logging.warning("Unexpected error: {}".format( 
                    sys.exc_info()[0])) 
                logging.info(self.report(self.service, "", "", sys.exc_info()))
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)
            logging.info(self.report('Slack', text, sys.exc_info()))
            self.sc = slack.WebClient(token=self.slack_token)

    def setPosts(self, channel='links'):
        logging.info(" Setting posts")
        self.posts = []
        #theChannel = self.getChanId(channel)
        try:
            history = self.sc.messages.list(channel)
            try:
                self.posts = history
            except:
                self.posts = []
        except:
            logging.warning(self.report(self.service, "", "", sys.exc_info()))
            self.posts = []

    def getPostId(self, post): 
        return (post['id'])

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

    def getPostTitle(self, post):
        if 'text' in post:
            text = post['text']
            pos = text.rfind('http')
            if pos>=0:
                return(text[:pos])
            else:
                return(text)
        else:
            return("")

    def getPostLink(self, post):
        if 'text' in post:
            text = post['text']
            pos = text.rfind('http')
            if pos>=0:
                return(text[pos:])
            else:
                return('')
        else:
            return('')

    def getId(self, i):
        post = self.getPosts()[i]
        return(post['ts'])

    def deleteGitter(self, idPost, idChannel):
        # This does not belong here
        room_id = idChannel
        # '/v1/rooms/:roomId/chatMessages/:chatMessageId"
        api_meth = 'rooms/{}/chatMessages/{}'.format(room_id, idPost)
        result = self.sc.delete(api_meth)
        logging.info("Result: {}".format(str(result)))
        return result

    def deletePost(self, idPost, idChannel): 
        #theChannel or the name of the channel?
        logging.info("Deleting id %s from %s" % (idPost, idChannel))
        
        try:
            result = self.deleteGitter(idPost, idChannel) 
        except:
            logging.info(self.report('Slack', "Error deleting", "", sys.exc_info()))
        logging.debug(result)
        return(result)
    
    def getChanId(self, name):
        logging.debug("getChanId %s"% self.service)

        chanList = self.sc.rooms.rooms_list
        for channel in chanList:
            if channel['name'].endswith(name):
                return(channel['id'])
        return(None)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

        print(self.getPosts()[i])
        if i < len(self.getPosts()):
            theTitle = self.getTitle(0)
            theLink = self.getLink(0)

            theLinks = None
            content = None
            theContent = None
            firstLink = theLink
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]
        if 'attachments' in post:
            post = post['attachments'][0]

        theContent = ''
        url = ''
        firstLink = ''
        logging.debug("i %d", i)
        logging.debug("post %s", post)

        theTitle = self.getTitle(i)
        theLink = self.getLink(i)
        logging.info(theTitle)
        logging.info(theLink)
        if theLink.find('tumblr')>0:
            theTitle = post['text']
        firstLink = theLink
        if 'text' in post: 
            content = post['text']
        else:
            content = theLink
        theSummary = content
        theSummaryLinks = content
        if 'image_url' in post:
            theImage = post['image_url']
        elif 'thumb_url' in post:
            theImage = post['thumb_url']
        else:
            logging.info("Fail image")
            logging.debug("Fail image %s", post)
            theImage = ''

        if 'original_url' in post: 
            theLink = post['original_url']
        elif url: 
            theLink = url
        else:
            theLink = self.getPostLink(post)

        if ('comment' in post):
            comment = post['comment']
        else:
            comment = ""

        #print("content", content)
        theSummaryLinks = ""

        if not content.startswith('http'):
            soup = BeautifulSoup(content, 'lxml')
            link = soup.a
            if link: 
                firstLink = link.get('href')
                if firstLink:
                    if firstLink[0] != 'h': 
                        firstLink = theLink

        if not firstLink: 
            firstLink = theLink

        if 'image_url' in post:
            theImage = post['image_url']
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks
        
        theContent = ""
        theSummaryLinks = ""
        #if self.getLinksToAvoid():
        #    (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
        #else:
        #    (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            
        if 'image_url' in post:
            theImage = post['image_url']
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks


        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:     ", theTitle)
        logging.debug("Link:      ", theLink)
        logging.debug("First Link:", firstLink)
        logging.debug("Summary:   ", content[:200])
        logging.debug("Sum links: ", theSummaryLinks)
        logging.debug("the Links"  , theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def publishPost(self, chan, msg):
        logging.info("Publishing %s" % msg)
        try:
            result = self.sc.messages.send(chan, msg)
        except:
            logging.info(self.report('Gitter', "", "", sys.exc_info()))
            result = self.sc.chat_postMessage(channel=theChan, 
                    text=msg)
        logging.info(result)
        if 'id' in result:
           logging.info(result['id'])
        logging.info("End publishing %s" % msg)
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

    site = moduleGitter.moduleGitter()

    CHANNEL = 'fernand0errbot/tavern-of-the-bots' 

    url = "https://gitter.im/fernand0errbot/tavern-of-the-bots"

    site.setUrl(url)

    site.setClient()
    theChannel = site.getChanId(CHANNEL)  
    print("the Channel %s" % theChannel)

    CHANNEL = 'fernand0errbot/links' 
    site.setPosts(CHANNEL)
    print(len(site.getPosts()))
    post = site.getPosts()[3]
    print(post)
    print("----------------")
    print("title {}".format(site.getPostTitle(post)))
    link = site.getPostLink(post)
    print("link {}".format(link))
    print(site.getLinkPosition(link))

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
    print(site.sc.api_call('channels.list'))
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
