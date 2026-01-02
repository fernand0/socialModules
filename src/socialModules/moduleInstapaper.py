#!/usr/bin/env python

import configparser
import os
import sys

import instapaper
from instapaper import Instapaper as ipaper

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleInstapaper(Content):
    def getKeys(self, config):
        instapaper_key = config.get(self.user, "instapaper_key")
        instapaper_secret = config.get(self.user, "instapaper_secret")
        oauth_consumer_id = config.get(self.user, "oauth_consumer_id")
        oauth_consumer_secret = config.get(self.user, "oauth_consumer_secret")
        email = config.get(self.user, "email")
        password = config.get(self.user, "password")

        return (instapaper_key, instapaper_secret, email, password, oauth_consumer_id, oauth_consumer_secret)

    def authorize(self):
        logging.info("Starting authorize process")
        # Add Instapaper authorization logic here

    def initApi(self, keys):
        msgLog = (
                f"{self.indent} Service {self.service} Start initApi " 
                f"{self.user}"
                )
        logMsg(msgLog, 2, False)
        self.postaction = "archive"

        instapaper_key, instapaper_secret, email, password, oauth_consumer_id, oauth_consumer_secret = keys
        # client = Instapaper(consumer_key=oauth_consumer_id, access_token=access_secret)
        # client = None # Replace with actual Instapaper client initialization
        client = ipaper(oauth_consumer_id, oauth_consumer_secret)
        client.login(email, password)
        msgLog = f"{self.indent} service {self.service} End initApi"
        logMsg(msgLog, 2, False)
        return client

    def get_user_info(self, client):
        me = client.get_user()
        return f"{me.get('username', 'Unknown')}"

    def get_post_id_from_result(self, result):
        return result

    def register_specific_tests(self, tester):
        pass

    def setApiPosts(self):
        posts = []
        # Add Instapaper API call to retrieve posts here
        try:
            posts = self.client.bookmarks()
        except:
            msgLog = f"setApiPosts generated an exception: {sys.exc_info()}"
            logging.debug(f"Msggg: {msgLog}")

        return posts[:100]

    def processReply(self, reply):
        res = ""
        if reply:
            idPost = self.getPostId(reply)
            title = self.getPostTitle(reply)
            # res = f"{title} https://getinstapaper.com/read/{idPost}" # Adjust URL if necessary
        msgLog = f"     Res: {res}"
        logMsg(msgLog, 2, False)
        return res

    def publishApiPost(self, *args, **kwargs):
        title = ""
        comment = ""
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)

        post = self.addComment(title, comment)
        res = "Fail!"
        try:
            b = instapaper.Bookmark( 
                                self.getClient(), {"url": link}
                                )
            res = b.save()
        except:
            res = self.report(self.getService(), kwargs, "", sys.exc_info())
            res = f"Fail! {res}"
        logging.info(f"Res: {res}")
        return res

    def archiveId(self, idPost):
        # Add Instapaper API call to archive a post here
        return "Not implemented"

    def archive(self, j):
        msgLog = "Archiving %d" % j
        logMsg(msgLog, 1, False)
        post = self.getPost(j)
        title = self.getPostTitle(post)
        idPost = self.getPostId(post)
        logging.info(f"Post {post}")
        logMsg(msgLog, 2, False)
        logging.info(f"Title {title}")
        logMsg(msgLog, 2, False)
        logging.info(f"Id {idPost}")
        logMsg(msgLog, 2, False)
        rep = self.archiveId(idPost)
        msgLog = f"Rep: {rep}"
        logMsg(msgLog, 2, False)
        if "Archived" in rep:
            self.posts = self.posts[:j] + self.posts[j + 1 :]
        return rep

    def delete(self, j):
        # Add Instapaper API call to delete a post here
        return "Not implemented"

    def getApiPostTitle(self, post):
        title = ""
        # Extract title from Instapaper post object
        return title

    def getPostId(self, post):
        idPost = ""
        if isinstance(post, str):
            idPost = post
        else:
            idPost = self.getAttribute(post, "bookmark_id")
        return idPost

    def getApiPostLink(self, post):
        link = ''
        # Extract link from Instapaper post object
        return link

    def setMax(self, maxVal):
        self.max = 100


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester
    
    instapaper_module = moduleInstapaper()
    tester = ModuleTester(instapaper_module)
    tester.run()


if __name__ == "__main__":
    main()

