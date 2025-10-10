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

class moduleRss(Content): #, Queue):

    def getRssFeed(self):
        return self.getRss()

    def getRss(self):
        rssFeed= ''
        if hasattr(self, 'rssFeed'):
            rssFeed = self.rssFeed
        return(rssFeed)

    def setUrl(self, url):
        self.url = url
        if self.getRss():
            self.setRssFeed(urllib.parse.urljoin(self.getUrl(),self.getRss()))

    def setUser(self, nick=''):
        if not nick:
            feed = self.getRss()
            if (not 'flickr' in feed) and (not 'dev.to' in feed):
                self.user = urllib.parse.urlparse(feed).netloc
            elif 'dev.to' in feed:
                self.user = feed.replace('feed/','')
            else:
                self.user = feed

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def setRss(self, feed):
        self.rssFeed = feed
        self.max = None
        self.bufMax = None
        if self.getRss():
            self.setRssFeed(urllib.parse.urljoin(self.getUrl(),self.getRss()))

    def setNick(self, nick=None):
        if not nick:
            nick = self.getRss()
        if not nick.startswith('http'):
            if hasattr(self, 'url'):
                nick = urllib.parse.urljoin(self.url,self.getRssFeed())
        self.nick = nick

    def setClient(self, feed):
        msgLog = (f"{self.indent} Start setClient account: {feed}")
        logMsg(msgLog, 1, 0)
        self.indent = f"{self.indent} "
        self.service = None
        self.rssFeed = ''
        self.feed = None
        self.title = None
        # msgLog = (f"{self.indent} Feed {feed}")
        # logMsg(msgLog, 2, 0)
        if isinstance(feed, str):
            self.rssFeed = feed
        elif isinstance(feed, tuple):
            self.rssFeed = feed[1]#+feed[1][1]
        else:
            self.rssFeed = feed
        if (not 'flickr' in feed) and (not 'dev.to' in feed):
            self.user = urllib.parse.urlparse(feed).netloc
        elif 'dev.to' in feed:
            self.user = feed.replace('feed/','')
        else:
            self.user = feed
        self.nick = self.user
        # msgLog = (f"{self.indent} Url + feed {self.rssFeed}")
        # logMsg(msgLog, 2, 0)
        self.client = 'client'
        self.service = 'Rss'

        self.indent = self.indent[:-1]
        msgLog = (f"{self.indent} End setClient")
        logMsg(msgLog, 1, 0)

    def setApiSearch(self):
        msgLog = f"{self.indent} Setting posts (search)"
        logMsg(msgLog, 2, 0)

        posts = self.setApiPosts()
        search = self.getSearch()
        selPosts = []
        if search:
            for post in posts:
                if search.startswith('!'):
                    if not (search[1:] in self.getPostLink(post)):
                        selPosts.append(post)
                else:
                    if search in  self.getPostLink(post):
                        selPosts.append(post)

        return selPosts

    def setApiPosts(self):
        msgLog = f"{self.indent} Service {self.service} Start setApiPosts"
        logMsg(msgLog, 2, 0)


        if self.rssFeed.find('http')>=0:
            urlRss = self.getRssFeed()
        else:
            urlRss = urllib.parse.urljoin(self.url,self.getRssFeed())
        msgLog = f"{self.indent} Service {self.service} Feed: {urlRss}"
        logMsg(msgLog, 2, 0)
        # if 'github.com' in urlRss:
        #     self.feed = feedparser.parse(urlRss,
        #             request_headers={'Accept':'application/atom+xml'})
        # else:
        self.feed = feedparser.parse(urlRss)
        if 'bozo_exception' in self.feed:
            self.feed = feedparser.parse(urlRss,
                                         request_headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36' })


        msgLog = f"{self.indent} Service {self.service} Feed content: {self.feed}"
        logMsg(msgLog, 2, 0)
        posts = self.feed.entries
        if hasattr(self.feed.feed, 'title'):
            self.title = self.feed.feed.title
        else:
            self.title = self.user

        msgLog = f"{self.indent} Service {self.service} End setApiPosts"
        logMsg(msgLog, 2, 0)
        return posts

    def getSiteTitle(self):
        title = ''
        if self.feed:
            title = self.feed.feed.get('title', '').replace('\n',' ')
        return title

    def getPostTime(self, post):
        time = None
        if post:
            time = post.get('published', None)
        return time

    def getApiPostTitle(self, post):
        title = ""
        if post:
            title = post.get('title', '').replace('\n',' ')
        return title

    def getPostLink(self, post):
        link = ''
        if post:
            link = post.get('link', '')
        return link

    def getPostContentHtml(self, post):
        summary = ""
        if 'content' in post:
            # WordPress
            summary = post.get('content', [{}])[0].get('value')
        elif 'summary' in post:
            summary = post.get('summary', '')
        return summary

    def getPostContentLink(self, post):
        content = self.getPostContentHtml(post)
        soup = BeautifulSoup(content, 'lxml')
        link = soup.find('a')
        if not link:
            link = self.getPostLink(post)
        else:
            link = link['href']
        return link

    def getPostImages(self, post):
        content = self.getPostContentHtml(post)
        soup = BeautifulSoup(content, 'lxml')
        link = soup.findAll('img')
        return link

    def getPostImage(self, post):
        link = self.getPostImages(post)
        if link:
            img = link[0]['src']
        else:
            img = ''
        return img

    def getPostImagesCode(self, post):
        images = self.getPostImages(post)
        code = ""
        # print(f"Images: {images}")
        for img in images:
            code = (f"{code}<br />\n"
                    f"{img['alt']}<br />\n"
                    f"{img}")
        return code

    def getPostContent(self, post):
        summary = self.getPostContentHtml(post)
        soup = BeautifulSoup(summary, 'lxml')
        for node in soup.find_all('blockquote'):
            node = node.get_text()
            # logging.debug(f"Node: {node}")
            node = f'"{node[1:-1]}"'
            # We need to delete before and after \n
            # logging.debug(f"Node: {node}")
        return soup.get_text()

def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    testingPosts = True
    if testingPosts:
        apiSrc.setPosts()
        print(f"Posts: {apiSrc.getPosts()}")
        listPosts = {}
        for i,post in enumerate(apiSrc.getPosts()):
            print(f"Post {i}): {post}")
            print(f"{i}) {apiSrc.getPostTitle(post)}")
            print(f"     {apiSrc.getPostLink(post)}")
        return

    testingSearch = False
    if testingSearch:
        key = ('rss', 'set', 'http://github.com/fernand0', 'search')
        apiSrc = rules.readConfigSrc("", key, None)
        apiSrc.setSearch("!personalAggregator")
        apiSrc.setPostsType('search')
        apiSrc.setPosts()
        print(f"Posts: {apiSrc.getPosts()}")
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"{i}) {apiSrc.getPostTitle(post)}")
            print(f"     {apiSrc.getPostLink(post)}")

        return

    testingGitHub = False
    if testingGitHub:
        rssFeed = 'https://github.com/fernand0'
        url = 'https://github.com/fernand0'
        blog = socialModules.moduleRss.moduleRss()
        blog.setClient(urllib.parse.urljoin(url,rssFeed))
        blog.setUrl(url)
        blog.setPostsType('posts')
        blog.setPosts()
        print(f"Title: {blog.getSiteTitle()}")
        for i, post in enumerate(blog.getPosts()):
            print(f"{i}) {blog.getPostTitle(post)}")
            print(f"     {blog.getPostLink(post)}")
            # print(f"Post: {post}")
        return

    print("Configured blogs:")

    accounts = ["Blog9", "Blog22", "Blog1"]
    for acc in accounts:
        print("Account: {}".format(acc))
        blog = moduleRss.moduleRss()
        try:
            url = config.get(acc, 'url')
            blog.setUrl(url)
            rssFeed = config.get(acc, 'rss')
        except:
            rssFeed = 'https://github.com/fernand0'
            url = 'https://github.com/fernand0'
        blog.setClient(urllib.parse.urljoin(url,rssFeed))
        #blog.setRssFeed(rssFeed)
        blog.setUrl(url)
        blog.setPosts()
        print(len(blog.getPosts()))
        print(f"Title: {blog.getSiteTitle()}")

        testingPost = True
        if testingPost:
            for post in blog.getPosts():
                # print(post)
                print(f" - {blog.getPostTitle(post)}")
                print(f" - {blog.getPostLink(post)}")
                # print(f" - {blog.getPostContent(post)}")
                # print(f" - {blog.extractPostLinks(post)}")

        continue
        for i, post in enumerate(blog.getPosts()):
            print(blog.getPosts()[i])
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content , links, comment) = (blog.obtainPostData(i, False))
            theId = comment
            url = firstLink
            print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")
            print("l",summaryLinks)
            print("h",summaryHtml)
        sys.exit()

    sys.exit()
    blogs = []

    for section in config.sections():
        print(section)
        blog = moduleRss.moduleRss()
        url = config.get(section, "url")
        print("Url: %s"% url)
        blog.setUrl(url)
        if 'rss' in config.options(section):
            rssFeed = config.get(section, "rss")
            print(rssFeed)
            blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "buffer"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("buffer" in config.options(section)):
            blog.setBufferapp(config.get(section, "buffer"))
        if ("cache" in config.options(section)):
            blog.setProgram(config.get(section, "cache"))

        blog.setSocialNetworks(config)

        print(blog.getSocialNetworks())
        blog.setCache()

        blogs.append(blog)

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        blog.setPosts()
        if blog.getPosts():
            for i, post in enumerate(blog.getPosts()):
                print(blog.getPosts()[i])
                print(blog.getTitle(i))
                print(blog.getLink(i))
                print(blog.getPostTitle(post))
                print(blog.getPostLink(post))
        else:
            print("No posts")

        for service in blog.getSocialNetworks():
            socialNetwork = (service, blog.getSocialNetworks()[service])

            linkLast, lastTime = checkLastLink(blog.getUrl(), socialNetwork)
            print("linkLast {} {}".format(socialNetwork, linkLast))
            print(blog.getUrl()+blog.getRssFeed(),
                    blog.getLinkPosition(linkLast))
        #if blog.getPosts():
        #    print("description ->", blog.getPosts()[5]['description'])
        #for post in blog.getPosts():
        #    if "content" in post:
        #        print(post['content'][:100])

if __name__ == "__main__":
    main()


