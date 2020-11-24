#!/usr/bin/env python

import configparser
import pickle
import os
from pocket import Pocket, PocketException

from configMod import *
from moduleContent import *
from moduleQueue import *

class modulePocket(Content,Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.client = None
        self.service = 'pocket'

    def setClient(self, pocket=''):
        logging.info("    Connecting Pocket")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssPocket')

            self.user = pocket

            consumer_key = config.get("appKeys", "consumer_key")
            access_token = config.get("appKeys", "access_token")

            try:
                client = Pocket(consumer_key=consumer_key, access_token=access_token)
            except:
                logging.warning("Pocket authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                client = None
        except:
            logging.warning("Account not configured")
            client = None

        self.client = client
 
    def getClient(self):
        return self.client    
    
    def setPosts(self):
        logging.info("  Setting posts")
        posts = []
        dictPosts = self.client.retrieve()['list']
        for post in dictPosts:
            posts.append(dictPosts[post])
        
        self.posts = posts[:100]

    def getPostTitle(self, post):
        if 'resolved_title' in post:
            return(post['resolved_title'])
        else:
            return ''

    def getPostLink(self, post):
        if 'resolved_url' in post:
            return(post['resolved_url'])
        else:
            return ''

    def publishPost(self, post, link, comment):
        logging.info(f"    Publishing in {self.service}: {post}")
    
        try:
            client = self.client 
            res = client.add(link)
            logging.info("Res: %s" % res)
            logging.info("Posted!: %s" % post)
            return(res)
        except:        
            return(self.report('Pocket', post, link, sys.exc_info()))

    def publish(self, j): 
        logging.info("Publishing %d"% j)
        post = self.obtainPostData(j)
        logging.info("Publishing %s"% post[0])
        update = ''
        title = self.getTitle(j)
        url = self.getLink(j)
        logging.info("Title: %s" % str(title))
        logging.info("Url: %s" % str(url))
        if self.getBuffer():            
            for profile in self.getSocialNetworks():
                if profile[0] in self.getBufferapp():
                    lenMax = self.len(profile)
                    logging.info("   getBuffer %s" % profile)
                    socialNetwork = (profile,self.getSocialNetworks()[profile])
                    listPosts = []
                    listPosts.append((title, url))
                    update = update + self.buffer[socialNetwork].addPosts(listPosts)
                    update = update + '\n'

        if self.getProgram():
            logging.info("getProgram")
            for profile in self.getSocialNetworks():
                nick = self.getSocialNetworks()[profile]
                logging.info("Social: {} Nick: {}".format(profile, nick))
                if ((profile[0] in self.getProgram()) or 
                        (profile in self.getProgram())): 
                    logging.info("Social: {} Nick: {}".format(profile, nick))
                    lenMax = self.len(profile)
                    socialNetwork = (profile, nick)

                    listP = self.cache[socialNetwork].setPosts()
                    listP = self.cache[socialNetwork].getPosts()
                    listPsts = self.obtainPostData(j)
                    listP = listP + [listPsts]
                    self.cache[socialNetwork].posts = listP
                    update = update + self.cache[socialNetwork].updatePostsCache()
                    logging.info("Uppdate: {}".format(update))
                    update = update + '\n'

        if not self.getBuffer() and not self.getProgram():
            logging.info("Not getBuffer, getProgram {}".format(self.getSocialNetworks()))
            delayedBlogs = []
            nowait = True
            for profile in self.getSocialNetworks():
                nick = self.getSocialNetworks()[profile]
                logging.info("Social: {} Nick: {}".format(profile, nick))
                listPosts = [ post ]
                print(listPosts)
                socialNetwork = (profile, nick)
                link = self.addNextPosts(listPosts, socialNetwork)
                delayedBlogs.append((self, socialNetwork, 1, nowait, 0)) 

                import concurrent.futures 
                import moduleSocial
                import time
                with concurrent.futures.ThreadPoolExecutor( 
                        max_workers=len(delayedBlogs)) as executor: 
                    delayedPosts = {executor.submit(moduleSocial.publishDelay, 
                        *args): 
                        args for args in delayedBlogs} 
                    time.sleep(5) 

                    for future in concurrent.futures.as_completed(delayedPosts):
                        dataBlog = delayedPosts[future] 
                        try: 
                            res = future.result() 
                            if res: 
                                print("  Published: %s"% str(res)) 
                                if not dataBlog[0].getProgram(): 
                                    posL = res.find('http') 
                                    if posL>=0: 
                                        link = res[posL:] 
                                        if link: 
                                            socialNetwork = dataBlog[1] 
                                            updateLastLink(dataBlog[0].getUrl(),
                                                    link, socialNetwork) 

                        except Exception as exc: 
                            print('{} generated an exception: {}'.format( 
                                str(dataBlog), exc))
 




    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, 
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None, 
                        None, None, None, None, None) 

        if i < len(self.getPosts()):
            theTitle = self.getTitle(i)
            theLink = self.getLink(i)

            theLinks = None
            content = None
            theContent = None
            firstLink = theLink
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main(): 

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    import modulePocket
    
    p = modulePocket.modulePocket()

    p.setClient('fernand0')

    p.setPosts()
    print(p.getPosts())

    for i, post in enumerate(p.getPosts()):
        print(i, p.getPostTitle(post), p.getPostLink(post))
        

    p.setSocialNetworks(config, "Blog25")
    print(p.getSocialNetworks())
    p.publish(99)

    sys.exit()
    
    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')

if __name__ == '__main__':
    main()

