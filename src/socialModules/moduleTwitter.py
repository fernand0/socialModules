#!/usr/bin/env python

import configparser
import sys
import os

import dateparser
import dateutil
import tweepy

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

# pip install twitter
# https://pypi.org/pypi/twitter
# https://github.com/sixohsix/twitter/tree
# http://mike.verdone.ca/twitter/

class moduleTwitter(Content): #, Queue):

    def getKeys(self, config):
        CONSUMER_KEY = config.get(self.user, "CONSUMER_KEY")
        CONSUMER_SECRET = config.get(self.user, "CONSUMER_SECRET")
        BEARER_TOKEN = config.get(self.user, "BEARER_TOKEN", fallback = '')
        TOKEN_KEY = config.get(self.user, "TOKEN_KEY")
        TOKEN_SECRET = config.get(self.user, "TOKEN_SECRET")

        return (CONSUMER_KEY, CONSUMER_SECRET, TOKEN_KEY,
                TOKEN_SECRET, BEARER_TOKEN)

    def initApi(self, keys):
        msgLog = (f"{self.indent} Service {self.service} Start initApi {self.user}")
        logMsg(msgLog, 2, 0)
        # FIXME: Do we call this method directly?
        self.base_url = 'https://twitter.com'
        self.url = f"{self.base_url}/{self.user}"
        # self.authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        # client = Twitter(auth=self.authentication)

        client = tweepy.Client(consumer_key=keys[0],
                               consumer_secret=keys[1],
                               access_token=keys[2],
                               access_token_secret=keys[3])
        auth = tweepy.OAuthHandler(consumer_key=keys[0],
                                   consumer_secret=keys[1],
                                   access_token=keys[2],
                                   access_token_secret=keys[3])
        api = tweepy.API(auth)

        self.api = api

        msgLog = (f"{self.indent} service {self.service} End initApi")
        logMsg(msgLog, 2, 0)
        return client

    def apiCall(self, command, **kwargs):
        msgLog = (f"   Calling: {command} with arguments {kwargs}")
        logMsg(msgLog, 2, 0)
        res = []

        try:
            msgLog = f"{self.indent}Command {command} "
            logMsg(msgLog, 2, 0)
            res = command(**kwargs)
        except:
            res = self.report('', res, '', sys.exc_info())

        # except twitter.api.TwitterHTTPError as twittererror:
        #     for error in twittererror.response_data.get("errors", []):
        #         logging.info(f"      Error code: "
        #                      f"{error.get('code', None)}")

        #         res = self.report(
        #             self.getService(), kwargs, '', sys.exc_info())
        #         res = f"Fail! {res}"
        return res

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        # Does not work with new API restrictions
        #posts = self.apiCall(self.getClient().statuses.user_timeline,
        posts = self.apiCall(self.getClient().get_home_timeline,
                             tweet_fields=['entities']) #, 
                # max_results=100) #, tweet_mode='extended')
        if not isinstance(posts, str):
            posts = posts[0]
        else:
            posts = []

        return posts

    def setApiFavs(self):
        # Not tested, the free API level does not allow this call
        # posts = self.apiCall(self.getClient().favorites.list,
        logging.debug(f"Id: {self.user}")
        # API v1.1
        # posts = self.apiCall(self.getClient().get_favorites,
        # API v2
        posts = self.apiCall(self.getClient().get_liked_tweets,
                             id=self.user) #, 
                             # user_auth=True) #, 
                #tweet_mode='extended')

        return posts

    def processReply(self, reply):
        """
        Processes the reply from a Tweepy API call.
        Extracts the URL from a successful publication.
        """
        msgLog = f"{self.indent}Reply: {reply}"
        logMsg(msgLog, 1, 1)

        # Handle Tweepy v2 Response object
        if hasattr(reply, 'data') and isinstance(reply.data, dict):
            tweet_id = reply.data.get('id')
            if tweet_id:
                # Return the direct URL, which is a simple and standard format.
                return f"https://twitter.com/{self.user}/status/{tweet_id}"

        # Handle error responses or other formats
        if hasattr(reply, 'errors') and reply.errors:
            return f"Fail! {reply.errors}"

        # Fallback for other cases or older response formats
        if isinstance(reply, str) and (('You have already retweeted' in reply)
            or ('Status is a duplicate.' in reply)
            or ('not allowed to create a Tweet with duplicate' in reply)):
            return reply + ' SAVELINK'

        return reply # Return the original reply if it's not a recognized success format

    def publishApiImage(self, *args, **kwargs):
        logging.debug(f"{args} Len: {len(args)}")
        if len(args) == 2:
            post, imageName = args
            more = kwargs
            if imageName:
                with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

                try:
                    # # FIXME
                    # configFile = f"{CONFIGDIR}/.rss{self.service}"
                    # try:
                    #     config = configparser.RawConfigParser()
                    #     config.read(f"{configFile}")
                    # except:
                    #     msgLog = (f"Does file {configFile} exist?")
                    #     self.report({self.indent}, msgLog, 0, '')
                    # keys = self.getKeys(config)


                    # auth = tweepy.OAuthHandler( keys[0], keys[1])
                    # auth.set_access_token(keys[2], keys[3])
                    # apiImage = tweepy.API(auth)

                    # # t_upload = Twitter(domain='upload.twitter.com',
                    # #                  auth=self.authentication)
                    # # self.getClient().domain = 'upload.twitter.com'
                    # # # FIXME Is this really needed?
                    # # id_img1 = self.getClient().media.upload(media=imagedata)['media_id_string']
                    id_img1 = self.apiCall(self.getApi().simple_upload,
                                           filename=imageName)

                    print(f"Id: {id_img1}")
                    if 'alt' in more:
                        # # t_upload.media.metadata.create(_json={"media_id": id_img1,
                        # self.getClient().media.metadata.create(_json={"media_id": id_img1, "alt_text": {"text": more['alt']}
                        #     })
                        logging.debug(f"Setting up alt: {more['alt']}"
                                      f" in image {id_img1}")
                        self.apiCall(self.getApi().create_media_metadata,
                                     media_id=id_img1.media_id,
                                     alt_text=more['alt'])

                    # self.getClient().domain = 'api.twitter.com'
                    # res = self.getClient().statuses.update(status=post,
                    #                                        media_ids=id_img1)

                    res = self.apiCall(self.getClient().create_tweet,
                               text=post, media_ids=[id_img1.media_id, ])
                    # if 'alt' in more:
                    #     # t_upload.media.metadata.create(_json={"media_id": id_img1,
                    #     self.getClient().media.metadata.create(_json={"media_id": id_img1,
                    #                                               "alt_text": {"text": more['alt']}
                    #                                               })
                    # res = self.getClient().statuses.update(status=post,
                    #                                        media_ids=id_img1)
                except twitter.api.TwitterHTTPError as twittererror:
                    for error in twittererror.response_data.get("errors", []):
                        logging.info(f"      Error code: "
                                     f"{error.get('code', None)}")
                    res = self.report(
                        'Twitter', post, imageName, sys.exc_info())
            else:
                logging.info(f"No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)
        return res

    def publishApiRT(self, *args, **kwargs):
        if args and len(args) == 3:
            post, link, comment = args
            idPost = link.split('/')[-1]
        if kwargs:
            more = kwargs
            tweet = more['post']
            link = self.getPostLink(tweet)
            idPost = self.getPostId(tweet)

        logging.debug("     Retweeting: %s id: {id_post}" % post)
        res = 'Fail!'
        if 'twitter' in link:
            #res = self.apiCall(self.getClient().statuses.retweet._id,
            res = self.apiCall(self.getClient().retweet, tweet_id=idPost)
        else:
            res = "Fail! Link {link} is not a tweet"

        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3 and args[0]:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        title = self.addComment(title, comment)

        # logging.info(f"Tittt: {title} {link} {comment}")
        # logging.info(f"Tittt: {link and ('twitter' in link)}")
        res = 'Fail!'
        # post = post[:(240 - (len(link) + 1))]
        if (link and ('twitter.com' in link) and ('status' in link)):
            logging.debug("     Retweeting: %s" % title)
            # If the link is a tweet, we will retweet.
            res = self.publishApiRT(title, link, comment)
        else:
            if link:
                title = title[:(240 - (23 + 1))]
                title = title+" " + link

            # https://help.twitter.com/en/using-twitter/how-to-tweet-a-link
            # A URL of any length will be altered to 23 characters, even if the
            # link itself is less than 23 characters long. Your character count
            # will reflect this.

            msgLog = f"{self.indent}Publishing {title} "
            logMsg(msgLog, 2, 0)
            res = self.apiCall(self.getClient().create_tweet, text=title)
            msgLog = f"{self.indent}Res: {res} "
            logMsg(msgLog, 2, 0)
        return res

    def deleteApiPosts(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        res= self.apiCall(self.getClient().delete_tweet, id=idPost)
        # res= self.apiCall(self.getClient().statuses.destroy, _id=idPost)
        logging.debug(f"Res: {res}")
        return (res)

    def deleteApiFavs(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        res = self.apiCall(self.getClient().unlike, tweet_id=idPost)
        # res = self.apiCall(self.getClient().favorites.destroy, _id=idPost)
        return (res)

    def getPostId(self, post):
        logging.info(f"Postttt: {post}")
        idPost = ''
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            idPost = post.data.get('data')
        return idPost

    def getPostApiSource(self, post):
        source = post.get('source')
        return source

    def getPostApiDate(self, post):
        date = post.get('created_at')
        return date

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getSiteTitle(self):
        title = ''
        if self.user:
            title = f"{self.user}'s {self.service}"
        return title

    def getApiPostTitle(self, post):
        # msgLog = (f"{self.indent} Postttt: {post}")
        # logMsg(msgLog, 2, 0)
        # print(f"post: {post}")
        title = ''
        if ('text' in post.data):
            title = post.data.get('text')
        else:
            title = post.data.get('full_text')
        return title

    def getApiPostUrl(self, post):
        idPost = self.getPostId(post)
        msgLog = f"{self.indent} getPostUrl: {post}"
        logMsg(msgLog, 1, 0)
        if idPost:
            res = f'{self.base_url}/{self.user}/status/{idPost}'
        else:
            res = ''
        return res

    def getApiPostLink(self, post):
        # FIXME: Are you sure? (inconsistent)
        if self.getPostsType() == 'favs':
            content, link = self.extractPostLinks(post)
        else:
            link = self.getPostUrl(post)
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post
        # if 'full_text' in post:
        #     result = post.get('full_text')
        return result

    def getPostContentLink(self, post):
        result = ''
        entities = post.entities
        if entities:
            if ('urls' in entities):
                if entities['urls']:
                    if 'expanded_url' in entities['urls'][0]:
                        result = entities['urls'][0]['expanded_url']
                elif ('full_text' in post) and ('http' in post['full_text']):
                    pos = post['full_text'].find('http')
                    posF = post['full_text'].find(' ', pos + 1)
                    result = post['full_text'][pos:posF+1]
            # elif ('url' in post['user']['entities']['url']
            #       and (post['user']['entities']['url']['urls'])):
            #     result = post['user']['entities']['url']['urls'][0]['expanded_url']
            elif ('media' in entities):
                if (entities['media']):
                    result = entities['media'][0]['expanded_url']

        if not result:
            result = self.getPostUrl(post)
        return result

    def searchApi(self, text):
        print("     Searching in Twitter...")
        logging.info("     Searching in Twitter...")
        res = self.apiCall(self.getClient().search_tweets, query=text)
        # res = self.apiCall(self.getClient().search_all_tweets, query=text)
        # res = self.apiCall(self.getClient().search.tweets, q=text)
        if res:
            return (res.get('statuses', []))

    def get_name(self):
        return "Twitter"

    def get_default_user(self):
        return "fernand0"

    def get_default_post_type(self):
        return "posts"

    def register_specific_tests(self, tester):
        tester.add_test("Search test", self.test_search)

    def get_user_info(self, client):
        me = client.get_me().data
        return f"{me.name} (@{me.username})"

    def get_post_id_from_result(self, result):
        return self.getUrlId(str(result[1]))

    def test_search(self, apiSrc):
        query = input("Enter search query: ").strip()
        if not query:
            print("No query provided")
            return

        results = apiSrc.searchApi(query)
        if results:
            print(f"Found {len(results)} tweets:")
            for i, tweet in enumerate(results[:5]):
                print(f"\n{i+1}. {apiSrc.getPostTitle(tweet)}")
                print(f"   by @{tweet['user']['screen_name']}")
                print(f"   Link: {apiSrc.getPostUrl(tweet)}")
        else:
            print("No results found.")
def main():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    from socialModules.moduleTester import ModuleTester
    
    twitter_module = moduleTwitter()
    tester = ModuleTester(twitter_module)
    tester.run()

if __name__ == '__main__':
    main()
