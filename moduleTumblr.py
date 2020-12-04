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
        logging.info(f"Url: {tumblr}")
        if isinstance(tumblr,str):
            self.url = f"https://{tumblr}.tumblr.com/"
        elif isinstance(tumblr,tuple): 
            self.url = f"https://{tumblr[1][1]}.tumblr.com/"
        logging.info(f"Url: {self.url}")
 
    def getClient(self):
        return self.tc
 
    def setPosts(self):
        logging.info("  Setting posts")
        logging.info(f"  Setting posts {self.getUrl()}")
        posts = self.getClient().get('posts', blog_url=self.getUrl())
        if 'posts' in posts:
            self.posts = posts['posts']
        else:
            self.posts = []
        drafts = self.getClient().get('posts/queue', blog_url=self.getUrl())
        if 'posts' in drafts: 
            self.drafts = drafts['posts']
        else:
            self.drafts = []

    def getPostTitle(self, post):
        logging.debug(f"getPostTitle {post}")       
        title = ""
        if post:
            if 'summary' in post:
                title = post['summary']
        return title

    def getPostUrl(self, post):
        logging.debug(f"getPostUrl {post}")       
        url = ""
        if post:
            if 'post_url' in post:
                url = post['post_url']
        return url


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
    t.setPostsType('posts')

    t.setPosts()
    print(t.getPosts())
    print(t.getPostTitle(t.getPosts()[0]))
    print(t.getPostUrl(t.getPosts()[0]))
    sys.exit()

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

