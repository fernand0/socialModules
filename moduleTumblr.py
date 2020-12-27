import click
import configparser
import logging
import os
import pickle
import requests
import sys
import urllib

import pytumblr

from bs4 import BeautifulSoup
from bs4 import Tag

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

    def getKeys(self, config): 
        consumer_key = config.get("Buffer1", "consumer_key") 
        consumer_secret = config.get("Buffer1", "consumer_secret") 
        oauth_token = config.get("Buffer1", "oauth_token")
        oauth_secret = config.get("Buffer1", "oauth_secret")

        return (consumer_key, consumer_secret, oauth_token, oauth_secret)


    def initApi(self, keys):
        client = pytumblr.TumblrRestClient(keys[0], keys[1], keys[2], keys[3])
        tumblr = self.user
        if isinstance(tumblr,str):
            self.url = f"https://{tumblr}.tumblr.com/"
        elif isinstance(tumblr[1],str): 
            self.url = f"https://{tumblr[1]}.tumblr.com/"
        elif isinstance(tumblr,tuple): 
            self.url = f"https://{tumblr[1][1]}.tumblr.com/"
        logging.info(f"Url: {self.url}")

        return client
 

    #def setClient(self, tumblr):
    #    logging.info("    Connecting {}: {}".format(self.service, tumblr))
    #    try:
    #        config = configparser.ConfigParser()
    #        config.read(CONFIGDIR + '/.rssTumblr')

    #        self.user = tumblr

    #        consumer_key = config.get("Buffer1", "consumer_key")
    #        consumer_secret = config.get("Buffer1", "consumer_secret")
    #        oauth_token = config.get("Buffer1", "oauth_token")
    #        oauth_secret = config.get("Buffer1", "oauth_secret")

    #        try:
    #            client = pytumblr.TumblrRestClient(consumer_key, 
    #                    consumer_secret, oauth_token, oauth_secret)
    #        except:
    #            logging.warning("Tumblr authentication failed!")
    #            logging.warning("Unexpected error:", sys.exc_info()[0])
    #            client = None
    #    except:
    #        logging.warning("Account not configured")
    #        client = None

    #    self.tc = client
    #    logging.info(f"Url: {tumblr}")
    #    if isinstance(tumblr,str):
    #        self.url = f"https://{tumblr}.tumblr.com/"
    #    elif isinstance(tumblr[1],str): 
    #        self.url = f"https://{tumblr[1]}.tumblr.com/"
    #    elif isinstance(tumblr,tuple): 
    #        self.url = f"https://{tumblr[1][1]}.tumblr.com/"
    #    logging.info(f"Url: {self.url}")
 
    def getBlogName(self):
        name = self.getUrl().split('/')[2]
        return name

    def setApiPosts(self):
        setApiPublished()

    def setApiPublished(self):
        posts = self.getClient().posts(self.getBlogName())
        if 'posts' in posts:
            self.posts = posts['posts']
        else:
            self.posts = []

    def setApiDrafts(self):
        drafts = self.getClient().drafts(self.getUrl().split('/')[2])
        #, offset="75")
        if 'posts' in drafts: 
            self.posts = drafts['posts']
        else:
            self.posts = []
 
    def setApiQueue(self):
        queue = self.getClient().queue(self.getUrl().split('/')[2])
        #, offset="75")
        if 'posts' in queue: 
            self.posts = queue['posts']
        else:
            self.posts = []

    #def setPosts(self):
    #    logging.info("  Setting posts")
    #    logging.info(f"  Setting posts {self.getUrl()}")
    #    posts = self.getClient().posts(self.getBlogName())
    #    if 'posts' in posts:
    #        self.posts = posts['posts']
    #    else:
    #        self.posts = []
    #    drafts = self.getClient().queue(self.getUrl().split('/')[2])
    #    #, offset="75")
    #    if 'posts' in drafts: 
    #        self.drafts = drafts['posts']
    #    else:
    #        self.drafts = []

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

    def getPostId(self, post):
        logging.debug(f"getPostId {post}")       
        idPost = ""
        if post:
            if 'id' in post:
                idPost = post['id']
        return idPost

    def getPostState(self, post):
        logging.debug(f"getPostState {post}")       
        state = ""
        if post:
            if 'state' in post:
                state = post['state']
        return state

    def processReply(self, reply): 
        logging.debug("Res: %s" % reply) 
        if 'id'  in reply: 
            logging.info("Res: %s" % reply['id']) 
            res = reply['id']
        return res

    def publishApiPost(self, postData):
        res = self.getClient().create_link(self.getBlogName(), state='queue',
                title=postData[0], url=postData[1], description=postData[2])

        res = self.processReply(res)
        return(res)

    #def publishPost(self, post, link, comment):
    #    logging.info("    Publishing in Tumblr: %s" % post)
    #    try:
    #        client = self.tc 
    #        res = client.create_link(self.getBlogName(), state='queue',
    #                title=post, url=link, description="")

    #        res = self.processReply(res)
    #        return(res)
    #    except:        
    #        return(self.report('Tumblr', post, link, sys.exc_info()))

    def publish(self, j):
        # This is not publishing but changing state -> editing
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service) 
        if hasattr(self, 'getPostsType') and (self.getPostsType() == 'drafts'): 
            logging.info("Changing draft state %d"% j)                
            res = self.edit(j, newState='published') 
        else:
            # Not tested
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks,
                    content, links, comment) = self.obtainPostData(j)
            logging.info("Publishing {} {}".format(title, link))
            res = self.publishPost(title, link, comment)

        return(res)

    def do_edit(self, j, **kwargs): 
        post = self.getPosts()[j]
        idPost = post['id']
        typePost = post['type']
        if ('newTitle' in kwargs) and kwargs['newTitle']:
            oldTitle = self.getPostTitle(post)
            newTitle = kwargs['newTitle']
            logging.info(f"New title {newTitle}")
            res = self.getClient().edit_post(self.getBlogName(), id=idPost, 
                    type=post['type'], title = newTitle)
        if ('newState' in kwargs) and kwargs['newState']:
            newState = kwargs['newState']
            logging.info("New state %s", newState)
            res = self.getClient().edit_post(self.getBlogName(), id=idPost, 
                    type=post['type'], title = oldTitle, state=newState)
        return res

    def edit(self, j, newTitle): 
        update = self.do_edit(j, newTitle=newTitle)
        return update

    #def edit(self, j, newTitle='', newState=''): 
    #    post = self.getPosts()[j]
    #    idPost = post['id']
    #    typePost = post['type']
    #    oldTitle = self.getPostTitle(post)
    #    oldState = self.getPostState(post)

    #    #if ('newTitle' in kwargs) and kwargs['newTitle']:
    #    #    newTitle = kwargs['newTitle']
    #    if newTitle:
    #        #if oldState == 'queued':
    #        #    # Seriously Tumblr? You return queued but the parameter that
    #        #    # must be passed is 'queue'?
    #        #    oldState = 'queue'
    #        logging.info(f"New title {newTitle} State {oldState}")
    #        res = self.getClient().edit_post(self.getBlogName(), id=idPost, 
    #                type=post['type'], 
    #                title = newTitle)
    #        res = self.processReply(res)
    #        update = "Changed "+oldTitle+" with "+newTitle+" id " + str(res)
    #    return update

    def edits(self, j, newTitle='', newState=''): 
        if newState:
            logging.info("New state %s", newState)
            res = self.getClient().edit_post(self.getBlogName(), id=idPost, 
                    type=post['type'], title = oldTitle, state=newState)
            res = self.processReply(res)
            update = "Changed "+oldState+" with "+newState+" id " + str(res)

        return(update)

    def deleteApi(self, j): 
        logging.info("Deleting id %s" % idPost)
        idPost = self.getId(j)
        return self.getClient().delete_post(self.getBlogName(), idPost)

    #def delete(self, j): 
    #    logging.info("Deleting id %s" % j)
    #    idPost = self.getId(j)
    #    #self.sc.token = self.user_slack_token        
    #    logging.info("Deleting id %s" % idPost)
    #    client = self.tc
    #    result = client.delete_post(self.getBlogName(), idPost)
    #    logging.info(result)
    #    res = self.processReply(res)
    #    return(res)


def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleTumblr

    t = moduleTumblr.moduleTumblr()

    t.setClient('fernand0')
    t.setPostsType('queue')
    t.setPosts()
    print(t.getPosts())

    sys.exit()

    t.setPostsType('drafts')

    t.setPosts()
    i=0
    print(t.getPosts())
    print(t.getPosts())
    print(len(t.getPosts()))
    print(t.getPostTitle(t.getPosts()[i]))
    print(t.getPostLink(t.getPosts()[i]))
    print(t.getPostId(t.getPosts()[i]))
    print(t.publish(i))
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

