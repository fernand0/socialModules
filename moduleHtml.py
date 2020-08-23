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
from bs4 import Tag
from pdfrw import PdfReader
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *

class moduleHtml():

    def __init__(self):
         self.url = ""
         self.name = ""
         self.rssFeed = ''
         self.Id = 0
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.postsRss = None
         self.time = []
         self.bufferapp = None
         self.program = None
         self.xmlrpc = None
         self.lastLinkPublished = {}
         #self.logger = logging.getLogger(__name__)
 
    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        self.name = name

    def getLinksToAvoid(self):
        return(self.linksToAvoid)
 
    def setLinksToAvoid(self,linksToAvoid):
        self.linksToAvoid = linksToAvoid
 
    def extractImage(self, soup):
        pageImage = soup.findAll("img")
        #  Only the first one
        if len(pageImage) > 0:
            imageLink = (pageImage[0]["src"])
        else:
            imageLink = ""
    
        if imageLink.find('?') > 0:
            return imageLink[:imageLink.find('?')]
        else:
            return imageLink

    def listLinks(self, text):
        theList = []
        posIni = text.find('http')
        textW = text
        while posIni >= 0:
            textWS = textW[posIni:].split(maxsplit=1)
            url = textWS[0]
            theList.append(url)
            textW = textWS[1:]
            if textW:
                textW = textW[-1]
                posIni = textW.find('http')
            else:
                posIni = -1

        return(theList)

    def extractLinks(self, soup, linksToAvoid=""):
        if isinstance(soup, BeautifulSoup):
            j = 0
            linksTxt = ""
            links = soup.find_all(["a","iframe"])
            for link in soup.find_all(["a","iframe"]):
                theLink = ""
                if len(link.contents) > 0: 
                    if not isinstance(link.contents[0], Tag):
                        # We want to avoid embdeded tags (mainly <img ... )
                        if link.has_attr('href'):
                            theLink = link['href']
                        else:
                            if 'src' in link: 
                                theLink = link['src']
                            else:
                                continue
                else:
                    if 'src' in link: 
                        theLink = link['src']
                    else:
                        continue
    
                if ((linksToAvoid == "") or
                   (not re.search(linksToAvoid, theLink))):
                        if theLink:
                            link.append(" ["+str(j)+"]")
                            linksTxt = linksTxt + "["+str(j)+"] " + \
                                link.contents[0] + "\n"
                            linksTxt = linksTxt + "    " + theLink + "\n"
                            j = j + 1
    
            if linksTxt != "":
                theSummaryLinks = linksTxt
            else:
                theSummaryLinks = ""
    
            return (soup.get_text().strip('\n'), theSummaryLinks)
                

    def obtainPostData(self, post, debug=False):
        theSummary = post['summary']
        content = post['description']
        if content.startswith('Anuncios'): content = ''
        theDescription = post['description']
        theTitle = post['title'].replace('\n', ' ')
        theLink = post['link']
        if ('comment' in post):
            comment = post['comment']
        else:
            comment = ""

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

        theSummary = soup.get_text()
        if self.getLinksToAvoid():
            (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
            logging.debug("theC", theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC", theContent)
        else:
            (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            logging.debug("theC", theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC", theContent)

        if 'media_content' in post: 
            theImage = post['media_content'][0]['url']
        else:
            theImage = self.extractImage(soup)
        logging.debug("theImage", theImage)
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks
            
        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:     ", theTitle)
        logging.debug("Link:      ", theLink)
        logging.debug("First Link:", firstLink)
        logging.debug("Summary:   ", content[:200])
        logging.debug("Sum links: ", theSummaryLinks)
        logging.debug("the Links"  , theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


if __name__ == "__main__":

    import moduleRss
    
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    print("Configured blogs:")

    blogs = []

    url = 'https://fernand0-errbot.slack.com/'
    blog = moduleRss.moduleRss()
    blog.setPosts()
    blog.setUrl(url)
    print(blog.obtainPostData(29))
    sys.exit()

    for section in config.sections():
        #print(section)
        #print(config.options(section))
        blog = moduleRss.moduleRss()
        url = config.get(section, "url")
        blog.setUrl(url)
        if 'rssfeed' in config.options(section): 
            rssFeed = config.get(section, "rssFeed")
            #print(rssFeed) 
            blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "buffer"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("buffer" in config.options(section)):
            blog.setBufferapp(config.get(section, "buffer"))
        if ("cache" in config.options(section)):
            blog.setBufferapp(config.get(section, "cache"))

        for option in config.options(section):
            if ('ac' in option) or ('fb' in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blogs.append(blog)

    
    blogs[7].setPostsRss()
    #print(blogs[7].getPostsRss().entries)
    numPosts = len(blogs[7].getPostsRss().entries)
    for i in range(numPosts):
        print(blog.obtainPostData(numPosts - 1 - i))

    sys.exit()

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        blog.setPostsRss()
        print(blog.getPostsRss().entries[0]['link'])
        print(blog.getLinkPosition(blog.getPostsRss().entries[0]['link']))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPostsRss().entries[5]['link']))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)
        if blog.getUrl().find('ando')>0:
            blog.newPost('Prueba %s' % time.asctime(), 'description %s' % 'prueba')
            print(blog.selectPost())

    for blog in blogs:
        import urllib
        urlFile = open(DATADIR + '/' 
              + urllib.parse.urlparse(blog.getUrl()+blog.getRssFeed()).netloc
              + ".last", "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPostsRss().entries[5]['description'])
        for post in posts:
            if "content" in post:
                print(post['content'][:100])

def main():
    import moduleHtml

    html = moduleHtml.moduleHtml()

if __name__ == "__main__":
    main()
