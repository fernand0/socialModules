# This module provides infrastructure for publishing and updating blog posts
# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import logging
import random
import re
import time
import urllib
from io import BytesIO

import pycurl

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# import textract
from bs4 import BeautifulSoup, Tag
from pdfrw import PdfReader

from socialModules.configMod import *
from socialModules.moduleContent import *

class DownloadError(Exception):
    """Custom exception for download failures."""

# https://github.com/fernand0/scripts/blob/master/moduleCache.py



class moduleHtml(Content): #, Queue):

    def initApi(self, keys):
        self.url = ""
        self.name = ""
        self.rssFeed = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.postsRss = None
        self.time = 0
        self.bufferapp = None
        self.program = None
        self.xmlrpc = None
        self.lastLinkPublished = {}
        self.service = "Html"
        # self.logger = logging.getLogger(__name__)

        return self

    def getKeys(self, config):
        return None

    def getLinksToAvoid(self):
        return self.linksToAvoid

    def setLinksToAvoid(self, linksToAvoid):
        self.linksToAvoid = linksToAvoid

    def setUrl(self, url):
        self.url = url

    def downloadUrl(self, url_to_download):
        msgLog = f"Downloading: {url_to_download}"
        logMsg(msgLog, 1, 1)

        response = None
        moreContent = ""

        # First and second attempts with requests
        try:
            retry_strategy = Retry(
                total=2,  # Two attempts
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount("https://", adapter)
            http.mount("http://", adapter)

            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = http.get(url_to_download, verify=False, timeout=10)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logMsg(f"Requests failed after 2 attempts: {e}", 2, 1)
            response = None # Ensure response is None on failure

        # Third attempt with pycurl if requests failed
        if response is None or not response.ok:
            sleep_time = random.uniform(0, 2)
            logMsg(f"Requests failed. Waiting for {sleep_time:.2f} seconds before trying with pycurl.", 1, 1)
            time.sleep(sleep_time)

            logMsg(f"Making a third attempt with pycurl.", 2, 1)
            try:
                buffer = BytesIO()
                c = pycurl.Curl()
                c.setopt(c.URL, url_to_download)
                c.setopt(c.WRITEDATA, buffer)
                c.setopt(c.FOLLOWLOCATION, True)
                c.setopt(c.TIMEOUT, 30)
                c.perform()

                status_code = c.getinfo(pycurl.HTTP_CODE)

                if 200 <= status_code < 300:
                    # Create a mock response object for consistency
                    response = requests.Response()
                    response.status_code = status_code
                    response._content = buffer.getvalue()
                    response.url = c.getinfo(pycurl.EFFECTIVE_URL)
                else:
                    logMsg(f"pycurl failed with status code {status_code}", 3, 1)
                    response = None

                c.close()

            except pycurl.error as e:
                logMsg(f"pycurl failed: {e}", 3, 1)
                response = None
            except Exception as e:
                logMsg(f"An unexpected error occurred with pycurl: {e}", 3, 1)
                response = None

        return response, None

        # if response and response.ok:
        #     moreContent = self._handle_blogger_content(response, url_to_download)
        #     return response, moreContent
        # else:
        #     raise DownloadError(f"Failed to download {url_to_download} after 3 attempts.")

    def _handle_blogger_content(self, response, url_to_download):
        moreContent = ""
        pos = response.text.find("https://www.blogger.com/feeds/")
        if pos >= 0:
            logMsg(f"Blogger", 1, 1)
            pos2 = response.text.find('"', pos + 1)
            theUrl2 = response.text[pos:pos2]
            import moduleRss

            blog = moduleRss.moduleRss()
            pos = theUrl2.find("/", 9)
            blog.setUrl(theUrl2[: pos + 1])
            rssFeed = theUrl2[pos + 1:]
            blog.setRssFeed(rssFeed)
            blog.setPosts()
            posPost = blog.getLinkPosition(url_to_download)
            data = blog.obtainPostData(posPost)
            moreContent = data[5][0]["value"]
        return moreContent

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
            logging.debug(cleanTxt)
            posUrl = url.find("?" + cleanTxt)
            if posUrl > 0:
                url = url[:posUrl]
                return url

        return url

    def getPdfTitle(self, req):
        nameFile = "/tmp/kkkkk.pdf"
        with open(nameFile, "wb") as f:
            f.write(req.content)
        theTitle = PdfReader(nameFile).Info.Title
        title = ""
        if theTitle:
            title = theTitle[1:-1]
        # else:
        #     lines = textract.process("/tmp/kkkkk.pdf").decode().split("\n")
        #     i = 0
        #     while len(title) < 25:
        #         title = title + " " + lines[i]
        #         i = i + 1

        return title

    def cleanDocument(self, text, url_to_download, response):
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
            ("\\n",""),
            ("\\t",""),
        ]

        from readability.readability import Document

        doc = Document(text)
        doc_title = doc.title()
        # from selectolax.parser import HTMLParser
        # doc = HTMLParser(text)
        # doc_title = doc.css_first('title').text()

        if not doc_title or (doc_title == "[no-title]"):
            if url_to_download.lower().endswith("pdf"):
                title = self.getPdfTitle(response)
                print(title)
                doc_title = "[PDF] " + title

        theTitle = doc_title

        # myText = doc.summary()
        myText = doc.content()
        # myText = doc.text(separator='\n')

        for a, b in replaceChars:
            myText = myText.replace(a, b)
            theTitle = theTitle.replace(a, b)

        return (myText, theTitle)

    def setUrl(self, url):
        self.url = url

    def setApiPosts(self):
        """
        Downloads the HTML content from the URL(s) stored in self.url.
        """
        urls = self.url if isinstance(self.url, list) else [self.url]
        self.posts = []
        for url in urls:
            try:
                response, _ = self.downloadUrl(url)
                if response and response.ok:
                    self.posts.append(response.text)
                else:
                    logging.warning(f"Failed to download content from {url}")
            except DownloadError as e:
                logging.error(f"Download error for {url}: {e}")

    def getPostContent(self, html_content):
        """
        Extracts the plain text content from HTML.
        Returns the concatenated plain text.
        """
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        return self._extract_text(soup)

    def _extract_text(self, soup):
        """
        Extracts plain text from a BeautifulSoup object, removing script and style tags.
        """
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        text = soup.get_text(separator="\n").strip()
        # text = re.sub(r"\n{2,}", "\n\n"content, text)
        text = re.sub(r'(\n\s*){2,}', '\n\n', text)
        return text

    def extractVideos(self, soup):
        videos =  soup.find_all('video')
        return videos

    def extractImages(self, soup):
        if not isinstance(soup, BeautifulSoup):
            soup = BeautifulSoup(soup, 'lxml')
        pageImages = soup.findAll("img")
        return pageImages

    def extractImage(self, soup):
        pageImage = self.extractImages(soup)
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
        if not isinstance(soup, BeautifulSoup):
            mySoup = BeautifulSoup(soup, "lxml")
        else:
            mySoup = soup
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

    def publishApiPost(self, *args, **kwargs):
        title, link, comment = args
        more = kwargs
        res = "No link!"
        if link:
            res = self.click(link)
        return res

    def click(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)"
            " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47"
            " Safari/537.36"
        }
        logging.debug(f"url: {url}")
        if ('http://' in url) or ('https://' in url):
            # Some people writes bad URLs in email
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
    # blog.setPosts()
    # blog.setUrl(url)
    # print(blog.obtainPostData(29))

    testingX = False
    if testingX:
        import moduleHtml
        blog = moduleHtml.moduleHtml()
        url_to_download = input("X link: ")
        blog.setUrl(url_to_download)
        blog.setPosts()
        data = blog.getPostContent()
        print(data)
        print(blog.extractLinks(data)[1])

    testingContent = True
    if testingContent:
        import moduleHtml
        blog = moduleHtml.moduleHtml()
        # New test case for setApiPosts and getPostContent
        print("\n--- Testing setApiPosts and getPostContent ---")
        test_url = "https://github.com/fernand0/socialModules/blob/master/src/socialModules/moduleHtml.py"
        blog.setUrl(test_url)
        print(f"Downloading content from: {test_url}")
        blog.setApiPosts()
        if blog.posts:
            print("Successfully downloaded HTML content.")
            html_content = blog.posts[0]
            print("Extracting text content...")
            content = blog.getPostContent(html_content)
            print("Extracted Content:")
            print(content[:500])  # Print first 500 characters
        else:
            print("Failed to download HTML content.")
        print("\n--- End of setApiPosts and getPostContent test ---")


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
