#!/usr/bin/env python

import logging
import sys

from bs4 import BeautifulSoup

import mastodon
# pip install Mastodon.py

from configMod import *
from moduleContent import *
from moduleQueue import *


class moduleMastodon(Content, Queue):

    def __init__(self):
        super().__init__()

    def getKeys(self, config):
        #if self.user.startswith('@'):
        #    self.user = self.user[1:]

        access_token = config[self.user]['access_token']
        return ((access_token, ))

    def initApi(self, keys):
        pos = self.user.find('@',1) # The first character can be @
        if pos > 0:
            self.base_url = f"https://{self.user[pos:]}"
            self.user = self.user[:pos]
        else:
            self.base_url = 'https://mastodon.social'
            
        logging.debug(f"Mastodon user:  {self.user} base: {self.base_url}")
        client = mastodon.Mastodon(access_token=keys[0],
                                   api_base_url=self.base_url)
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

    def publishApiImage(self, postData):
        post, image, plus = postData

        res = 'Fail!'
        if True:
            res = self.getClient().media_post(image, "image/png")
            res = self.getClient().status_post(post, media_ids = res['id'])
        else:
            res = self.getClient().status_post(post+" "+link,
                    visibility='private')
        print(f"res: {res}")
        return res
 
    def publishApiPost(self, postData):
        post, link, comment, plus = postData
        post = self.addComment(post, comment)

        res = 'Fail!'
        if True:
            res = self.getClient().toot(post+" "+link)
        else:
            res = self.getClient().status_post(post+" "+link,
                    visibility='private')
            # 'direct' 'private' 'unlisted' 'public'


        return self.processReply(res)

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
            link = self.getAttribute(post['card'], 'url')
        else:
            soup = BeautifulSoup(post['content'], 'lxml')
            link = soup.a
            if link:
                link = link['href']
            else:
                link = self.getAttribute(post, 'uri')
        return link

    def extractDataMessage(self, i):
        logging.info(f"Service {self.service}")
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

            theLinks = [firstLink, ]
            content = None
            theContent = None
            if 'card' in post and post['card']:
                theContent = self.getAttribute(post['card'], 'description')

            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = theId

        return (theTitle, theLink, firstLink, theImage, theSummary,
                content, theSummaryLinks, theContent, theLinks, comment)

    def search(self, text):
        pass


def main():

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('@fernand0Test@fosstodon.org')
    print("Testing posting and deleting")
    res = mastodon.publishImage("Prueba ", "/tmp/prueba.png")
    print(res)
    idPost = mastodon.getUrlId(res)
    print(idPost)
    input('Delete? ')
    mastodon.deletePostId(idPost)
    # sys.exit()
    print("Testing posts")
    mastodon.setPostsType('posts')
    mastodon.setPosts()
    print(mastodon.getClient().me())
    for i, post in enumerate(mastodon.getPosts()):
        # print(post)
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
        # input("Delete ?")
        # mastodon.deletePost(post)

    # sys.exit()

    print("Testing title and link")

    print("Posts")

    mastodon.setPostsType('posts')
    mastodon.setPosts()
    for post in mastodon.getPosts():
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print(f"Title: {title}\nLink: {link}\n")

    print("Favs")

    mastodon.setPostsType("favs")
    mastodon.setPosts()
    for i, post in enumerate(mastodon.getPosts()):
        print("i", i)
        print("1", post)
        print("2", mastodon.getPost(i))
        title = mastodon.getPostTitle(post)
        link = mastodon.getPostLink(post)
        print(f"Title: {title}\nLink: {link}\n")
        print(mastodon.extractDataMessage(i))

    sys.exit()
    (theTitle, theLink, firstLink, theImage, theSummary, content,
     theSummaryLinks, theContent, theLinks, comment) \
             = mastodon.extractDataMessage(0)

    # config = configparser.ConfigParser()
    # config.read(CONFIGDIR + '/.rssBlogs')

    # import modulePocket
    #
    # p = modulePocket.modulePocket()

    # p.setClient('fernand0')
    # p.publishPost(theTitle, firstLink, '')

    mastodon.publishPost("I'll publish several links each day about "
                         "technology, social internet, security, ... "
                         " as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
