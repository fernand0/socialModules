#!/usr/bin/env python

import os
import sys

import configparser

from html.parser import HTMLParser

import mastodon
#pip install Mastodon.py

from configMod import *
from moduleContent import *
from moduleQueue import *


class moduleMastodon(Content,Queue):


    def __init__(self):
        super().__init__()
        self.service = None

    def setClient(self, user):
        logging.info("     Connecting Mastodon")
        self.service = 'Mastodon'
        try:
            maCli = mastodon.Mastodon( 
               access_token = CONFIGDIR + '/.rssMastodon', 
               api_base_url = 'https://mastodon.social'
            )

        except: 
            logging.warning("Mastodon authentication failed!") 
            logging.warning("Unexpected error:", sys.exc_info()[0])

        self.ma = maCli
        self.user = user


    def getClient(self):
        return self.ma

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        #posts = self.getClient().timeline_home()
        posts = self.getClient().account_statuses(self.getClient().me())
        for toot in  posts:
            self.posts.append(toot)

    def publishPost(self, post, link, comment):
        logging.debug("    Publishing in Mastodon...")
        if comment == None:
            comment = ''
        title = post
        content = comment
        post = comment + " " + post + " " + link
        h = HTMLParser()
        post = h.unescape(post)
        try:
            logging.info("     Publishing in Mastodon: %s" % post)
            res = self.getClient().toot(post)
            logging.debug("Res: %s" % res)
            if 'uri' in res:
                logging.info("     Toot: %s" % res['uri'])
                return(res['uri'])
            return res
        except:        
            return(self.report('Mastodon', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'card' in post and post['card']:
            if 'title' in post['card']:
                return(post['card']['title'])
        if 'content' in post:
            return(post['content'].replace('\n', ' '))

    def getPostLink(self, post):
        if 'uri' in post:
            return(post['uri'])
        else:
            return ''

def main():
    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('fernand0')
    print("Testing posts")
    mastodon.setPosts()
    print(mastodon.getClient().me())
    for post in mastodon.getPosts():
        print(post)

    print("Testing title and link")

    for post in mastodon.getPosts():
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))


    #mastodon.publishPost("I'll publish several links each day about technology, social internet, security, ... as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
