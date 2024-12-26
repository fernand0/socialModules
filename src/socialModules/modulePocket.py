#!/usr/bin/env python

import configparser
import os

from pocket import Pocket, PocketException

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class modulePocket(Content): #,Queue):

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
        logging.info("Starting authorize process")
        #url = f"https://getpocket.com/v3/oauth/request"
        config = configparser.ConfigParser(interpolation=None)
        fileConfig = f"{CONFIGDIR}/.rss{self.service}"
        config.read(fileConfig)
        name = self.user
        logging.debug(f"Name: {name}")
        # Based on https://github.com/dogsheep/pocket-to-sqlite/blob/main/pocket_to_sqlite/cli.py
        consumer_key = config.get(name, 'consumer_key')
        redir = config.get(name, 'redirect_uri')
        if not redir:
            redir = "https://getpocket.com/connected_applications"
        try:
            response = requests.post(
                "https://getpocket.com/v3/oauth/request",
                json = { "consumer_key": consumer_key,
                  "redirect_uri": redir,
                },
            )
            request_token = dict(urllib.parse.parse_qsl(response.text))["code"]
            print("Visit this page and sign in with your Pocket account:\n")
            print(f"https://getpocket.com/auth/authorize?"
                  f"request_token={request_token}&redirect_uri={redir}\n")
            input("Once you have signed in there, hit <enter> to continue")
        except: # PocketException as exc:
            msgLog = (f"Authorize request exception: {sys.info_exc()}")
            logMsg(msgLog, 1, 0)

        # Now exchange the request_token for an access_token
        try:
            response2 = requests.post(
                   "https://getpocket.com/v3/oauth/authorize",
                   {"consumer_key": consumer_key, "code": request_token},
            )
            logging.debug(f"Response: {response2}")
            logging.debug(f"Response: {response2.text}")
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
        msgLog = (f"{self.indent} Service {self.service} Start initApi {self.user}")
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
            dictPosts = self.client.retrieve(state="unread", sort="oldest")
            dictPosts = dictPosts['list']
            for post in dictPosts:
                posts.append(dictPosts[post])
        except: # PocketException as exc:
            msgLog = (f"authorize generated an exception: {sys.exc_info()}")
            logging.debug(f"Msggg: {msgLog}")
            self.authorize()
            logMsg(msgLog, 3, 0)
            dictposts = []

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
            msgLog=(f"post: {post} link {link}")
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

        tags = ""
        if comment:
            tags = [comment, ]
        # logging.info(f"ll: {link}")
        # This belongs here?
        if post and not link:
            link = post
        if not link.startswith('http'):
            msgLog = (f"Link that does not start with < {link}")
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
            msgLog = (f"Tags: {tags}")
            logMsg(msgLog, 2, 0)
            res = self.getClient().add(link) #, tags=tags)
        except PocketException as exc:
            msgLog = (f"publishApiPosts generated an exception: {exc}")
            logMsg(msgLog, 3, 0)
            # msgLog = (f"publishApiPosts generated an exception: {exc}")
            # logMsg(msgLog, 3, 0)
            # self.authorize()
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
        # if not title:
        #     title = self.getPostLink(post)
        return title

    def getPostId(self, post):
        idPost = post.get('item_id','')
        return idPost

    def getPostLink(self, post):
        link = ''
        if 'given_url' in post:
            link = post['given_url']
            # if not link and 'given_url' in post:
            #     link = post['given_url']
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
                    and (key[2] == 'fernand0')):
                apiSrc = rules.readConfigSrc(key, rules.more[key])

                try:
                    apiSrc.setPosts()
                except:
                    apiSrc.authorize()
                for post in apiSrc.getPosts():
                        print(f"Title: {apiSrc.getPostTitle(post)}")
        return

    testingPublish = False
    if testingPublish:
        for key in rules.rules.keys():
            if ((key[0] == 'pocket')
                    and (key[2] == 'fernand0')):
                apiSrc = rules.readConfigSrc(key, rules.more[key])
                res = apiSrc.setPosts()
                apiSrc.publishPost('titulo',
                                   'https://github.com/danielbrendel/hortusfox-web',
                                   '')
        return

    testingSlack = False
    if testingSlack:
        api = rules.selectActionInteractive('slack')
        api.setPosts()
        posts = api.getPosts()
        pos = api.getLinkPosition('https://internetdelascosas.xyz/articulo.php?id=1159')
        for key in rules.rules.keys():
            if ((key[0] == 'pocket')
                    and (key[2] == 'fernand0kobo')):
                apiDst = rules.readConfigSrc(key, rules.more[key])
        print(f"Posts: {pos}")
        for post in range(pos+1, len(posts)):
            print(f"Post: {posts[post]}")
            title = api.getPostTitle(posts[post])
            link = api.getPostLink(posts[post])
            apiDst.publishPost(title, link, '')
            import time
            time.sleep(1)

        return


    PATH = '/tmp/kobo'
    try:
        os.mkdir(PATH)
    except FileExistsError:
        logging.info(f"Creation of the directory {PATH} failed. "
                     f"It exists")

    # Moved to a program
    # testingPostsArticle = True
    # if testingPostsArticle:
    #     for key in rules.rules.keys():
    #         if (key
    #             and (key[0] == 'pocket')
    #             and (key[2] == 'fernand0kobo')
    #             ):

    #             apiSrc = rules.readConfigSrc("",key, rules.more[key])

    #             apiSrc.setPosts()
    #             print(f"Posts({len(apiSrc.getPosts())}): {apiSrc.getPosts()}")
    #             for pos, post in enumerate(reversed(apiSrc.getPosts())):
    #                 title = apiSrc.getPostTitle(post)
    #                 print(f"Title: {title}")
    #                 link = apiSrc.getPostLink(post)
    #                 print(f"Link: {link}")
    #                 idPost = post['item_id']
    #                 # if 'word_count' in post:
    #                 #     print(f"Word: {post['word_count']}")
    #                 archive = False
    #                 if (('youtube' in  link) or link.endswith('pdf')):
    #                     archive = True
    #                 elif ((('is_article' in post)
    #                       and (post['is_article'] == '0'))
    #                       # and (post['status'] != '1')
    #                       or (('word_count' in post)
    #                           and (post['word_count'] == '0'))
    #                       or ((title == '') and (not (('word_count' in post))))):
    #                     msg = (f"No data in the article '{title}'")
    #                     print(msg)
    #                     import requests
    #                     from readabilipy import simple_json_from_html_string
    #                     try:
    #                         req = requests.get(link,
    #                                            headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84"})
    #                         error = False
    #                         if req.status_code < 400:
    #                             msg = title
    #                             article = simple_json_from_html_string(req.text,
    #                                                        use_readability=True)
    #                             if not article['content']:
    #                                 print(f"Nottttt")
    #                                 res = ""
    #                                 from playwright.sync_api import sync_playwright
    #                                 with sync_playwright() as p:
    #                                     browser = p.chromium.launch()
    #                                     page = browser.new_page()

    #                                     # Abrir la URL
    #                                     page.goto(link)
    #                                     page.wait_for_timeout(5000)

    #                                     paragraphs = page.locator("p").all_text_contents()
    #                                     for p in paragraphs:
    #                                         res = f"{res}\n {p}"

    #                                 print(f"Res: {res}")

    #                             else:
    #                                 res = article['content']

    #                             if res:
    #                                 from ebooklib import epub
    #                                 book = epub.EpubBook()

    #                                 book.set_title(title)
    #                                 book.set_identifier(idPost)
    #                                 c = epub.EpubHtml(title='Page',
    #                                                   file_name='page.xhtml',
    #                                                   lang='en')
    #                                 c.content= res
    #                                 book.add_item(c)
    #                                 book.add_item(epub.EpubNcx())
    #                                 book.add_item(epub.EpubNav())
    #                                 book.spine = ['nav', c]
    #                                 name = re.sub(r'[^a-zA-Z0-9]+', '-', title)
    #                                 epub.write_epub(f"{PATH}/{post['time_added']}_{name}.epub",
    #                                                 book, {})
    #                                 archive = True
    #                             else:
    #                                 print(f"No content in article")
    #                                 error = True
    #                         else:
    #                             error = True
    #                         if error:
    #                             print(f"Something is wrong "
    #                                   f"{req.status_code}")

    #                             src = rules.selectRule('cache', 'smtp')
    #                             indent = ''
    #                             src = src[0]
    #                             more = None
    #                             indent = ''
    #                             apiAux = rules.readConfigSrc(src, more)
    #                             action =  rules.rules[src][0]
    #                             msgLog = (f"Action: {action}")
    #                             logMsg(msgLog, 2, 0)
    #                             newAction = (action[:3] +
    #                                 ('fernand0Pocket@elmundoesimperfecto.com',))

    #                             apiDst = rules.readConfigDst(indent,
    #                                                          newAction,
    #                                                          more, apiAux)
    #                             msgLog = (f"apiDst: {apiDst}")
    #                             logMsg(msgLog, 2, 0)
    #                             apiDst.publishPost(f"Fail Pocket! {title}",
    #                                                   link, f"{req.text}")
    #                             archive = True
    #                     except:
    #                         print(f"Problem with link: {link}")
    #                 if archive:
    #                     input(f"Archive ({msg})? ")
    #                     apiSrc.archiveId(idPost)

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

