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
        self.client = None
        self.service = 'Twitter'

    def getKeys(self, config): 
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
        return(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_KEY, TOKEN_SECRET)

    def initApi(self, keys):
        try:
            authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
            t = Twitter(auth=authentication)
        except:
            logging.warning("Twitter authentication failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            return("Fail")
        return t

    #    self.client = t
 
    #def setClient(self, twitterAC):
    #    logging.info("     Connecting {}: {}".format(self.service, twitterAC))
    #    try:
    #        config = configparser.ConfigParser()
    #        config.read(CONFIGDIR + '/.rssTwitter')

    #        if isinstance(twitterAC, str): 
    #            self.user = twitterAC
    #        elif isinstance(twitterAC[1],str):
    #            self.user = twitterAC[1]
    #        else:
    #            self.user = twitterAC[1][1]

    #        try: 
    #            CONSUMER_KEY = config.get(self.user, "CONSUMER_KEY")
    #        except: 
    #            CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
    #        try: 
    #            CONSUMER_SECRET = config.get(self.user, "CONSUMER_SECRET")
    #        except: 
    #            CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
    #        TOKEN_KEY = config.get(self.user, "TOKEN_KEY")
    #        TOKEN_SECRET = config.get(self.user, "TOKEN_SECRET")

    #        try:
    #            authentication = OAuth(
    #                        TOKEN_KEY,
    #                        TOKEN_SECRET,
    #                        CONSUMER_KEY,
    #                        CONSUMER_SECRET)
    #            t = Twitter(auth=authentication)
    #        except:
    #            logging.warning("Twitter authentication failed!")
    #            logging.warning("Unexpected error:", sys.exc_info()[0])
    #            return("Fail")
    #    except:
    #        logging.warning("Account not configured")
    #        logging.warning("Unexpected error:", sys.exc_info()[0])
    #        t = None

    #    self.client = t

    def setApiPosts(self):
        posts = self.getClient().statuses.user_timeline()
        return posts

    def setApiFavs(self): 
        posts = self.getClient().favorites.list(count=100)
        return posts

    #def setPosts(self):
    #    logging.info("  Setting posts")
    #    self.posts = []
    #    #tweets = self.client.statuses.home_timeline()
    #    try: 
    #        self.posts = self.client.statuses.user_timeline()
    #    except:
    #        self.posts = []
    #    if True:
    #        self.favs = self.client.favorites.list(count=100)
    #        #print(self.favs)
    #        for post in self.favs: 
    #            title = self.getPostTitle(post) 
    #            link = self.getPostLink(post) 
    #            url = self.getPostUrl(post) 
    #            #print("Created: {}\nTitle: {}\nLink: {}\nUrl:{}\n".format(
    #            #    post['created_at'], title,link,url))
    #    else:
    #        self.favs = []

    #    #outputData = {}
    #    serviceName = 'Twitter'

    def processReply(self, reply): 
        if reply: 
            res = reply
            logging.debug("Res: %s" % res)
            urlTw = "https://twitter.com/%s/status/%s" % (self.user, 
                    self.getPostId(res))
            logging.info("     Link: %s" % urlTw)
            return(urlTw)

    def publishApiPost(self, postData): 
        post = postData[0]
        link = postData[1]
        comment = postData[2]

        if comment: 
            post = comment + " " + post
        try:
            h = HTMLParser()
            post = h.unescape(post)
        except:
            import html
            post = html.unescape(post)

        res = None
        try:
            post = post[:(240 - (len(link) + 1))]
            logging.info("     Publishing: %s" % post)
            res = self.client.statuses.update(status=post+" " + link)

            return res

        except twitter.api.TwitterHTTPError as twittererror:        
            for error in twittererror.response_data.get("errors", []): 
                logging.info("      Error code: %s" % error.get("code", None))
            return(self.report('Twitter', post, link, sys.exc_info()))


    #def publishPost(self, post, link='', comment=''):
    #    logging.info("     Publishing in {}...".format(self.service))
    #    if comment != None: 
    #        post = comment + " " + post
    #    try:
    #        h = HTMLParser()
    #        post = h.unescape(post)
    #    except:
    #        import html
    #        post = html.unescape(post)

    #    res = None
    #    try:
    #        logging.info("     Publishing: %s" % post)
    #        post = post[:(240 - (len(link) + 1))]
    #        res = self.client.statuses.update(status=post+" " + link)

    #        if res: 
    #            logging.debug("Res: %s" % res)
    #            urlTw = "https://twitter.com/%s/status/%s" % (self.user, res['id'])
    #            logging.info("     Link: %s" % urlTw)
    #            return(post +'\n'+urlTw)

    #    except twitter.api.TwitterHTTPError as twittererror:        
    #        for error in twittererror.response_data.get("errors", []): 
    #            logging.info("      Error code: %s" % error.get("code", None))
    #        return(self.report('Twitter', post, link, sys.exc_info()))
    #    except:        
    #        logging.info("Fail!")
    #        return(self.report('Twitter', post, link, sys.exc_info()))

    def deleteApiPost(self, idPost): 
        result = self.client.favorites.destroy(_id=idPost)
        logging.info(f"Res: {result}")
        return(result)

    def deleteApi(self, j): 
        idPost = self.getId(self.getPost(j))
        print(idPost)
        sys.exit()
        result = self.client.favorites.destroy(_id=idPost)
        logging.info(f"Res: {result}")
        return(result)

    def getPostId(self, post):
        return self.getAttribute(post, 'id')

    def getPostTitle(self, post):
        return self.getAttribute(post, 'text')

    def getPostLink(self, post):
        return 'https://twitter.com/{}/status/{}'.format(
               self.user, self.getAttribute(post, 'id_str'))

    def getPostUrl(self, post):
        logging.debug(post)
        #import pprint
        #pprint.pprint(post)
        if ('urls' in post['entities']): 
            if post['entities']['urls']:
                if 'expanded_url' in post['entities']['urls'][0]:
                    return(post['entities']['urls'][0]['expanded_url'])
        elif ('url' in post['user']['entities']['url'] 
                and (post['user']['entities']['url']['urls'])): 
                return(post['user']['entities']['url']['urls'][0]['expanded_url'])
        elif ('media' in post['entities']): 
                if (post['entities']['media']): 
                    return (post['entities']['media'][0]['expanded_url'])
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
            #import pprint
            #pprint.pprint(post)
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
            res = self.client.search.tweets(q=text)

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

    tw.publishPost("Prueba", "http://elmundoesimperfecto.com/", '')
    print("Testing posts")
    tw.setPostsType('posts')
    tw.setPosts()

    print("Testing title and link")
    
    for post in tw.getPosts():
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nLink: {}\nUrl:{}\n".format(title,link,url))

    print("Favs")

    tw.setPostsType("favs")
    tw.setPosts()


    i=0
    post = tw.getPost(i)
    title = tw.getPostTitle(post)
    link = tw.getPostLink(post)
    url = tw.getPostUrl(post)
    print(post)
    print("Title: {}\nTuit: {}\nLink: {}\n".format(title,link,url))
    tw.deletePost(post)
    sys.exit()

    for i, post in enumerate(tw.getPosts()):
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title,link,url))
        input("Delete?")
        print("Deleted https://twitter.com/i/status/{}".format(tw.delete(i)))
        import time
        time.sleep(5)




    sys.exit()

    res = tw.search('url:fernand0')

    for tt in res['statuses']: 
        #print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()


if __name__ == '__main__':
    main()

