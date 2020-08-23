#!/usr/bin/env python

import configparser
import os
import sys

from medium import Client

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleMedium(Content,Queue):

    def __init__(self):
        super().__init__()
        self.service = None

    def setClient(self, channel):
        logging.info("     Connecting Medium")
        self.service = 'Medium'
        try:
            config = configparser.ConfigParser() 
            config.read(CONFIGDIR + '/.rssMedium') 
            
            application_id = config.get("appKeys","ClientID")
            application_secret = config.get("appKeys","ClientSecret")

            
            try: 
                client = Client(application_id = application_id, 
                        application_secret = application_secret)
                client.access_token = config.get("appKeys","access_token") 
                # Get profile details of the user identified by the access
                # token.  
                user = client.get_current_user()
            except: 
                logging.warning("Medium authentication failed!") 
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except: 
            logging.warning("Account not configured") 
            client = None
            user = None

        self.tc = client
        self.user = user

    def getClient(self):
        return self.tc

    def getUser(self):
        return self.user

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

        import moduleRss
        content = moduleRss.moduleRss()
        rssFeed='https://medium.com/feed/@{}'.format(self.user['username'])
        #print(rssFeed)
        content.setRssFeed(rssFeed)
        content.setPosts()
        for post in content.getPosts():
            self.posts.append(post)

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in Medium...")
        client = self.tc
        user = self.user

        title = post
        content = comment
        links = ""

        from html.parser import HTMLParser
        h = HTMLParser()
        title = h.unescape(title)
        textOrig = 'Publicado originalmente en <a href="%s">%s</a>\n\n' % (link, title)

        try:
            res = client.create_post(user_id=user["id"], title=title,
                content="<h4>"+title+"</h4><br />"+textOrig+content,
                canonical_url = link, content_format="html",
                publish_status="public")#"public") #draft") 
            logging.info("Res: %s" % res)
            return(res)
        except:
            return(self.report('Medium', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'title' in post:
            return(post['title'].replace('\n', ' '))

    def getPostLink(self, post):
        return(post['link'])

def main():
    import moduleMedium

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    section = 'Blog2'
    url = config.get(section, "url")
    rssFeed = config.get(section, "rssFeed")
    logging.info(" Blog RSS: %s"% rssFeed)
    import moduleRss
    blog = moduleRss.moduleRss()
    # It does not preserve case
    blog.setRssFeed(rssFeed)
    blog.setUrl(url)
    blog.setPosts()
    post = blog.obtainPostData(1)

    tel = moduleMedium.moduleMedium()

    tel.setClient('fernand0')

    tel.setPosts()
    title = post[0]
    link = post[1]
    content = post[7]
    links = post[8]
    tel.publishPost(title,link,content)


if __name__ == '__main__':
    main()

