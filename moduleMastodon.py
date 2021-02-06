#!/usr/bin/env python

import configparser
import sys

from bs4 import BeautifulSoup
from bs4 import Tag
from html.parser import HTMLParser

import mastodon
#pip install Mastodon.py

from configMod import *
from moduleContent import *
from moduleQueue import *


class moduleMastodon(Content,Queue):


    def __init__(self):
        super().__init__()

    def getKeys(self, config):
        access_token = config[self.user]['access_token']
        return ((access_token, ))

    def initApi(self, keys):
        client = mastodon.Mastodon(access_token = keys[0], 
                api_base_url = 'https://mastodon.social')
        return client

    def setApiPosts(self):
        posts = self.getClient().account_statuses(self.getClient().me())
        return posts

    def setApiFavs(self):
        posts = self.getClient().favourites()
        return posts

    def processReply(self, reply): 
        res = ''
        if reply: 
            res = self.getAttribute(reply, 'uri')
        return res

    def publishApiPost(self, postData):
        post, link, comment, plus = postData
        post = self.addComment(post, comment)

        res=''
        res = self.getClient().toot(post+" "+link)

        return res

    def deleteApiPosts(self, idPost): 
        result = self.getClient().status_delete(idPost)
        logging.info(f"Res: {result}")
        return(result)

    def deleteApiFavs(self, idPost): 
        logging.info("Deleting: {}".format(str(idPost)))
        print("Deleting: {}".format(str(idPost)))
        result = self.client.status_unfavourite(idPost)
        logging.info(f"Res: {result}")
        return(result)

    def getPostId(self, post): 
        if isinstance(post, str):
            idPost = post
        else: 
            idPost = self.getAttribute(post, 'id')
        return idPost

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getPostTitle(self, post):
        result = ''
        if 'content' in post:
            result = self.getAttribute(post, 'content').replace('\n', ' ')
        elif 'card' in post and post['card']:
            result = self.getAttribute(post['card'], 'title')
        return result

    def getPostUrl(self, post):
        return self.getAttribute(post, 'url')

    def getPostLink(self, post): 
        if ('card' in post) and post['card']:
            link =  self.getAttribute(post['card'], 'url')
        else: 
            soup = BeautifulSoup(post['content'], 'lxml')
            link = soup.a
            if link: 
                link = link['href']
            else:
                link =  self.getAttribute(post, 'uri')
        return link

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, 
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None, 
                        None, None, None, None, None) 

        if i < len(self.getPosts()):
            post = self.getPost(i)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostUrl(post)
            firstLink = self.getPostLink(post)
            theId = self.getPostId(post)

            theLinks = [ firstLink , ]
            content = None 
            theContent = None
            if 'card' in post and post['card']: 
                theContent = self.getAttribute(post['card'], 'description')

            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = theId

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def search(self, text):
        pass

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('fernand0')
    #print("Testing posting and deleting")
    #res = mastodon.publishPost("Prueba ", "http://elmundoesimperfecto.com/", '')
    #print(res)
    #idPost = mastodon.getUrlId(res)
    #print(idPost)
    #input('Delete? ')
    #mastodon.deletePostId(idPost)
    #sys.exit()
    print("Testing posts")
    mastodon.setPostsType('posts')
    mastodon.setPosts()
    print(mastodon.getClient().me())
    for i, post in enumerate(mastodon.getPosts()):
        #print(post)
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        url = mastodon.getPostUrl(post)
        theId = mastodon.getPostId(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")

    print("Favorites")
    mastodon.setPostsType('favs')
    mastodon.setPosts()
    for post in mastodon.getPosts():
        print(post) 
        print(mastodon.getPostTitle(post)) 
        #input("Delete ?") 
        #mastodon.deletePost(post)

    #sys.exit()

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

    sys.exit()
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
