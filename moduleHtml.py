# This module provides infrastructure for publishing and updating blog posts
# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import time
import urllib
import requests
import logging
from bs4 import BeautifulSoup
from bs4 import Tag
from pdfrw import PdfReader

# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *
from moduleContent import *
from moduleQueue import *


class moduleHtml(Content, Queue):
    def __init__(self):
        self.url = ""
        self.name = ""
        self.rssFeed = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.postsRss = None
        self.time = []
        self.bufferapp = None
        self.program = None
        self.xmlrpc = None
        self.lastLinkPublished = {}
        self.service = "Html"
        # self.logger = logging.getLogger(__name__)

    def initApi(self, keys):
        return self

    def getKeys(self, config):
        return None

    def getLinksToAvoid(self):
        return self.linksToAvoid

    def setLinksToAvoid(self, linksToAvoid):
        self.linksToAvoid = linksToAvoid

    def downloadUrl(self, theUrl):
        msgLog = f"Downloading: {theUrl}"
        logMsg(msgLog, 1, 1)

        # Based on https://github.com/moshfiqur/html2mobi
        retry = False
        moreContent = ""
        try:
            response = requests.get(theUrl, verify=False)
            pos = response.text.find("https://www.blogger.com/feeds/")
            # Some blogspot blogs do not render ok because they use javascript
            # to load content. We add the content from the RSS feed.  Dirty
            # trick
            if pos >= 0:
                pos2 = response.text.find('"', pos + 1)
                theUrl2 = response.text[pos:pos2]
                import moduleRss

                blog = moduleRss.moduleRss()
                pos = theUrl2.find("/", 9)
                blog.setUrl(theUrl2[: pos + 1])
                rssFeed = theUrl2[pos + 1:]
                blog.setRssFeed(rssFeed)
                blog.setPosts()
                posPost = blog.getLinkPosition(theUrl)
                data = blog.obtainPostData(posPost)
                moreContent = data[5][0]["value"]
        except:
            retry = True
        if retry or response.status_code >= 401:
            response = requests.get(
                theUrl, headers={"User-Agent": "Mozilla/5.0"}, verify=False
            )

        return response, moreContent

    def cleanUrl(self, url):
        cleaning = [
            "source",
            "utm_",
            "gi",
            "from_action",  # slideshare
            "source",
            "infoq_content",  # infoq
            "hash",  # Links Facebook
            "trk",  # linkedin
            "imm_",  # medium
            "gi",  # uxdesign #codelikeagirl
            "fbclid",  # Links from Facebook
            "fsrc",  # Links from The Economist
            "mbid",  # arstechnica
        ]

        for cleanTxt in cleaning:
            logging.info(cleanTxt)
            posUrl = url.find("?" + cleanTxt)
            if posUrl > 0:
                url = url[:posUrl]
                return url

        return url

    def getPdfTitle(req):
        nameFile = "/tmp/kkkkk.pdf"
        with open(nameFile, "wb") as f:
            f.write(req.content)
        theTitle = PdfReader(nameFile).Info.Title
        title = ""
        if theTitle:
            title = theTitle[1:-1]
        else:
            lines = textract.process("/tmp/kkkkk.pdf").decode().split("\n")
            i = 0
            while len(title) < 25:
                title = title + " " + lines[i]
                i = i + 1

        return title

    def cleanDocument(self, text, theUrl):
        replaceChars = [
            ("“", '"'),
            ("”", '"'),
            ("‘", "'"),
            ("’", "'"),
            ("`", "'"),
            ("`", "'"),
            ("′", "'"),
            ("—", "-"),
            ("–", "-"),
            ("…", "..."),
            ("•", "."),
            ("«", '"'),
            ("»", '"'),
            ("„", '"'),
            ("μ", "micro"),
            ("™", "(TM)"),
            ("≤", "<="),
            ("≥", ">="),
            ("∀", "ForAll"),
            ("⇒", "=>"),
            ("б", "(6)"),
            ("š", "s"),
            ("├", "|-"),
            ("─", "--"),
            ("|", "| "),
            ("│", "| "),
            ("└", "-"),
            ("→", "->"),
            ("⁄", "/"),
            ("⅓", "1/3"),
            ("📸", "(camera)"),
            ("✅", "(x)"),
            ("👽", "(alien)"),
            ("👍", "(ok)"),
            ("🙀", "(oh)"),
            ("🚀", "(despegar)"),
        ]

        from readability import Document

        doc = Document(text)
        doc_title = doc.title()

        if not doc_title or (doc_title == "[no-title]"):
            if theUrl.lower().endswith("pdf"):
                title = getPdfTitle(response)
                print(title)
                doc_title = "[PDF] " + title

        theTitle = doc_title

        myText = doc.summary()
        for a, b in replaceChars:
            myText = myText.replace(a, b)
            theTitle = theTitle.replace(a, b)

        return (myText, theTitle)

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

    def listLinks(self, text):
        theList = []
        posIni = text.find("http")
        textW = text
        while posIni >= 0:
            textWS = textW[posIni:].split(maxsplit=1)
            url = textWS[0]
            theList.append(url)
            textW = textWS[1:]
            if textW:
                textW = textW[-1]
                posIni = textW.find("http")
            else:
                posIni = -1

        return theList

    def extractLinks(self, soup, linksToAvoid=""):
        if isinstance(soup, BeautifulSoup):
            j = 0
            linksTxt = ""
            links = soup.find_all(["a", "iframe"])
            for link in links:
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

                if (linksToAvoid == "") or (
                    not re.search(linksToAvoid, theLink)
                ):
                    if theLink:
                        link.append(" [" + str(j) + "]")
                        linksTxt = (
                            linksTxt
                            + "["
                            + str(j)
                            + "] "
                            + link.contents[0]
                            + "\n"
                        )
                        linksTxt = linksTxt + "    " + theLink + "\n"
                        j = j + 1

            if linksTxt != "":
                theSummaryLinks = linksTxt
            else:
                theSummaryLinks = ""

            return (soup.get_text().strip("\n"), theSummaryLinks)

    def obtainPostData(self, post, debug=False):
        theSummary = post["summary"]
        content = post["description"]
        if content.startswith("Anuncios"):
            content = ""
        theDescription = post["description"]
        theTitle = post["title"].replace("\n", " ")
        theLink = post["link"]
        if "comment" in post:
            comment = post["comment"]
        else:
            comment = ""

        theSummaryLinks = ""

        soup = BeautifulSoup(theDescription, "lxml")

        link = soup.a
        if link is None:
            firstLink = theLink
        else:
            firstLink = link["href"]
            pos = firstLink.find(".")
            if firstLink.find("https") >= 0:
                lenProt = len("https://")
            else:
                lenProt = len("http://")
            if firstLink[lenProt:pos] == theTitle[: pos - lenProt]:
                # A way to identify retumblings. They have the name of the
                # tumblr at the beggining of the anchor text
                theTitle = theTitle[pos - lenProt + 1:]

        theSummary = soup.get_text()
        if self.getLinksToAvoid():
            (theContent, theSummaryLinks) = self.extractLinks(
                soup, self.getLinkstoavoid()
            )
            logging.debug("theC", theContent)
            if theContent.startswith("Anuncios"):
                theContent = ""
            logging.debug("theC", theContent)
        else:
            (theContent, theSummaryLinks) = self.extractLinks(soup, "")
            logging.debug("theC", theContent)
            if theContent.startswith("Anuncios"):
                theContent = ""
            logging.debug("theC", theContent)

        if "media_content" in post:
            theImage = post["media_content"][0]["url"]
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

    def publishPost(self, title, url, comment = None):
        return self.click(url)

    def click(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)"
            " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47"
            " Safari/537.36"
        }
        logging.debug(f"url: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.info(response.text)
        return "Click OK"


if __name__ == "__main__":

    import moduleRss

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + "/.rssBlogs")

    print("Configured blogs:")

    blogs = []

    url = "https://fernand0-errbot.slack.com/"
    blog = moduleRss.moduleRss()
    blog.setPosts()
    blog.setUrl(url)
    print(blog.obtainPostData(29))
    sys.exit()

    for section in config.sections():
        # print(section)
        # print(config.options(section))
        blog = moduleRss.moduleRss()
        url = config.get(section, "url")
        blog.setUrl(url)
        if "rssfeed" in config.options(section):
            rssFeed = config.get(section, "rssFeed")
            # print(rssFeed)
            blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "buffer"]
        if "linksToAvoid" in config.options(section):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if "time" in config.options(section):
            blog.setTime(config.get(section, "time"))
        if "buffer" in config.options(section):
            blog.setBufferapp(config.get(section, "buffer"))
        if "cache" in config.options(section):
            blog.setBufferapp(config.get(section, "cache"))

        for option in config.options(section):
            if ("ac" in option) or ("fb" in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blogs.append(blog)

    blogs[7].setPostsRss()
    # print(blogs[7].getPostsRss().entries)
    numPosts = len(blogs[7].getPostsRss().entries)
    for i in range(numPosts):
        print(blog.obtainPostData(numPosts - 1 - i))

    sys.exit()

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if "twitterac" in blog.getSocialNetworks():
            print(blog.getSocialNetworks()["twitterac"])
        blog.setPostsRss()
        print(blog.getPostsRss().entries[0]["link"])
        print(blog.getLinkPosition(blog.getPostsRss().entries[0]["link"]))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPostsRss().entries[5]["link"]))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)
        if blog.getUrl().find("ando") > 0:
            blog.newPost(
                "Prueba %s" % time.asctime(), "description %s" % "prueba"
            )
            print(blog.selectPost())

    for blog in blogs:

        urlFile = open(
            DATADIR
            + "/"
            + urllib.parse.urlparse(blog.getUrl() + blog.getRssFeed()).netloc
            + ".last",
            "r",
        )
        linkLast = urlFile.read().rstrip()  # Last published
        print(
            blog.getUrl() + blog.getRssFeed(), blog.getLinkPosition(linkLast)
        )
        print("description ->", blog.getPostsRss().entries[5]["description"])
        for post in posts:
            if "content" in post:
                print(post["content"][:100])


def main():
    import moduleHtml

    html = moduleHtml.moduleHtml()
    html.setClient(reflexioneseirreflexiones)


if __name__ == "__main__":
    main()
