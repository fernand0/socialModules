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
        # self.service = 'twitter'
        self.url = f"https://twitter.com/{self.user}"
        self.authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        client = Twitter(auth=self.authentication)
        return client

    def setApiPosts(self):
        posts = self.getClient().statuses.user_timeline(count=100)
        #posts = self.getClient().statuses.user_timeline(_id='fernand0')
        return posts

    def setApiFavs(self): 
        posts = self.getClient().favorites.list(tweet_mode='extended') 
        #count=100)
        # https://stackoverflow.com/questions/38717816/twitter-api-text-field-value-is-truncated
        return posts

    def processReply(self, reply): 
        res = ''
        if reply: 
            if not ('Fail!' in reply):
                idPost = self.getPostId(reply)
                title = self.getAttribute(reply, 'title')
                res = f"{title} https://twitter.com/{self.user}/status/{idPost}"
            else:
                res = reply
        return(res)

    def publishApiImage(self, postData): 
        logging.debug(f"{postData} Len: {len(postData)}")
        if len(postData) == 3:
            post, imageName, more = postData
            if imageName:
                with open(imageName, "rb") as imagefile:
                        imagedata = imagefile.read()
    
                try:
                    t_upload = Twitter(domain='upload.twitter.com', 
                                    auth=self.authentication)
                    id_img1 = t_upload.media.upload(media=imagedata)["media_id_string"]
                    if 'alt' in more:
                        t_upload.media.metadata.create(_json={ "media_id": id_img1, 
                            "alt_text": { "text": more['alt'] }
})
                    res = self.getClient().statuses.update(status=post, 
                        media_ids=id_img1)
                except twitter.api.TwitterHTTPError as twittererror:        
                    for error in twittererror.response_data.get("errors", []): 
                        logging.info("      Error code: %s" % error.get("code", None))
                    res = self.report('Twitter', post, imageName, sys.exc_info())
            else:
                logging.info(f"No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)
        return res

    # def publishApiPosts(self, postData): 
    #     return self.publishApiPost(postData)

    def publishApiRT(self, postData): 
        post, link, comment, plus = postData
        idPost = plus['idPost']

        logging.debug("     Retweeting: %s" % post)
        res = 'Fail!'
        try:
            res = self.getClient().statuses.retweet._id(_id=idPost)
            #         result = t.statuses.retweet._id(_id=tweet['id'])
        except twitter.api.TwitterHTTPError as twittererror:        
            for error in twittererror.response_data.get("errors", []): 
                logging.info("      Error code: %s" % error.get("code", None))
            res = self.report('Twitter', post, link, sys.exc_info())

        return res

    def publishApiPost(self, postData): 
        post, link, comment, plus = postData
        post = self.addComment(post, comment)

        # post = post[:(240 - (len(link) + 1))]
        if link:
            post = post[:(240 - (23 + 1))]
            post = post+" " + link
        # https://help.twitter.com/en/using-twitter/how-to-tweet-a-link
        # A URL of any length will be altered to 23 characters, even if the
        # link itself is less than 23 characters long. Your character count
        # will reflect this.

        logging.debug("     Publishing: %s" % post)
        res = 'Fail!'
        try:
            res = self.getClient().statuses.update(status=post)
        except twitter.api.TwitterHTTPError as twittererror:        
            for error in twittererror.response_data.get("errors", []): 
                logging.info("      Error code: %s" % error.get("code", None))
            res = self.report('Twitter', post, link, sys.exc_info())

        return res

    def deleteApiPosts(self, idPost): 
        result = self.getClient().statuses.destroy(_id=idPost)
        logging.debug(f"Res: {result}")
        return(result)

    def deleteApiFavs(self, idPost): 
        logging.info("Deleting: {}".format(str(idPost)))
        result = self.getClient().favorites.destroy(_id=idPost)
        logging.debug(f"Res: {result}")
        return(result)

    def getPostId(self, post):
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            idPost = self.getAttribute(post, 'id')
        return  idPost

    def getPostApiSource(self, post):
        source = self.getAttribute(post, 'source')
        return source

    def getPostApiDate(self, post):
        date = self.getAttribute(post, 'created_at')
        return date

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getPostTitle(self, post):
        title = ""
        if 'text' in post:
            title = self.getAttribute(post, 'text')
        elif 'full_text' in post:
            title = self.getAttribute(post, 'full_text')
        # if 'http' in title:
            # title = title.split('http')[0]
        return title

    def getPostUrl(self, post):
        idPost = self.getAttribute(post, 'id_str')
        return f'https://twitter.com/{self.user}/status/{idPost}'

    def getPostLink(self, post):
        return self.getPostUrl(post)

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = ''
        if 'full_text' in post:
            result = self.getAttribute(post, 'full_text')
        return result

    def getPostContentLink(self, post):
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
            firstLink = self.getPostContentLink(post)
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

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    import moduleTwitter
    tw = moduleTwitter.moduleTwitter()

    tw.setClient('fernand0Test')

    testingFav = True
    if testingFav:
        print("Testing Fav")
        tw.setClient('fernand0')
        tw.setPostsType('favs')
        tw.setPosts()
        tweet = tw.getPosts()[0]
        tweet = tw.getNextPost()
        print(tweet)
        print(f" -Title {tw.getPostTitle(tweet)}")
        print(f" -Link {tw.getPostLink(tweet)}")
        print(f" -Content link {tw.getPostContentLink(tweet)}")
        print(f" -Post link {tw.extractPostLinks(tweet)}")
        sys.exit()

    testingRT = False
    if testingRT:
        print("Testing RT")
        tw1 = moduleTwitter.moduleTwitter() 
        tw1.setClient('reflexioneseir')
        tw1.setPosts()
        tweet = tw1.getPosts()[10]
        idPost = tweet['id']
        title = tw1.getPostTitle(tweet)
        link = tw1.getPostLink(tweet)
        tw.publishApiRT((title, link, '', {'idPost' : idPost}))

        sys.exit()


    testingSearch = False
    if testingSearch:
        myLastLink = 'https://twitter.com/reflexioneseir/status/1235128399452164096'
        myLastLink = 'http://fernand0.blogalia.com//historias/78135'
        tw1 = moduleTwitter.moduleTwitter() 
        tw1.setClient('reflexioneseir')
        tw1.setPostsType('posts')
        tw1.setPosts()
        i = tw1.getLinkPosition(myLastLink)
        print(i)
        print(tw1.getPosts()[i-1])
        print(tw1.getPostLink(tw1.getPosts()[i-1]))
        num = 1
        lastLink = myLastLink
        listPosts = tw1.getNumPostsData(num, i, lastLink)
        print(listPosts)
        sys.exit()

    sys.exit()

    print("Testing duplicate post")

    res = tw.publishPost("Best Practices for Writing a Dockerfile", "https://blog.bitsrc.io/best-practices-for-writing-a-dockerfile-68893706c3", '')
    print(f"Res: {res}")
    print(f"End Res")
    print(res.find('Status is a duplicate'))
    input("Repeat?")
    res = tw.publishPost("Best Practices for Writing a Dockerfile", "https://blog.bitsrc.io/best-practices-for-writing-a-dockerfile-68893706c3", '')

    sys.exit()
    # print("Testing bad link")
    # res = tw.publishPost("Post MTProto Analysis: Accessible Overview", "https://telegra.ph/LoU-ETH-4a-proof-07-16", '')

    # logging.info(f"Res: {res}")

    # return

    #print("Testing followers")
    #tw.setFriends()
    #sys.exit()

    # res = tw.publishImage("Prueba imagen", "/tmp/2021-06-25_image.png", 
    #        alt= "Imagen con alt")
    #print("Testing posting and deleting")
    # res = tw.publishPost("Prueba borrando 7", "http://elmundoesimperfecto.com/", '')
    # print(res)
    # idPost = tw.getUrlId(res)
    # print(idPost)
    # input('Delete? ')
    # tw.deletePostId(idPost)
    # return
    #sys.exit()

    # print("Testing posts")
    # tw.setPostsType('favs')
    # tw.setPosts()

    print("Testing title and link")
    
    for i, post in enumerate(tw.getPosts()):
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        theId = tw.getPostId(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")

    return

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

