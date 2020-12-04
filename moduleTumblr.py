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
from moduleQueue import *

# Configuration
# 
# [Buffer1]
# consumer_key:
# consumer_secret:
# oauth_token:
# oauth_secret:

class moduleTumblr(Content,Queue):

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

            import pytumblr
            try:
                client = pytumblr.TumblrRestClient(consumer_key, 
                        consumer_secret, oauth_token, oauth_secret)
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
 
    def getBlogName(self):
        name = self.getUrl().split('/')[2]
        return name

    def setPosts(self):
        logging.info("  Setting posts")
        logging.info(f"  Setting posts {self.getUrl()}")
        posts = self.getClient().posts(self.getBlogName())
        if 'posts' in posts:
            self.posts = posts['posts']
        else:
            self.posts = []
        drafts = self.getClient().drafts(self.getUrl().split('/')[2])
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

    def getPostLink(self, post):
        logging.debug(f"getPostUrl {post}")       
        url = ""
        if post:
            if 'post_url' in post:
                url = post['post_url']
        return url

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in Tumblr: %s" % post)
        try:
            client = self.tc 
            res = client.create_link(self.getBlogName(), state='queue',
                    title=post, url=link, description="")

            #res = client.post('post', blog_url, params={'type':'link',
            #    'state':'queue', 
            #    'title': post, 
            #    'thumbnail': None, 
            #    'url': link, 
            #    #'excerpt': summaryHtml, 
            #    'publisher': ''}) 

            logging.info("Res: %s" % res)
            if 'id'  in res:
                res = res['id']

            return(res)
        except:        
            return(self.report('Tumblr', post, link, sys.exc_info()))

    def edit(self, j, newTitle=''): 
        logging.info("New title %s", newTitle)
        post = self.getPosts()[j]
        url=self.getUrl()
        name = url.split('/')[2]
        idPost = post['id']
        res = self.getClient().edit_post(name, id=idPost, 
                type=post['type'], title = newTitle)
        logging.info("Res: {}".format(res))
        update = "Changed "+oldTitle+" with "+newTitle
        return(update)


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
    print(t.getPostTitle(t.getPosts()[18]))
    print(t.getPostLink(t.getPosts()[18]))

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

