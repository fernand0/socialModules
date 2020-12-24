# This module provides infrastructure for reading content from different places
# It stores in a convenient and consistent way the content in order to be used
# in other programs

import configparser
import os
import pickle
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
        self.nextPosts = {}
        self.time = 0
        self.bufferapp = None
        self.program = None
        self.buffer = None
        self.cache = None
        self.xmlrpc = None
        self.api = {}
        self.lastLinkPublished = {}

    def setClient(self, account):
        logging.info("    Connecting {}: {}".format(self.service, account))

        self.user = account
        try:
            config = configparser.ConfigParser()
            config.read(f"{CONFIGDIR}/.rss{self.service}")
            keys = self.getKeys(config)

            try:
                client = self.initApi(keys)
            except:
                logging.warning(f"{self.service} authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                client = None
        except:
            logging.warning("Account not configured")
            client = None

        self.client = client
        print(self.client)

    def setPosts(self):
        logging.info(f"  Setting posts in {self.service}: {self.getUrl()}")
        self.setApiPosts()
        self.setApiDrafts()

    def setApiPosts(self):
        self.posts = []

    def setApiDrafts(self):
        self.drafts = []
 
    def getClient(self):
        return self.client

    def getUrl(self):
        return(self.url)


    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        self.name = name

    def setPostAction(self, action):
        self.postaction = action

    def getPostAction(self):
        if hasattr(self, 'postaction'):
            return(self.postaction)

    def getSocialNetworks(self):
        return(self.socialNetworks)

    def getSocialNetworksAPI(self):
        return(self.api)

    def setSocialNetworks(self, socialNetworksConfig):
        socialNetworksOpt = ['twitter', 'facebook', 'telegram', 
                'wordpress', 'medium', 'linkedin','pocket', 'mastodon',
                'instagram', 'imgur', 'tumblr', 'slack', 'refind','file'] 
        logging.debug("  sNC {}".format(socialNetworksConfig))
        for sN in socialNetworksConfig:
            if sN in socialNetworksOpt:
                self.addSocialNetwork((sN, socialNetworksConfig[sN]))
        logging.debug("  sNN {}".format(self.getSocialNetworks()))

    def oldsetSocialNetworks(self, config, section):
        socialNetworksOpt = ['twitter', 'facebook', 'telegram', 
                'wordpress', 'medium', 'linkedin','pocket', 'mastodon',
                'instagram', 'imgur', 'tumblr', 'slack','refind'] 
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

    def assignPosts(self, posts):
        if hasattr(self, 'getPostsType'): 
            if self.getPostsType() == 'drafts': 
                self.drafts = posts
            else:
                self.posts = posts
        else:
            self.posts = posts

    def getPosts(self):
        if hasattr(self, 'getPostsType'): 
            logging.debug("  Posts type {}".format(self.getPostsType()))
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPublished() 
        else:
            posts = self.posts
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

    def getId(self, j):
        post = self.getPosts()[j]
        return self.getPostId(post)

    def splitPost(self, post): 
        splitListPosts = []
        for imgL in post[3]: 
            myPost = list(post) 
            myPost[3] = imgL 
            splitListPosts.append(tuple(myPost))

        return (splitListPosts)

    def getNumPostsData(self, num, i, lastLink=None): 
        listPosts = []
        for j in range(num, 0, -1): 
            logging.debug("j, i %d - %d"% (j,i))
            i = i - 1
            if (i < 0):
                break
            post = self.obtainPostData(i, False)
            listPosts.append(post)
        return(listPosts)

    def getDrafts(self):
        if hasattr(self, 'drafts'): 
            return self.drafts
        else:
            return None

    def setPostsType(self, postsType):
        self.postsType = postsType

    def getPostsType(self):
        if hasattr(self, 'postsType'): 
            return self.postsType 
        else:
            return 'posts' 

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in {self.service}: %s" % post)
        try: 
            return self.publishApiPost((post,link,comment))
        except:        
            return(self.report(self.service, post, link, sys.exc_info()))


    def updatePostsCache(self,socialNetwork):
        service = socialNetwork[0]
        nick = socialNetwork[1]
        fileNameQ = fileNamePath(self.url, (service, nick)) + ".queue"

        with open(fileNameQ, 'wb') as f:
            pickle.dump(self.nextPosts, f)
        logging.debug("Writing in %s" % fileNameQ)

        return 'Ok'

    def getNextPosts(self, socialNetwork):
        if socialNetwork in self.nextPosts:
            return self.nextPosts[socialNetwork]
        else:
            return None

    def addNextPosts(self, listPosts, socialNetwork):
        link = ''
        if listPosts:
            self.nextPosts[socialNetwork] =  listPosts
            link = listPosts[len(listPosts) - 1][1]
        return(link)

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

    #def getBuffer(self):
    #    return(self.buffer)

    #def setBuffer(self): 
    #    import moduleBuffer 
    #    # https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
    #    self.buffer = {}
    #    for service in self.getSocialNetworks():
    #        if service[0] in self.getBufferapp():
    #            nick = self.getSocialNetworks()[service]
    #            buf = moduleBuffer.moduleBuffer() 
    #            buf.setClient(self.url, (service, nick))
    #            buf.setPosts()
    #            self.buffer[(service, nick)] = buf

    #def getBufferapp(self):
    #    return(self.bufferapp)
 
    #def setBufferapp(self, bufferapp):
    #    self.bufferapp = bufferapp
    #    self.setBuffer()
    
    def setMax(self, maxVal):
        self.max = maxVal

    def getMax(self):
        if hasattr(self, 'max') and self.max:
                max = int(self.max)
        else:
            max = None
        return max

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
        program = program.split('\n')
        self.program = program
        self.setCache()

    def setBufMax(self, bufMax):
        self.bufMax = bufMax

    def getBufMax(self):
        if hasattr(self, 'bufMax') and self.bufMax: 
            return self.bufMax

    def len(self, profile):
        service = profile
        nick = self.getSocialNetworks()[profile]
        posts = []
        if self.cache and (service, nick) in self.cache:
            posts = self.cache[(service, nick)].getPosts()
        elif self.buffer and (service, nick) in self.buffer:
            posts = self.buffer[(service, nick)].getPosts()
        
        return (len(posts))

    def getPostByLink(self, link):
        pos = self.getLinkPosition(link)
        if pos >= 0:
            return(self.getPosts()[pos])
        else: 
            return (None)

    def getLinkPosition(self, link):
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
                logging.debug("{} {}".format(url, linkS))
                #print("{} {}".format(url, linkS))
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
        logging.warning("%s failed!" % profile) 
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
        logging.info("ppost {}".format(post))
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
                title = iimg[1]
                text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="{} {}" width="776" height="1035" /></a></p>'.format(text,url, iimg[0],title, description)
        return(text)

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

if __name__ == '__main__':
    main()
