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

import facebook

from html.parser import HTMLParser

from configMod import *
from moduleContent import *
from moduleQueue import *

# We are using facebook-sdk 
# You can find the way to obtain tokens and so on at:
# https://facebook-sdk.readthedocs.io/
# 
# Config file
# [Facebook]
# oauth_access_token: #<- We only need this one
# client_token:
# app_token:
# app_id:

class moduleFacebook(Content,Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.client = None
        self.service = 'Facebook'

    def getKeys(self, config): 
        oauth_access_token = config.get("Facebook", "oauth_access_token")
        return ((oauth_access_token,))

    def initApi(self, keys):
        try:
            graph = facebook.GraphAPI(keys[0], version='3.0') 
            self.client = graph
            self.setPage(self.user)
        except: 
            logging.warning("Facebook authentication failed!") 
            logging.warning("Unexpected error:", sys.exc_info()[0]) 
            print("Fail!")

        return self.client

    #def setClient(self, facebookAC='me'):
    #    logging.info("     Connecting {}: {}".format(self.service,
    #        str(facebookAC)))
    #    try:
    #        config = configparser.ConfigParser()
    #        config.read(CONFIGDIR + '/.rssFacebook')

    #        if isinstance(facebookAC, str): 
    #            self.user = facebookAC
    #        elif isinstance(facebookAC[1], str):
    #            self.user = facebookAC[1]
    #        else: 
    #            # Deprecated
    #            self.user = facebookAC[1][1]

    #        try:
    #            oauth_access_token = config.get("Facebook", "oauth_access_token")
    #            graph = facebook.GraphAPI(oauth_access_token, version='3.0') 
    #            self.client = graph
    #            self.setPage(self.user)

    #        except: 
    #            logging.warning("Facebook authentication failed!") 
    #            logging.warning("Unexpected error:", sys.exc_info()[0]) 
    #            print("Fail!")
    #    except:
    #        logging.warning("Facebook authentication failed!")
    #        logging.warning("Unexpected error:", sys.exc_info()[0])
    #        print("Fail!")

    def setPage(self, facebookAC='me'):
        perms = ['publish_actions','manage_pages','publish_pages'] 
        pages = self.getClient().get_connections("me", "accounts") 
        self.pages = pages

        if (facebookAC != 'me'): 
            for i in range(len(pages['data'])): 
                logging.debug("Selecting %s %s"% (pages['data'][i]['name'], facebookAC)) 
                if (pages['data'][i]['name'] == facebookAC): 
                    logging.info("     Selected... %s"% pages['data'][i]['name']) 
                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token']) 
                    self.page = graph2
                    self.pageId = pages['data'][i]['id']
                    break
                else: 
                    # Publishing as me 
                    self.page = facebookAC 

    def setApiPosts(self, numPosts=20):
        posts = []
        count = 5
        postsF = self.page.get_connections(self.pageId, 
                connection_name='posts') 

        if 'data' in postsF: 
            for post in postsF['data']: 
                postt = self.page.get_connections(post['id'], 
                        connection_name='attachments') 
                if 'message' in post:
                    posts.append(post)

        return posts
        #outputData = {}
        #serviceName = 'Facebook'
        #outputData[serviceName] = {'sent': [], 'pending': []}
        #for post in self.getPosts():
        #    (page, idPost) = post['id'].split('_')
        #    url = 'https://facebook.com/' + page + '/posts/' + idPost
        #    outputData[serviceName]['sent'].append((post['message'], url, 
        #            '', post['created_time'], '','','','',''))

        #self.postsFormatted = outputData

    #def setPosts(self):
    #    logging.info("  Setting posts")
    #    self.posts = []
    #    count = 5
    #    posts = self.page.get_connections(self.pageId, connection_name='posts') 

    #    for post in posts['data']:
    #        print("-->",post)
    #        postt = self.page.get_connections(post['id'], connection_name='attachments') 
    #        #if postt['data']: 
    #        #    print(postt['data'][0])
    #        #    if 'url' in postt['data'][0]:
    #        #        print(urllib.parse.unquote(postt['data'][0]['url']).split('=')[1])#.split('&')[0])
    #        if 'message' in post:
    #            self.posts.append(post)

    #    outputData = {}
    #    serviceName = 'Facebook'
    #    outputData[serviceName] = {'sent': [], 'pending': []}
    #    for post in self.getPosts():
    #        (page, idPost) = post['id'].split('_')
    #        url = 'https://facebook.com/' + page + '/posts/' + idPost
    #        outputData[serviceName]['sent'].append((post['message'], url, 
    #                '', post['created_time'], '','','','',''))

    #    self.postsFormatted = outputData

    def processReply(self, reply): 
        res = reply
        if reply: 
            logging.debug("Res: %s" % reply) 
            if 'id' in reply: 
                res = 'https://www.facebook.com/{}'.format(reply['id'])
                logging.info("     Link: {}".format(res)) 
        return(res)
 
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

        res = "Fail!"
        logging.info("     Publishing: %s" % post[:250])
        if (not isinstance(self.page, str)):
            res = self.page.put_object('me', "feed", message=post, link=link)
        return res

    #def publishPost(self, post, link='', comment=''):
    #    logging.debug("    Publishing in Facebook...")
    #    if comment == None:
    #        comment = ''
    #    post = comment + " " + post
    #    h = HTMLParser()
    #    post = h.unescape(post)
    #    res = None
    #    try:
    #        logging.info("     Publishing: %s" % post[:250])
    #        if (not isinstance(self.page, str)):
    #            res = self.page.put_object('me', "feed", message=post, link=link)
    #            #res = self.page.put_object(self.client.get_object('me')['id'], "feed", message=post, link=link)
    #            if res:
    #                logging.debug("Res: %s" % res)
    #                if 'id' in res:
    #                    urlFb = 'https://www.facebook.com/%s' % res['id']
    #                    logging.info("     Link: %s" % urlFb)
    #                    return(urlFb)

    #                return(res)
    #        else:
    #            return("Fail")
    #    except:        
    #        return(self.report('Facebook', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        return self.getAttribute(post, 'message')

    def getPostLink(self, post):
        return self.getAttribute(post, 'id')

    def getPostImages(self,idPost):
        res = []
        post = self.client.get_object('me',fields='id')
        myId = post['id']
        field='attachments'
        post = self.client.get_object('{}_{}'.format(myId,idPost),fields=field)
        res.append(post['attachments']['data'][0]['media']['image']['src'])
        subAttach = post['attachments']['data'][0]['subattachments']
        for img in subAttach['data']:
            res.append(img['media']['image']['src'])

        return(res)

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleFacebook

    fc = moduleFacebook.moduleFacebook()

    fc.setClient('me')
    fc.setPage('Enlaces de fernand0')
    fc.setPostsType('posts')
    fc.setPosts()
    for post in fc.getPosts():
        print(fc.getPostTitle(post))
        print(fc.getPostLink(post))
        print(post)
        #print("@%s: %s" %(tweet[2], tweet[0]))
    sys.exit()
    fc.publishPost("Prueba")
    print(fc.user)
    sys.exit()
    images = fc.getPostImages('10157835018558264')
    print(images)
    print(len(images))
    images = fc.getPostImages('10157761305288264')
    print(images)
    print(len(images))
    sys.exit()
    print(fc.get_object(id='me'))

    print("Listing pages")
    for page in fc.pages['data']:
        print(page['name'], page)

    fc.setPosts()
    for post in fc.getPosts():
        print(post)
        #print("@%s: %s" %(tweet[2], tweet[0]))
    sys.exit()

    print("Testing title and link")
    
    for post in fc.getPosts():
        print(post)
        title = fc.getPostTitle(post)
        link = fc.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))

 
    sys.exit()


    fc.setPosts()
    posts = fc.getPosts()
    for post in posts:
        print(post)
        #print("%s: %s" %(post[0], post[1]))


if __name__ == '__main__':
    main()

