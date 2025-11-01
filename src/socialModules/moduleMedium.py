#!/usr/bin/env python

import configparser
import os
import sys

from medium import Client
# local version, to add notifyFollower parameter
# Medium has deprecated its API, so this module is discontinued

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class moduleMedium(Content):  # ,Queue):
    def get_user_info(self, client):
        return f"{self.user}"

    def get_post_id_from_result(self, result):
        return result.get('id')

    # def authorize(self):
    #     config = configparser.ConfigParser()
    #     configFile = CONFIGDIR + '/.rssMedium'
    #     config.read(configFile)
    #     application_id = config.get("appKeys","ClientID")
    #     application_secret = config.get("appKeys","ClientSecret")
    #     try:
    #         client = Client(application_id = application_id,
    #                 application_secret = application_secret)
    #         auth = client.exchange_authorization_code(application_secret,
    #                                       "https://elmundoesimperfecto.com/callback/medium")
    #         access_token = auth["access_token"]
    #         config.set("appKeys", 'access_token', token)
    #         shutil.copyfile(configFile, '{}.bak'.format(configFile))
    #         with open(configFile, 'w') as configfile:
    #             config.write(configfile)
    #     except:
    #         logging.info("Failure with authentication")

    def setClient(self, channel):
        # FIXME: Adapt this method
        logging.info(f"     Connecting {self.service} {channel}")
        self.service = "Medium"
        client = None
        userRaw = None
        user = None
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssMedium")
            application_id = config.get("appKeys", "ClientID")
            application_secret = config.get("appKeys", "ClientSecret")

            try:
                client = Client(
                    application_id=application_id, application_secret=application_secret
                )

                try:
                    client.access_token = config.get(channel, "access_token")
                except:
                    client.access_token = config.get("appKeys", "access_token")
                # client.access_token = config.get("appKeys","access_token")
                # Get profile details of the user identified by the access
                # token.
                userRaw = client.get_current_user()
                logging.warning(f"User: {userRaw}")
                user = userRaw["username"]
            except:
                logging.warning(f"Client: {client}")
                logging.warning(f"Client: {client.__dir__()}")
                logging.warning(f"Client: {client.get_current_user()}")
                logging.warning("Medium authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info())
        except:
            logging.warning(f"Client: {client}")
            # res = self.authorize()
            logging.warning("Account not configured")

        self.client = client
        self.user = user
        self.userRaw = userRaw

    def getUser(self):
        return self.user

    def getUserRaw(self):
        return self.userRaw

    def setPosts(self):
        logging.info(f"{self.indent} Setting posts")
        self.posts = []

        import moduleRss

        content = moduleRss.moduleRss()
        rssFeed = "https://medium.com/feed/@{}".format(self.getUser())
        # print(rssFeed)
        content.setRssFeed(rssFeed)
        content.setPosts()
        for post in content.getPosts():
            self.posts.append(post)

    def publishApiPost(self, *args, **kwargs):
        mode = ""
        tags = []
        if args and len(args) == 3:
            post, link, comment = args
            notifyFollowers = True
        if kwargs:
            more = kwargs
            comment = more.get("comment", "")
            post = more.get("title", "")
            link = more.get("link", "")
            mode = more.get("mode", "")
            tags = more.get("tags", [])
            notifyFollowers = more.get("notifyFollowers", False)
            print(f"Notify: {notifyFollowers}")
        if not mode:
            mode = "public"
        logging.info(f"    Publishing in {self.service} ...")
        logging.info(f"    Tags {tags}")
        client = self.client
        user = self.getUserRaw()
        logging.info(f"    User {user}")

        title = post
        content = comment
        # print(content)
        links = ""

        # from html.parser import HTMLParser
        # h = HTMLParser()
        # title = h.unescape(title)
        from html import unescape

        title = unescape(title)
        if link and title:
            textOrig = (
                f'Publicado originalmente en <a href="{link}">' f"{title}</a><br />\n\n"
            )
        else:
            textOrig = ""

        try:
            res = client.create_post(
                user_id=user["id"],
                title=title,
                content="<h4>" + title + "</h4><br />" + textOrig + content,
                canonical_url=link,
                content_format="html",
                publish_status=mode,
                tags=tags,
                notifyFollowers=notifyFollowers,
            )
            # "public") #draft")
            logging.debug("Res: %s" % res)
            return res
        except:
            return self.report("Medium", post, link, sys.exc_info())

    def publishApiImage(self, *postData, **kwargs):
        logging.debug(f"{self.service} postData: {postData} " f"Len: {len(postData)}")
        client = self.client
        if len(postData) == 2:
            post, imageName = postData
            more = kwargs
            if imageName:
                # with open(imageName, "rb") as imagefile:
                #         imagedata = imagefile.read()

                try:
                    myImage = client.upload_image(imageName, "image/png")
                    myImageUrl = myImage["url"]
                    if "content" in more:
                        text = f"{more['content']}\n"
                        title = text.split("\n")[0]
                        text = (
                            f"<br/><figure>\n"
                            f'<img src="{myImageUrl}">'
                            f"\n</figure>"
                            f"<br/>{text}"
                        )
                        res = self.publishApiPost(
                            title=title, comment=text, mode="draft"
                        )
                    elif "alt" in more:
                        text = f"{post}\n<br />"
                        title = text.split("\n")[0]
                        text = (
                            f"<br/><figure>\n"
                            f'<img src="{myImageUrl}">'
                            f"\n</figure>"
                            f"<br/>{text}"
                        )
                        res = self.publishApiPost(title=title, comment=text)

                    print(res)
                except:
                    res = self.report("Medium", post, imageName, sys.exc_info())
            else:
                logging.info(f"No image available")
                res = "Fail! No image available"
        else:
            res = "Fail! Not published, not enough arguments"
            logging.debug(res)
        return res

    def getApiPostTitle(self, post):
        if "title" in post:
            return post["title"].replace("\n", " ")

    def getApiPostLink(self, post):
        return(post['link'])

def main():
    import logging
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    medium_module = moduleMedium()
    tester = ModuleTester(medium_module)
    tester.run()


if __name__ == "__main__":
    main()
