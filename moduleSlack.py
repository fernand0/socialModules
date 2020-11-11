#!/usr/bin/env python

import configparser
import pickle
import os
import urllib
import logging
#try: 
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
# https://slack.dev/python-slack-sdk/v3-migration/

import sys
import time
import click
import logging
import requests
from bs4 import BeautifulSoup
from bs4 import Tag

import moduleTumblr
from moduleContent import *
from moduleQueue import *


class moduleSlack(Content,Queue):

    def __init__(self):
        super().__init__()
        self.service = None
        self.sc = None
        self.keys = []
        self.service = 'Slack'

    def setClient(self):
        # https://api.slack.com/authentication/basics
        logging.info("     Setting Client")
        logging.info("     Connecting {}".format(self.service))
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssSlack')

            if config.sections(): 
                self.slack_token = config.get('Slack', 'oauth-token') 
                self.user_slack_token = config.get('Slack', 'user-oauth-token') 

                self.sc = WebClient(self.slack_token)
            else:
                logging.warning("Account not configured") 
                if sys.exc_info()[0]: 
                    logging.warning("Unexpected error: {}".format( 
                        sys.exc_info()[0])) 
                print("Please, configure a {} Account".format(self.service))
                sys.exit(-1)
        except:
            logging.warning("Something failed. not configured") 
            if sys.exc_info()[0]: 
                logging.warning("Unexpected error: {}".format( 
                    sys.exc_info()[0])) 
                logging.info(self.report(self.service, "", "", sys.exc_info()))
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)
            logging.info(self.report('Slack', text, sys.exc_info()))
            self.sc = slack.WebClient(token=self.slack_token)

        logging.info("     Connected {}".format(self.service))



    def setSlackClient(self, slackCredentials):
        self.service = 'slack'
        config = configparser.ConfigParser()
        if not slackCredentials: 
            slackCredentials = CONFIGDIR + '/.rssSlack'
        config.read(slackCredentials)
    
        self.slack_token = config["Slack"].get('oauth-token')
        self.user_slack_token = config["Slack"].get('user-oauth-token')
        
        try: 
            self.sc = WebClient(self.slack_token)
        except:
            logging.info(self.report('Slack', "","", sys.exc_info()))
            self.sc = slack.WebClient(token=self.slack_token)

        config = configparser.ConfigParser()
        config.read(CONFIGDIR + '/.rssBlogs')
        section = "Blog7"

        url = config.get(section, "url")
        self.setUrl(url)
        self.setSocialNetworks(config, section)
        #if ('buffer' in config.options(section)): 
        #    self.setBufferapp(config.get(section, "buffer"))

        if ('cache' in config.options(section)): 
            self.setProgram(config.get(section, "cache"))


    def getSlackClient(self):
        return self.sc
 
    def setPosts(self, channel='links'):
        logging.info(" Setting posts")
        self.posts = []
        theChannel = self.getChanId(channel)
        try:
            self.sc.token = self.slack_token        
            data = {'count':1000, 'channel':theChannel}
            history = self.sc.api_call( "conversations.history", data= data) #, count=1000, channel=theChannel)
            try:
                self.posts = history['messages']
            except:
                self.posts = []
        except:
            logging.warning(self.report(self.service, "", "", sys.exc_info()))
            self.posts = []

        logging.info(" Set posts")

    def getTitle(self, i):
        post = self.getPosts()[i]
        return(self.getPostTitle(post))

    def getLink(self, i):
        post = self.getPosts()[i]
        return(self.getPostLink(post))

    def getPostTitle(self, post):
        if ('attachments' in post) and ('title' in post['attachments'][0]):
            return(post['attachments'][0]['title'])
        elif 'text' in post:
            text = post['text']
            if text.startswith('<'): 
                title = text.split('|')[1]
                titleParts = title.split('>')
                title = titleParts[0]
                if ((len(titleParts)>1) and (titleParts[1].find('<') >= 0)):
                    # There is a link
                    title = title + titleParts[1].split('<')[0]
            else:
                pos = text.find('<')
                title=text[:pos]
            return(title)
        else:
            return("No title")

    def getPostLink(self, post):
        if 'attachments' in post:
            return(post['attachments'][0]['original_url'])
        else:
            text = post['text']
            if ((text.startswith('<') and text.count('<')==1)): 
                # The link is the only text
                url = post['text'][1:-1]
            else:
                # Some people include URLs in the title of the page
                pos = text.rfind('<')
                url=text[pos+1:-1]
            return(url) 

    #def isForMe(self, args):
    #    return ((self.service[0].capitalize() in args.split()[0])
    #           or (args[0] == '*'))

    def publish(self, j):
        logging.info("Publishing %d"% j)
        post = self.obtainPostData(j)
        logging.info("Publishing %s"% post[0])
        update = ''
        title = self.getTitle(j)
        url = self.getLink(j)
        logging.info("Title: %s" % str(title))
        logging.info("Url: %s" % str(url))
        if self.getBuffer():            
            for profile in self.getSocialNetworks():
                if profile[0] in self.getBufferapp():
                    lenMax = self.len(profile)
                    logging.info("   getBuffer %s" % profile)
                    socialNetwork = (profile,self.getSocialNetworks()[profile])
                    listPosts = []
                    listPosts.append((title, url))
                    update = update + self.buffer[socialNetwork].addPosts(listPosts)
                    update = update + '\n'

        if self.getProgram():
            for profile in self.getSocialNetworks():
                if profile[0] in self.getProgram():
                    lenMax = self.len(profile)
                    socialNetwork = (profile,self.getSocialNetworks()[profile])

                    listP = self.cache[socialNetwork].setPosts()
                    listP = self.cache[socialNetwork].getPosts()
                    listPsts = self.obtainPostData(j)
                    listP = listP + [listPsts]
                    self.cache[socialNetwork].posts = listP
                    update = update + self.cache[socialNetwork].updatePostsCache()
                    update = update + '\n'
        t = moduleTumblr.moduleTumblr()
        t.setClient('fernand0')
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        update = update + t.publishPost(title, url, '')['display_text']
        # Res: {'id': 187879917068, 'state': 'queued', 'display_text': 'Added to queue.'}


        theChannel = self.getChanId("links")  
        res = self.deletePost(self.getId(j), theChannel)
        logging.info("Res: %s" % str(res))
        update = update + str(res['ok'])
 
        logging.info("Publishing title: %s" % title)
        logging.info("Update before return %s"% update)
        return(update)
 

    def getId(self, i):
        post = self.getPosts()[i]
        return(post['ts'])

    def getKeys(self):
        return(self.keys)
    
    def setKeys(self, keys):
        self.keys = keys

    def delete(self, j, theChannel=None): 
        logging.info("Deleting id %s" % j)
        if not theChannel: 
            theChannel = self.getChanId("links")  
        idPost = self.getId(j)
        #self.sc.token = self.user_slack_token        
        logging.info("Deleting id %s" % idPost)
        result = self.sc.api_call("chat.delete", channel=theChannel, ts=idPost)
        #self.sc.token = self.slack_token        
        logging.info(result)
        return(result['ok'])

    def deletePost(self, idPost, chan): 
        #theChannel or the name of the channel?
        theChan = self.getChanId(chan)
        logging.info("Deleting id %s from %s" % (idPost, theChan))
        
        try:
            self.sc.token = self.user_slack_token        
            data = {'channel': theChan, 'ts': idPost}
            result = self.sc.api_call("chat.delete", data=data) #, channel=theChannel, ts=idPost)
        except:
            logging.info(self.report('Slack', "Error deleting", "", sys.exc_info()))
    
        logging.debug(result)
        return(result)
    
    def getChanId(self, name):
        logging.debug("getChanId %s"% self.service)

        self.sc.token = self.user_slack_token        
        #chanList = self.sc.api_call("channels.list")['channels']
        #print(chanList)
        # Upgrading to the new conversations API
        chanList = self.sc.api_call("conversations.list")['channels']
        #print(chanList)
        self.sc.token = self.slack_token        
        for channel in chanList:
            if channel['name_normalized'] == name:
                return(channel['id'])
        return(None)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

        if i < len(self.getPosts()):
            theTitle = self.getTitle[0]
            theLink = self.getLink[1]

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
        theChan = self.getChanId(chan)
        logging.info("Publishing %s" % msg)
        try:
            self.sc.token = self.user_slack_token        
            data = {'channel': theChan, 'text': msg}
            result = self.sc.api_call("chat.postMessage", data= data) #, 
                #channel = theChan, text = msg)
            self.sc.token = self.slack_token        
        except:
            logging.info(self.report('Slack', "", "", sys.exc_info()))
            result = self.sc.chat_postMessage(channel=theChan, 
                    text=msg)
        logging.info(result['ok'])
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
                    theTime = "%d-%d-%d"%time.localtime(float(msg['ts']))[:3]
                    msgs[name] = (ip, command, theTime)
        theBots = [] 
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a,b,c,name))
        return(theBots)

    def search(self, channel, text):
        logging.debug("     Searching in Slack...")
        try: 
            theChannel = self.getChanId(channel)
            self.sc.token = self.slack_token        
            data = {'query':text}
            res = self.sc.api_call("search.messages", data=data) #, query=text)

            if res: 
                logging.info(self.report(self.service, "", "", sys.exc_info()))
                return(res)
        except:        
            return(self.report('Slack', text, sys.exc_info()))


def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')


    import moduleSlack

    site = moduleSlack.moduleSlack()

    CHANNEL = 'tavern-of-the-bots' 

    url = "http://fernand0-errbot.slack.com/" 
    site.setUrl(url)


    site.setClient()
    site.setPosts()
    print("Posts: {}".format(site.getPosts()))
    theChannel = site.getChanId(CHANNEL)  
    print("the Channel {} has code {}".format(CHANNEL, theChannel))
    site.setPosts(CHANNEL)
    # post = site.getPosts()[0] # Delete de last post
    post = site.publishPost(CHANNEL, "test")
    print(post)
    input("Delete ?")
    print(site.deletePost(post['ts'], CHANNEL))
    res=site.search('links', 'https://www.pine64.org/2020/01/24/setting-the-record-straight-pinephone-misconceptions/a')
    print("res",res)
    print("res",res['messages']['total'])
    sys.exit()
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

    site.setSocialNetworks(config, section)

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
