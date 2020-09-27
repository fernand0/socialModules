# This module provides infrastructure for reading content from different places
# It stores in a convenient and consistent way the content in order to be used
# in other programs

import configparser
import os
import logging
from bs4 import Tag
from urllib.request import urlopen
from bs4 import BeautifulSoup

from configMod import *

class Content:

    def __init__(self):
        self.url = ""
        self.name = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.posts = None
        self.postsFormatted = None
        self.time = []
        self.bufferapp = None
        self.program = None
        self.buffer = None
        self.cache = None
        self.xmlrpc = None
        self.api = {}
        self.lastLinkPublished = {}
 
    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        self.name = name

    def getSocialNetworks(self):
        return(self.socialNetworks)

    def getSocialNetworksAPI(self):
        return(self.api)

    def setSocialNetworks(self, config, section):
        socialNetworksOpt = ['twitter', 'facebook', 'telegram', 'wordpress', 
                'medium', 'linkedin','pocket', 'mastodon','instagram', 'imgur'] 
        for option in config.options(section):
            if (option in socialNetworksOpt):
                nick = config.get(section, option)
                socialNetwork = (option, nick)
                self.addSocialNetwork(socialNetwork)

    def addSocialNetworkAPI(self, socialNetwork):
        sN = socialNetwork[0]
        nick = socialNetwork[1]
        #if sN == 'twitter':
        #    self.api[socialNetwork] = moduleTwitter.moduleTwitter()
        #    self.api[socialNetwork].setClient(nick)
        
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def getPublished(self):
        return(self.posts)

    def getPosts(self):
        if hasattr(self, 'getPostsType'): 
            logging.info("  Setting posts type {}".format(self.getPostsType()))
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPublished() 
        else:
            posts = sefl.getPosts()
        return(posts)

    def getPost(self, i):
        posts = self.getPosts()
        if i < len(posts): 
            return(self.getPosts()[i])
        else:
            return None

    def getTitle(self, i):        
        post = self.getPost(i)
        return(self.getPostTitle(post))

    def getLink(self, i):
        post = self.getPost(i)
        return(self.getPostLink(post))

    def getNumPostsData(self, num, i): 
        listPosts = []
        for j in range(num, 0, -1): 
            logging.debug("j, i %d - %d"% (j,i))
            i = i - 1
            if (i < 0):
                break
            post = self.obtainPostData(i, False)
            if isinstance(post[3], list):
                for imgL in post[3]:
                    myPost = list(post)
                    myPost[3] = imgL
                    listPosts.append(tuple(myPost))
            else:
                listPosts.append(post)
            print("      Scheduling...")
            print("       - Post: %s" % post[0])
            print("       - Link: %s" % post[1])
            logging.info("    Scheduling post %s" % post[0])
        return(listPosts)

    def getDrafts(self):
        return self.drafts

    def setPostsType(self, postsType):
        self.postsType = postsType

    def getPostsType(self):
        if hasattr(self, 'postsType'): 
            return self.postsType 
        else:
            return 'posts' 

    def setPosts(self):
        pass 

    def addLastLinkPublished(self, socialNetwork, lastLink, lastTime):
        self.lastLinkPublished[socialNetwork] = (lastLink, lastTime)

    def getLastLinkPublished(self):
        return(self.lastLinkPublished)
 
    def getLinksToAvoid(self):
        return(self.linksToAvoid)
 
    def setLinksToAvoid(self,linksToAvoid):
        self.linksToAvoid = linksToAvoid
 
    def getTime(self):
        return(self.time)
 
    def setTime(self, time):
        self.time = time

    def getBuffer(self):
        return(self.buffer)

    def setBuffer(self): 
        import moduleBuffer 
        # https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
        self.buffer = {}
        for service in self.getSocialNetworks():
            if service[0] in self.getBufferapp():
                nick = self.getSocialNetworks()[service]
                buf = moduleBuffer.moduleBuffer() 
                buf.setClient(self.url, (service, nick))
                buf.setPosts()
                self.buffer[(service, nick)] = buf

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self, bufferapp):
        self.bufferapp = bufferapp
        self.setBuffer()
    
    def setMax(self, maxVal):
        self.max = maxVal

    def getMax(self):
        return(self.max)

    def getCache(self):
        return(self.cache)

    def setCache(self): 
        import moduleCache 
        # https://github.com/fernand0/scripts/blob/master/moduleCache.py
        self.cache = {}
        for service in self.getSocialNetworks():
            if ((self.getProgram() 
                    and isinstance(self.getProgram(), list) 
                    and service in self.getProgram()) or 
                (self.getProgram() 
                    and isinstance(self.getProgram(), str) 
                    and (service[0] in self.getProgram()))): 

                    nick = self.getSocialNetworks()[service]
                    cache = moduleCache.moduleCache() 
                    param = (self.url, (service, nick))
                    cache.setClient(param)
                    cache.setPosts()
                    self.cache[(service, nick)] = cache

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        if (len(program)>4) or program.find('\n')>0:
            program = program.split('\n')
        self.program = program
        self.setCache()

    def setBufMax(self, bufMax):
        self.bufMax = bufMax

    def getBufMax(self):
        return(self.bufMax)

    def len(self, profile):
        service = profile
        nick = self.getSocialNetworks()[profile]
        print("Profile %s, Nick %s" % (service, nick))
        if self.cache and (service, nick) in self.cache:
            if self.cache[(service, nick)].getPosts(): 
                return(len(self.cache[(service, nick)].getPosts()))
            else:
                return(0)
        elif self.buffer and (service, nick) in self.buffer:
            if self.buffer[(service, nick)].getPosts(): 
                return(len(self.buffer[(service, nick)].getPosts()))
            else:
                return(0)

    def getPostByLink(self, link):
        pos = self.getLinkPosition(link)
        if pos >= 0:
            return(self.getPosts()[pos])
        else: 
            return (None)

    def getLinkPosition(self, link):
        if hasattr(self, 'getPostsType'):
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPosts()
        pos = len(posts) 
        if posts:
            if not link:
                logging.debug(self.getPosts())
                return(len(self.getPosts()))
            for i, entry in enumerate(posts):
                linkS = link
                if isinstance(link, bytes):
                    linkS = linkS.decode()
                url = self.getPostLink(entry)
                logging.debug(url, linkS)
                lenCmp = min(len(url), len(linkS))
                if url[:lenCmp] == linkS[:lenCmp]:
                    # When there are duplicates (there shouldn't be) it returns
                    # the last one
                    pos = i
            return(pos)
        else:
            return -1

    def datePost(self, pos):
        print(self.getPosts())
        if 'entries' in self.getPosts():
            return(self.getPosts().entries[pos]['published_parsed'])
        else:
            return(self.getPosts()[pos]['published_parsed'])

    def extractImage(self, soup):
        #This should go to the moduleHtml
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

    def extractLinks(self, soup, linksToAvoid=""):
        #This should go to the moduleHtml
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

    def report(self, profile, post, link, data): 
        logging.warning("%s posting failed!" % profile) 
        logging.warning("Post %s %s" % (post[:80],link)) 
        logging.warning("Unexpected error: %s"% data[0]) 
        logging.warning("Unexpected error: %s"% data[1]) 
        print("%s posting failed!" % profile) 
        print("Post %s %s" % (post[:80],link)) 
        print("Unexpected error: %s"% data[0]) 
        print("Unexpected error: %s"% data[1]) 
        return("Fail! %s" % data[1])
        #print("----Unexpected error: %s"% data[2]) 


    def getPostTitle(self, post):
        return str(post)
    
    def getPostDate(self, post):
        return None

    def getPostLink(self, post):
        return ''

    def getImages(self, i):        
        if hasattr(self, 'getPostsType'):
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPosts()
        theTitle = None
        theLink = None
        res = None
        if i < len(posts):
            post = posts[i]
            logging.debug("Post: %s"% post)
            res = self.extractImages(post)
        return(res)

    def getImagesTags(self, i):        
        res = self.getImages(i)
        tags = [] 
        for iimg in res: 
            for tag in iimg[3]:
                if tag not in tags:
                    tags.append(tag)

        return tags

    def getImagesCode(self, i):        
        res = self.getImages(i)
        url = self.getPostLink(self.getPosts()[i]) 
        text = ""
        for iimg in res: 
            if iimg[2]:
                description = iimg[2]
            else:
                description = ""
            if description: 
                import string
                if iimg[1].endswith(' ') or iimg[1].endswith('\xa0'): 
                    # \xa0 is actually non-breaking space in Latin1 (ISO
                    # 8859-1), also chr(160). 
                    # https://stackoverflow.com/questions/10993612/how-to-remove-xa0-from-string-in-python
                    title = iimg[1][:-1]
                else:
                    title = iimg[1]
                if title[-1] in string.punctuation: 
                    text = '{}\n<p><h4>{}</h4></p><p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="{} {}" width="776" height="1035" /></a></p>'.format(text,description,url, iimg[0],title, description)
                else:
                    text = '{}\n<p><h4>{}</h4></p><p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="{}. {}" width="776" height="1035" /></a></p>'.format(text,description,url, iimg[0],title, description)
            else: 
                text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="{} {}" width="776" height="1035" /></a></p>'.format(text,url, iimg[0],title, description)
        return(text)


