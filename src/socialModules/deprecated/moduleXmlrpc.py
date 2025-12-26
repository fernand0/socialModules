# This module provides infrastructure for publishing and updating blog posts
# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import logging
import os
import pickle
import time
import urllib
import xmlrpc.client

import requests
from bs4 import BeautifulSoup, Tag
from pdfrw import PdfReader

import socialModules.moduleCache
from socialModules.configMod import *
# https://github.com/fernand0/socialMeodules/blob/master/moduleCache.py
from socialModules.moduleContent import *

# https://github.com/fernand0/socialMeodules/blob/master/moduleContent.py


class moduleXmlrpc(Content):
    def setClient(self, nick):
        self.url = ""
        self.name = ""
        self.rssFeed = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.xmlrpc = None
        self.postsXmlRpc = None
        self.time = 0
        self.bufferapp = None
        self.program = None
        self.lastLinkPublished = {}
        self.keys = []
        # self.logger = logging.getLogger(__name__)
        self.user = nick
        self.setXmlRpc()

    def addLastLinkPublished(self, socialNetwork, lastLink, lastTime):
        self.lastLinkPublished[socialNetwork] = (lastLink, lastTime)

    def getLastLinkPublished(self):
        return self.lastLinkPublished

    def getLinksToAvoid(self):
        return self.linksToAvoid

    def setLinksToAvoid(self, linksToAvoid):
        self.linksToAvoid = linksToAvoid

    def getTime(self):
        return self.time

    def setTime(self, time):
        self.time = time

    def getBufferapp(self):
        return self.bufferapp

    def setBufferapp(self, bufferapp):
        self.bufferapp = bufferapp

    def getProgram(self):
        return self.program

    def setProgram(self, program):
        self.program = program

    def getXmlRpc(self):
        return self.getXmlrpc()

    def getXmlrpc(self):
        return self.xmlrpc

    def setXmlrpc(self, xmlrpc=None):
        self.xmlrpc = xmlrpc

    def setXmlRpc(self, xmlrpc=None):
        # FIXME: ???
        # We need to fix this
        logging.info(f"{self.indent} Xmlrpc: {xmlrpc}")
        conf = configparser.ConfigParser()
        conf.read(CONFIGDIR + "/.blogaliarc")
        for section in conf.sections():
            usr = conf.get(section, "login")
            pwd = conf.get(section, "password")
            srv = conf.get(section, "server")
            domain = self.url[self.url.find(".") :]
            if srv.find(domain) > 0:
                self.xmlrpc = (xmlrpc.client.ServerProxy(srv), usr, pwd)
                blogId, blogName = self.blogId(srv, usr, pwd)
                self.setId(blogId)
                self.setName(blogName)
        self.client = self.xmlrpc

    def getPostsXmlRpc(self):
        return self.postsXmlRpc

    def setPosts(self):
        self.setPostsXmlRpc()
        self.posts = self.postsXmlRpc

    def setPostsXmlRpc(self):
        logging.info("xml %s" % self.xmlrpc)
        logging.info("xml %s" % self.Id)
        if self.xmlrpc and self.Id:
            logging.info("Yes")
            self.postsXmlRpc = self.xmlrpc[0].blogger.getRecentPosts(
                "", self.Id, self.xmlrpc[1], self.xmlrpc[2], 10
            )

    def getId(self):
        return self.Id

    def setId(self, Id):
        self.Id = Id

    def blogId(self, srv, usr, pwd):
        server = self.xmlrpc[0]
        usr = self.xmlrpc[1]
        pwd = self.xmlrpc[2]

        listMet = server.system.listMethods()
        if "wp" in listMet[-1]:
            userBlogs = server.wp.getUsersBlogs(usr, pwd)
        else:
            userBlogs = server.blogger.getUsersBlogs("", usr, pwd)
        for blog in userBlogs:
            identifier = self.url[self.url.find("/") + 2 : self.url.find(".")]
            if blog["url"].find(identifier) > 0:
                return (blog["blogid"], blog["blogName"])

        return -1

    def getKeys(self):
        return self.keys

    def setKeys(self, keys):
        self.keys = keys

    def getLinkPosition(self, link):
        i = 0
        # To be done
        return i

    def newPost(self, title, content):
        server = self.xmlrpc
        data = {"title": title, "description": content}
        server[0].metaWeblog.newPost(self.Id, server[1], server[2], data, True)

    def editPost(self, idPost, title, content):
        server = self.xmlrpc
        data = {"title": title, "description": content}
        server[0].metaWeblog.editPost(idPost, server[1], server[2], data, True)

    def selectPost(self):
        logging.info("Selecting post")
        server = self.xmlrpc
        logging.debug(server)
        print(server)
        posts = server[0].metaWeblog.getRecentPosts(self.Id, server[1], server[2], 10)
        i = 1
        print("Posts:")
        for post in posts:
            print("%d) %s - %s" % (i, post["title"], post["postid"]))
            i = i + 1
        thePost = int(input("Select one: "))
        print(
            "Post ... %s - %s"
            % (posts[thePost - 1]["title"], posts[thePost - 1]["postid"])
        )
        return posts[thePost - 1]["title"], posts[thePost - 1]["postid"]

    def deletePost(self, idPost):
        logging.info("Deleting id %s" % idPost)
        result = None
        if self.xmlrpc:
            server = self.xmlrpc
            result = server[0].blogger.deletePost(
                "", idPost, server[1], server[2], True
            )
        logging.info(result)
        return result

    def extractImage(self, soup):
        pageImage = soup.findAll("img")
        #  Only the first one
        if len(pageImage) > 0:
            imageLink = pageImage[0]["src"]
        else:
            imageLink = ""

        if imageLink.find("?") > 0:
            return imageLink[: imageLink.find("?")]
        else:
            return imageLink

    def extractLinks(self, soup, linksToAvoid=""):
        j = 0
        linksTxt = ""
        links = soup.find_all(["a", "iframe"])
        for link in soup.find_all(["a", "iframe"]):
            theLink = ""
            if len(link.contents) > 0:
                if not isinstance(link.contents[0], Tag):
                    # We want to avoid embdeded tags (mainly <img ... )
                    if link.has_attr("href"):
                        theLink = link["href"]
                    else:
                        if "src" in link:
                            theLink = link["src"]
                        else:
                            continue
            else:
                if "src" in link:
                    theLink = link["src"]
                else:
                    continue

            if (linksToAvoid == "") or (not re.search(linksToAvoid, theLink)):
                if theLink:
                    link.append(" [" + str(j) + "]")
                    linksTxt = linksTxt + "[" + str(j) + "] " + link.contents[0] + "\n"
                    linksTxt = linksTxt + "    " + theLink + "\n"
                    j = j + 1

        if linksTxt != "":
            theSummaryLinks = linksTxt
        else:
            theSummaryLinks = ""

        return (soup.get_text().strip("\n"), theSummaryLinks)

    def obtainPostData(self, i, debug=False):
        if self.postsXmlRpc:
            posts = self.getPostsXmlRpc()
            print(posts[i])
            print(posts[i].keys())
            theContent = ""
            url = ""
            firstLink = ""
            logging.debug("i %d", i)
            logging.debug("post %s", posts[i])
            # print("i", i)
            # print("post", posts[i])
            if "attachments" in posts[i]:
                post = posts[i]["attachments"][0]
            else:
                post = posts[i]

            if "title" in post:
                theTitle = post["title"]
                theLink = post["title_link"]
                if theLink.find("tumblr") > 0:
                    theTitle = post["text"]
                firstLink = theLink
                if "text" in post:
                    content = post["text"]
                else:
                    content = theLink
                theSummary = content
                theSummaryLinks = content
                if "image_url" in post:
                    theImage = post["image_url"]
                elif "thumb_url" in post:
                    theImage = post["thumb_url"]
                else:
                    logging.info("Fail image")
                    logging.info("Fail image %s", post)
                    theImage = ""
            elif "text" in post:
                if post["text"].startswith("<h"):
                    # It's an url
                    url = post["text"][1:-1]
                    req = requests.get(url)

                    if req.text.find("403 Forbidden") >= 0:
                        theTitle = url
                        theSummary = url
                        content = url
                        theDescription = url
                    else:
                        if url.lower().endswith("pdf"):
                            nameFile = "/tmp/kkkkk.pdf"
                            with open(nameFile, "wb") as f:
                                f.write(req.content)
                            theTitle = PdfReader(nameFile).Info.Title
                            if theTitle:
                                theTitle = theTitle[1:-1]
                            else:
                                theTitle = url
                            theUrl = url
                            theSummary = ""
                            content = theSummary
                            theDescription = theSummary
                        else:
                            soup = BeautifulSoup(req.text, "lxml")
                            # print("soup", soup)
                            theTitle = soup.title
                            if theTitle:
                                theTitle = str(theTitle.string)
                            else:
                                # The last part of the path, without the dot part, and
                                # capitized
                                urlP = urllib.parse.urlparse(url)
                                theTitle = (
                                    os.path.basename(urlP.path)
                                    .split(".")[0]
                                    .capitalize()
                                )
                            theSummary = str(soup.body)
                            content = theSummary
                            theDescription = theSummary
                else:
                    theSummary = post["text"]
                    content = post["text"]
                    theDescription = post["text"]
                    theTitle = post["text"]
            else:
                theSummary = post["title"]
                content = post["title"]
                theDescription = post["title"]

            if "original_url" in post:
                theLink = post["original_url"]
            elif url:
                theLink = url
            else:
                theLink = post["text"]

            if "comment" in post:
                comment = post["comment"]
            else:
                comment = ""

            # print("content", content)
            theSummaryLinks = ""

            soup = BeautifulSoup(content, "lxml")
            if not content.startswith("http"):
                link = soup.a
                if link:
                    firstLink = link.get("href")
                    if firstLink:
                        if firstLink[0] != "h":
                            firstLink = theLink

            if not firstLink:
                firstLink = theLink

            if "image_url" in post:
                theImage = post["image_url"]
            else:
                theImage = None
            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks

            if self.getLinksToAvoid():
                (theContent, theSummaryLinks) = self.extractLinks(
                    soup, self.getLinkstoavoid()
                )
            else:
                (theContent, theSummaryLinks) = self.extractLinks(soup, "")

            if "image_url" in post:
                theImage = post["image_url"]
            else:
                theImage = None
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
        logging.debug("the Links", theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")

        return (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        )


def main():
    import socialModules.moduleXmlrpc

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + "/.rssBlogs")

    print("Configured blogs:")

    blogs = []

    for b in ["Blog8", "Blog2"]:
        blog = moduleXmlrpc.moduleXmlrpc()
        url = config.get(b, "url")
        blog.setUrl(url)
        xmlrpc = config.get(b, "xmlrpc")
        blog.setXmlRpc()
        blog.setPostsXmlRpc()
        print(blog.getPostsXmlRpc()[9])
        print(blog.obtainPostData(9))
    sys.exit()

    for section in config.sections():
        # print(section)
        # print(config.options(section))
        blog = moduleXmlrpc.moduleXmlrpc()
        url = config.get(section, "url")
        blog.setUrl(url)
        optFields = ["linksToAvoid", "time", "buffer"]
        if "linksToAvoid" in config.options(section):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if "time" in config.options(section):
            blog.setTime(config.get(section, "time"))
        if "buffer" in config.options(section):
            blog.setBufferapp(config.get(section, "buffer"))
        if "cache" in config.options(section):
            blog.setBufferapp(config.get(section, "cache"))
        if "xmlrpc" in config.options(section):
            blog.setXmlRpc()

        for option in config.options(section):
            if ("ac" in option) or ("fb" in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blogs.append(blog)

    blogs[7].setPostsXmlrpc()
    # print(blogs[7].getPostsXmlrpc().entries)
    numPosts = len(blogs[7].getPostsXmlrpc().entries)
    for i in range(numPosts):
        print(blog.obtainPostData(numPosts - 1 - i))

    sys.exit()

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getSocialNetworks())
        if "twitterac" in blog.getSocialNetworks():
            print(blog.getSocialNetworks()["twitterac"])
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)
        if blog.getUrl().find("ando") > 0:
            blog.newPost("Prueba %s" % time.asctime(), "description %s" % "prueba")
            print(blog.selectPost())

    for blog in blogs:
        import urllib

        linkLast = urlFile.read().rstrip()  # Last published
        blog.setPostsXmlrpc()
        posts = blog.getPostsXmlrpc()
        for post in posts:
            if "content" in post:
                print(post["content"][:100])


if __name__ == "__main__":
    main()
