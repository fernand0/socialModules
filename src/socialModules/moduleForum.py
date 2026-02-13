import configparser
import logging
import sys
import time
import urllib.parse
from typing import Dict, List, Optional, Union

import bs4
import requests
from bs4 import BeautifulSoup

from socialModules.configMod import CONFIGDIR, checkLastLink
from socialModules.moduleContent import Content

# This module reads directly the HTML code
#
# Config file .rssForums
# [Forum URL]
# url=
# forums: string 1 # Strings to identify the subforum, one in each line
#       string 2
#       string 3
# selector: string 1 # Strings used to identify subforums links
#         string 2
# idSeparator: # character used for the identification of a post


class moduleForum(Content):  # , Queue):
    def __init__(self):
        super().__init__()
        self.selected: Optional[List[str]] = None
        self.selector: Optional[List[str]] = None
        self.idSeparator: Optional[str] = None
        self.service: Optional[str] = None
        self.max: int = 15
        self.url: Optional[str] = None
        self.selectorby: Optional[str] = None
        self.selectorlink: Optional[str] = None
        self.idWhere: Optional[str] = None

    def setClient(self, forumData: Union[str, tuple]) -> None:
        """
        Initialize the forum client with configuration data.

        Args:
            forumData: Either a URL string or a tuple containing forum data
        """
        logging.info(f"Forum: {forumData}")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssForums")

            if isinstance(forumData, str):
                self.url = forumData
            else:
                self.url = forumData[1]

            self.selected = [item.strip() for item in config.get(self.url, "forums").split("\n") if item.strip()]
            self.selector = [item.strip() for item in config.get(self.url, "selector").split("\n") if item.strip()]
            self.idSeparator = config.get(self.url, "idSeparator")

            if "selectorby" in config[self.url]:
                self.selectorby = config.get(self.url, "selectorby")
            if "selectorlink" in config[self.url]:
                self.selectorlink = config.get(self.url, "selectorlink")
            if "idWhere" in config[self.url]:
                self.idWhere = config.get(self.url, "idWhere")
        except configparser.NoSectionError:
            logging.warning(f"Configuration section for {forumData} not found in .rssForums")
        except configparser.NoOptionError as e:
            logging.warning(f"Missing option in configuration: {e}")
        except Exception as e:
            logging.warning(f"Forum not configured! Unexpected error: {e}")

        self.service = "Forum"

    def getLinks(self, url: str, idSelector: int) -> Optional[List]:
        """
        Extract links from the given URL based on the selector.

        Args:
            url: The URL to fetch and parse
            idSelector: Index of the selector to use

        Returns:
            A list of BeautifulSoup elements or None if no links found
        """
        # Sanitize inputs to prevent injection attacks
        if not url or idSelector < 0:
            logging.warning("Invalid input parameters for getLinks")
            return None

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/39.0.2171.95 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        headers.update({"referer": self.url})

        selector = self.selector[idSelector]
        try:
            # Add timeout to prevent hanging requests
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out for URL {url}")
            return None
        except requests.RequestException as e:
            logging.error(f"Error fetching URL {url}: {e}")
            return None

        soup = BeautifulSoup(response.content, features="lxml")
        logging.debug(f"Soup: {soup}")
        logging.debug(f"Selector: {selector}")

        if hasattr(self, "selectorby") and (self.selectorby == "a"):
            logging.debug(f"Selector by: {self.selectorby}")
            links = soup.find_all("a", {"class": selector})
        else:
            links = soup.find_all(class_=selector)

        logging.debug(f"Links: {links}")

        # Check if we have enough links
        if len(links) < 10:
            links = None

        # If no links found with the selector, try getting all anchor tags
        if not links:
            logging.debug(f"Soup 2: {soup}")
            links = soup.find_all("a")
            for i, l in enumerate(links):
                logging.debug(f"{i}) -> {l}")

        logging.debug(f"Links: {links}")
        return links

    def getClient(self):
        return self

    def extractLink(self, data) -> Optional[str]:
        """
        Extract the full URL from a BeautifulSoup element.

        Args:
            data: BeautifulSoup element containing href attribute

        Returns:
            Full URL string or None if extraction fails
        """
        url = self.url
        logging.debug(f"Url:  {url}")
        logging.debug(f"Data: {data}")

        href = data.get("href")

        if not href:
            return None

        # Security: Validate and sanitize the href to prevent malicious schemes
        parsed_href = urllib.parse.urlparse(href)
        if parsed_href.scheme and parsed_href.scheme not in ['http', 'https', '']:
            logging.warning(f"Invalid scheme in href: {parsed_href.scheme}")
            return None

        if "index.php" in url:
            link = url[:-9] + href
        else:
            link = urllib.parse.urljoin(url, href)

        # Security: Validate the resulting URL
        parsed_link = urllib.parse.urlparse(link)
        if not parsed_link.scheme or not parsed_link.netloc:
            logging.warning(f"Invalid URL formed: {link}")
            return None

        # Clean up the link
        if "sid" in link:
            link = link.split("&sid")[0]
        if "page" in link:
            return None  # Skip pagination links

        logging.debug("Link: %s" % link)
        return link

    def extractId(self, link: str) -> Optional[int]:
        """
        Extract the ID from a link string.

        Args:
            link: URL string to extract ID from

        Returns:
            Integer ID or None if extraction fails
        """
        # Security: Validate input
        if not link or not isinstance(link, str):
            logging.warning("Invalid link provided to extractId")
            return None

        pos2 = 0
        if hasattr(self, "idWhere") and self.idWhere == "0":
            pos2 = link.find(self.idSeparator)
            pos = link.rfind("/")
        else:
            pos = link.rfind(self.idSeparator)

        if not link[-1].isdigit() and (pos2 == 0):
            idPost = link[pos + 1:-1]
        else:
            if pos2 > 0:
                idPost = link[pos + 1:pos2]
            else:
                idPost = link[pos + 1:]

        logging.debug(f"Link: {link} idPost: {idPost}")

        # Security: Check for invalid IDs that could be malicious
        if any(invalid_str in idPost for invalid_str in ["http", "mailto", "#", "..", "//"]):
            return None

        # Try to convert to integer
        try:
            return int(idPost)
        except ValueError:
            try:
                return int(idPost[1:])  # Try removing first character
            except ValueError:
                # Look for digits in various formats
                parts = idPost.split("/")
                for part in parts:
                    if part.isdigit():
                        return int(part)

                parts = idPost.split("-")
                for part in parts:
                    if part.isdigit():
                        return int(part)

                return None

        logging.debug(f"Id: {idPost}")
        return idPost

    def setPosts(self) -> None:
        """Fetch and set the posts from the forum."""
        # Security: Validate URL
        if not self.url:
            logging.warning("URL not set for forum")
            return

        url = self.url
        listId = []
        posts: Dict[int, List[str]] = {}

        if not url.startswith("rss"):
            try:
                forums = self.getLinks(url, 0)
                if not forums:
                    forums = []
            except Exception as e:
                logging.error(f"Error getting forum links: {e}")
                forums = []

            logging.debug("Selected forums: %s" % self.selected)
            logging.info("Reading in: %s" % self.url)

            for i, forum in enumerate(forums):
                if not forum:
                    continue

                logging.debug("Forum html: %s" % forum)
                logging.debug("Forum name: %s" % forum.name)

                # Handle cases where the link is nested inside other tags
                if forum.name != "a":
                    # It is inside some other tag
                    logging.debug(f"Forum contents: {forum.contents}")
                    if forum.contents:
                        if isinstance(forum.contents[0], bs4.element.Tag):
                            forum = forum.contents[0]
                        elif len(forum.contents) > 1:
                            forum = forum.contents[1]

                    logging.debug("Forum in html: %s" % forum)

                text = forum.text.strip()
                logging.debug(f"Text: {text}")

                if (text.lower() in self.selected) or (text in self.selected):
                    logging.debug(f"Forum: {forum}")
                    link = self.extractLink(forum)

                    if link:
                        logging.info(f"  - {text} {link}")

                        links = self.getLinks(link, 1)
                        if links:
                            for j, post in enumerate(links):
                                logging.info(f"Post {post}")
                                linkF = self.extractLink(post)

                                if linkF:
                                    if hasattr(self, "selectorlink"):
                                        logging.info(f"Selector: {self.selectorlink}")
                                        if self.selectorlink not in linkF:
                                            linkF = None

                                    if linkF:
                                        idPost = self.extractId(linkF)
                                    else:
                                        idPost = None

                                    logging.info(f"idPost {idPost}")

                                    if idPost and post.text.strip():
                                        if idPost not in listId:
                                            # Performance: Limit the number of posts to avoid memory issues
                                            if len(listId) >= self.max * 2:  # Allow some buffer
                                                break

                                            listId.append(idPost)
                                            logging.debug(f"Post: {post}")
                                            textF = post.text.strip()
                                            logging.debug(f"textF: {textF}")

                                            # Security: Sanitize text to prevent injection
                                            textF = textF.replace('\0', '')  # Remove null bytes
                                            posts[idPost] = [textF, linkF]

                    # Rate limiting to be respectful to the server
                    time.sleep(1)
        else:
            # Handle RSS feeds
            url = self.url.replace("rss", "https")
            src = ("rss", "set", url, "posts")
            more = []
            import socialModules.moduleRules

            rules = socialModules.moduleRules()
            apiAux = rules.readConfigSrc("", src, more)
            apiAux.setPosts()

            for post in apiAux.getPosts():
                idPost = self.extractId(apiAux.getPostLink(post))
                textF = apiAux.getPostTitle(post)
                linkF = apiAux.getPostLink(post)

                if idPost and "• Re: " not in textF:
                    if idPost not in listId:
                        # Performance: Limit the number of posts to avoid memory issues
                        if len(listId) >= self.max * 2:  # Allow some buffer
                            break

                        listId.append(idPost)
                        logging.debug(f"Post: {post}")
                        logging.debug(f"textF: {textF}")

                        # Security: Sanitize text to prevent injection
                        textF = textF.replace('\0', '')  # Remove null bytes
                        posts[idPost] = [textF, linkF]

        if listId:
            self.posts = []
            self.lastId = listId[-1]
            listId.sort()

            # Get the most recent posts up to max count
            for i in listId[-self.max:]:
                if i in posts:
                    self.posts.append(posts[i])

            lastLink, lastTime = checkLastLink(self.url)
            logging.debug(f"LastLink: {lastLink}")

            pos = self.getLinkPosition(lastLink)
            logging.debug(f"Position: {pos} Len: {len(self.posts)}")

            if pos == len(self.posts):
                pos = 0

            if pos < len(self.posts):
                # Format posts that are new
                for i, post in enumerate(self.posts[pos:]):
                    self.posts[pos + i][0] = f"> {post[0]}\n{post[1]}"
                self.posts = self.posts[pos:]

    def getApiPostTitle(self, post) -> str:
        """Get the title of a post."""
        return post[0]

    def getApiPostLink(self, post) -> str:
        """Get the link of a post."""
        return post[1]


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )
    import socialModules.moduleRules

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    # return

    # forums = [
    #     #"http://foro.infojardin.com/",
    #     'https://cactuspro.com/forum/',
    #     #'https://garden.org/forums/'
    #     #'http://www.agaveville.org/index.php'
    #     #"https://www.cactuseros.com/foro/index.php",
    #     #"https://mammillaria.forumotion.net/",
    #     #"https://cactiguide.com/forum/",
    # ]
    forum = apiSrc
    forum.setPosts()
    logging.debug(f"Posts: {forum.getPosts()}")
    lastLink, lastTime = checkLastLink(forum.url)
    logging.debug(f"Last: {lastLink} - {lastTime}")
    pos = forum.getLinkPosition(lastLink)
    logging.debug(f"Pos: {pos}")

    if pos > len(forum.getPosts()) - 1:
        print("No new posts!\n")
    else:
        for post in forum.getPosts()[pos:]:
            print("   {}".format(post[0]))
            print("   {}".format(post[1]))
        # updateLastLink(forum.url, forum.getPosts()[-1][1])
    for i, post in enumerate(forum.getPosts()):
        print(f"{i}) p0{post[0]}.\n   p1{post[1]}")


if __name__ == "__main__":
    main()
