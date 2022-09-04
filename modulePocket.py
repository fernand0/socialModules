#!/usr/bin/env python

import configparser
import os

from pocket import Pocket, PocketException

from configMod import *
from moduleContent import *
from moduleQueue import *

class modulePocket(Content,Queue):

    def __init__(self):
        super().__init__()
        self.postaction='archive'

    def getKeys(self, config):
        logging.debug(f"Nick: {self.user}")
        consumer_key = config.get(self.user, "consumer_key")
        try: 
            access_token = config.get(self.user, "access_token")
        except:
            logging.info(f"Needs authorization")
            self.authorize()
            access_token = config.get(self.user, "access_token")
        logging.debug(f"Consumer: {consumer_key}")

        return(consumer_key, access_token)

    def authorize(self):
        #url = f"https://getpocket.com/v3/oauth/request"
        config = configparser.ConfigParser(interpolation=None)
        fileConfig = f"{CONFIGDIR}/.rss{self.service}"
        config.read(fileConfig)
        name = self.user
        try:
            # Based on https://github.com/dogsheep/pocket-to-sqlite/blob/main/pocket_to_sqlite/cli.py
            consumer_key = config.get(name, 'consumer_key')
            response = requests.post( 
                "https://getpocket.com/v3/oauth/request", 
                { "consumer_key": consumer_key, 
                  "redirect_uri": "https://getpocket.com/connected_applications", 
                },
            )
            request_token = dict(urllib.parse.parse_qsl(response.text))["code"]
            print("Visit this page and sign in with your Pocket account:\n")
            print("https://getpocket.com/auth/authorize?request_token={}&redirect_uri={}\n".format(
                request_token, "https://getpocket.com/connected_applications"
                )
            )
            input("Once you have signed in there, hit <enter> to continue")
            # Now exchange the request_token for an access_token
            response2 = requests.post( 
                   "https://getpocket.com/v3/oauth/authorize", 
                   {"consumer_key": consumer_key, "code": request_token},
            )
            codes = dict(urllib.parse.parse_qsl(response2.text))
            access_token = codes['access_token']
            config.set(name, 'access_token', access_token)
            #import shutil
            shutil.copyfile(fileConfig, '{}.bak'.format(fileConfig))
            with open(fileConfig, 'w') as configfile:
                config.write(configfile)

        except:
            print(f"Something failed")
 
    def initApi(self, keys):
        consumer_key, access_token = keys
        client = Pocket(consumer_key=consumer_key, access_token=access_token)
        return client

    def setApiPosts(self):
        posts = []
        try:
            dictPosts = self.client.retrieve()
            dictPosts = dictPosts['list']
        except PocketException as exc:
            logging.warning(f"setApiPosts generated an exception: {exc}")
            dictposts = []
        for post in dictPosts:
            posts.append(dictPosts[post])

        return(posts[:100])

    def processReply(self, reply):
        res = ''
        if reply:
            idPost = self.getPostId(reply)
            title = self.getPostTitle(reply)
            res = f"{title} https://getpocket.com/read/{idPost}"
        logging.info(f"     Res: {res}")
        return(res)

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            post, link, comment = args
            print(f"args: {args} in {self}")
        if kwargs:
            more = kwargs
            print(f"postData: {more} in {self}")

        tags = []
        if comment:
            tags = [comment, ]
        print(f"ll: {link}")
        # This belongs here?
        if not link.startswith('http'):
            logging.warning(f"Link that does not stat with < {link}")
            pos = link.find('http')
            link = link[pos:]

            pos = link.find(' ')
            if pos >=0:
                # Sometimes there are two links or something after the link
                link=link[:pos]
        try:
            res = self.getClient().add(link, tags=tags)
        except PocketException as exc:
            logging.warning(f"publishApiPosts generated an exception: {exc}")
            res = "Fail!"

        return res

    # def publishh(self, j):
    #     # This does not belong here
    #     logging.info("...Publishing %d"% j)
    #     #post = self.obtainPostData(j)
    #     #logging.info("Publishing %s"% post[0])
    #     update = ''
    #     title = self.getTitle(j)
    #     logging.info("Title: %s" % str(title))
    #     url = self.getLink(j)
    #     logging.info("Url: %s" % str(url))

    #     if self.getProgram():
    #         logging.info("getProgram")
    #         for profile in self.getSocialNetworks():
    #             nick = self.getSocialNetworks()[profile]
    #             logging.info("Social: {} Nick: {}".format(profile, nick))
    #             if ((profile[0] in self.getProgram()) or
    #                     (profile in self.getProgram())):
    #                 logging.info("Social: {} Nick: {}".format(profile, nick))
    #                 lenMax = self.len(profile)
    #                 socialNetwork = (profile, nick)

    #                 listP = self.cache[socialNetwork].setPosts()
    #                 listP = self.cache[socialNetwork].getPosts()
    #                 listPsts = self.obtainPostData(j)
    #                 listP = listP + [listPsts]
    #                 self.cache[socialNetwork].posts = listP
    #                 update = update + self.cache[socialNetwork].updatePostsCache()
    #                 logging.info("Uppdate: {}".format(update))
    #                 update = update + '\n'

    #     if  not self.getProgram(): #not self.getBuffer() and
    #         logging.info("Not getBuffer, getProgram {}".format(self.getSocialNetworks()))
    #         return ""
    #         delayedBlogs = []
    #         nowait = True
    #         for profile in self.getSocialNetworks():
    #             nick = self.getSocialNetworks()[profile]
    #             logging.info("Social: {} Nick: {}".format(profile, nick))
    #             listPosts = [ post ]
    #             socialNetwork = (profile, nick)
    #             link = self.addNextPosts(listPosts, socialNetwork)
    #             delayedBlogs.append((self, socialNetwork, 1, nowait, 0))

    #             import concurrent.futures
    #             import moduleSocial
    #             import time
    #             with concurrent.futures.ThreadPoolExecutor(
    #                     max_workers=len(delayedBlogs)) as executor:
    #                 delayedPosts = {executor.submit(moduleSocial.publishDelay,
    #                     *args):
    #                     args for args in delayedBlogs}
    #                 time.sleep(5)

    #                 for future in concurrent.futures.as_completed(delayedPosts):
    #                     dataBlog = delayedPosts[future]
    #                     try:
    #                         res = future.result()
    #                         if res:
    #                             print("  Published: %s"% str(res))
    #                             if not dataBlog[0].getProgram():
    #                                 posL = res.find('http')
    #                                 if posL>=0:
    #                                     link = res[posL:]
    #                                     if link:
    #                                         socialNetwork = dataBlog[1]
    #                                         updateLastLink(dataBlog[0].getUrl(),
    #                                                 link, socialNetwork)

    #                     except Exception as exc:
    #                         print('{} generated an exception: {}'.format(
    #                             str(dataBlog), exc))

    def archive(self, j):
        logging.info("Archiving %d"% j)
        client = self.client
        post = self.getPost(j)
        title = self.getPostTitle(post)
        idPost = self.getPostId(post)
        logging.info(f"Post {post}")
        logging.info(f"Title {title}")
        logging.info(f"Id {idPost}")
        try:
            res = client.archive(int(idPost))
            res = client.commit()
            logging.info("Post id res {}".format(str(res)))
            logging.info("Post id res {}".format(str(res["action_results"])))
            if res['action_results']:
                rep = f"Archived {title}"
                self.posts = self.posts[:j] + self.posts[j+1:]
            else:
                rep = "Fail!"
        except:
            logging.warning("Archiving failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            rep = "Fail"
        return rep

    def delete(self, j):
        logging.info("Deleting %d"% j)
        client = self.client
        post = self.getPost(j)
        title = self.getPostTitle(post)
        logging.info("Post {}".format(str(post)))
        logging.info("Title {}".format(title))
        res = client.delete(int(self.getPostId(post)))
        res = client.commit()
        logging.info("Post id res {}".format(str(res)))
        logging.info("Post id res {}".format(str(res["action_results"])))
        if res['action_results']:
            rep = f"Deleted {title}"
        else:
            rep = "Fail!"
        return rep

    def getPostTitle(self, post):
        title = ''
        if 'resolved_title' in post:
            title = post['resolved_title']
            if not title and ('given_title' in post):
                title = post['given_title']
        #elif 'item' in post:
        #    if 'title' in post['item']:
        #        title = (post['item']['title'])
        if not title:
            title = self.getPostLink(post)
        return title

    def getPostId(self, post):
        idPost = post.get('item_id','')
        return idPost

    def getPostLink(self, post):
        link = ''
        if 'resolved_url' in post:
            link = post['resolved_url']
            if not link and 'given_url' in post:
                link = post['given_url']
        return link

    # def extractDataMessage(self, i):
    #     logging.info("Service %s"% self.service)
    #     (theTitle, theLink, firstLink, theImage, theSummary,
    #             content, theSummaryLinks, theContent, theLinks, comment) = (
    #                     None, None, None, None, None,
    #                     None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         theTitle = self.getTitle(i)
    #         theLink = self.getLink(i)

    #         theLinks = None
    #         content = None
    #         theContent = None
    #         firstLink = theLink
    #         theImage = None
    #         theSummary = None

    #         theSummaryLinks = None
    #         comment = None

    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules('Blog43')

    testingPosts = True
    if testingPosts: 
        for key in rules.rules.keys(): 
            if ((key[0] == 'pocket')
                    and (key[2] == 'fernand0kobo')): 
                print(f"Key: {key}")

                apiSrc = rules.readConfigSrc("", key, rules.more[key])

                # config = configparser.ConfigParser(interpolation=None)
                # fileConfig = f"{CONFIGDIR}/.rssPocket"
                # config.read(fileConfig)

                # name = "fernand0kobo"
                # redirect_uri = config.get(name, 'redirect_uri')
                # consumer_key = config.get(name, 'consumer_key')
                # print(f"Cons: {consumer_key}")
                
                # # Based on https://github.com/dogsheep/pocket-to-sqlite/blob/main/pocket_to_sqlite/cli.py
                # response = requests.post( 
                #         "https://getpocket.com/v3/oauth/request", 
                #         { "consumer_key": consumer_key, 
                #           "redirect_uri": "https://getpocket.com/connected_applications", 
                #         },
                #     )
                # request_token = dict(urllib.parse.parse_qsl(response.text))["code"]
                # print("Visit this page and sign in with your Pocket account:\n")
                # print("https://getpocket.com/auth/authorize?request_token={}&redirect_uri={}\n".format(
                #     request_token, "https://getpocket.com/connected_applications"
                #     )
                # )
                # input("Once you have signed in there, hit <enter> to continue")
                # # Now exchange the request_token for an access_token
                # response2 = requests.post( 
                #        "https://getpocket.com/v3/oauth/authorize", 
                #        {"consumer_key": consumer_key, "code": request_token},
                # )
                # print(f"res: {response2.text}")
                # codes = dict(urllib.parse.parse_qsl(response2.text))

                # print(codes)
                # #codes["consumer_key"] = consumer_key
                # #print(codes)
                apiSrc.setPosts()
                print(apiSrc.getPosts())

    return
 
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs2')

    import modulePocket

    p = modulePocket.modulePocket()

    p.setClient('fernand0')
    p.setPostsType('posts')

    p.setPosts()
    print(p.getPosts())
    return

    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')
    sys.exit()

    for i, post in enumerate(p.getPosts()):
        print(i, p.getPostTitle(post), p.getPostLink(post))

    sys.exit()
    #i=7
    #print(i,p.getTitle(i))

    p.setSocialNetworks(config)
    print(p.getSocialNetworks())
    p.publish(99)

    sys.exit()

    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')

if __name__ == '__main__':
    main()

