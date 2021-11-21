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

                try:
                    client.access_token = config.get(channel,"access_token")
                except:
                    client.access_token = config.get("appKeys","access_token")
                # client.access_token = config.get("appKeys","access_token") 
                # Get profile details of the user identified by the access
                # token.  
                userRaw = client.get_current_user()
                user = userRaw['username']
            except: 
                logging.warning("Medium authentication failed!") 
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except: 
            logging.warning("Account not configured") 
            client = None
            userRaw = None
            user = None

        self.client = client
        self.user = user
        self.userRaw = userRaw

    def getUser(self):
        return self.user

    def getUserRaw(self):
        return self.userRaw

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

        import moduleRss
        content = moduleRss.moduleRss()
        rssFeed='https://medium.com/feed/@{}'.format(self.getUser())
        #print(rssFeed)
        content.setRssFeed(rssFeed)
        content.setPosts()
        for post in content.getPosts():
            self.posts.append(post)

    def publishApiPost(self, postData):
        post, link, comment, more = postData
        logging.info("    Publishing in {} ...".format(self.service))
        client = self.client
        user = self.getUserRaw()

        title = post
        content = comment
        print(content)
        links = ""

        from html.parser import HTMLParser
        h = HTMLParser()
        title = h.unescape(title)
        textOrig = 'Publicado originalmente en <a href="%s">%s</a><br />\n\n' % (link, title)

        try:
            res = client.create_post(user_id=user["id"], title=title,
                content="<h4>"+title+"</h4><br />"+textOrig+content,
                canonical_url = link, content_format="html",
                publish_status="public")#"public") #draft") 
            logging.debug("Res: %s" % res)
            return(res)
        except:
            return(self.report('Medium', post, link, sys.exc_info()))

    def publishApiImage(self, postData): 
        logging.debug(f"{postData} Len: {len(postData)}")
        client = self.client
        if len(postData) == 3:
            post, imageName, more = postData
            if imageName:
                # with open(imageName, "rb") as imagefile:
                #         imagedata = imagefile.read()
    
                try:
                    myImage = client.upload_image(imageName, 'image/png')
                    myImageUrl =  myImage['url']
                    res = self.publishPost(post, '', 
                           f"{more['content']}\n<br/>\n"
                           f'<figure>\n<img src="{myImageUrl}">\n</figure>') 
                    print(res)
                except:
                    res = self.report('Medium', post, imageName, sys.exc_info())
            else:
                logging.info(f"No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)
        return res

    def getPostTitle(self, post):
        if 'title' in post:
            return(post['title'].replace('\n', ' '))

    def getPostLink(self, post):
        return(post['link'])

def main():
    import moduleMedium


    testingBotElectrico = True
    if testingBotElectrico:
        url = 'https://medium.com/@botElectrico'
        tel = moduleMedium.moduleMedium()

        tel.setClient('botElectrico')
        tel.publishImage("Prueba",
                '/tmp/2021-11-01_image.png',
                content = "Evolución precio para el día 2021-11-01")

    return
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

