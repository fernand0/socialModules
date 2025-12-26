#!/usr/bin/env python

import sys

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

        return (
            instapaper_key,
            instapaper_secret,
            email,
            password,
            oauth_consumer_id,
            oauth_consumer_secret,
        )

    def authorize(self):
        logging.info("Starting authorize process")
        # Add Instapaper authorization logic here

    def initApi(self, keys):
        msgLog = f"{self.indent} Service {self.service} Start initApi " f"{self.user}"
        logMsg(msgLog, 2, False)
        self.postaction = "archive"

        (
            instapaper_key,
            instapaper_secret,
            email,
            password,
            oauth_consumer_id,
            oauth_consumer_secret,
        ) = keys
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
        link = ""

        if args and len(args) == 3:
            title, link, comment = args
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)

        if not link:
            self.res_dict["error_message"] = "No link provided to save to Instapaper."
            return self.res_dict

        try:
            # The instapaper library seems to handle the bookmark object internally.
            # We add a URL, and it gets saved.
            # The library does not seem to return a specific object with details on success.
            # We will assume success if no exception is raised.
            res = self.getClient().add_bookmark(link, title=title)
            self.res_dict["raw_response"] = res

            # The `add_bookmark` method in the library doesn't return a direct URL to the saved item,
            # but we can consider the original link as the "post_url" in this context.
            if res:
                self.res_dict["success"] = True
                self.res_dict["post_url"] = link
            else:
                self.res_dict["error_message"] = "Failed to save to Instapaper."

        except Exception as e:
            self.res_dict["error_message"] = self.report(
                self.getService(), kwargs, "", sys.exc_info()
            )
            self.res_dict["raw_response"] = e

        logging.info(f"Res: {self.res_dict}")
        return self.res_dict

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
        link = ""
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
