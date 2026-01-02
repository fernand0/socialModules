#!/usr/bin/env python

import sys

from atproto import Client, models, IdResolver

from socialModules.configMod import *
from socialModules.moduleContent import *

# from socialModules.moduleQueue import *


class moduleBlsk(Content):  # , Queue):
    def getKeys(self, config):
        USER = config.get(self.user, "user")
        PASSWORD = config.get(self.user, "password")

        return (USER, PASSWORD)

    def initApi(self, keys):
        # FIXME: Do we call this method directly?
        self.base_url = "https://bsky.app"
        self.url = f"{self.base_url}/profile/{self.user}"
        # self.authentication = OAuth(keys[2], keys[3], keys[0], keys[1])
        # client = Twitter(auth=self.authentication)

        client = Client()
        try:
            profile = client.login(keys[0], keys[1])
            self.me = client.get_profile(actor=keys[0])
        # except atproto_client.exceptions.NetworkError:
        #     self.report(
        #         self.service, "Error in setApiFavs. Network Error. ", "", sys.exc_info()
        #     )
        except:
            res = self.report(self.indent, "Error in initApi", "", sys.exc_info())
            logging.info(res)
            client = None
        # if hasattr(client, 'app'):
        #     client = client.app.bsky.feed
        self.api = client
        self.fileName = ""
        return client

    def getClient(self):
        return self.api

    def getApi(self):
        api = None
        if hasattr(self, "api"):
            api = self.api
        return api

    def setNick(self, nick=None):
        nick = ""
        if not nick:
            nick = self.getUrl()
            if nick:
                nick = nick.split("/")[-1].split(".")[0]
        self.nick = nick

    def setApiPosts(self):
        posts = []

        posts, error = self.apiCall(commandName="get_author_feed",
                                    actor=self.me.did)
        print(f"Posts: {posts}")
        print(f"Error: {error}")

        if error:
            return []

        if not error:
            posts = posts["feed"]

        return posts

    def setApiFavs(self):
        posts = []

        if hasattr(self, "me"):
            try:
                posts, error = self.apiCall(
                    "get_actor_likes",
                    api=self.client.app.bsky.feed,
                    params={"actor": self.me.did},
                )

                if not error:
                    posts = posts["feed"]
            except atproto_client.exceptions.NetworkError:
                self.report(
                    self.service,
                    "Error en setApiFavs. Network Error. ",
                    "",
                    sys.exc_info(),
                )
            except:
                self.report(self.service, "Error en setApiFavs", "", sys.exc_info())

        return posts

    def getApiPostTitle(self, post):
        title = ""
        try:
            title = post.post.record.text
        except:
            title = ""
        return title

    def getApiPostUrl(self, post):
        idPost = self.getPostId(post)
        msgLog = f"{self.indent} getPostUrl: {post}"
        logMsg(msgLog, 2, False)
        if idPost:
            user = self.getPostHandle(post)
            idPost = idPost.split("/")[-1]
            res = f"{self.base_url}/profile/{user}/post/{idPost}"
        else:
            res = ""
        msgLog = f"{self.indent} getPostUrl res: {res}"
        logMsg(msgLog, 2, False)
        return res

    def getApiPostLink(self, post):
        # FIXME: Are you sure? (inconsistent)
        content, link = self.extractPostLinks(post)
        return link

    def extractPostLinks(self, post, linksToAvoid=""):
        return (self.getPostContent(post), self.getPostContentLink(post))

    def getPostContent(self, post):
        result = post.post.record.text
        # if 'full_text' in post:
        #     result = post.get('full_text')
        return result

    def getPostContentLink(self, post):
        result = ""
        logging.debug(f"Record: {post.post.record}")
        if hasattr(post.post.record, "uri"):
            logging.debug("Uri")
            result = post.post.record.uri
        elif (
            hasattr(post.post.record, "facets")
            and post.post.record.facets
            and hasattr(post.post.record.facets[0].features[0], "uri")
        ):
            logging.debug("Facets > Uri")
            result = post.post.record.facets[0].features[0].uri
        elif (
            hasattr(post.post.record, "embed")
            and hasattr(post.post.record.embed, "external")
            and hasattr(post.post.record.embed.external, "uri")
        ):
            logging.debug("Embed > Uri")
            result = post.post.record.embed.external.uri
        if not result:
            result = self.getPostUrl(post)

        return result

    def publishApiImage(self, *args, **kwargs):
        res = None
        if len(args) == 2:
            post, imageName = args
            more = kwargs
            if imageName and os.path.exists(imageName):
                with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

                try:
                    imgAlt = None
                    if "alt" in more:
                        logging.debug(
                            f"Setting up alt: {more['alt']}" f" in image {imageName}"
                        )
                        imgAlt = more["alt"]
                    res, error = self.apiCall(
                        "send_image",
                        api=self.api,
                        text=post,
                        image=imagedata,
                        image_alt=imgAlt,
                    )

                except:
                    res = self.report(self.service, post, imageName, sys.exc_info())
            else:
                logging.info("No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)

        return res

    def publishApiRT(self, *args, **kwargs):
        if args and len(args) == 3:
            post, link, comment = args
            # idPost = link.split("/")[-1]
        # if kwargs:
            # more = kwargs
            # tweet = more["post"]
            # link = self.getPostLink(tweet)
            # idPost = self.getPostId(tweet)

        res = None
        # TODO

        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3 and args[0]:
            title, link, comment = args
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)
        else:
            self.res_dict["error_message"] = "Not enough arguments to publish."
            return self.res_dict

        title = self.addComment(title, comment)
        embed_external = None
        if link:
            title = title[:300]
            embed_external = models.AppBskyEmbedExternal.Main(
                external=models.AppBskyEmbedExternal.External(
                    title=title,
                    description="",
                    uri=link,
                )
            )

        msgLog = f"{self.indent}Publishing {title} ({len(title)})"
        logMsg(msgLog, 2, False)

        try:
            res, error = self.apiCall(
                "send_post", api=self.api, text=title, embed=embed_external
            )
            self.res_dict["raw_response"] = res
            if error:
                self.res_dict["error_message"] = str(error)
                self.res_dict["raw_response"] = error
            elif res and hasattr(res, "uri"):
                self.res_dict["success"] = True
                self.res_dict["post_url"] = (
                    f"{self.base_url}/profile/{self.me.handle}/post/{res.uri.split('/')[-1]}"
                )
            else:
                self.res_dict["error_message"] = (
                    "Publication failed for an unknown reason."
                )
        except atproto_client.exceptions.BadRequestError as e:
            self.res_dict["error_message"] = self.report(
                self.service, f"Bad Request: {title} {link}", title, sys.exc_info()
            )
            self.res_dict["raw_response"] = e
        except Exception as e:
            self.res_dict["error_message"] = self.report(
                self.service, f"Other Exception: {title} {link}", title, sys.exc_info()
            )
            self.res_dict["raw_response"] = e

        msgLog = f"{self.indent}Res: {self.res_dict['raw_response']} "
        logMsg(msgLog, 2, False)
        return self.res_dict

    def deleteApiPosts(self, idPost):
        self.res_dict = self.get_empty_res_dict()
        msgLog = f"{self.indent} deleteApiPosts deleting: {idPost}"
        logMsg(msgLog, 1, False)
        res, error = self.apiCall("delete_post", self.api, post_uri=idPost)
        if error:
            self.res_dict["success"] = False
            self.res_dict["error_message"] = error
            self.res_dict["raw_response"] = res
        else:
            self.res_dict["success"] = True
            self.res_dict["raw_response"] = res

        return self.res_dict

    def deleteApiFavs(self, idPost):
        self.res_dict = self.get_empty_res_dict()
        logging.info(f"Deleting: {idPost}")
        res, error = self.apiCall("delete_like", self.api, like_uri=idPost)
        if error:
            self.res_dict["success"] = False
            self.res_dict["error_message"] = error
            self.res_dict["raw_response"] = res
        else:
            self.res_dict["success"] = True
            self.res_dict["raw_response"] = res

        msgLog = f"{self.indent} res: {self.res_dict}"
        logMsg(msgLog, 1, False)
        return self.res_dict

    def getPostHandle(self, post):
        handle = post.post.author.handle
        return handle

    def getPostId(self, post):
        idPost = ""
        if isinstance(post, str) or isinstance(post, int):
            # It is the tweet URL
            idPost = post
        else:
            if self.getPostsType() == "favs":
                idPost = post.post.viewer.like
            else:
                idPost = post.post.uri

        return idPost

    def processReply(self, reply):
        res = ""
        # msgLog = f"{self.indent}Reply: {reply}"
        # logMsg(msgLog, 1, False)

        if hasattr(reply, "uri"):
            # Success: The reply object has a 'uri', which is the post identifier.
            res = "https://bsky.app/profile/fernand0.bsky.social/post/"
            res = f"{res}{reply.uri.split('/')[-1]}"
        elif hasattr(reply, "post_url"):
            res = reply["post_url"]
        elif isinstance(reply, bool):
            res = reply
        elif isinstance(reply, str) and "Fail" in reply:
            # Failure: The reply is an explicit failure string.
            res = reply
        elif not reply:
            # Failure: The reply is None, False, or empty.
            res = "Fail! No reply from API."
        else:
            # Failure: The reply is in an unexpected format.
            res = f"Fail! Unexpected reply type: {type(reply)}"

        return res

    def register_specific_tests(self, tester):
        # No specific tests for now
        pass

    def get_user_info(self, apiSrc):
        profile = apiSrc.getClient().get_profile(actor=apiSrc.user)
        if profile:
            return f"{profile.display_name} (@{profile.handle})"
        return "Unknown user"

    def get_post_id_from_result(self, result):
        if hasattr(result, "uri"):
            return result.uri
        return None


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    blsk_module = moduleBlsk()
    tester = ModuleTester(blsk_module)
    tester.run()


if __name__ == "__main__":
    main()
