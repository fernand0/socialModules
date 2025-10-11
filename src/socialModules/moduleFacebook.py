#!/usr/bin/env python

import configparser
import sys
from html.parser import HTMLParser

import facebook
from bs4 import BeautifulSoup, Tag

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

# We are using facebook-sdk
# You can find the way to obtain tokens and so on at:
# https://facebook-sdk.readthedocs.io/
#
# Config file
# [Facebook]
# oauth_access_token: #<- We only need this one
# client_token:
# app_token:
# app_id:

class moduleFacebook(Content): #,Queue):

    def getKeys(self, config):
        oauth_access_token = config.get(self.service, "oauth_access_token")
        app_id = config.get(self.service, "app_id")
        client_token = config.get(self.service, "client_token")

        return ((oauth_access_token, app_id, client_token))

    def initApi(self, keys):
        # msgLog = f"{self.indent} initApi {self.service}"
        # logMsg(msgLog, 2, 0)
        self.page = None
        self.oauth_access_token = keys[0]
        self.app_id = keys[1]
        self.client_token = keys[2]
        graph = facebook.GraphAPI(keys[0], version='19.0')
        # msgLog = f"{self.indent} initApi res {graph}"
        # logMsg(msgLog, 2, 0)
        return graph

    def getPage(self):
        return self.page

    def setPage(self, facebookAC='me'):
        perms = ['publish_actions',
                 'manage_pages',
                 'publish_pages',
                 'pages_read_engagement',
                 'pages_manage_posts']
        try:
            pages = self.getClient().get_connections('me', 'accounts')
        except:
            # Not tested
            url = (f"https://graph.facebook.com/oauth/access_token"
                   f"?client_id={self.app_id}"
                   f"&client_secret={self.client_token}"
                   f"&grant_type=client_credentials")
            logging.info(f"Url: {url}")
            import requests
            result = requests.get(url)
            logging.info(f"Result: {result.text}")
            import json
            data = json.loads(result.text)
            self.access_token = data['access_token']
            url2 = (f"https://graph.facebook.com/{self.client_token}/"
                    f"accounts?access_token={self.access_token}")
            result = requests.get(url2)
            logging.info(f"Result: {result.text}")
            # pages = self.getClient().get_connections("me", "accounts")
        self.pages = pages

        # Publishing as me
        self.page = facebookAC

        if (facebookAC != 'me'):
            for i in range(len(pages['data'])):
                msgLog = (f"{self.indent} Page: {pages['data'][i]['name']} "
                          f"{facebookAC}")
                logMsg(msgLog, 2, 0)
                if (pages['data'][i]['name'] == facebookAC):
                    msgLog = (f"{self.indent} Selected "
                              f"{pages['data'][i]['name']}")
                    logMsg(msgLog, 2, 0)
                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
                    self.page = graph2
                    self.pageId = pages['data'][i]['id']
                    break

    def setApiPosts(self):
        if not self.page:
            self.setPage(self.user)

        posts = []
        postsF = self.getPage().get_connections(
                self.pageId, connection_name='posts')
        if 'data' in postsF:
            for post in postsF['data']:
                postt = self.page.get_connections(post['id'],
                        connection_name='attachments')
                if 'data' in postt:
                    # We need to merge the two dictionaries to have the id and
                    # the other data
                    if postt['data']:
                        posts.append({**postt['data'][0] , **postt})

        return posts
        #outputData = {}
        #serviceName = 'Facebook'
        #outputData[serviceName] = {'sent': [], 'pending': []}
        #for post in self.getPosts():
        #    (page, idPost) = post['id'].split('_')
        #    url = 'https://facebook.com/' + page + '/posts/' + idPost
        #    outputData[serviceName]['sent'].append((post['message'], url,
        #            '', post['created_time'], '','','','',''))

        #self.postsFormatted = outputData

    def processReply(self, reply):
        res = reply
        if reply:
            if isinstance(reply, dict) and 'id' in reply:
                res = 'https://www.facebook.com/{}'.format(reply['id'])
                msgLog = ("{self.indent} Link process reply: {res}")
                logMsg(msgLog, 2, 0)
            elif 'reported as abusive' in reply:
                res = f"abusive! {res}"

        return(res)

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            # logging.info(f"Api: {api}")
            title = api.getPostTitle(post)
            # logging.info(f"Title: {title}")
            link = api.getPostLink(post)
            # logging.info(f"Link: {link}")
            comment = ''

        post = self.addComment(title, comment)

        if not self.page:
            self.setPage(self.user)

        res = "Fail!"
        logging.info(f"Facebook acc: {self.page}")
        if (not isinstance(self.page, str)):
            try:
                res = self.page.put_object("me", "feed",
                                           message=title, link=link)
            except:
                res = self.report('', res, '', sys.exc_info())
        # res = self.processReply(res)
        return res

    def publishApiImage(self, *args, **kwargs):
        res = 'Fail!'
        msgLog = (f"{self.indent} {args} Len: {len(args)}")
        logMsg(msgLog, 2, 0)
        if len(args) == 3:
            post, imageName, more = args
            yield(f" publishing api {post} - {imageName} - {more}")
            with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

            try:
                if 'alt' in kwargs:
                    res = self.page.put_photo(imagedata, message=post,
                        alt_text_custom = kwargs['alt'])
                else:
                    res = self.page.put_photo(imagedata, message=post)
            except:
                res = self.report('Facebook', post, '', sys.exc_info())
        else:
            msgLog = (f"{self.indent} not published")
            logMsg(msgLog, 2, 0)
        return res

    def deleteApiPosts(self, idPost):
        result = self.page.delete_object(idPost)
        msgLog = (f"{self.indent} Res: {result}")
        logMsg(msgLog, 2, 0)
        return(result)

    def getPostId(self, post):
        result = self.getAttribute(post, 'id')
        return result

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def getApiPostTitle(self, post):
        return self.getAttribute(post, "title")

    def getPostUrl(self, post):
        idPost = self.getPostId(post)
        return f"https://facebook.com/{idPost}"
        #return f'https://twitter.com/{self.user}/status/{idPost}'

    def getApiPostLink(self, post):
        result = self.getAttribute(post, 'url')
        pos = result.find('=')
        pos2 = result.find('&',pos)
        import urllib.parse
        return urllib.parse.unquote(result[pos+1:pos2])

    def getPostImages(self,idPost):
        res = []
        post = self.client.get_object('me',fields='id')
        myId = post['id']
        field='attachments'
        post = self.client.get_object('{}_{}'.format(myId,idPost),fields=field)
        res.append(post['attachments']['data'][0]['media']['image']['src'])
        subAttach = post['attachments']['data'][0]['subattachments']
        for img in subAttach['data']:
            res.append(img['media']['image']['src'])

        return(res)

