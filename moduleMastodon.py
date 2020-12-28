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

        self.client = maCli
        self.user = user

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        self.favs = []
        #posts = self.getClient().timeline_home()
        posts = self.getClient().account_statuses(self.getClient().me())
        for toot in  posts:
            self.posts.append(toot)

        favs = self.getClient().favourites()
        for toot in  favs:
            self.favs.append(toot)

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

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, 
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None, 
                        None, None, None, None, None) 

        if i < len(self.getPosts()):
            post = self.getPost(i)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLink(post)

            theLinks = None
            content = None 
            theContent = None
            if 'card' in post and post['card']: 
                if 'description' in post['card']: 
                    theContent = post['card']['description']
            firstLink = theLink
            if 'card' in post and post['card']: 
                if 'url' in post['card']: 
                    firstLink = post['card']['url']
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():
    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('fernand0')
    print("Testing posts")
    mastodon.setPosts()
    print(mastodon.getClient().me())
    for post in mastodon.getPosts():
        print(post)
    print("Favorites")
    for post in mastodon.favs:
        print(post)

    print("Testing title and link")

    print("Posts")

    for post in mastodon.getPosts():
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))

    print("Favs")

    mastodon.setPostsType("favs")
    for i, post in enumerate(mastodon.favs):
        print("i",i)
        print("1",post)
        print("2",mastodon.getPost(i))
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))
        print(mastodon.extractDataMessage(i))

    (theTitle, theLink, firstLink, theImage, theSummary, 
            content, theSummaryLinks, theContent, theLinks, comment) = mastodon.extractDataMessage(0)

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    import modulePocket
    
    p = modulePocket.modulePocket()

    p.setClient('fernand0')
    p.publishPost(theTitle, firstLink, '')



    #mastodon.publishPost("I'll publish several links each day about technology, social internet, security, ... as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
