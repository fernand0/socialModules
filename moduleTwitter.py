#!/usr/bin/env python

import click
import configparser
import logging
import os
import pickle
import requests
import sys
import urllib

from bs4 import BeautifulSoup
from bs4 import Tag

import twitter
from twitter import *
# pip install twitter
#https://pypi.python.org/pypi/twitter
#https://github.com/sixohsix/twitter/tree
#http://mike.verdone.ca/twitter/
from html.parser import HTMLParser

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleTwitter(Content,Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.tc = None
        self.service = None

    def setClient(self, twitterAC):
        logging.info("     Connecting Twitter")
        self.service = 'Twitter'
        try:
            logging.info("     Twitter Acc {}".format(str(twitterAC)))
            logging.info("     Dir {}".format(str(CONFIGDIR + '/.rssTwitter')))
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTwitter')

            if isinstance(twitterAC, str): 
                self.user = twitterAC
            else:
                self.user = twitterAC[1][1]
            logging.info("     Twitter User %s"%str(self.user))
            try: 
                CONSUMER_KEY = config.get(self.user, "CONSUMER_KEY")
            except: 
                CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
            try: 
                CONSUMER_SECRET = config.get(self.user, "CONSUMER_SECRET")
            except: 
                CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
            TOKEN_KEY = config.get(self.user, "TOKEN_KEY")
            TOKEN_SECRET = config.get(self.user, "TOKEN_SECRET")

            try:
                authentication = OAuth(
                            TOKEN_KEY,
                            TOKEN_SECRET,
                            CONSUMER_KEY,
                            CONSUMER_SECRET)
                t = Twitter(auth=authentication)
            except:
                logging.warning("Twitter authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                return("Fail")
        except:
            logging.warning("Account not configured")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            t = None

        self.tc = t
 
    def getClient(self):
        return self.tc
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        #tweets = self.tc.statuses.home_timeline()
        try: 
            self.posts = self.tc.statuses.user_timeline()
        except:
            self.posts = []
        try:
            self.favs = self.tc.favorites.list()
        except:
            self.favs = []

        #outputData = {}
        serviceName = 'Twitter'

    def getFavs(self):
         return self.favs

    def getPosts(self):
        if hasattr(self, 'getPostsType'): 
            logging.debug("  Posts type {}".format(self.getPostsType()))
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            if self.getPostsType() == 'favs':
                posts = self.getFavs()
            else:
                posts = self.getPublished() 
        else:
            posts = self.posts
        return(posts)


    def publishPost(self, post, link='', comment=''):
        logging.info("     Publishing in {}...".format(self.service))
        if comment != None: 
            post = comment + " " + post
        try:
            h = HTMLParser()
            post = h.unescape(post)
        except:
            import html
            post = html.unescape(post)

        res = None
        try:
            logging.info("     Publishing: %s" % post)
            post = post[:(240 - (len(link) + 1))]
            res = self.tc.statuses.update(status=post+" " + link)

            if res: 
                logging.debug("Res: %s" % res)
                urlTw = "https://twitter.com/%s/status/%s" % (self.user, res['id'])
                logging.info("     Link: %s" % urlTw)
                return(post +'\n'+urlTw)

        except twitter.api.TwitterHTTPError as twittererror:        
            for error in twittererror.response_data.get("errors", []): 
                logging.info("      Error code: %s" % error.get("code", None))
            return(self.report('Twitter', post, link, sys.exc_info()))
        except:        
            logging.info("Fail!")
            return(self.report('Twitter', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'text' in post:
            return(post['text'])
        else:
            return ''

    def getPostLink(self, post):
        if 'id_str' in post:
            return('https://twitter.com/{}/status/{}'.format(
                self.user, post['id_str']))
        else:
            return ''

    def getPostUrl(self, post):
        logging.debug(post)
        if (('urls' in post['entities']) and (post['entities']['urls'])):
            return(post['entities']['urls'][0]['expanded_url'])
        else:
            return ''

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, 
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None, 
                        None, None, None, None, None) 

        if i < len(self.getPosts()):
            post = self.getPost(i)
            import pprint
            pprint.pprint(post)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLink(post)

            theLinks = None
            content = None 
            theContent = None
            if 'text' in post and post['text']: 
                theContent = post['text']
            firstLink = theLink
            pos = theContent.find('http')
            if pos >= 0:
                firstLink=theContent[pos:].split(' ')[0]
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


    def search(self, text):
        logging.debug("     Searching in Twitter...")
        try:
            res = self.tc.search.tweets(q=text)

            if res: 
                logging.debug("Res: %s" % res)
                return(res)
        except:        
            return(self.report('Twitter', text, sys.exc_info()))

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleTwitter
    tw = moduleTwitter.moduleTwitter()


    tw.setClient('fernand0')

    #print("Testing followers")
    #tw.setFriends()
    #sys.exit()

    print("Testing posts")
    tw.setPosts()
    for i, tweet in enumerate(tw.getPosts()):
        print("{}) {}".format(i,tweet))
        #print("@%s: %s" %(tweet[2], tweet[0]))


    print("Testing title and link")
    
    for post in tw.getPosts():
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nLink: {}\nUrl:{}\n".format(title,link,url))

    print("Favs")

    tw.setPostsType("favs")
    #tw.publishPost("Tuit desde podman", "", '')

    for i, post in enumerate(tw.favs):
        print("i",i)
        print("1",post)
        print("2",tw.getPost(i))
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))
        print(tw.extractDataMessage(i))

    sys.exit()

    res = tw.search('url:fernand0')

    for tt in res['statuses']: 
        #print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()

    tw.publishPost("Inscripciones 2019 | Congreso Web", "http://congresoweb.es/cw19/inscripciones/", '')

if __name__ == '__main__':
    main()

