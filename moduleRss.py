# This module provides infrastructure for publishing and updating blog posts

# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import os
import time
import urllib
import requests
import feedparser
import pickle
import logging
from bs4 import BeautifulSoup
from pdfrw import PdfReader
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleRss(Content, Queue):

    def __init__(self):
        super().__init__()
        self.service = None
        self.rssFeed = ''
 
    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed
        self.max = None
        self.bufMax = None

    def setClient(self, feed):
        logging.debug("Feed %s" % str(feed))
        if isinstance(feed, str):
            self.rssFeed = feed
        elif isinstance(feed, tuple):
            self.rssFeed = feed[1]#+feed[1][1]
        else:
            self.rssFeed = feed
        if (not 'flickr' in feed) and (not 'dev.to' in feed):
            self.user = urllib.parse.urlparse(feed).netloc
        else:
            self.user = feed
        logging.debug("The Feed %s" % str(self.rssFeed))
        self.service = 'Rss'

    def setPosts(self):
        msgLog = "  Setting posts"
        logging.info(msgLog)

        logging.debug(f"   Feed {self.rssFeed}") 
        if self.rssFeed.find('http')>=0: 
            urlRss = self.getRssFeed()
        else: 
            urlRss = urllib.parse.urljoin(self.url,self.getRssFeed())
        logging.debug("Rss: %s" % urlRss)
        self.posts = feedparser.parse(urlRss).entries
 
    def getPostTitle(self, post):
        if 'title' in post:
            return(post['title'].replace('\n', ' '))

    def getPostLink(self, post):
        return post.get('link','')

    def getPostContentHtml(self, post):
        summary = ""
        if 'content' in post:
            # WordPress
            summary = post.get('content', [{}])[0].get('value')
        elif 'summary' in post:
            summary = self.getAttribute(post, 'summary')
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
        print(f"Imagesss: {link}")
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
        print(f"Images: {images}")
        return images

    def getPostContent(self, post):
        summary = self.getPostContentHtml(post)
        soup = BeautifulSoup(summary, 'lxml')
        for node in soup.find_all('blockquote'):
            node = node.get_text()
            logging.debug(f"Node: {node}")
            node = f'"{node[1:-1]}"'
            # We need to delete before and after \n
            logging.debug(f"Node: {node}")
        return soup.get_text()
        
        
    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
        if not posts:
            return (None, None, None, None, None, None, None, None, None)

        post = posts[i]
        #print(post)

        if 'summary' in post:
            theSummary = post['summary']
            content = theSummary
        if 'content' in post:
            content = post['content']
            if isinstance(content, str):
                if content.startswith('Anuncios'): content = ''
        if 'description' in post:
            theDescription = post['description']
        theTitle = self.getPostTitle(post)
        if 'link' in post:
            theLink = post['link']
        if ('comment' in post):
            comment = post['comment']
        else:
            comment = ""#theSummary

        pos = theLink.find('?source=rss')
        if pos >=0:
            theLink = theLink[:pos]

        theSummaryLinks = ""

        soup = BeautifulSoup(theDescription, 'lxml')

        link = soup.a
        if link is None:
           firstLink = theLink 
        else:
           firstLink = link['href']
           pos = firstLink.find('.')
           if firstLink.find('https')>=0:
               lenProt = len('https://')
           else:
               lenProt = len('http://')
           if (firstLink[lenProt:pos] == theTitle[:pos - lenProt]):
               # A way to identify retumblings. They have the name of the
               # tumblr at the beggining of the anchor text
               theTitle = theTitle[pos - lenProt + 1:]

        code = soup.find_all('code')
        for cod in code: 
            cod.string = cod.string.replace('<','&lt;')
            cod.string = cod.string.replace('>','&gt;')
            cod = cod.string


        theSummary = soup.get_text()
        if hasattr(self, 'getLinksToAvoid') and self.getLinksToAvoid():
            (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinksToAvoid())
            logging.debug("theC %s" % theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC %s"% theContent)
        else:
            (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            logging.debug("theC %s"% theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC %s"% theContent)

        if 'media_content' in posts[i]: 
            theImage = ''
            for media in posts[i]['media_content']:
                if media['url'].find('avatar')<0: 
                    theImage = media['url']
        else:
            theImage = self.extractImage(soup)
        logging.debug("theImage %s"% theImage)
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + '\n' + theLinks
            
        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:      %s"% theTitle)
        logging.debug("Link:       %s"% theLink)
        logging.debug("First Link: %s"% firstLink)
        logging.debug("Summary:    %s"% content[:200])
        logging.debug("Sum links:  %s"% theSummaryLinks)
        logging.debug("the Links   %s"% theLinks)
        logging.debug("Comment:    %s"% comment)
        logging.debug("Image;      %s"% theImage)
        logging.debug("Post        %s"% theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks) #, comment)

    #def isForMe(self, args):
    #    logging.info("isForMe %s" % str(self.service))
    #    serviceName = self.service
    #    lookAt = []
    #    if (serviceName[0] in args) or ('*' in args): 
    #        if serviceName[0] + serviceName[-1] in args[:-1]:
    #            lookAt.append(serviceName)
    #    return lookAt


def main(): 

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleRss
     
    if os.path.exists(CONFIGDIR + '/.rssBlogs'):
        config = configparser.ConfigParser()
        config.read(CONFIGDIR + '/.rssBlogs') 
    else:
        print("no")

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
            rssFeed = 'http://rss.slashdot.org/Slashdot/slashdotMain'
            url = 'http://slashdot.org/'
        blog.setClient(urllib.parse.urljoin(url,rssFeed))
        #blog.setRssFeed(rssFeed)
        blog.setUrl(url)
        blog.setPosts()
        print(len(blog.getPosts()))
        testingPost = True
        if testingPost:
            post = blog.getPosts()[0]
            print(post)
            print(f" - {blog.getPostTitle(post)}")
            print(f" - {blog.getPostLink(post)}")
            print(f" - {blog.getPostContent(post)}")
            print(f" - {blog.extractPostLinks(post)}")

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


