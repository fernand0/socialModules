#!/usr/bin/env python

import configparser
import logging
import sys

import flickrapi

from socialModules.configMod import *
from socialModules.moduleContent import *

# from socialModules.moduleQueue import *


class moduleFlickr(Content):  # , Queue):
    def getKeys(self, config):
        KEY = config.get(self.user, "key")
        SECRET = config.get(self.user, "secret")

        return (KEY, SECRET)

    def authorize(self):
        # Get the API keys - need to determine the user first
        config = configparser.RawConfigParser()
        config.read(CONFIGDIR + '/.rssFlickr')

        # Get the first available user from the config file
        if not hasattr(self, 'user') or self.user is None:
            sections = config.sections()
            if sections:
                # Use the first section as the user
                user = sections[0]
                self.user = user
            else:
                print("No user found in config file.")
                return None

        keys = self.getKeys(config)

        # Initialize the API to get the token
        try:
            flickr = flickrapi.FlickrAPI(
                keys[0],
                keys[1],
                format="parsed-json",
                token_cache_location=f"{CONFIGDIR}",
            )

            if not hasattr(flickr, "token_valid") or not flickr.token_valid(
                perms="write"
            ):

                # Get a request token
                flickr.get_request_token(oauth_callback="oob")

                # Open a browser at the authentication URL. Do this however
                # you want, as long as the user visits that URL.
                authorize_url = flickr.auth_url(perms="write")
                print(f"Visit {authorize_url} and copy the result")

                # Get the verifier code from the user. Do this however you
                # want, as long as the user gives the application the code.
                verifier = str(input("Verifier code: "))

                # Trade the request token for an access token
                flickr.get_access_token(verifier)

                print("Authorization successful! Token has been saved.")
            else:
                print("Authorization was ok!")

        except flickrapi.exceptions.FlickrError as e:
            print(f"Authorization failed: {e}")
            return None
        except Exception as e:
            print(f"Authorization error: {e}")
            return None

        return flickr

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.base_url = "https://flickr.com"
        self.url = f"{self.base_url}/photos/{self.user}"

        authorized = False
        try:
            flickr = flickrapi.FlickrAPI(
                keys[0],
                keys[1],
                format="parsed-json",
                token_cache_location=f"{CONFIGDIR}",
            )
            if not hasattr(flickr, "token_valid") or not flickr.token_valid(
                perms="write"
            ):
                authorized = False
            else:
                authorized = True
        except requests.exceptions.ConnectionError:
            res = self.report(
                self.indent, "Error in initApi. Connection Error", "", sys.exc_info()
            )
        except flickrapi.exceptions.FlickrError:
            res = self.report(
                self.indent, "Error in initApi. Flickr Error", "", sys.exc_info()
            )
        except:
            res = self.report(self.indent, "Error in initApi", "", sys.exc_info())
            logging.info(res)
            client = None

        if not authorized:
            # Get a request token
            flickr.get_request_token(oauth_callback="oob")

            # Open a browser at the authentication URL. Do this however
            # you want, as long as the user visits that URL.
            authorize_url = flickr.auth_url(perms="write")
            print(f"Visit {authorize_url} and copy the result")

            # Get the verifier code from the user. Do this however you
            # want, as long as the user gives the application the code.
            verifier = str(input("Verifier code: "))

            # Trade the request token for an access token
            flickr.get_access_token(verifier)

        self.api = flickr
        client = flickr

        return client

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setApiPosts(self):
        posts = []

        return posts

    def setApiFavs(self):
        posts = []

        return posts

    def setApiDrafts(self):
        posts = []
        posts = self.apiCall("people.getPhotos", user_id="fernand0")
        # logging.debug(f"Post: {posts[0]}")
        # logging.debug(f"Post photos: {posts[0]['photos']}")
        # logging.debug(f"Post photos photo: {posts[0]['photos']['photo']}")
        posts = posts[0]["photos"]["photo"]
        return posts

    def getApiPostTitle(self, post):
        title = ""
        try:
            title = post["title"]
        except:
            title = ""
        return title

    def getApiPostUrl(self, post):
        res = ""

        return res

    def getApiPostLink(self, post):
        logging.debug(f"{self.indent} Post: {post}")
        link = f"{self.url}/{post['id']}"
        # logging.debug(f"{self.indent} Post link: {link}")
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post.post.record.text
        return result

    def getPostContentLink(self, post):
        result = ""
        return result

    def publishApiImage(self, *args, **kwargs):
        res = None
        return res

    def publishApiRT(self, *args, **kwargs):
        res = None
        # TODO

        return res

    def publishApiPost(self, *args, **kwargs):
        res = None
        # TODO

        return res

    def publishApiDrafts(self, *args, **kwargs):
        return self.publishApiDraft(*args, **kwargs)

    def publishApiDraft(self, *args, **kwargs):
        logging.debug(f"Args: {args} Kwargs: {kwargs}")
        if kwargs:
            post = kwargs.get("post", "")
            api = kwargs.get("api", "")
        else:
            self.res_dict["error_message"] = "Not enough arguments to publish."
            return self.res_dict

        logging.debug(f"Post: {post} Api: {api}")

        try:
            res, error = self.apiCall(
                "photos.setPerms",
                photo_id=post["id"],
                is_public=1,
                is_friend=1,
                is_family=1,
            )
            self.res_dict["raw_response"] = res

            if error:
                self.res_dict["error_message"] = str(error)
            elif res and res.get("stat") == "ok":
                self.res_dict["success"] = True
                self.res_dict["post_url"] = f"{self.url}/{post['id']}"
            elif not res:  # The original code considered a falsy response a success.
                self.res_dict["success"] = True
                self.res_dict["post_url"] = f"{self.url}/{post['id']}"
                self.res_dict["raw_response"] = "OK. Published!"
            else:
                self.res_dict["error_message"] = f"Flickr API error: {res}"
        except Exception as e:
            self.res_dict["error_message"] = f"Exception during Flickr API call: {e}"
            self.res_dict["raw_response"] = sys.exc_info()

        logging.debug(f"Res: {self.res_dict}")
        return self.res_dict

    def deleteApiPosts(self, idPost):
        res = None

        return res

    def deleteApiFavs(self, idPost):
        res = None

        return res

    def processReply(self, reply):
        res = ""
        msgLog = f"{self.indent}Reply: {reply}"
        logMsg(msgLog, 1, False)
        origReply = reply[0]
        if "stat" in origReply and origReply.get("stat") == "ok":
            if "Fail!" not in reply:
                idPost = self.getPostId(origReply)
                res = f"https://flickr.com/photos/{self.user}/status/{idPost}"
        return res

    def getPostHandle(self, post):
        res = None
        logging.info(res)
        print(f"Post: {post}")

        return handle

    def getPostId(self, post):
        try:
            idPost = post.get("photoid").get("_content")
        except:
            idPost = ""

        return idPost


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    flickr_module = moduleFlickr()
    if len(sys.argv) > 1 and (
        sys.argv[1] == "authenticate" or sys.argv[1] == "authorize"
    ):
        flickr_module.authorize()
        sys.exit(0)

    from socialModules.moduleTester import ModuleTester

    tester = ModuleTester(flickr_module)
    tester.run()


if __name__ == "__main__":
    main()
