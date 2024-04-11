#!/usr/bin/env python

import configparser
import sys
import dateparser
import dateutil
from atproto import Client, models

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

class moduleBlsk(Content): #, Queue):

    def getKeys(self, config):
        USER = config.get(self.user, "user")
        PASSWORD = config.get(self.user, "password")

        return (USER, PASSWORD)

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.base_url = 'https://bsky.app'
        self.url = f"{self.base_url}/profile/{self.user}"
        logging.info("Initializing API")
        # self.authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        # client = Twitter(auth=self.authentication)

        client = Client()
        try:
            profile = client.login(keys[0], keys[1])
            if hasattr(client, 'me'):
                self.me = client.me
            else:
                self.me = None
        except:
            res = self.report(self.indent, 'Error in initApi', 
                              '', sys.exc_info())
            client = None
        self.api = client
        if hasattr(client, 'app'):
            client = client.app.bsky.feed
        return client


    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        posts = []

        posts, error = self.apiCall('get_timeline')

        if not error:
            posts = posts['feed']


        return posts

    def setApiFavs(self):
        posts = []

        posts, error = self.apiCall('get_actor_likes', 
                                    params={'actor':self.me.did})

        if not error:
            posts = posts['feed']

        return posts

    def getPostTitle(self, post):
        title = ''
        try:
            title = post.post.record.text
        except:
            title = ''
        return title

    def getPostUrl(self, post):
        idPost = self.getPostId(post)
        msgLog = f"{self.indent} getPostUrl: {post}"
        logMsg(msgLog, 2, 0)
        if idPost:
            res = f'{self.base_url}/profile/{self.getPostHandle(post)}/post/{idPost}'
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
        result = post.post.record.text
        # if 'full_text' in post:
        #     result = post.get('full_text')
        return result

    def getPostContentLink(self, post):
        result = ''
        logging.debug(f"Record: {post.post.record}")
        if hasattr(post.post.record, 'uri'):
            logging.debug(f"Uri")
            result = post.post.record.uri
        elif (hasattr(post.post.record, 'facets') 
              and post.post.record.facets 
              and hasattr(post.post.record.facets[0].features[0], 'uri')):
            logging.debug(f"Facets > Uri")
            result = post.post.record.facets[0].features[0].uri
        elif (hasattr(post.post.record, 'embed')
              and hasattr(post.post.record.embed, 'external')
              and hasattr(post.post.record.embed.external, 'uri')):
            logging.debug(f"Embed > Uri")
            result = post.post.record.embed.external.uri

        return result
 
    def publishApiImage(self, *args, **kwargs):
        res = None
        if len(args) == 2:
            post, imageName = args
            more = kwargs
            if imageName and os.path.exists(imageName):
                with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

                try:
                    imgAlt = None
                    if 'alt' in more:
                        logging.debug(f"Setting up alt: {more['alt']}"
                                      f" in image {imageName}")
                        imgAlt = more['alt']
                    res, error = self.apiCall('send_image', api=self.api,
                                              text=post, 
                                              image=imagedata, 
                                              image_alt=imgAlt)

                except: 
                    res = self.report(self.service, post, 
                                      imageName, sys.exc_info())
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

        res = None
        # TODO

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

        facets =  []
        if link:
            title = title[:(300 - (len(link)+1))]

            embed_external = models.AppBskyEmbedExternal.Main( 
                              external=models.AppBskyEmbedExternal.External( 
                                title=title, 
                                description='', 
                                uri=link,
                            )
                        )
            # facets.append(models.AppBskyRichtextFacet.Main( 
            #     features=[models.AppBskyRichtextFacet.Link(uri=link)],
            #     index=models.AppBskyRichtextFacet.ByteSlice(
            #         byte_start=len(title)+1, 
            #         byte_end=len(title)+len(link)+1),
            #     )
            # )

            title = title+" " + link
            #embed_post = models.AppBskyEmbedRecord.Main(record=models.create_strong_ref(post_with_link_card))
        else:
            embed_external = None


        msgLog = f"{self.indent}Publishing {title} ({len(title)}"
        logMsg(msgLog, 2, 0) 
        client = self.api
        #try:
        res, error = self.apiCall('send_post', api=client, 
                               text=title, embed=embed_external)
        #    # res = client.com.atproto.repo.create_record(
        #    #         models.ComAtprotoRepoCreateRecord.Data(
        #    #          repo=client.me.did, 
        #    #          collection=models.ids.AppBskyFeedPost, 
        #    #          record=models.AppBskyFeedPost.Main(
        #    #              created_at=client.get_current_time_iso(), 
        #    #              text=title, facets=facets),
        #    #          )
        #    #         )
        #except: 
        #    res = self.report(self.service, 
        #                        f"{title} {link}", title, sys.exc_info())

        msgLog = f"{self.indent}Res: {res} "
        logMsg(msgLog, 2, 0)
        return res

    def deleteApiPosts(self, idPost): 
        res = None
        res, error = self.apiCall('delete_post', self.api,  post_uri=idPost)

        return (res)

    def deleteApiFavs(self, idPost): 
        res = None
        logging.info(f"Deleting: {idPost}")
        res = self.api.unlike(idPost)
        # res = self.apiCall(self.getClient().favorites.destroy, _id=idPost)
        return (res)

    def getPostHandle(self, post):
        handle = post.post.author.handle
        return handle

    def getPostId(self, post):
        idPost = ''
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            if self.getPostsType() == 'favs':
                idPost = post.post.viewer.like
            else:
                idPost = post.post.uri
                idPost = idPost.split('/')[-1]

        return idPost

    def processReply(self, reply):
        res = ''
        msgLog = f"{self.indent}Reply: {reply}"
        logMsg(msgLog, 1, 1)
        origReply = reply
        if reply:
            #if isinstance(reply, str) and 'Fail' in reply:
                res = reply
            # else:
            #     res = "OK!"
        else:
            res = "Fail!"

        return (res)


