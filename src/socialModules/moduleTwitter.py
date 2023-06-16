#!/usr/bin/env python

import configparser
import sys

import dateparser
import dateutil
import twitter
from twitter import *

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

# pip install twitter
# https://pypi.python.org/pypi/twitter
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
        # FIXME: Do we call this method directly?
        self.base_url = 'https://twitter.com'
        self.url = f"{self.base_url}/{self.user}"
        logging.info("Initializing API")
        self.authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        client = Twitter(auth=self.authentication)
        return client

    def apiCall(self, command, **kwargs):
        msgLog = (f"   Calling: {command.uriparts} with arguments {kwargs}")
        logMsg(msgLog, 2, 0)
        res = []

        try:
            logging.info(f"Command: {command}")
            res = command(**kwargs)
            logging.info(f"Res: {res}")

        except twitter.api.TwitterHTTPError as twittererror:
            logging.info(f"Error: {twittererror}")
            for error in twittererror.response_data.get("errors", []):
                logging.info(f"      Error code: "
                             f"{error.get('code', None)}")

                res = self.report(
                    self.getService(), kwargs, '', sys.exc_info())
                res = f"Fail! {res}"
        return res

    def setApiPosts(self):
        try:
            posts = self.apiCall(self.getClient().statuses.user_timeline,
                 count=100, tweet_mode='extended')
        except:
             logging.info(self.report('Twitter', text, sys.exc_info()))
             posts = []

        return posts

        # try:
        #     posts = self.getClient().statuses.user_timeline(count=100)
        # except twitter.api.TwitterHTTPError as twittererror:
        #     for error in twittererror.response_data.get("errors", []):
        #         logging.info(f"      Error code: "
        #                      f"{error.get('code', None)}")

        # return posts

    def setApiFavs(self):
        posts = self.apiCall(self.getClient().favorites.list,
                tweet_mode='extended')

        return posts
        # posts = self.getClient().favorites.list(tweet_mode='extended')
        # # count=100)
        # # https://stackoverflow.com/questions/38717816/twitter-api-text-field-value-is-truncated
        # return posts

    def processReply(self, reply):
        res = ''
        if reply:
            if not ('Fail!' in reply):
                idPost = self.getPostId(reply)
                title = reply.get('title')
                res = f"{title} https://twitter.com/{self.user}/status/{idPost}"
            else:
                res = reply
                if (('You have already retweeted' in res) or
                        ('Status is a duplicate.' in res)):
                    res = res + ' SAVELINK'
        return (res)

    def publishApiImage(self, *args, **kwargs):
        logging.debug(f"{args} Len: {len(args)}")
        if len(args) == 2:
            post, imageName = args
            more = kwargs
            if imageName:
                with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

                try:
                    # t_upload = Twitter(domain='upload.twitter.com',
                     #                  auth=self.authentication)
                    self.getClient().domain = 'upload.twitter.com'
                    # FIXME Is this really needed?
                    id_img1 = self.getClient().media.upload(media=imagedata)['media_id_string']
                    print(f"Id: {id_img1}")
                    if 'alt' in more:
                        # t_upload.media.metadata.create(_json={"media_id": id_img1,
                        self.getClient().media.metadata.create(_json={"media_id": id_img1, "alt_text": {"text": more['alt']}
                                                              })
                    self.getClient().domain = 'api.twitter.com'
                    res = self.getClient().statuses.update(status=post,
                                                           media_ids=id_img1)
                    # if 'alt' in more:
                    #     # t_upload.media.metadata.create(_json={"media_id": id_img1,
                    #     self.getClient().media.metadata.create(_json={"media_id": id_img1,
                    #                                           "alt_text": {"text": more['alt']}
                    #                                           })
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

        logging.debug("     Retweeting: %s" % post)
        res = 'Fail!'
        if 'twitter' in link:
            res = self.apiCall(self.getClient().statuses.retweet._id,
                    _id=idPost)
            # try:
            #     res = self.getClient().statuses.retweet._id(_id=idPost)
            #     #         result = t.statuses.retweet._id(_id=tweet['id'])
            # except twitter.api.TwitterHTTPError as twittererror:
            #     for error in twittererror.response_data.get("errors", []):
            #         logging.info("      Error code: %s" %
            #                      error.get("code", None))
            #     res = self.report('Twitter', post, link, sys.exc_info())
        else:
            res = "Fail! Link {link} is not a tweet"

        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        title = self.addComment(title, comment)

        logging.info(f"Tittt: {title} {link} {comment}")
        logging.info(f"Tittt: {link and ('twitter' in link)}")
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

            logging.debug(f"     Publishing: {title}")
            res = self.apiCall(self.getClient().statuses.update,
                    status=title)
            logging.debug(f"     Res: {res}")

        return res

    def deleteApiPosts(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        res= self.apiCall(self.getClient().statuses.destroy, _id=idPost)
        logging.debug(f"Res: {res}")
        return (res)

    def deleteApiFavs(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        res = self.apiCall(self.getClient().favorites.destroy, _id=idPost)
        return (res)

    def getPostId(self, post):
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            idPost = post.get('id')
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


    def getPostTitle(self, post):
        msgLog = (f"{self.indent} Postttt: {post}")
        logMsg(msgLog, 2, 0)
        title = post.get('text')
        if not title:
            title = post.get('full_text')
        # if 'http' in title:
            # title = title.split('http')[0]
        return title

    def getPostUrl(self, post):
        idPost = post.get('id_str', '')
        msgLog = f"{self.indent} getPostUrl: {post}"
        logMsg(msgLog, 2, 0)
        if idPost:
            res = f'{self.base_url}/{self.user}/status/{idPost}'
        else:
            res = ''
        return res

    def getPostLink(self, post):
        # FIXME: Are you sure? (inconsistent)
        if self.getPostsType() == 'favs':
            content, link = self.extractPostLinks(post)
        else:
            link = self.getPostUrl(post)
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = ''
        if 'full_text' in post:
            result = post.get('full_text')
        return result

    def getPostContentLink(self, post):
        result = ''
        if ('urls' in post['entities']):
            if post['entities']['urls']:
                if 'expanded_url' in post['entities']['urls'][0]:
                    result = post['entities']['urls'][0]['expanded_url']
            elif ('full_text' in post) and ('http' in post['full_text']):
                pos = post['full_text'].find('http')
                posF = post['full_text'].find(' ', pos + 1)
                result = post['full_text'][pos:posF+1]
        elif ('url' in post['user']['entities']['url']
              and (post['user']['entities']['url']['urls'])):
            result = post['user']['entities']['url']['urls'][0]['expanded_url']
        elif ('media' in post['entities']):
            if (post['entities']['media']):
                result = post['entities']['media'][0]['expanded_url']

        if not result:
            result = self.getPostUrl(post)
        return result

    def searchApi(self, text):
        print("     Searching in Twitter...")
        logging.info("     Searching in Twitter...")
        res = self.apiCall(self.getClient().search.tweets, q=text)
        if res:
            return (res.get('statuses', []))

        # try:
        #     res = self.getClient().search.tweets(q=text)
        #     if res:
        #         logging.debug("Res: %s" % res)
        #         return (res.get('statuses'))
        # except:
        #     return (self.report('Twitter', text, sys.exc_info()))

def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()
    src, more = rules.selectRule('twitter', 'kk')
    print(f"Src: {src}")
    print(f"More: {more}")
    indent = ""
    apiSrc = rules.readConfigSrc(indent, src, more)

    testingPosts = False
    if testingPosts:
        for key in rules.rules.keys():
            print(f"Key: {key}")
            if ((key[0] == 'twitter')
                    and ('reflexioneseir' in key[2])
                    and (key[3] == 'posts')):
                print("Testing Posts")
                apiSrc.setPosts()
                tweet = apiSrc.getPosts()[0]
                tweet = apiSrc.getNextPost()
                print(f"Tweet: {tweet}")
                print(f" -Title {apiSrc.getPostTitle(tweet)}")
                print(f" -Link {apiSrc.getPostLink(tweet)}")
                print(f" -Content link {apiSrc.getPostContentLink(tweet)}")
                print(f" -Post link {apiSrc.extractPostLinks(tweet)}")
                print(f"Len: {len(apiSrc.getPosts())}")
        return

    testingFav = False
    if testingFav:
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                    and ('fernand0' in key[2])
                    and (key[3] == 'favs')):
                apiSrc = rules.readConfigSrc("", key, rules.more[key])
                apiSrc.setPosts()
                for i, tweet in enumerate(apiSrc.getPosts()):
                    print(f" -Title {apiSrc.getPostTitle(tweet)}")
                    print(f" -Link {apiSrc.getPostLink(tweet)}")
                    print(f" -Content link {apiSrc.getPostContentLink(tweet)}")
                    print(f" -Post link {apiSrc.extractPostLinks(tweet)}")
                    print(f" -Created {tweet.get('created_at')}")
                    parsedDate = dateutil.parser.parse(
                        apiSrc.getPostApiDate(tweet))
                    print(
                        f" -Created {parsedDate.year}-{parsedDate.month}-{parsedDate.day}")
                print(f"Len: {len(apiSrc.getPosts())}")
        return

    testingPost = True
    if testingPost:
        print("Testing Post")
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                and ('mbpfernand0' in key[2])
                and (key[3] == 'posts')):
                    break
        key = ('twitter', 'set', 'fernand0', 'posts')
        print(key)
        print(rules.more[key])
        # more = {'url': 'https://twitter.com/fernand0', 'service': 'twitter', 'posts': 'posts', 'direct': 'twitter', 'twitter': 'fernand0', 'time': '23.1', 'max': '1', 'hold': 'no'}

        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        title = "Test"
        link = "https://twitter.com/fernand0Test"
        apiSrc.publishPost(title, link, '')
        return

    testingPostImages = False
    if testingPostImages:
        image = '/tmp/prueba.png'
        title = 'Prueba imagen'
        altText = "Texto adicional"
        key =  ('twitter', 'set', 'fernand0Test', 'posts')

        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        print(f"Res: {apiSrc.publishApiImage(title, image, alt=altText)}")

        return

    testingRT = False
    if testingRT:
        print("Testing RT")
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                    and ('reflexioneseir' in key[2])
                    and (key[3] == 'posts')):
                apiNew = rules.readConfigSrc("", key, rules.more[key])

                apiNew.setPosts()
                tweet = apiNew.getPosts()[10]
                idPost = apiNew.getPostId(tweet)
                title = apiNew.getPostTitle(tweet)
                link = apiNew.getPostLink(tweet)
                print(f"Res: {apiSrc.publishApiRT(title, link, '', post=tweet)}")
        return

    testingDelete = False
    if testingDelete:
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                and ('fernand0Test' in key[2])
                and (key[3] == 'posts')):
                    break
        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        apiSrc.setPosts()
        post = apiSrc.getPosts()[0]
        idPost = apiSrc.getPostId(post)
        print(f"Deleting: {apiSrc.deleteApiPosts(idPost)}")
        return

    testingDeleteFavs = True
    if testingDeleteFavs:
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                and ('fernand0' in key[2])
                and (key[3] == 'favs')):
                    break
        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        apiSrc.setPosts()
        post = apiSrc.getPosts()[0]
        idPost = apiSrc.getPostId(post)
        print(f"Deleting: {apiSrc.getPostTitle(post)}")
        print(f"Deleting: {apiSrc.deleteApiFavs(idPost)}")
        return

    testingSearch = False
    if testingSearch:
        print("Testing Search")
        for key in rules.rules.keys():
            print(f"Key: {key}")
            if ((key[0] == 'twitter')
                    and ('fernand0' == key[2])
                    # and (key[3] == 'posts')
                    ):
                break
        apiSrc = rules.readConfigSrc("", key, rules.more[key])

        res = apiSrc.searchApi('tetris')
        print(f"Res: {res}")
        for tweet in res:
            print(f"Title: {apiSrc.getPostTitle(tweet)}")
        return

        myLastLink = 'https://twitter.com/reflexioneseir/status/1235128399452164096'
        myLastLink = 'http://fernand0.blogalia.com//historias/78135'
        i = apiNew.getLinkPosition(myLastLink)
        print(i)
        print(apiNew.getPosts()[i-1])
        print(apiNew.getPostLink(apiNew.getPosts()[i-1]))
        num = 1
        lastLink = myLastLink
        listPosts = apiNew.getNumPostsData(num, i, lastLink)
        print(listPosts)
        return

    sys.exit()

    print("Testing duplicate post")

    res = tw.publishPost("Best Practices for Writing a Dockerfile",
                         "https://blog.bitsrc.io/best-practices-for-writing-a-dockerfile-68893706c3", '')
    print(f"Res: {res}")
    print(f"End Res")
    print(res.find('Status is a duplicate'))
    input("Repeat?")
    res = tw.publishPost("Best Practices for Writing a Dockerfile",
                         "https://blog.bitsrc.io/best-practices-for-writing-a-dockerfile-68893706c3", '')

    sys.exit()
    # print("Testing bad link")
    # res = tw.publishPost("Post MTProto Analysis: Accessible Overview", "https://telegra.ph/LoU-ETH-4a-proof-07-16", '')

    # logging.info(f"Res: {res}")

    # return

    #print("Testing followers")
    # tw.setFriends()
    # sys.exit()

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
    # sys.exit()

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
        print("Title: {}\nLink: {}\nUrl:{}\n".format(title, link, url))
    print(len(tw.getPosts()))

    sys.exit()

    i = 0
    post = tw.getPost(i)
    title = tw.getPostTitle(post)
    link = tw.getPostLink(post)
    url = tw.getPostUrl(post)
    print(post)
    print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
    tw.deletePost(post)
    sys.exit()

    for i, post in enumerate(tw.getPosts()):
        title = tw.getPostTitle(post)
        link = tw.getPostLink(post)
        url = tw.getPostUrl(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
        input("Delete?")
        print("Deleted https://twitter.com/i/status/{}".format(tw.delete(i)))
        import time
        time.sleep(5)

    sys.exit()

    res = tw.search('url:fernand0')

    for tt in res['statuses']:
        # print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(
            tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()


if __name__ == '__main__':
    main()
