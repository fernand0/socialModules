from bs4 import BeautifulSoup
import configparser
import logging
import requests
import time

from moduleContent import *
from moduleQueue import *
from configMod import *

# This moule reads directly the HTML code
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


class moduleForum(Content, Queue):
    def __init__(self):
        super().__init__()
        self.url = ""
        self.selected = None
        self.selector = None
        self.idSeparator = None
        self.service = None
        self.max = 15

    def setClient(self, forumData):
        """
        [http://foro.infojardin.com/]
        forums:Identificar cactus
               9. Cactusi
               10. Suculentas (no cactáceas)
        selector:nodeTitle
                 PreviewTooltip
        idSeparator:.
        [https://cactiguide.com/forum/]
        forums:General-Succulents
               Cacti Identification
               Succulent Identification
        selector:forumtitle
                 topictitle
        idSeparator:=
        """
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssForums")

            if isinstance(forumData, str):
                self.url = forumData
            else:
                self.url = forumData[1]
            self.selected = config.get(self.url, "forums").split("\n")
            self.selector = config.get(self.url, "selector").split("\n")
            self.idSeparator = config.get(self.url, "idSeparator")
            if "selectorby" in config[self.url]:
                self.selectorby = config.get(self.url, "selectorby")
            if "idWhere" in config[self.url]:
                self.idWhere = config.get(self.url, "idWhere")
        except:
            logging.warning("Forum not configured!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
        self.service = "Forum"

    def getLinks(self, url, idSelector):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/39.0.2171.95 Safari/537.36"
        }

        selector = self.selector[idSelector]
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, features="lxml")
        # print(f"Soup: {soup}")
        if hasattr(self, "selectorby") and (self.selectorby == "a"):
            links = soup.find_all("a", {"class": selector})
        else:
            links = soup.find_all(class_=selector)
        if not links:
            links = soup.find_all('a')

        logging.debug(f"Links: {links}")
        return links

    def getClient(self):
        return self

    def extractLink(self, data):
        url = self.url
        logging.debug(f"Url:  {url}")
        logging.debug(f"Data: {data}")
        if "index.php" in url:
            link = url[:-9] + data.get("href")
        else:
            if url[-1] != '/':
                link = url + "/" + data.get("href")
            else:
                link = url + data.get("href")
        if "sid" in link:
            link = link.split("&sid")[0]
        logging.debug("Link: %s" % link)
        return link

    def extractId(self, link):
        pos2 = 0
        if hasattr(self, 'idWhere') and self.idWhere == '0':
            pos2 = link.find(self.idSeparator)
            pos = link.rfind('/')
        else:
            pos = link.rfind(self.idSeparator)
        if not link[-1].isdigit() and (pos2 == 0):
            # idPost = int(link[pos + 1 : -1])
            idPost = link[pos + 1 : -1]
        else:
            if pos2>0: 
                idPost = link[pos+1:pos2]
            else:
                # idPost = int(link[pos + 1 :])
                idPost = link[pos + 1 :]
        logging.debug(f"Link: {link} idPost: {idPost}")
        try: 
            idPost = int(idPost)
        except:
            idPost = int(idPost[1:])

        logging.debug(f"Id: {idPost}")
        return idPost

    def setPosts(self):
        url = self.url

        forums = self.getLinks(url, 0)

        logging.info(" Reading in .... %s" % self.url)
        listId = []
        posts = {}
        for i, forum in enumerate(forums):
            logging.debug("forum %s" % forum)
            if forum.name != "a":
                # It is inside some other tag
                forum = forum.contents[0]
            text = forum.text
            if text in self.selected:
                link = self.extractLink(forum)
                logging.debug(f"  - {text} {link}")
                links = self.getLinks(link, 1)
                for j, post in enumerate(links):
                    logging.debug(f"Post {post}")
                    linkF = self.extractLink(post)
                    logging.debug(f"linkF {linkF}")
                    if linkF:
                        idPost = self.extractId(linkF)
                        logging.debug(f"idPost {idPost}")
                        listId.append(idPost)
                        textF = post.text
                        posts[idPost] = [textF, linkF]

                time.sleep(1)

        if listId:
            self.posts = []
            self.lastId = listId[-1]
            listId.sort()
            for i in listId[-self.max :]:
                self.posts.append(posts[i])

            lastLink, lastTime = checkLastLink(self.url)
            logging.debug(f"LastLink: {lastLink}")
            # for i, post in enumerate(self.posts):
            #    print("{}) {}".format(i, post))
            # print(lastLink)
            pos = self.getLinkPosition(lastLink)
            logging.debug(f"Position: {pos} Len: {len(self.posts)}")
            # print(self.posts[pos][1])
            # print('>>>',pos, len(self.posts))
            if pos == len(self.posts):  
                # and (str(lastLink) != self.posts[pos][1]):
                pos = 0
            if pos < len(self.posts) - 1:
                for i, post in enumerate(self.posts[pos:]):
                    self.posts[pos + i][0] = "> {}\n{}".format(
                        self.posts[pos + i][0], self.posts[pos + i][1]
                    )
                self.posts = self.posts[pos:]

    def getPostTitle(self, post):
        return post[0]

    def getPostLink(self, post):
        return post[1]


def main():

    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    forums = [
        #'https://cactuspro.com/forum/',
        "https://mammillaria.forumotion.net/",
        "https://www.cactuseros.com/foro/index.php",
        "http://foro.infojardin.com/",
        "https://cactiguide.com/forum/",
    ]
    for forumData in forums:
        forum = moduleForum()
        forum.setClient(forumData)
        forum.setPosts()
        lastLink, lastTime = checkLastLink(forum.url)
        pos = forum.getLinkPosition(lastLink)
        logging.debug(f"Pos: {pos}")

        if pos >= len(forum.getPosts()) - 1:
            print("No new posts!\n")
        else:
            for post in forum.getPosts()[pos:]:
                print("   {}".format(post[0]))
                print("   {}".format(post[1]))
            # updateLastLink(forum.url, forum.getPosts()[-1][1])
        sys.exit()
        print(forum.getPosts())


if __name__ == "__main__":
    main()
