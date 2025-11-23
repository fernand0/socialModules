#!/usr/bin/env python

import configparser
import sys
import dateparser
import dateutil
from atproto import Client, models

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

        posts, error = self.apiCall(commandName = "get_author_feed", 
                                    actor = self.getUser())
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
        title = ''
        try:
            title = post.post.record.text
        except:
            title = ""
        return title

    def getApiPostUrl(self, post):
        idPost = self.getPostId(post)
        msgLog = f"{self.indent} getPostUrl: {post}"
        logMsg(msgLog, 2, 0)
        if idPost:
            user = self.getPostHandle(post)
            idPost = idPost.split("/")[-1]
            res = f"{self.base_url}/profile/{user}/post/{idPost}"
        else:
            res = ""
        msgLog = f"{self.indent} getPostUrl res: {res}"
        logMsg(msgLog, 2, 0)
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
            logging.debug(f"Uri")
            result = post.post.record.uri
        elif (
            hasattr(post.post.record, "facets")
            and post.post.record.facets
            and hasattr(post.post.record.facets[0].features[0], "uri")
        ):
            logging.debug(f"Facets > Uri")
            result = post.post.record.facets[0].features[0].uri
        elif (
            hasattr(post.post.record, "embed")
            and hasattr(post.post.record.embed, "external")
            and hasattr(post.post.record.embed.external, "uri")
        ):
            logging.debug(f"Embed > Uri")
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
                logging.info(f"No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)

        return res

    def publishApiRT(self, *args, **kwargs):
        if args and len(args) == 3:
            post, link, comment = args
            idPost = link.split("/")[-1]
        if kwargs:
            more = kwargs
            tweet = more["post"]
            link = self.getPostLink(tweet)
            idPost = self.getPostId(tweet)

        res = None
        # TODO

        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3 and args[0]:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        title = self.addComment(title, comment)

        # logging.info(f"Tittt: {title} {link} {comment}")
        # logging.info(f"Tittt: {link and ('twitter' in link)}")
        res = "Fail!"
        # post = post[:(240 - (len(link) + 1))]

        facets = []
        if link:
            title = title[:(300)]

            embed_external = models.AppBskyEmbedExternal.Main(
                external=models.AppBskyEmbedExternal.External(
                    title=title,
                    description="",
                    uri=link,
                )
            )
            # facets.append(models.AppBskyRichtextFacet.Main(
            #     features=[models.AppBskyRichtextFacet.Link(uri=link)],
            #     index=models.AppBskyRichtextFacet.ByteSlice(
            #         byte_start=len(title)+1,
            #         byte_end=len(title)+len(link)+1),
            #     )
            # )

            # title = title + " " + link
            # embed_post = models.AppBskyEmbedRecord.Main(record=models.create_strong_ref(post_with_link_card))
        else:
            embed_external = None

        msgLog = f"{self.indent}Publishing {title} ({len(title)})"
        logMsg(msgLog, 2, 0)
        client = self.api
        try:
            res, error = self.apiCall(
                "send_post", api=client, text=title, embed=embed_external
            )
        except atproto_client.exceptions.BadRequestError:
            res = self.report(self.service, f"Bad Request: {title} {link}", title, sys.exc_info())
        except:
            res = self.report(self.service, f"Other Exception: {title} {link}", title, sys.exc_info())

        msgLog = f"{self.indent}Res: {res} "
        logMsg(msgLog, 2, 0)
        return res

    def deleteApiPosts(self, idPost):
        res = None

        msgLog = f"{self.indent} deleteApiPosts deleting: {idPost}"
        logMsg(msgLog, 1, 0)
        res, error = self.apiCall("delete_post", self.api, post_uri=idPost)

        return res

    def deleteApiFavs(self, idPost):
        res = None
        logging.info(f"Deleting: {idPost}")
        res = self.api.delete_like(idPost)
        # res, error = self.apiCall('delete_like', self.api,  like_uri=idPost)
        msgLog = f"{self.indent} res: {res}"  # error: {error}"
        logMsg(msgLog, 1, 0)
        return res

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
        msgLog = f"{self.indent}Reply: {reply}"
        logMsg(msgLog, 1, 1)

        if hasattr(reply, "uri"):
            # Success: The reply object has a 'uri', which is the post identifier.
            res = f"https://bsky.app/profile/fernand0.bsky.social/post/"
            res = f"{res}{reply.uri.split('/')[-1]}"
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
