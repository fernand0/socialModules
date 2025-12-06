# This module provides infrastructure for publishing and updating blog posts

# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)
import configparser
import logging
import os
import pickle
import time
import urllib

import feedparser
from bs4 import BeautifulSoup

import socialModules.moduleCache
from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

# https://github.com/fernand0/scripts/blob/master/moduleCache.py


class moduleRss(Content):  # , Queue):
    def get_user_info(self, client):
        return f"{self.user}"

    def get_post_id_from_result(self, result):
        return result.id

    def getRssFeed(self):
        return self.getRss()

    def getRss(self):
        rssFeed = ""
        if hasattr(self, "rssFeed"):
            rssFeed = self.rssFeed
        return rssFeed

    def setUrl(self, url):
        self.url = url
        if self.getRss():
            self.setRssFeed(urllib.parse.urljoin(self.getUrl(), self.getRss()))

    def setUser(self, nick=""):
        if not nick:
            feed = self.getRss()
            if (not "flickr" in feed) and (not "dev.to" in feed):
                self.user = urllib.parse.urlparse(feed).netloc
            elif "dev.to" in feed:
                self.user = feed.replace("feed/", "")
            else:
                self.user = feed

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def setRss(self, feed):
        self.rssFeed = feed
        self.max = None
        self.bufMax = None
        if self.getRss():
            self.setRssFeed(urllib.parse.urljoin(self.getUrl(), self.getRss()))

    def setNick(self, nick=None):
        if not nick:
            nick = self.getRss()
        if not nick.startswith("http"):
            if hasattr(self, "url"):
                nick = urllib.parse.urljoin(self.url, self.getRssFeed())
        self.nick = nick

    def setClient(self, feed):
        msgLog = f"{self.indent} Start setClient account: {feed}"
        logMsg(msgLog, 1, False)
        self.indent = f"{self.indent} "
        self.service = None
        self.rssFeed = ""
        self.feed = None
        self.title = None
        # msgLog = (f"{self.indent} Feed {feed}")
        # logMsg(msgLog, 2, 0)
        if isinstance(feed, str):
            self.rssFeed = feed
        elif isinstance(feed, tuple):
            self.rssFeed = feed[1]  # +feed[1][1]
        else:
            self.rssFeed = feed
        if (not "flickr" in feed) and (not "dev.to" in feed):
            self.user = urllib.parse.urlparse(feed).netloc
        elif "dev.to" in feed:
            self.user = feed.replace("feed/", "")
        else:
            self.user = feed
        self.nick = self.user
        # msgLog = (f"{self.indent} Url + feed {self.rssFeed}")
        # logMsg(msgLog, 2, 0)
        self.client = "client"
        self.service = "Rss"

        self.indent = self.indent[:-1]
        msgLog = f"{self.indent} End setClient"
        logMsg(msgLog, 1, False)

    def setApiSearch(self):
        msgLog = f"{self.indent} Setting posts (search)"
        logMsg(msgLog, 2, False)

        posts = self.setApiPosts()
        search = self.getSearch()
        selPosts = []
        if search:
            for post in posts:
                if search.startswith("!"):
                    if not (search[1:] in self.getPostLink(post)):
                        selPosts.append(post)
                else:
                    if search in self.getPostLink(post):
                        selPosts.append(post)

        return selPosts

    def setApiPosts(self):
        msgLog = f"{self.indent} Service {self.service} Start setApiPosts"
        logMsg(msgLog, 2, False)

        if self.rssFeed.find("http") >= 0:
            urlRss = self.getRssFeed()
        else:
            urlRss = urllib.parse.urljoin(self.url, self.getRssFeed())
        msgLog = f"{self.indent} Service {self.service} Feed: {urlRss}"
        logMsg(msgLog, 2, False)
        # if 'github.com' in urlRss:
        #     self.feed = feedparser.parse(urlRss,
        #             request_headers={'Accept':'application/atom+xml'})
        # else:
        self.feed = feedparser.parse(urlRss)
        if "bozo_exception" in self.feed:
            self.feed = feedparser.parse(
                urlRss,
                request_headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
                },
            )

        msgLog = f"{self.indent} Service {self.service} Feed content: {self.feed}"
        logMsg(msgLog, 2, False)
        posts = self.feed.entries
        if hasattr(self.feed.feed, "title"):
            self.title = self.feed.feed.title
        else:
            self.title = self.user

        msgLog = f"{self.indent} Service {self.service} End setApiPosts"
        logMsg(msgLog, 2, False)
        return posts

    def getSiteTitle(self):
        title = ""
        if self.feed:
            title = self.feed.feed.get("title", "").replace("\n", " ")
        return title

    def getPostTime(self, post):
        time = None
        if post:
            time = post.get("published", None)
        return time

    def getApiPostTitle(self, post):
        title = ""
        if post:
            title = post.get("title", "").replace("\n", " ")
        return title

    def getApiPostLink(self, post):
        link = ''
        if post:
            link = post.get("link", "")
        return link

    def getPostContentHtml(self, post):
        summary = ""
        if "content" in post:
            # WordPress
            summary = post.get("content", [{}])[0].get("value")
        elif "summary" in post:
            summary = post.get("summary", "")
        return summary

    def getPostContentLink(self, post):
        content = self.getPostContentHtml(post)
        soup = BeautifulSoup(content, "lxml")
        link = soup.find("a")
        if not link:
            link = self.getPostLink(post)
        else:
            link = link["href"]
        return link

    def getPostImages(self, post):
        content = self.getPostContentHtml(post)
        soup = BeautifulSoup(content, "lxml")
        link = soup.findAll("img")
        return link

    def getPostImage(self, post):
        link = self.getPostImages(post)
        if link:
            img = link[0]["src"]
        else:
            img = ""
        return img

    def getPostImagesCode(self, post):
        images = self.getPostImages(post)
        code = ""
        # print(f"Images: {images}")
        for img in images:
            code = f"{code}<br />\n" f"{img['alt']}<br />\n" f"{img}"
        return code

    def getPostContent(self, post):
        summary = self.getPostContentHtml(post)
        soup = BeautifulSoup(summary, "lxml")
        for node in soup.find_all("blockquote"):
            node = node.get_text()
            # logging.debug(f"Node: {node}")
            node = f'"{node[1:-1]}"'
            # We need to delete before and after \n
            # logging.debug(f"Node: {node}")
        return soup.get_text()


def main():
    import logging
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    rss_module = moduleRss()
    tester = ModuleTester(rss_module)
    tester.run()


if __name__ == "__main__":
    main()
