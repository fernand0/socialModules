#!/usr/bin/env python

import configparser
import os

from instapaper import Instapaper as ipaper

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleInstapaper(Content):
    def getKeys(self, config):
        instapaper_key = config.get(self.user, "instapaper_key")
        instapaper_secret = config.get(self.user, "instapaper_secret")
        email = config.get(self.user, "email")
        password = config.get(self.user, "password")

        return (instapaper_key, instapaper_secret, email, password)

    def authorize(self):
        logging.info("Starting authorize process")
        # Add Instapaper authorization logic here

    def initApi(self, keys):
        msgLog = f"{self.indent} Service {self.service} Start initApi {self.user}"
        logMsg(msgLog, 2, 0)
        self.postaction = "archive"

        instapaper_key, instapaper_secret, email, password = keys
        # client = Instapaper(consumer_key=consumer_key, access_token=access_token)
        # client = None # Replace with actual Instapaper client initialization
        client = ipaper(instapaper_key, instapaper_secret)
        client.login(email, password)
        msgLog = f"{self.indent} service {self.service} End initApi"
        logMsg(msgLog, 2, 0)
        return client

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
        logMsg(msgLog, 2, 0)
        return res

    def publishApiPost(self, *args, **kwargs):
        # Add Instapaper API call to publish a post here
        return "Not implemented"

    def archiveId(self, idPost):
        # Add Instapaper API call to archive a post here
        return "Not implemented"

    def archive(self, j):
        msgLog = "Archiving %d" % j
        logMsg(msgLog, 1, 0)
        post = self.getPost(j)
        title = self.getPostTitle(post)
        idPost = self.getPostId(post)
        logging.info(f"Post {post}")
        logMsg(msgLog, 2, 0)
        logging.info(f"Title {title}")
        logMsg(msgLog, 2, 0)
        logging.info(f"Id {idPost}")
        logMsg(msgLog, 2, 0)
        rep = self.archiveId(idPost)
        msgLog = f"Rep: {rep}"
        logMsg(msgLog, 2, 0)
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
        # Extract ID from Instapaper post object
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

    import socialModules.moduleRules

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Example of how to use the module
    # for key in rules.rules.keys():
    #     if ((key[0] == 'instapaper')
    #             and (key[2] == 'YourUser')):
    #         apiSrc = rules.readConfigSrc("", key, rules.more[key])
    #
    #         try:
    #             apiSrc.setPosts()
    #         except:
    #             apiSrc.authorize()
    #         for post in apiSrc.getPosts():
    #                 print(f"Title: {apiSrc.getPostTitle(post)}")


if __name__ == "__main__":
    main()
