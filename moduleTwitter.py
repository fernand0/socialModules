#!/usr/bin/env python

import configparser
import sys

import twitter
from twitter import *
# pip install twitter
#https://pypi.python.org/pypi/twitter
#https://github.com/sixohsix/twitter/tree
#http://mike.verdone.ca/twitter/

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleTwitter(Content,Queue):

    def __init__(self):
        super().__init__()

    def getKeys(self, config): 
        try: 
            CONSUMER_KEY = config.get(self.user, "CONSUMER_KEY") 
        except: 
            CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
        try: 
            CONSUMER_SECRET = config.get(self.user, "CONSUMER_SECRET")
        except: 
            CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
        TOKEN_KEY = config.get(self.user, "TOKEN_KEY")
        TOKEN_SECRET = config.get(self.user, "TOKEN_SECRET")
        return(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_KEY, TOKEN_SECRET)

    def initApi(self, keys):
        authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        client = Twitter(auth=authentication)
        return client

    def setApiPosts(self):
        posts = self.getClient().statuses.user_timeline()
        return posts

    def setApiFavs(self): 
        posts = self.getClient().favorites.list(tweet_mode='extended') 
        #count=100)
        # https://stackoverflow.com/questions/38717816/twitter-api-text-field-value-is-truncated
        return posts

    def processReply(self, reply): 
        res = ''
        if reply: 
            idPost = self.getPostId(reply)
            res = f"https://twitter.com/{self.user}/status/{idPost}"
        logging.info("     Res: %s" % res)
        return(res)

    def publishApiPost(self, postData): 
        post, link, comment, plus = postData
        post = self.addComment(post, comment)

        post = post[:(240 - (len(link) + 1))]
        logging.info("     Publishing: %s" % post)
        res = 'Fail!'
        try:
            res = self.getClient().statuses.update(status=post+" " + link)
        except twitter.api.TwitterHTTPError as twittererror:        
            for error in twittererror.response_data.get("errors", []): 
                logging.info("      Error code: %s" % error.get("code", None))
            res = self.report('Twitter', post, link, sys.exc_info())
        return res

    def deleteApiPosts(self, idPost): 
        result = self.getClient().statuses.destroy(_id=idPost)
        logging.info(f"Res: {result}")
        return(result)

    def deleteApiFavs(self, idPost): 
        logging.info("Deleting: {}".format(str(idPost)))
        result = self.getClient().favorites.destroy(_id=idPost)
        logging.info(f"Res: {result}")
        return(result)

    def getPostId(self, post):
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            idPost = self.getAttribute(post, 'id')
        return  idPost

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getPostTitle(self, post):
        return self.getAttribute(post, 'text')

    def getPostUrl(self, post):
        idPost = self.getAttribute(post, 'id_str')
        return f'https://twitter.com/{self.user}/status/{idPost}'

    def getPostLink(self, post):
        result = ''
        if ('urls' in post['entities']): 
            if post['entities']['urls']:
                if 'expanded_url' in post['entities']['urls'][0]:
                    result = post['entities']['urls'][0]['expanded_url']
        elif ('url' in post['user']['entities']['url'] 
            and (post['user']['entities']['url']['urls'])): 
            result = post['user']['entities']['url']['urls'][0]['expanded_url']
        elif ('media' in post['entities']): 
            if (post['entities']['media']): 
                result = post['entities']['media'][0]['expanded_url']
        return result

    def extractDataMessage(self, i):
        (theTitle, theLink, firstLink, theImage, theSummary, 
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None, 
                        None, None, None, None, None) 

        if i < len(self.getPosts()):
            post = self.getPost(i)
            #import pprint
            #pprint.pprint(post)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostUrl(post)
            firstLink = self.getPostLink(post)
            theId = self.getPostId(post)

            theLinks = [ firstLink, ]
            content = None 
            theContent = theTitle

            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = theId

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def search(self, text):
        logging.debug("     Searching in Twitter...")
        try:
            res = self.client.search.tweets(q=text)

            if res: 
                logging.debug("Res: %s" % res)
                return(res)
        except:        
            return(self.report('Twitter', text, sys.exc_info()))

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleTwitter
    tw = moduleTwitter.moduleTwitter()

    tw.setClient('fernand0Test')

    #print("Testing followers")
    #tw.setFriends()
    #sys.exit()

    #print("Testing posting and deleting")
    #res = tw.publishPost("Prueba borrando 7", "http://elmundoesimperfecto.com/", '')
    #print(res)
    #idPost = tw.getUrlId(res)
    #print(idPost)
    #input('Delete? ')
    #tw.deletePostId(idPost)
    #sys.exit()
    print("Testing posts")
    tw.setPostsType('posts')
    tw.setPosts()

    print("Testing title and link")
    
    for i, post in enumerate(tw.getPosts()):
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        theId = tw.getPostId(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")

    print("Favs")

    tw.setPostsType("favs")
    tw.setPosts()

    for post in tw.getPosts():
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nLink: {}\nUrl:{}\n".format(title,link,url))
    print(len(tw.getPosts()))

    sys.exit()



    i=0
    post = tw.getPost(i)
    title = tw.getPostTitle(post)
    link = tw.getPostLink(post)
    url = tw.getPostUrl(post)
    print(post)
    print("Title: {}\nTuit: {}\nLink: {}\n".format(title,link,url))
    tw.deletePost(post)
    sys.exit()

    for i, post in enumerate(tw.getPosts()):
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title,link,url))
        input("Delete?")
        print("Deleted https://twitter.com/i/status/{}".format(tw.delete(i)))
        import time
        time.sleep(5)




    sys.exit()

    res = tw.search('url:fernand0')

    for tt in res['statuses']: 
        #print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()


if __name__ == '__main__':
    main()