def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    testingPostDelete = True
    if testingPostDelete:
        res = apiSrc.publishPost("prueba","https://elmundoesimperfecto.com/", "")
        print(f"Published: {res}")
        idPost = res.uri
        delete = input(f"Delete (write the id {idPost})? ")
        if delete:
            print(f"Deleting: {apiSrc.deleteApiPosts(delete)}")
        else:
            print(f"Deleting: {apiSrc.deleteApiPosts(idPost)}")

        return

    testingPosts = False
    if testingPosts:
        apiSrc.setPosts()
        for i,post in enumerate(apiSrc.getPosts()):
            print(f"Post {i}): {post.post}")
            print(f"id {post.post.uri}")
            print(f"Post {i}): {apiSrc.getPostUrl(post)}")
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

    testingPosts = False
    if testingPosts:
        print("Testing Posts")
        key = ('twitter', 'set', 'fernand0', 'posts')
        logging.debug(f"Key: {key}")
        apiSrc = rules.readConfigSrc("", key, None)
        apiSrc.setPosts()
        posts = apiSrc.getPosts()
        # print(f"Tweets: {posts}")
        for tweet in posts:
            print(f"Tweet: {tweet}")
            print(f"Tweet: {tweet.entities}")
            print(f" -Title {apiSrc.getPostTitle(tweet)}")
            print(f" -Link {apiSrc.getPostLink(tweet)}")
            print(f" -Content link {apiSrc.getPostContentLink(tweet)}")
            print(f" -Post link {apiSrc.extractPostLinks(tweet)}")
            print(f"Len: {len(apiSrc.getPosts())}")
        return

    testingFav = False
    if testingFav:
        logging.info(f"Testing Favs")
        key = ('twitter', 'set', 'fernand0', 'favs')
        logging.debug(f"Key: {key}")
        apiSrc = rules.readConfigSrc("", key, None)
        apiSrc.setPostsType('favs')

        print(f"User: {apiSrc.user}")
        apiSrc.setPosts()
        posts = apiSrc.api.get_favorites()
        print(f"Posts: {posts}")
        for i, tweet in enumerate(apiSrc.getPosts()):
            print(f" -Title {apiSrc.getPostTitle(tweet)}")
            print(f" -Link {apiSrc.getPostLink(tweet)}")
            print(f" -Content link {apiSrc.getPostContentLink(tweet)}")
            print(f" -Post link {apiSrc.extractPostLinks(tweet)}")
            print(f" -Created {tweet.get('created_at')}")
            # parsedDate = dateutil.parser.parse(
            #     apiSrc.getPostApiDate(tweet))
            # print(
            #     f" -Created {parsedDate.year}-{parsedDate.month}-{parsedDate.day}")
        print(f"Len: {len(apiSrc.getPosts())}")
        return

    testingPost = False
    if testingPost:
        print("Testing Post")
        # for key in rules.rules.keys():
        #     if ((key[0] == 'twitter')
        #         and ('reflexioneseir' in key[2])
        #         and (key[3] == 'posts')):
        #             break
        key = ('twitter', 'set', 'fernand0', 'posts')
        print(key)
        print(rules.more[key])
        # more = {'url': 'https://twitter.com/fernand0', 'service': 'twitter', 'posts': 'posts', 'direct': 'twitter', 'twitter': 'fernand0', 'time': '23.1', 'max': '1', 'hold': 'no'}

        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        title = "Test"
        link = "https://twitter.com/fernand0Test"
        print(f"Publishing {apiSrc.publishPost(title, link, '')}")
        delete = input("Delete (write the id)? ")
        if delete:
            print(f"Deleting: {apiSrc.deleteApiPosts(delete)}")

        return

    testingDM = False
    if testingDM:
        key =  ('twitter', 'set', 'mbpfernand0', 'posts')

        apiSrc = rules.readConfigSrc("", key, None)

        print(f"Direct: {apiSrc.api.get_direct_messages()}")
        return

    testingPostImages = True
    if testingPostImages:
        image = '/tmp/2023-07-16_image.svg'
        # Does not work with svg
        image = '/tmp/2023-08-04_image.png'

        title = 'Prueba imagen'
        altText = "Texto adicional"
        key =  ('twitter', 'set', 'fernand0', 'posts')

        apiSrc = rules.readConfigSrc("", key, None)
        print(f"Testing posting with images")
        res = apiSrc.publishImage("Prueba imagen", image, alt= altText)
        print(f"Res: {res}")

        return

        print(f"Res: {apiSrc.publishApiImage(title, image, alt=altText)}")

        return

    testingRT = False
    if testingRT:
        print("Testing RT")
        title= ''
        link ='https://twitter.com/fernand0/status/1141952205702029312'
        print(f"Res: {apiSrc.publishApiRT(title, link, '')}")
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

    testingDeleteFavs = False
    if testingDeleteFavs:
        for key in rules.rules.keys():
            if ((key[0] == 'twitter')
                and ('fernand0Test' in key[2])):
                #and (key[3] == 'favs')):
                    break
        apiSrc = rules.readConfigSrc("", key, rules.more[key])
        rules.more['posts'] = 'favs'
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
