#!/usr/bin/env python

import configparser
import sys

import socialModules.moduleRss
from socialModules.configMod import *
from socialModules.moduleContent import *

class moduleReddit(Content): #, Queue):

    def getKeys(self, config):
        user = self.user
        idR = config.get(user, 'id')

        return (idR, )

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.id = keys[0]
        self.base_url = self.user.split('u')[0]
        self.url = self.user
        self.nick = self.user.split('/')[-1]
        self.rssFeedAll = (f"{self.base_url}/.rss?feed="
                           f"{self.id}&user={self.nick}")
        print(f"Base: {self.rssFeedAll}")

        self.setPages()

        self.setPage()

        blog = socialModules.moduleRss.moduleRss()
        blog.setUrl(self.base_url)
        blog.setRssFeed(self.rssFeed)

        client = blog

        return client

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        if self.page:
            self.client.setRssFeed(self.rssFeed)
            self.client.setPosts()
        posts = self.client.getPosts()
            
        lastLink, lastTime = checkLastLink(self.url)
        logging.info(f"Last: {lastLink} |  {lastTime}")

        return posts

    def setChannel(self, page=None):
        self.setPage(page)

    def setPage(self, page=None):
        if page:
            self.page = page
        else:
            if self.groups:
                self.page = self.groups[0]
            else:
                self.warning("You need to join, at least, one group")
        if self.page:
            self.rssFeed = f"r/{self.page}/new/.rss?sort=new"

    def getUrl(self):
        url = self.url
        page = self.getPage()
        if page:
            url = f"{url}/r/{page}"
        return url

    def getPage(self):
        page = self.page
        return page

    def setPages(self):
        blog = socialModules.moduleRss.moduleRss()
        blog.setUrl(self.base_url)
        blog.setRssFeed(self.rssFeedAll)
        blog.setPosts()
        groups = []
        for post in blog.getPosts():
            link = post['link']
            posIni = link.find('/r')+3
            posFin = link.find('/', posIni)
            group = link[posIni:posFin]
            if not group in groups:
                groups.append(group)
        self.groups = groups
        logging.info(f"Groups: {self.groups}")

    def getPages(self):
        return self.groups

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
        link = post['link']
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post['content'][0]['value']
        return result

    def getPostContentLink(self, post):
        result = ''
        return result

    def getPostTime(self, post):
        time = None
        if post:
            time = post.get('updated', None)
        return time

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
        res = None

        return res

    def deleteApiPosts(self, idPost):
        res = None

        return (res)

    def deleteApiFavs(self, idPost):
        res = None

        return (res)

    def processReply(self, reply):
        res = ''

        return (res)

    def getPostHandle(self, post):
        res = None

        return handle

    def getPostId(self, post):
        try:
            idPost = post.get('photoid').get('_content')
        except:
            idpost = ''

        return idPost

def main():

    logLevel = logging.INFO
    logging.basicConfig(stream=sys.stdout, level=logLevel,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    testingPosts = False
    if testingPosts:
        apiSrc.setPosts()
        print(apiSrc.getPosts())
        for i,post in enumerate(apiSrc.getPosts()):
            logging.debug(f"Post {i}): {post}")
            try:
                print(f" -Title {apiSrc.getPostTitle(post)}")
                print(f" -Link {apiSrc.getPostLink(post)}")
                print(f" -Content link {apiSrc.getPostContentLink(post)}")
                print(f" -Post link {apiSrc.extractPostLinks(post)}")
                print(f"Len: {len(apiSrc.getPosts())}")
            except:
                print(f"Post: {post}")

        return

    testingGroups = False
    if testingGroups:
        print(f"Pages:")
        for page in apiSrc.getPages():
            print(f"  {page}")
        return

    testingGroupsPosts = True
    if testingGroupsPosts:
        print(f"Posts in groups")
        for page in apiSrc.getPages():
            apiSrc.setPage(page)
            apiSrc.setPosts()
            apiSrc.setLastLink(None)
            lastLink = apiSrc.getLastLinkPublished()
            print(f"Last link: {lastLink}")
            for i,post in enumerate(apiSrc.getPosts()):
                try:
                    print(f"  -Title {apiSrc.getPostTitle(post)}")
                    print(f"  -Link {apiSrc.getPostLink(post)}")
                    print(f"  -Time {apiSrc.getPostTime(post)}")
                    print(f"  -Comments {apiSrc.getPostContent(post).count('/comments/')}")
                    if post['updated'] != post['published']:
                        print(f"Different!")
                except:
                    print(f" Post {i}): {post}")
            resUpdate = apiSrc.updateLastLink((page,'cache'), '')
            print(f"Update: {resUpdate}")
            import time
            time.sleep(1)
        return

if __name__ == '__main__':
    main()
