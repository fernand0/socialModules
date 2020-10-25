#!/usr/bin/env python

import configparser
import logging
import os
import pickle
import sys
import urllib

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
        self.service = 'Twitter'

    def setClient(self, twitterAC):
        logging.info("     Connecting {}".format(self.service))
        try:
            logging.info("     Twitter Acc %s"%str(twitterAC))
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTwitter')

            if isinstance(twitterAC, str): 
                self.user = twitterAC
            else:
                self.user = twitterAC[1][1]
            logging.info("     {} User {}".format(self.service, str(self.user)))
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
                logging.warning("{} authentication failed!".format(self.service))
                logging.warning("Unexpected error:", sys.exc_info()[0])
                return("Fail")
        except:
            logging.warning("Account not configured")
            if sys.exc_info()[0]: 
                logging.warning("Unexpected error: {}".format(
                    sys.exc_info()[0]))
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)

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

        #outputData = {}
        serviceName = 'Twitter'
        #outputData[serviceName] = {'sent': [], 'pending': []}
        #for post in self.getPosts():
        #    #print(post)
        #    url = 'https://twitter.com/' + post['user']['screen_name'] + '/status/' + str(post['id'])
        #    if 'urls' in post:
        #        link = post['urls'][0]['expanded_url']
        #    else:
        #        link = ''

        #    outputData[serviceName]['sent'].append((post['text'], url, 
        #            post['user']['screen_name'],     
        #            post['created_at'], link,'','','',''))

        #self.postsFormatted = outputData

    def publishPost(self, post, link='', comment=''):
        logging.info("     Publishing in {}...".format(self.service))
        if comment != None: 
            post = comment + " " + post
        h = HTMLParser()
        post = h.unescape(post)
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
            return(self.report(self.service, post, link, sys.exc_info()))
        except:        
            logging.info("Fail!")
            return(self.report(self.service, post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'text' in post:
            return(post['text'])
        else:
            return ''

    def getPostLink(self, post):
        if 'id_str' in post:
            return('https://twitter.com/{}/status/{}'.format(self.user, post['id_str']))
        else:
            return ''

    def getPostUrl(self, post):
        logging.debug(post)
        if (('urls' in post['entities']) and (post['entities']['urls'])):
            return(post['entities']['urls'][0]['expanded_url'])
        else:
            return ''

    def search(self, text):
        logging.debug("     Searching in {}...".format(self.service))
        try:
            res = self.tc.search.tweets(q=text)

            if res: 
                logging.debug("Res: %s" % res)
                return(res)
        except:        
            return(self.report(self.service, text, sys.exc_info()))

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleTwitter

    tw = moduleTwitter.moduleTwitter()

    tw.setClient('makingfernand0')

    tw.publishPost("Testing posting tweets", "", '')

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

    res = tw.search('url:fernand0')

    for tt in res['statuses']: 
        print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()

    tw.publishPost("Inscripciones 2019 | Congreso Web", "http://congresoweb.es/cw19/inscripciones/", '')

if __name__ == '__main__':
    main()

