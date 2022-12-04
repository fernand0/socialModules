#!/usr/bin/env python

import logging
import sys

import mastodon
from bs4 import BeautifulSoup

from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleQueue import *

# pip install Mastodon.py



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
            #self.user = self.user[:pos]
        else:
            self.base_url = 'https://mastodon.social'

        client = mastodon.Mastodon(access_token=keys[0],
                                   api_base_url=self.base_url)
        return client

    def setApiPosts(self):
        posts = []
        if self.getClient():
            try:
                posts = self.getClient().account_statuses(self.getClient().me())
            except:
                posts = []
        return posts

    def setApiFavs(self):
        posts = []
        if self.getClient():
            try:
                posts = self.getClient().favourites()
            except:
                posts = []
        return posts

    def processReply(self, reply):
        res = ''
        if reply:
            res = self.getAttribute(reply, 'uri')
        return res

    def publishApiImage(self, *args, **kwargs):
        post, image = args
        more = kwargs

        res = 'Fail!'
        if True:
            res = self.getClient().media_post(image, "image/png")
            res = self.getClient().status_post(post, media_ids = res['id'])
        else:
            res = self.getClient().status_post(post+" "+link,
                    visibility='private')
        print(f"res: {res}")
        return res

    def publishApiPost(self, *args, **kwargs):
        title = ''
        if args and len(args) == 3:
            logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = ''

        post = self.addComment(title, comment)

        res = 'Fail!'
        try:
            res = self.getClient().toot(post+" "+link)
            res = self.processReply(res)
        except:
            res = self.report(self.getService(), kwargs, '', sys.exc_info())
            res = f"Fail! {res}"
# else:
        #     res = self.getClient().status_post(post+" "+link,
        #             visibility='private')
        #     # 'direct' 'private' 'unlisted' 'public'


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

    def getSiteTitle(self):
        title = ''
        if self.user:
            title = f"{self.user}'s {self.service}"
        return title


    def getPostTitle(self, post):
        result = ''
        # import pprint
        # print(f"post: {post}")
        # pprint.pprint(post)
        print(f"PPPPPost: {post}")
        card = post.get('card')
        if card:
            result = f"{card.get('title')} {card.get('url')}"
        if not result:
            result = post.get('content')
        print(f"RRRRResult: {result}")
        # soup = BeautifulSoup(result, 'lxml')
        if result.startswith('<'):
            result = result[3:]
        if result.endswith('>'):
            result = result[:-4]
        print(f"RRRRResult: {result}")
        pos = result.find('<')
        posH = result.find('http')
        posF = result.find('"',posH+1)
        result = f"{result[:pos]} {result[posH:posF]}"

        # if 'card' in post and post['card'] and 'title' in post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        # elif 'content' in post:
        #     result = self.getAttribute(post, 'content').replace('\n', ' ')
        # elif 'card' in post and post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        return result

    def getPostUrl(self, post):
        return self.getAttribute(post, 'url')

    def getPostLink(self, post):
        if self.getPostsType() == 'favs':
            content, link = self.extractPostLinks(post)
        else:
            link = self.getPostUrl(post)
        return link
        
    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = ''
        if 'content' in post:
            result = self.getAttribute(post, 'content')
        return result

    def getPostContentLink(self, post):
        link = ''
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

    # def extractDataMessage(self, i):
    #     logging.info(f"Service {self.service}")
    #     (theTitle, theLink, firstLink, theImage, theSummary,
    #      content, theSummaryLinks, theContent, theLinks, comment) = (
    #                     None, None, None, None, None,
    #                     None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         post = self.getPost(i)
    #         theTitle = self.getPostTitle(post)
    #         theLink = self.getPostUrl(post)
    #         firstLink = self.getPostContentLink(post)
    #         theId = self.getPostId(post)

    #         theLinks = [firstLink, ]
    #         content = None
    #         theContent = None
    #         if 'card' in post and post['card']:
    #             theContent = self.getAttribute(post['card'], 'description')

    #         theImage = None
    #         theSummary = None

    #         theSummaryLinks = None
    #         comment = theId

    #     return (theTitle, theLink, firstLink, theImage, theSummary,
    #             content, theSummaryLinks, theContent, theLinks, comment)

    def search(self, text):
        pass


def main():

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()

    mastodon.setClient('@fernand0Test@mastodon.social')
    testingPosts = True
    if testingPosts:
        print("Testing Posts")
        mastodon.setClient('fernand0')
        mastodon.setPostsType('posts')
        mastodon.setPosts()
        if mastodon.getPosts():
            toot = mastodon.getPosts()[0]
            # toot = mastodon.getNextPost()[0]
            print(toot)
            print(f" -Title {mastodon.getPostTitle(toot)}")
            print(f" -Link {mastodon.getPostLink(toot)}")
            print(f" -Content link {mastodon.getPostContentLink(toot)}")
            print(f" -Post link {mastodon.extractPostLinks(toot)}")
        return

    mastodon.setClient('@fernand0Test@fosstodon.org')
    testingFav = False
    if testingFav:
        print("Testing Fav")
        mastodon.setClient('fernand0')
        mastodon.setPostsType('favs')
        mastodon.setPosts()
        if mastodon.getPosts():
            toot = mastodon.getPosts()[0]
            toot = mastodon.getNextPost()[0]
            print(toot)
            print(f" -Title {mastodon.getPostTitle(toot)}")
            print(f" -Link {mastodon.getPostLink(toot)}")
            print(f" -Content link {mastodon.getPostContentLink(toot)}")
            print(f" -Post link {mastodon.extractPostLinks(toot)}")
        return

    mastodon.setClient('@fernand0Test@fosstodon.org')

    testingPost = False
    if testingPost:
        print("Testing Post")
        title = "Test"
        link = "https://twitter.com/fernand0Test"
        mastodon.publishApiPost(title, link, '')
        return

    testingPostImages = False
    if testingPostImages:
        image = '/tmp/E8dCZoWWQAgDWqX.png'
        title = 'Prueba imagen'
        mastodon.publishApiImage(title, image)


        return


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
