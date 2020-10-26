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

            if config.sections():
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
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)

            client = None

        self.tc = client
 
    def getClient(self):
        return self.tc
 
    def setPosts(self):
        logging.info("  Setting posts")
        posts = self.tc.posts('https://fernand0.tumblr.com/')
        if 'posts' in posts:
            self.posts = posts['posts']

    def publishPost(self, post, link, comment):
    
        try:
            logging.info("    Publishing in Tumblr: %s" % post)
            client = self.tc 
            blog_url = client.post('user/info')['user']['blogs'][0]['url'] 
            if comment: 
                if link:
                    comment = '<a href="{}">{}</a><br /> <br />{}'.format(
                            link, post, comment)
                params={'type':'text',
                'state':'queue', 
                'title': post, 
                'body' : comment} 
            else:
                params={'type':'link', 
                        'state':'queue', 'title': post, 
                        'url': link, 
                        'publisher': ''}
            res = client.post('post', blog_url, params=params) 

            logging.info("Res: %s" % res)
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

    print(t.getPosts())

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    title = "Test" 
    link = "https://elmundoesimperfecto.com/"
    content = "" #"Testing publishing in Tumblr"
    t.publishPost(title,link,content)


if __name__ == '__main__':
    main()

