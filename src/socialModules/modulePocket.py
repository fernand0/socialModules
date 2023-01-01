#!/usr/bin/env python

import configparser
import os

from pocket import Pocket, PocketException

from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleQueue import *


class modulePocket(Content,Queue):

    def getKeys(self, config):
        if self.user.startswith('@'):
            #FIXME: Maybe we should avoid this in the configuration file
            self.user = self.user[1:]
        consumer_key = config.get(self.user, "consumer_key")
        try:
            access_token = config.get(self.user, "access_token")
        except:
            msgLog = (f"Needs authorization")
            logMsg(msgLog, 3, 0)
            self.authorize()
            access_token = config.get(self.user, "access_token")

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
        msgLog = (f"{self.indent} service {self.service} Start initApi {self.user}")
        logMsg(msgLog, 2, 0)
        self.postaction='archive'

        consumer_key, access_token = keys
        client = Pocket(consumer_key=consumer_key, access_token=access_token)
        msgLog = (f"{self.indent} service {self.service} End initApi")
        logMsg(msgLog, 2, 0)
        return client

    def setApiPosts(self):
        posts = []
        try:
            dictPosts = self.client.retrieve()
            dictPosts = dictPosts['list']
        except PocketException as exc:
            msgLog = (f"setApiPosts generated an exception: {exc}")
            logMsg(msgLog, 3, 0)
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
        msgLog=(f"     Res: {res}")
        logMsg(msgLog, 2, 0)
        return(res)

    def publishApiPost(self, *args, **kwargs):
        comment = ''
        link = ''
        title = ''
        if args and len(args) == 3:
            post, link, comment = args
            msgLog=(f"args: {args} in {self}")
            logMsg(msgLog, 2, 0)
        if kwargs:
            more = kwargs
            api = more['api']
            msgLog=(f"postData: {more} in {self}")
            logMsg(msgLog, 2, 0)
            post = more['post']
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment= ''

        tags = []
        if comment:
            tags = [comment, ]
        # logging.info(f"ll: {link}")
        # This belongs here?
        if not link.startswith('http'):
            msgLog = (f"Link that does not stat with < {link}")
            logMsg(msgLog, 3, 0)
            pos = link.find('http')
            link = link[pos:]

            pos = link.find(' ')
            if pos >=0:
                # Sometimes there are two links or something after the link
                link=link[:pos]
        try:
            msgLog = (f"Link: {link}")
            logMsg(msgLog, 2, 0)
            res = self.getClient().add(link, tags=tags)
        except PocketException as exc:
            msgLog = (f"publishApiPosts generated an exception: {exc}")
            logMsg(msgLog, 3, 0)
            res = "Fail!"

        return res

    def archiveId(self, idPost):
        client = self.client
        try:
            res = client.archive(int(idPost))
            res = client.commit()
            # logging.info("Post id res {}".format(str(res)))
            # logging.info("Post id res {}".format(str(res["action_results"])))
            if res['action_results']:
                rep = f"Archived {idPost}"
            else:
                rep = "Fail!"
        except:
            self.report("Archiving failed!", '', '', sys.exc_info()[0])
            rep = "Fail"

        return rep

    def archive(self, j):
        msgLog = ("Archiving %d"% j)
        logMsg(msgLog, 1, 0)
        post = self.getPost(j)
        title = self.getPostTitle(post)
        idPost = self.getPostId(post)
        logging.info(f"Post {post}")
        logMsg(msgLog, 2, 0)
        logging.info(f"Title {title}")
        logMsg(msgLog, 2, 0)
        logging.info(f"Id {idPost}")
        logMsg(msgLog, 2, 0)
        rep = self.archiveId(idPost)
        msgLog = (f"Rep: {rep}")
        logMsg(msgLog, 2, 0)
        if 'Archived' in rep:
            self.posts = self.posts[:j] + self.posts[j+1:]
        return rep

    def delete(self, j):
        msgLog = ("Deleting %d"% j)
        logMsg(msgLog, 1, 0)
        client = self.client
        post = self.getPost(j)
        title = self.getPostTitle(post)
        msgLog = ("Post {}".format(str(post)))
        logMsg(msgLog, 2, 0)
        msgLog = ("Title {}".format(title))
        logMsg(msgLog, 2, 0)
        res = client.delete(int(self.getPostId(post)))
        res = client.commit()
        # logging.info("Post id res {}".format(str(res)))
        # logging.info("Post id res {}".format(str(res["action_results"])))
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

    def setMax(self, maxVal):
        self.max = 100

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

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    testingPosts = False
    if testingPosts:
        for key in rules.rules.keys():
            if ((key[0] == 'pocket')
                    and (key[2] == 'fernand0kobo')):
                print(f"Key: {key}")

                apiSrc = rules.readConfigSrc("", key, rules.more[key])

                apiSrc.setPosts()
                print(apiSrc.getPosts())
                for post in apiSrc.getPosts():
                        print(f"Title: {apiSrc.getPostTitle(post)}")
        return

    PATH = '/tmp/kobo'
    try:
        os.mkdir(PATH)
    except FileExistsError:
        logging.info(f"Creation of the directory {PATH} failed. "
                     f"It exists")

    testingPostsArticle = True
    if testingPostsArticle:
        for key in rules.rules.keys():
            print(f"Key: {key}")
            if ((key[0] == 'pocket')
                    and (key[2] == 'fernand0kobo')):
                print(f"Key: {key}")

                apiSrc = rules.readConfigSrc("", key, rules.more[key])

                apiSrc.setPosts()
                print(apiSrc.getPosts())
                for pos, post in enumerate(apiSrc.getPosts()):
                    title = apiSrc.getPostTitle(post)
                    print(f"Title: {title}")
                    if ('is_article' in post) and post['is_article'] == '0':
                        link = apiSrc.getPostLink(post)
                        print(f"Title: {title}")
                        print(f"Link: {link}")
                        import requests
                        from readabilipy import simple_json_from_html_string
                        req = requests.get(link)
                        article = simple_json_from_html_string(req.text,
                                                               use_readability=True)
                        if not article['content']:
                            continue
                        from ebooklib import epub
                        book = epub.EpubBook()

                        book.set_title(title)
                        idPost = post['item_id']
                        book.set_identifier(idPost)
                        c = epub.EpubHtml(title='Page',
                                          file_name='page.xhtml', lang='en')
                        c.content= article['content']
                        book.add_item(c)
                        book.add_item(epub.EpubNcx())
                        book.add_item(epub.EpubNav())
                        book.spine = ['nav', c]
                        name = re.sub(r'[^a-zA-Z0-9]+', '-', title)
                        epub.write_epub(f"{PATH}/{post['time_added']}_{name}.epub",
                                        book, {})
                        input("Archive? ")
                        apiSrc.archiveId(idPost)





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