def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    key = ('facebook', 'set', 'Enlaces de Fernand0', 'posts')
    try:
        apiSrc = rules.readConfigSrc("", key, None)
    except:
        url = (f"https://graph.facebook.com/oauth/access_token"
               f"?client_id={apiSrc.app_id}"
               f"&client_secret={apiSrc.client_token}"
               f"&grant_type=client_credentials")
        print(f"Url: {url}")
        import requests
        result = requests.get(url)
        print(f"Result: {result}")
        return

    testingToken = False
    if testingToken:
        url = (f"https://graph.facebook.com/oauth/access_token"
               f"?client_id={apiSrc.app_id}"
               f"&client_secret={apiSrc.client_token}"
               f"&grant_type=client_credentials")
        print(f"Url: {url}")

        return

    testingPages = False
    if testingPages:
        print("Testing Pages")
        pages = apiSrc.getClient().get_connections('me', 'accounts')
        print(f"Pages: {pages}")
        print(f"Data: {pages['data'][0].keys()}")
        for page in pages['data']:
            print(f"Page: {page['name']}")

        return

    testingPost = True
    if testingPost:

        apiSrc.setPage('Enlaces de fernand0')
        res = apiSrc.publishPost("Prueba texto",
                             "https://elmundoesimperfecto.com/", "")
        print(res)
        return

    testingImages = False
    if testingImages:
        res = fc.publishImage("prueba imagen", "/tmp/prueba.png",
                              alt="Imagen con alt")
        print(res)
        return

    testingPosts = False
    if testingPosts:
        fc.setPostsType('posts')
        fc.setPosts()
        for i, post in enumerate(fc.getPosts()):
            title = fc.getPostTitle(post)
            link = fc.getPostLink(post)
            url = fc.getPostUrl(post)
            theId = fc.getPostId(post)
            print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}"
                  f"\nId: {theId}\n")
        return

    sys.exit()
    fc.publishPost("Prueba")
    print(fc.user)
    sys.exit()
    images = fc.getPostImages('10157835018558264')
    print(images)
    print(len(images))
    images = fc.getPostImages('10157761305288264')
    print(images)
    print(len(images))
    sys.exit()
    print(fc.get_object(id='me'))

    print("Listing pages")
    for page in fc.pages['data']:
        print(page['name'], page)

    fc.setPosts()
    for post in fc.getPosts():
        print(post)
        #print("@%s: %s" %(tweet[2], tweet[0]))
    sys.exit()

    print("Testing title and link")

    for post in fc.getPosts():
        print(post)
        title = fc.getPostTitle(post)
        link = fc.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))


    sys.exit()


    fc.setPosts()
    posts = fc.getPosts()
    for post in posts:
        print(post)
        #print("%s: %s" %(post[0], post[1]))


if __name__ == '__main__':
    main()

