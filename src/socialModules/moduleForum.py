import configparser
import logging
import time

import requests
import bs4
from bs4 import BeautifulSoup

from socialModules.configMod import *
from socialModules.moduleContent import *
#from socialModules.moduleQueue import *

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


class moduleForum(Content): #, Queue):

    def setClient(self, forumData):
        logging.info(f"Ffffforum: {forumData}")
        self.selected = None
        self.selector = None
        self.idSeparator = None
        self.service = None
        self.max = 15
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
        self.selected = None
        self.selector = None
        self.idSeparator = None
        self.service = None
        self.max = 15
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
            if "selectorlink" in config[self.url]:
                self.selectorlink = config.get(self.url, "selectorlink")
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

        headers.update({'referer': self.url})

        selector = self.selector[idSelector]
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, features="lxml")
        logging.debug(f"Soup: {soup}")
        logging.debug(f"Selector: {selector}")
        if hasattr(self, "selectorby") and (self.selectorby == "a"):
            logging.debug(f"Selector by: {self.selectorby}")
            links = soup.find_all("a", {"class": selector})
        else:
            links = soup.find_all(class_=selector)
        logging.debug(f"Links: {links}")
        if len(links) < 10:
            links = None
        if not links:
            logging.debug(f"Soup 2: {soup}")
            links = soup.find_all('a')
            for i, l in enumerate(links):
                logging.debug(f"{i}) -> {l}")

        logging.debug(f"Links: {links}")
        return links

    def getClient(self):
        return self

    def extractLink(self, data):
        url = self.url
        logging.debug(f"Url:  {url}")
        logging.debug(f"Data: {data}")
        link = ''
        if "index.php" in url:
            href = data.get("href")
            if href:
                link = url[:-9] + href
        else:
            if url[-1] != '/':
                link = urllib.parse.urljoin(url, data.get("href"))
            else:
                link = urllib.parse.urljoin(url, data.get("href"))
                #link = url + data.get("href")
        if link:
            logging.debug(f"Link: {link}")
        else:
            logging.debug(f"Link else: {data}")
        if "sid" in link:
            link = link.split("&sid")[0]
        if "page" in link:
            link = None
        #    link = link.split(",page")[0]
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
        if idPost.find('http')>=0:
            idPost = None
        elif idPost.find('mailto')>=0:
            idPost = None
        elif idPost.find('#')>=0:
            idPost = None # int(idPost.split('#')[0])
        else:
            try: 
                idPost = int(idPost)
            except:
                try:
                    idPost = int(idPost[1:])
                except:
                    ids = [int(s) for s in idPost.split('/') if s.isdigit()]
                    if ids:
                        idPost = ids[0]
                    else:
                        ids = [int(s) for s in idPost.split('-') if s.isdigit()]
                        if ids:
                            idPost = ids[0]
                        else:
                            idPost = None

        logging.debug(f"Id: {idPost}")
        return idPost

    def setPosts(self):
        url = self.url

        print(f"Uuuuuurl: {url} {url.startswith('rss')}")
        listId = []
        posts = {}
        if not url.startswith('rss'):
            try:
                forums = self.getLinks(url, 0)
            except:
                forums = []

            logging.debug(" Selected .... %s" % self.selected)
            logging.info(" Reading in .... %s" % self.url)
            for i, forum in enumerate(forums):
                logging.debug("Forum html: %s" % forum)
                logging.debug("Forum name: %s" % forum.name)
                if forum.name != "a":
                    # It is inside some other tag
                    logging.debug(f"Forum contents:{forum.contents}")
                    if isinstance(forum.contents[0], bs4.element.Tag):
                        forum = forum.contents[0]
                    else:
                        forum = forum.contents[1]

                    logging.debug("Forum in html: %s" % forum)
                text = forum.text
                logging.debug(f"Text: {text}")
                if ((text.lower() in self.selected)
                        or (text in self.selected)):
                    logging.debug(f"Forum: {forum}")
                    link = self.extractLink(forum)
                    logging.info(f"  - {text} {link}")
                    links = self.getLinks(link, 1)
                    for j, post in enumerate(links):
                        logging.info(f"Post {post}")
                        linkF = self.extractLink(post)
                        logging.info(f"linkF {linkF}")
                        if linkF:
                            if hasattr(self, 'selectorlink'):
                                logging.info(f"Selectorrrr: {self.selectorlink}")
                                if not self.selectorlink in linkF:
                                    linkF = None
                            if linkF:
                                idPost = self.extractId(linkF)
                            else:
                                idPost = None
                            logging.info(f"idPost {idPost}")
                            if idPost and post.text:
                                if not idPost in listId:
                                    listId.append(idPost)
                                    logging.debug(f"Post: {post}")
                                    textF = post.text
                                    logging.debug(f"textF: {textF}")
                                    posts[idPost] = [textF, linkF]

                    time.sleep(1)
        else:
            url = self.url.replace('rss', 'https')
            src = ('rss', 'set', url, 'posts')
            more = []
            import socialModules.moduleRules
            rules = socialModules.moduleRules.moduleRules()
            apiAux = rules.readConfigSrc("", src, more)
            print(f"Uuuuurl: {apiAux.url}")
            apiAux.setPosts()
            for post in apiAux.getPosts():
                idPost = self.extractId(apiAux.getPostLink(post))
                textF = apiAux.getPostTitle(post)
                linkF = apiAux.getPostLink(post)
                if idPost:
                    if not idPost in listId:
                        listId.append(idPost)
                        logging.debug(f"Post: {post}")
                        logging.debug(f"textF: {textF}")
                        posts[idPost] = [textF, linkF]

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
            # # print(lastLink)
            pos = self.getLinkPosition(lastLink)
            logging.debug(f"Position: {pos} Len: {len(self.posts)}")
            # print(self.posts[pos][1])
            # print('>>>',pos, len(self.posts))
            if pos == len(self.posts):  
                # and (str(lastLink) != self.posts[pos][1]):
                pos = 0
            if pos < len(self.posts):
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
        stream=sys.stdout, level=logging.DEBUG, 
        format="%(asctime)s %(message)s"
    )
    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    apiSrc = rules.selectRuleInteractive()

    #return


    #forums = [
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

    print(f"Fffffforum: {forum.getPosts()}")

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
