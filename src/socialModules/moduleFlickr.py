#!/usr/bin/env python

import configparser
import dateparser
import dateutil
import flickrapi
import sys
from atproto import Client, models

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

class moduleFlickr(Content): #, Queue):

    def getKeys(self, config):
        KEY = config.get(self.user, "key")
        SECRET = config.get(self.user, "secret")

        return (KEY, SECRET)

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.base_url = 'https://flickr.com'
        self.url = f"{self.base_url}/photos/{self.user}"
        logging.info("Initializing API")

        try:
            flickr = flickrapi.FlickrAPI(keys[0], keys[1], format='parsed-json',
                        token_cache_location=f"{CONFIGDIR}")
            if not flickr.token_valid(perms='write'):
                # Get a request token
                flickr.get_request_token(oauth_callback='oob')

                # Open a browser at the authentication URL. Do this however
                # you want, as long as the user visits that URL.
                authorize_url = flickr.auth_url(perms='write')
                print(f"Visit {authorize_url} and copy the result")

                # Get the verifier code from the user. Do this however you
                # want, as long as the user gives the application the code.
                verifier = str(input('Verifier code: '))

                # Trade the request token for an access token
                flickr.get_access_token(verifier)
        except:
            res = self.report(self.indent, 'Error in initApi', 
                              '', sys.exc_info())
            client = None
        self.api = flickr
        client = flickr

        return client

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        posts = []

        return posts

    def setApiFavs(self):
        posts = []

        return posts

    def setApiDrafts(self):

        posts = []
        posts = self.apiCall('people.getPhotos', user_id='fernand0')
        posts = posts[0]['photos']['photo']
        return posts

    def getPostTitle(self, post):
        title = ''
        try:
            title = post['title']
        except:
            title = ''
        return title

    def getPostUrl(self, post):
        res = ''

        return res

    def getPostLink(self, post):
        logging.debug(f"Post: {post}")
        link = f"{self.url}/{post['id']}"
        logging.debug(f"Post link: {link}")
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post.post.record.text
        return result

    def getPostContentLink(self, post):
        result = ''
        return result
 
    def publishApiImage(self, *args, **kwargs):
        res = None
        return res

    def publishApiRT(self, *args, **kwargs):
        res = None
        # TODO

        return res

    def publishApiPost(self, *args, **kwargs):
        res = None
        # TODO

        return res

    def publishApiDrafts(self, *args, **kwargs):
        return self.publishApiDraft(*args, **kwargs)

    def publishApiDraft(self, *args, **kwargs):
        res = ''
        logging.debug(f"Args: {args} Kwargs: {kwargs}")
        if kwargs:
            post = kwargs.get('post', '')
            api = kwargs.get('api', '')
        logging.debug(f"Post: {post} Api: {api}")
        res = self.apiCall('photos.setPerms', photo_id=post['id'], 
                     is_public=1, is_friend=1, is_family=1)
        logging.debug(f"Res: {res}")
        if not res:
            res = "OK. Published!"
        return res

    def deleteApiPosts(self, idPost): 
        res = None

        return (res)

    def deleteApiFavs(self, idPost): 
        res = None

        return (res)

    def processReply(self, reply):
        res = ''
        msgLog = f"{self.indent}Reply: {reply}"
        logMsg(msgLog, 1, 1)
        origReply = reply[0]
        if 'stat' in origReply and origReply.get('stat') == 'ok':
            if not ('Fail!' in reply):
                idPost = self.getPostId(origReply)
                res = (f"https://flickr.com/photos/{self.user}/status/{idPost}")
        return (res)

    def getPostHandle(self, post):
        res = None
        print(f"Post: {post}")

        return handle

    def getPostId(self, post):
        try:
            idPost = post.get('photoid').get('_content')
        except:
            idpost = ''

        return idPost

def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    testingPostsPos = True
    if testingPostsPos:
        apiSrc.setPosts()
        apiSrc.lastLinkPublished='https://flickr.com/photos/fernand0/53624853058'
        print(f"Link: {apiSrc.getLastLinkPublished()}")
        print(f"Link: {apiSrc.getNextPost()}")
        print(f"Link: {apiSrc.getPosNextPost()}")
        print(f"Link: {apiSrc.getPosNextPost()}")
        post = apiSrc.getPosts()[0]
        print(f"Url: {apiSrc.getPostUrl(post)}")
        return

    testingPosts = False
    if testingPosts:
        apiSrc.setPosts()
        for i,post in enumerate(apiSrc.getPosts()):
            print(f"Post {i}): {post}")
        return

    testingPublishDraft = False
    if testingPublishDraft:
        apiSrc.setPosts()
        post = apiSrc.getPosts()[0]
        print(f"Post: {post}")
        apiSrc.publishApiDraft(api= apiSrc.getClient(), post=post)
        return

    testingPost = False
    if testingPost:
        apiSrc.publishPost("prueba","https://elmundoesimperfecto.com/", "")
        return

    testingPostImages = False
    if testingPostImages:
        image = '/tmp/2024-03-30_image.png'
        # Does not work with svg
        # image = '/tmp/2023-08-04_image.png'

        title = 'Prueba imagen '
        altText = "Texto adicional"

        print(f"Testing posting with images")
        res = apiSrc.publishImage("Prueba imagen", image, alt= altText)
        print(f"Res: {res}")

        return


    return 

    testingPost = False
    if testingPost:
        print("Testing Post")
        key = ('twitter', 'set', 'fernand0', 'posts')
        apiSrc = rules.readConfigSrc("", key, None)
        keyD = ('direct', 'post', 'blsk', 'fernand0.bsky.social')
        indent = ""
        more = None
        apiDst = rules.readConfigDst(indent, keyD, more, apiSrc)

        # Example of long post
        title = "'The situation has become appalling': fake scientific papers push research credibility to crisis point |  Peer review and scientific publishing |  The Guardian"
        link = "https://www.theguardian.com/science/2024/feb/03/the-situation-has-become-appalling-fake-scientific-papers-push-research-credibility-to-crisis-point"
        print(f"Publishing {apiDst.publishPost(title, link, '')}")
        delete = input("Delete (write the id)? ")
        if delete:
            print(f"Deleting: {apiDst.deleteApiPosts(delete)}")

        return
    return


if __name__ == '__main__':
    main()
