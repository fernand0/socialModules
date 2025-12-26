#!/usr/bin/env python

import logging
import sys

import mastodon
from bs4 import BeautifulSoup

from socialModules.configMod import *
from socialModules.moduleContent import *

# from socialModules.moduleQueue import *

# pip install Mastodon.py


class moduleMastodon(Content):  # , Queue):
    def getKeys(self, config):
        # if self.user.startswith('@'):
        #    self.user = self.user[1:]

        logMsg(f"User: {self.user}", 1, False)
        access_token = config[self.user]["access_token"]
        return (access_token,)

    def initApi(self, keys):
        pos = self.user.find("@", 1)  # The first character can be @
        if pos > 0:
            self.base_url = f"https://{self.user[pos:]}"
            # self.user = self.user[:pos]
        else:
            self.base_url = "https://mastodon.social"

        client = mastodon.Mastodon(access_token=keys[0], api_base_url=self.base_url)
        return client

    def setApiPosts(self):
        logging.info(f"setApiPosts {self.getClient()}")
        posts = []
        if self.getClient():
            try:
                logging.info(f"meeeee: {self.getClient().me()}")
                posts = self.getClient().account_statuses(self.getClient().me())
            except:
                posts = []
        return posts

    def setApiFavs(self):
        posts = []
        if self.getClient():
            try:
                posts = self.getClient().favourites()
            except:
                posts = []
        return posts

    def processReply(self, reply):
        res = ""
        if reply:
            res = f"{self.getAttribute(reply, 'uri')}"
        return res

    def publishApiImage(self, *args, **kwargs):
        post, image = args
        more = kwargs

        res = "Fail!"
        try:
            logging.info(f"{self.indent} First, the image")
            res = self.getClient().media_post(image, "image/png")
            self.lastRes = res
            logging.info(f"{self.indent} res {res}")
            logging.info(f"{self.indent} Now the post")
            res = self.getClient().status_post(post, media_ids=res["id"])
            self.lastRes = res
        except:
            res = self.getClient().status_post(post + " " + link, visibility="private")
        print(f"res: {res}")
        return res

    def publishApiPost(self, *args, **kwargs):
        title = ""
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        comment = ""
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)

        post = self.addComment(title, comment)

        try:
            res = self.getClient().toot(post + " " + link)
            self.res_dict["success"] = True
            self.res_dict["post_url"] = self.getAttribute(res, "uri")
            self.res_dict["raw_response"] = res
        except mastodon.errors.MastodonServiceUnavailableError as e:
            error_report = self.report(
                self.getService(), kwargs, "Not available", sys.exc_info()
            )
            self.res_dict["error_message"] = f"Service unavailable: {error_report}"
            self.res_dict["raw_response"] = e
        except Exception as e:
            error_report = self.report(self.getService(), kwargs, "", sys.exc_info())
            self.res_dict["error_message"] = f"Publication failed: {error_report}"
            self.res_dict["raw_response"] = e

        return self.res_dict

    def deleteApiPosts(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        try:
            result = self.getClient().status_delete(idPost)
        except:
            result = self.report(self.service, "", "", sys.exc_info())
        logging.info(f"Res: {result}")
        return result

    def deleteApiFavs(self, idPost):
        logging.info("Deleting: {}".format(str(idPost)))
        try:
            result = self.client.status_unfavourite(idPost)
        except:
            result = self.report(self.service, "", "", sys.exc_info())
        logging.info(f"Res: {result}")
        return result

    def getPostTime(self, post):
        time = None
        if post:
            time = post.get("created_at", None)
        return time

    def getPostId(self, post):
        if isinstance(post, str):
            idPost = post
        else:
            idPost = self.getAttribute(post, "id")
        return idPost

    def getUrlId(self, post):
        return post.split("/")[-1]

    def getSiteTitle(self):
        title = ""
        if self.user:
            title = f"{self.user}'s {self.service}"
        return title

    def getApiPostTitle(self, post):
        result = ""
        logging.info(f"Post: {post}")
        # import pprint
        # print(f"post: {post}")
        # pprint.pprint(post)
        card = post.get("card", "")
        if card:
            result = f"{card.get('title')} {card.get('url')}"

        if not result:
            result = post.get("content", "")
        if not result:
            result = post.get("text", "")
        # soup = BeautifulSoup(result, 'lxml')
        if result.startswith("<"):
            result = result[3:]
        if result.endswith(">"):
            result = result[:-4]
        # print(f"RRRRResult: {result}")
        pos = result.find("<")
        posH = result.find("http")
        posF = result.find('"', posH + 1)
        result = f"{result[:pos]} {result[posH:posF]}"

        # if 'card' in post and post['card'] and 'title' in post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        # elif 'content' in post:
        #     result = self.getAttribute(post, 'content').replace('\n', ' ')
        # elif 'card' in post and post['card']:
        #     result = self.getAttribute(post['card'], 'title')
        return result

    def getApiPostUrl(self, post):
        return self.getAttribute(post, "url")

    def getApiPostLink(self, post):
        content, link = self.extractPostLinks(post)
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = ""
        print(f"Post content: {post}")
        if post and "content" in post:
            result = self.getAttribute(post, "content")
        return result

    def getPostContentLink(self, post):
        link = ""
        if ("card" in post) and post["card"]:
            link = self.getAttribute(post["card"], "url")
        else:
            soup = BeautifulSoup(post["content"], "lxml")
            link = soup.a
            if link:
                link = link["href"]
            else:
                link = self.getAttribute(post, "uri")
        return link

    def search(self, text):
        pass

    def register_specific_tests(self, tester):
        pass

    def get_user_info(self, client):
        me = client.me()
        return f"{me.get('display_name', 'Unknown')} (@{me.get('username', 'unknown')})"

    def get_post_id_from_result(self, result):
        return self.getUrlId(str(result)) if hasattr(mastodon, "getUrlId") else None


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    mastodon_module = moduleMastodon()
    tester = ModuleTester(mastodon_module)
    tester.run()


if __name__ == "__main__":
    main()
