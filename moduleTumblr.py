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

from tumblpy import Tumblpy
# pip install python-tumblpy

from configMod import *
from moduleContent import *

# Configuration
# 
# [Buffer1]
# consumer_key:
# consumer_secret:
# oauth_token:
# oauth_secret:

class moduleTumblr(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.tc = None
        self.service = 'Tumblr'

    def setClient(self, tumblr):
        logging.info("    Connecting {}".format(self.service))
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTumblr')

            self.user = tumblr

            consumer_key = config.get("Buffer1", "consumer_key")
            consumer_secret = config.get("Buffer1", "consumer_secret")
            oauth_token = config.get("Buffer1", "oauth_token")
            oauth_secret = config.get("Buffer1", "oauth_secret")

            try:
                client = Tumblpy(consumer_key, consumer_secret, 
                                       oauth_token, oauth_secret)
            except:
                logging.warning("Tumblr authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                client = None
        except:
            logging.warning("Account not configured")
            client = None

        self.tc = client
 
    def getClient(self):
        return self.tc
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

    def publishPost(self, post, link, comment):
    
        try:
            logging.info("    Publishing in Tumblr: %s" % post)
            client = self.tc 
            blog_url = client.post('user/info')['user']['blogs'][0]['url'] 
            res = client.post('post', blog_url, params={'type':'link',
                'state':'queue', 
                'title': post, 
                'thumbnail': None, 
                'url': link, 
                #'excerpt': summaryHtml, 
                'publisher': ''}) 

            logging.info("Res: %s" % res)
            if 'id'  in res:
                res = res['id']

            return(res)
        except:        
            return(self.report('Tumblr', post, link, sys.exc_info()))

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleTumblr

    t = moduleTumblr.moduleTumblr()

    t.setClient('fernand0')

    t.setPosts()

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    section = 'Blog2'
    url = config.get(section, "url")
    rssFeed = config.get(section, "rss")
    logging.info(" Blog RSS: %s"% rssFeed)
    import moduleRss
    blog = moduleRss.moduleRss()
    # It does not preserve case
    blog.setRssFeed(rssFeed)
    blog.setUrl(url)
    blog.setPosts()
    post = blog.obtainPostData(1)

    title = post[0]
    link = post[1]
    content = post[7]
    links = post[8]
    t.publishPost(title,link,content)


if __name__ == '__main__':
    main()

