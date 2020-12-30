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
        self.service = 'Mastodon'

    def getKeys(self, config):
        access_token = config[self.user]['access_token']
        return ((access_token, ))

    def initApi(self, keys):
        maCli = mastodon.Mastodon(
                access_token = keys[0], 
                api_base_url = 'https://mastodon.social'
        )

        return maCli

    #def setClient(self, user):
    #    logging.info("     Connecting Mastodon")
    #    self.service = 'Mastodon'
    #    try:
    #        maCli = mastodon.Mastodon( 
    #           access_token = CONFIGDIR + '/.rssMastodon', 
    #           api_base_url = 'https://mastodon.social'
    #        )

    #    except: 
    #        logging.warning("Mastodon authentication failed!") 
    #        logging.warning("Unexpected error:", sys.exc_info()[0])

    #    self.client = maCli
    #    self.user = user

    def setApiPosts(self):
        statuses = self.getClient().account_statuses(self.getClient().me())
        posts = []
        for toot in  statuses:
            posts.append(toot)
        return posts

    def setApiFavs(self):
        statuses = self.getClient().favourites()
        posts = []
        for toot in  statuses:
            posts.append(toot)
        return posts

    #def setPosts(self):
    #    logging.info("  Setting posts")
    #    self.posts = []
    #    self.favs = []
    #    #posts = self.getClient().timeline_home()
    #    posts = self.getClient().account_statuses(self.getClient().me())
    #    for toot in  posts:
    #        self.posts.append(toot)

    #    favs = self.getClient().favourites()
    #    for toot in  favs:
    #        self.favs.append(toot)

    #def getFavs(self):
    #     return self.favs
    
    def processReply(self, reply): 
        res = reply
        logging.debug("Res: %s" % res) 
        if 'uri' in res: 
            logging.info("     Toot: %s" % res['uri']) 
            res = res['uri']
        return res

    def publishApiPost(self, postData):
        post = postData[0]
        link = postData[1] 
        comment = postData[2]
        post = post + " " + link
        if comment: 
            post = comment + " " + post

        h = HTMLParser()
        post = h.unescape(post)
        try:
            res = self.getClient().toot(post)
        except:        
            res = self.report('Mastodon', post, link, sys.exc_info())
        return res

    #def publishPost(self, post, link, comment):
    #    logging.debug("    Publishing in Mastodon...")
    #    if comment == None:
    #        comment = ''
    #    title = post
    #    content = comment
    #    post = comment + " " + post + " " + link
    #    h = HTMLParser()
    #    post = h.unescape(post)
    #    try:
    #        logging.info("     Publishing in Mastodon: %s" % post)
    #        res = self.getClient().toot(post)
    #        logging.debug("Res: %s" % res)
    #        if 'uri' in res:
    #            logging.info("     Toot: %s" % res['uri'])
    #            return(res['uri'])
    #        return res
    #    except:        
    #        return(self.report('Mastodon', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'card' in post and post['card']:
            if 'title' in post['card']:
                return(post['card']['title'])
        if 'content' in post:
            return(post['content'].replace('\n', ' '))

    def getPostLink(self, post): 
        self.getAttribute(post, 'uri')

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

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('fernand0')
    print("Testing posts")
    mastodon.setPostsType('posts')
    mastodon.setPosts()
    print(mastodon.getClient().me())
    for post in mastodon.getPosts():
        print(post)


    print("Favorites")
    mastodon.setPostsType('posts')
    mastodon.setPosts()
    for post in mastodon.getPosts():
        print(post)

    print("Testing title and link")

    print("Posts")

    mastodon.setPostsType('posts')
    mastodon.setPosts()
    for post in mastodon.getPosts():
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))

    print("Favs")

    mastodon.setPostsType("favs")
    mastodon.setPosts()
    for i, post in enumerate(mastodon.getPosts()):
        print("i",i)
        print("1",post)
        print("2",mastodon.getPost(i))
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))
        print(mastodon.extractDataMessage(i))

    (theTitle, theLink, firstLink, theImage, theSummary, 
            content, theSummaryLinks, theContent, theLinks, comment) = mastodon.extractDataMessage(0)

    #config = configparser.ConfigParser()
    #config.read(CONFIGDIR + '/.rssBlogs')

    #import modulePocket
    #
    #p = modulePocket.modulePocket()

    #p.setClient('fernand0')
    #p.publishPost(theTitle, firstLink, '')



    mastodon.publishPost("I'll publish several links each day about technology, social internet, security, ... as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
