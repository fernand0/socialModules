#!/usr/bin/env python

import configparser
import praw
import sys

import socialModules.moduleRss
from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleReddit(Content):  # , Queue):
    def get_user_info(self, client):
        return f"{self.user}"

    def get_post_id_from_result(self, result):
        return result.id

    def getKeys(self, config):
        user = self.user
        idR = config.get(user, "id")
        client_id = config.get(user, "client_id")
        client_secret = config.get(user, "client_secret")

        return (
            idR,
            client_id,
            client_secret,
        )

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.id = keys[0]
        self.client_id = keys[1]
        self.client_secret = keys[2]

        self.base_url = self.user.split("u")[0]
        self.url = self.user
        self.nick = self.user.split("/")[-1]
        # self.rssFeedAll = (f"{self.base_url}/.rss?feed="
        #                    f"{self.id}&user={self.nick}")

        # # logging.info(f"Srcccc: {self.src}")
        # #     self.setPage()

        # blog = socialModules.moduleRss.moduleRss()
        # blog.base_url = self.base_url
        # blog.setRssFeed(self.rssFeed)

        # self.clientRss = blog
        try:
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent="socialModules",
            )
        except:
            print(f"Exception: {sys.exc_info()}")

        print(f"Rrrrrredit: {reddit.read_only}")
        client = reddit

        return client

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        posts = []
        if self.page:
            subreddit = self.getClient().subreddit(self.page)
            for submission in subreddit.hot(limit=20):
                posts.append(submission)
            # self.clientRss.setRssFeed(self.rssFeed)
            # self.clientRss.setUrl(self.base_url)
            # self.clientRss.setRss(self.rssFeed)
            # self.clientRss.setPosts()
            # comments = socialModules.moduleRss.moduleRss()
            # #self.rssFeed = f"r/{self.page}/new/.rss?sort=new"
            # comments.setUrl(self.base_url)
            # comments.setRssFeed(f"r/{self.page}/comments/.rss")
            # comments.setPosts()
            # for com in comments.getPosts():
            #     link = comments.getPostLink(com)
            #     linkN = link[:link[:-1].rfind('/')+1]
            #     pos = self.clientRss.getLinkPosition(linkN)
            #     if pos>=0:
            #         title = self.clientRss.getPosts()[pos]['title']
            #         if title.endswith('*)'):
            #             title = f"{title[:-1]}*)"
            #         else:
            #             title = f"{title} (*)"
            #         self.clientRss.getPosts()[pos]['title'] = title

            # posts = self.clientRss.getPosts()
            # posts.reverse()
            # FIXME: This should not be here
            # self.posts = posts[:-1] # The last one seems to be the always the
            # same post

        # lastLink, lastTime = checkLastLink(self.getUrl())
        # logging.info(f"Last: {lastLink} |  {lastTime}")
        # pos = self.getLinkPosition(lastLink)
        # logging.info(f"Position: {pos} Len: {len(posts)}")
        # if pos<0:
        #     pos = 0
        # posts = self.posts[pos:]

        return posts

    def setChannel(self, page=None):
        msgLog = f"{self.indent} Start setChannel with channel {page}"
        logMsg(msgLog, 2, 0)
        self.setPage(page)

    def setPage(self, page=None):
        msgLog = f"{self.indent} Start setPage with page {page}"
        logMsg(msgLog, 2, 0)
        if page:
            self.page = page
        else:
            if self.groups:
                self.page = self.groups[0]
            else:
                self.warning("You need to join, at least, one group")
        # if self.page:
        #     self.rssFeed = f"r/{self.page}/new/.rss?sort=new"
        #     self.clientRss.setRss(urllib.parse.urljoin(self.clientRss.base_url, self.rssFeed))

    def getUrl(self):
        url = self.url
        page = self.getPage()
        if page:
            url = f"{url}/r/{page}"
        return url

    def getPage(self):
        page = ""
        if hasattr(self, "page"):
            page = self.page
        return page

    def setPages(self):
        blog = socialModules.moduleRss.moduleRss()
        blog.setUrl(self.base_url)
        blog.setRssFeed(self.rssFeedAll)
        blog.setRss(self.rssFeedAll)
        indent = self.indent
        self.indent = f"{self.indent} Checking Pages"
        blog.setPosts()
        self.indent = indent
        groups = []
        for post in blog.getPosts():
            link = post["link"]
            posIni = link.find("/r") + 3
            posFin = link.find("/", posIni)
            group = link[posIni:posFin]
            if not group in groups:
                groups.append(group)
        self.groups = groups
        logging.info(f"{self.indent} Groups: {self.groups}")

    def getPages(self):
        return self.groups

    def getApiPostTitle(self, post):
        print(f"Post: {post}")
        title = ""
        try:
            title = post.title
        except:
            title = ""
        return title

    def getApiPostUrl(self, post):
        link = ''
        try:
            print(f"{post.__dir__()}")
            link = f"{urllib.parse.urljoin(self.getUrl(),post.permalink)}"
        except:
            link = ""
        return link

    def getApiPostLink(self, post):
        link = ''
        try:
            link = post.url
        except:
            link = ""
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post.selftext  # ['content'][0]['value']
        soup = BeautifulSoup(result, "lxml")
        title = self.getPostTitle(post)
        (theContent, theSummaryLinks) = self.extractLinks(soup, "")
        content = f"{title}\n{theContent}\n{theSummaryLinks}"

        return content

    def getPostContentLink(self, post):
        result = ""
        return result

    def getPostTime(self, post):
        res = None
        try:
            res = post.created_utc
        except:
            res = None
        return res

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

        return res

    def deleteApiFavs(self, idPost):
        res = None

        return res

    def processReply(self, reply):
        res = ""

        return res

    def getPostHandle(self, post):
        res = None

        return handle

    def getPostId(self, post):
        try:
            idPost = post.get("photoid").get("_content")
        except:
            idpost = ""

        return idPost


def main():
    import logging
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    reddit_module = moduleReddit()
    tester = ModuleTester(reddit_module)
    tester.run()


if __name__ == "__main__":
    main()
