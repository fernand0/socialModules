#!/usr/bin/env python

import configparser
import logging
import urllib
from slack_sdk import WebClient

# from slack_sdk.errors import SlackApiError

# https://slack.dev/python-slack-sdk/v3-migration/

import sys
import time
import click
from bs4 import BeautifulSoup

from moduleContent import *
from moduleQueue import *


class moduleSlack(Content, Queue):
    def __init__(self):
        super().__init__()
        self.slack_token = None
        self.user_slack_token = None
        self.channel = None

    def getKeys(self, config):
        slack_token = config.get(self.service, "oauth-token")
        user_slack_token = config.get(self.service, "user-oauth-token")
        return (slack_token, user_slack_token)

    def initApi(self, keys):
        client = WebClient(keys[0])
        self.slack_token = keys[0]
        self.user_slack_token = keys[1]
        return client

    def setChannel(self, channel="links"):
        # setPage in Facebook
        theChannel = self.getChanId(channel)
        self.channel = theChannel

    def getChannel(self):
        return self.channel

    # def setClient(self, user=None):
    #    # https://api.slack.com/authentication/basics
    #    logging.info("     Setting Client")
    #    logging.info("     Connecting {}".format(self.service))
    #    try:
    #        config = configparser.ConfigParser()
    #        config.read(CONFIGDIR + "/.rssSlack")

    #        if config.sections():
    #            self.slack_token = config.get("Slack", "oauth-token")
    #            self.user_slack_token
    #                   = config.get("Slack", "user-oauth-token")

    #            self.sc = WebClient(self.slack_token)
    #        else:
    #            logging.warning("Account not configured")
    #            if sys.exc_info()[0]:
    #                logging.warning(
    #                    "Unexpected error: {}".format(sys.exc_info()[0])
    #                )
    #            print("Please, configure a {} Account".format(self.service))
    #            sys.exit(-1)
    #    except:
    #        logging.warning("Something failed. not configured")
    #        if sys.exc_info()[0]:
    #            logging.warning(
    #                "Unexpected error: {}".format(sys.exc_info()[0])
    #            )
    #            logging.info(self.report(self.service,
    #                         "", "", sys.exc_info()))
    #        print("Please, configure a {} Account".format(self.service))
    #        sys.exit(-1)
    #        logging.info(self.report("Slack", text, sys.exc_info()))
    #        self.sc = slack.WebClient(token=self.slack_token)

    #    config = configparser.ConfigParser()
    #    config.read(CONFIGDIR + "/.rssBlogs")
    #    section = "Blog7"

    #    url = config.get(section, "url")
    #    self.setUrl(url)
    #    self.setSocialNetworks(config[section])
    #    # if ('buffer' in config.options(section)):
    #    #    self.setBufferapp(config.get(section, "buffer"))

    #    if "cache" in config.options(section):
    #        self.setProgram(config.get(section, "cache"))
    #        logging.info("getProgram {}".format(str(self.getProgram())))

    #    logging.info("     Connected {}".format(self.service))

    def setSlackClient(self, slackCredentials):
        self.service = "slack"
        config = configparser.ConfigParser()
        if not slackCredentials:
            slackCredentials = CONFIGDIR + "/.rssSlack"
        config.read(slackCredentials)

        self.slack_token = config["Slack"].get("oauth-token")
        self.user_slack_token = config["Slack"].get("user-oauth-token")

        try:
            self.sc = WebClient(self.slack_token)
        except:
            logging.info(self.report("Slack", "", "", sys.exc_info()))
            self.sc = slack.WebClient(token=self.slack_token)

        config = configparser.ConfigParser()
        config.read(CONFIGDIR + "/.rssBlogs")
        section = "Blog7"

        url = config.get(section, "url")
        self.setUrl(url)
        self.oldsetSocialNetworks(config, section)
        #    # if ('buffer' in config.options(section)):
        #    #    self.setBufferapp(config.get(section, "buffer"))

        if "cache" in config.options(section):
            self.setProgram(config.get(section, "cache"))
            logging.info("getProgram {}".format(str(self.getProgram())))

    def getSlackClient(self):
        return self.sc

    def setApiPosts(self):
        if not self.channel:
            # Can we improve this in mosuleSlack and moduleFacebook?
            self.setChannel('links')
        posts = []
        theChannel = self.getChannel()
        self.getClient().token = self.slack_token
        data = {"count": 1000, "channel": theChannel}
        history = self.getClient().api_call("conversations.history", data=data)
        try:
            posts = history["messages"]
        except:
            posts = []

        return posts

    # def setPosts(self, channel="links"):
    #     logging.info(" Setting posts")
    #     self.posts = []
    #     theChannel = self.getChanId(channel)
    #     try:
    #         self.getClient().token = self.slack_token
    #         data = {"count": 1000, "channel": theChannel}
    #         history = self.getClient().api_call("conversations.history",
    #                                             data=data)
    #         try:
    #             self.posts = history["messages"]
    #         except:
    #             self.posts = []
    #     except:
    #         logging.warning(self.report(self.service, "",
    #                         "", sys.exc_info()))
    #         self.posts = []

    #     logging.info(" Set posts")

    def processReply(self, reply):
        if self.getAttribute(reply, "ok"):
            res = self.getAttribute(reply, "ts")
        else:
            res = "Fail!"
        return res

    def publishApiPost(self, postData):
        post, link, comment, plus = postData
        chan = self.getChannel()
        # logging.info(f"Publishing {post} in {chan}")
        self.getClient().token = self.user_slack_token
        data = {"channel": chan, "text": f"{post} {link}"}
        result = self.getClient().api_call("chat.postMessage", data=data)  # ,
        self.getClient().token = self.slack_token
        return result

    def deleteApiPosts(self, idPost):
        # theChannel or the name of the channel?
        theChan = self.getChannel()

        result = None

        self.getClient().token = self.user_slack_token
        data = {"channel": theChan, "ts": idPost}
        result = self.getClient().api_call(
            "chat.delete", data=data
        )  # , channel=theChannel, ts=idPost)

        return result

    # def deletePost(self, idPost, chan):
    #     # theChannel or the name of the channel?
    #     theChan = self.getChanId(chan)
    #     logging.info("Deleting id %s from %s" % (idPost, theChan))

    #     result = None

    #     try:
    #         self.getClient().token = self.user_slack_token
    #         data = {"channel": theChan, "ts": idPost}
    #         result = self.getClient().api_call(
    #             "chat.delete", data=data
    #         )  # , channel=theChannel, ts=idPost)
    #     except:
    #         logging.info(
    #             self.report("Slack", "Error deleting", "", sys.exc_info())
    #         )

    #     logging.debug(result)
    #     return result

    def getPostId(self, post):
        idPost = self.getAttribute(post, "ts")
        return idPost

    def getPostTitle(self, post):
        if ("attachments" in post) and ("title" in post["attachments"][0]):
            return post["attachments"][0]["title"]
        elif "text" in post:
            text = post["text"]
            if text.startswith("<"):
                title = text.split("|")[1]
                titleParts = title.split(">")
                title = titleParts[0]
                if (len(titleParts) > 1) and (titleParts[1].find("<") >= 0):
                    # There is a link
                    title = title + titleParts[1].split("<")[0]
            else:
                pos = text.find("<")
                title = text[:pos]
            return title
        else:
            return "No title"

    def getPostUrl(self, post):
        return (
            f"{self.getUser()}archives/"
            f"{self.getChannel()}/p{self.getPostId(post)}"
        )

    def getPostLink(self, post):
        if "attachments" in post:
            link = post["attachments"][0]["original_url"]
        else:
            text = post["text"]
            if text.startswith("<") and text.count("<") == 1:
                # The link is the only text
                link = post["text"][1:-1]
            else:
                # Some people include URLs in the title of the page
                pos = text.rfind("<")
                link = text[pos + 1 : -1]
        return link

    def publish(self, j):
        logging.info("Publishing %d" % j)
        post = self.obtainPostData(j)
        logging.info("Publishing %s" % post[0])
        update = ""
        title = self.getTitle(j)
        url = self.getLink(j)
        logging.info("Title: %s" % str(title))
        logging.info("Url: %s" % str(url))

        if self.getProgram():
            logging.info("getProgram")
            for profile in self.getSocialNetworks():
                nick = self.getSocialNetworks()[profile]
                logging.info("Social: {} Nick: {}".format(profile, nick))
                if (profile[0] in self.getProgram()) or (
                    profile in self.getProgram()
                ):
                    logging.info("Social: {} Nick: {}".format(profile, nick))
                    socialNetwork = (profile, nick)

                    listP = self.cache[socialNetwork].setPosts()
                    listP = self.cache[socialNetwork].getPosts()
                    listPsts = self.obtainPostData(j)
                    listP = listP + [listPsts]
                    self.cache[socialNetwork].posts = listP
                    update = (
                        update + self.cache[socialNetwork].updatePostsCache()
                    )
                    logging.info("Uppdate: {}".format(update))
                    update = update + "\n"

        theChannel = "links"  # self.getChanId("links")
        res = self.deletePost(self.getId(j), theChannel)
        logging.info("Res: %s" % str(res))
        update = update + str(res["ok"])

        logging.info("Publishing title: %s" % title)
        logging.info("Update before return %s" % update)
        return update

    # def delete(self, j, theChannel=None):
    #     logging.info("Deleting id %s" % j)
    #     if not theChannel:
    #         theChannel = self.getChanId("links")
    #     idPost = self.getId(j)
    #     # self.sc.token = self.user_slack_token
    #     logging.info("Deleting id %s" % idPost)
    #     data = {"channel": theChannel, "ts": idPost}
    #     result = self.getClient().api_call("chat.delete", data=data)
    #     # self.sc.token = self.slack_token
    #     logging.info(result)
    #     return result["ok"]

    def getChanId(self, name):
        logging.debug("getChanId %s" % self.service)

        self.getClient().token = self.user_slack_token
        chanList = self.getClient().api_call("conversations.list")["channels"]
        self.getClient().token = self.slack_token
        for channel in chanList:
            if channel["name_normalized"] == name:
                return channel["id"]
        return None

    def extractDataMessage(self, i):
        logging.info("Service %s" % self.service)
        (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        ) = (None, None, None, None, None, None, None, None, None, None)

        if i < len(self.getPosts()):
            post = self.getPost(i)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLinkl(post)

            theLinks = None
            content = None
            theContent = None
            firstLink = theLink
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        )

    def obtainPostData(self, i, debug=False):
        # This does not belong here
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]
        if "attachments" in post:
            post = post["attachments"][0]

        theContent = ""
        url = ""
        firstLink = ""
        logging.debug("i %d", i)
        logging.debug("post %s", post)

        theTitle = self.getTitle(i)
        theLink = self.getLink(i)
        logging.info(theTitle)
        logging.info(theLink)
        if theLink.find("tumblr") > 0:
            theTitle = post["text"]
        firstLink = theLink
        if "text" in post:
            content = post["text"]
        else:
            content = theLink
        theSummary = content
        theSummaryLinks = content
        if "image_url" in post:
            theImage = post["image_url"]
        elif "thumb_url" in post:
            theImage = post["thumb_url"]
        else:
            logging.info("Fail image")
            logging.debug("Fail image %s", post)
            theImage = ""

        if "original_url" in post:
            theLink = post["original_url"]
        elif url:
            theLink = url
        else:
            theLink = self.getPostLink(post)

        if "comment" in post:
            comment = post["comment"]
        else:
            comment = ""

        # print("content", content)
        theSummaryLinks = ""

        if not content.startswith("http"):
            soup = BeautifulSoup(content, "lxml")
            link = soup.a
            if link:
                firstLink = link.get("href")
                if firstLink:
                    if firstLink[0] != "h":
                        firstLink = theLink

        if not firstLink:
            firstLink = theLink

        if "image_url" in post:
            theImage = post["image_url"]
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks

        theContent = ""
        theSummaryLinks = ""

        if "image_url" in post:
            theImage = post["image_url"]
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks

        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:     ", theTitle)
        logging.debug("Link:      ", theLink)
        logging.debug("First Link:", firstLink)
        logging.debug("Summary:   ", content[:200])
        logging.debug("Sum links: ", theSummaryLinks)
        logging.debug("the Links", theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")

        return (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        )

    # def publishPost(self, msg, link, chan="links"):
    #     theChan = self.getChanId(chan)
    #     logging.info(f"Publishing {msg} in {chan}")
    #     try:
    #         self.getClient().token = self.user_slack_token
    #         data = {"channel": theChan, "text": f"{msg} {link}"}
    #         result = self.getClient().api_call(
    #             "chat.postMessage", data=data
    #         )  # ,
    #         self.getClient().token = self.slack_token
    #     except:
    #         logging.info(self.report("Slack", "", "", sys.exc_info()))
    #         result = self.getClient().chat_postMessage(
    #             channel=theChan, text=f"{msg} {link}"
    #         )
    #     logging.info(result["ok"])
    #     logging.info("End publishing %s" % msg)
    #     return result

    def getBots(self, channel="tavern-of-the-bots"):
        if not self.posts:
            oldChan = self.getChannel()
            self.setChannel(channel)
            self.setPosts()
            self.channel = oldChan
        msgs = {}
        for msg in self.getPosts():
            if msg["text"].find("Hello") >= 0:
                posN = msg["text"].find("Name:") + 6
                posFN = msg["text"].find('"', posN)
                posI = msg["text"].find("IP:") + 4
                posFI = msg["text"].find(" ", posI + 1) - 1
                posC = msg["text"].find("[")
                name = msg["text"][posN:posFN]
                ip = msg["text"][posI:posFI]
                command = msg["text"][posC + 1 : posC + 2]
                if name not in msgs:
                    theTime = "%d-%d-%d" % time.localtime(float(msg["ts"]))[:3]
                    msgs[name] = (ip, command, theTime)
        theBots = []
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a, b, c, name))
        return theBots

    def search(self, channel, text):
        logging.debug("     Searching in Slack...")
        try:
            self.getClient().token = self.slack_token
            data = {"query": text}
            res = self.getClient().api_call(
                "search.messages", data=data
            )  # , query=text)

            if res:
                logging.info(self.report(self.service, "", "", sys.exc_info()))
                return res
        except:
            return self.report("Slack", text, sys.exc_info())


def main():

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    import moduleSlack

    site = moduleSlack.moduleSlack()
    # CHANNEL = "tavern-of-the-bots"

    try:
        # My own config settings
        config = configparser.ConfigParser()
        config.read(CONFIGDIR + "/.rssBlogs")

        section = "Blog7"
        url = config.get(section, "url")
        site.setSocialNetworks(config)
        print(site.getSocialNetworks())
    except:
        url = "http://fernand0-errbot.slack.com/"
    site.setClient(url)
    site.setChannel("links")

    # site.setSocialNetworks(socialNetworks)
    # print("---")
    # print(site.getSocialNetworks())
    # print("---")
    # print(site.getSocialNetworks())

    # print("Testing posting and deleting")
    res = site.publishPost(
        "Prueba borrando 7", "http://elmundoesimperfecto.com/", ""
    )
    print("res", res)
    # idPost = res
    # print(idPost)
    # input("Delete? ")
    # site.deletePostId(idPost)
    # sys.exit()
    print("Testing posts")
    site.setPostsType("posts")
    site.setPosts()

    print("Testing title and link")

    for i, post in enumerate(site.getPosts()):
        title = site.getPostTitle(post)
        link = site.getPostLink(post)
        url = site.getPostUrl(post)
        theId = site.getPostId(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")

    i = 0
    post = site.getPost(i)
    title = site.getPostTitle(post)
    link = site.getPostLink(post)
    url = site.getPostUrl(post)
    print(post)
    print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
    input("Delete?")
    site.delete(i)
    sys.exit()

    for i, post in enumerate(site.getPosts()):
        title = site.getPostTitle(post)
        link = site.getPostLink(post)
        url = site.getPostUrl(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
        input("Delete?")
        print("Deleted https://twitter.com/i/status/{}".format(site.delete(i)))

        time.sleep(5)

    sys.exit()

    res = site.search("url:fernand0")

    for tt in res["statuses"]:
        # print(tt)
        print(
            "- @{0} {1} https://twitter.com/{0}/status/{2}".format(
                tt["user"]["name"], tt["text"], tt["id_str"]
            )
        )
    sys.exit()


if __name__ == "__main__":
    main()
    print("Set Client")
    site.setClient("fernand0-errbot")
    print("sc", site.getClient())
    site.setUrl(url)
    site.setPosts()

    print("Posts: {}".format(site.getPosts()))
    sys.exit()
    theChannel = site.getChanId(CHANNEL)
    print("the Channel {} has code {}".format(CHANNEL, theChannel))
    site.setPosts(CHANNEL)
    # post = site.getPosts()[0] # Delete de last post
    post = site.publishPost(CHANNEL, "test")
    print(post)
    input("Delete ?")
    print(site.deletePost(post["ts"], CHANNEL))
    res = site.search(
        "links",
        "https://elmundoesimperecto.com/",
    )
    print("res", res)
    print("res", res["messages"]["total"])
    sys.exit()
    post = site.getPosts()[0]
    print(site.getPostTitle(post))
    print(site.getPostLink(post))
    rep = site.publishPost("tavern-of-the-bots", "hello")
    input("Delete %s?" % rep)
    theChan = site.getChanId("tavern-of-the-bots")
    rep = site.deletePost(rep["ts"], theChan)

    sys.exit()

    site.setPosts("links")
    site.setPosts("tavern-of-the-bots")
    print(site.getPosts())
    print(site.getBots())
    print(site.sc.api_call("channels.list"))
    sys.exit()
    rep = site.publishPost("tavern-of-the-bots", "hello")
    site.deletePost(rep["ts"], theChan)
    sys.exit()

    site.setSocialNetworks(config, section)

    if "buffer" in config.options(section):
        site.setBufferapp(config.get(section, "buffer"))

    if "cache" in config.options(section):
        site.setProgram(config.get(section, "cache"))

    theChannel = site.getChanId("links")

    i = 0
    listLinks = ""

    lastUrl = ""
    for i, post in enumerate(site.getPosts()):
        url = site.getLink(i)
        if urllib.parse.urlparse(url).netloc == lastUrl:
            listLinks = listLinks + "%d>> %s\n" % (i, url)
        else:
            listLinks = listLinks + "%d) %s\n" % (i, url)
        lastUrl = urllib.parse.urlparse(url).netloc
        print(site.getTitle(i))
        print(site.getLink(i))
        print(site.getPostTitle(post))
        print(site.getPostLink(post))
        i = i + 1

    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == "x":
        sys.exit()

    elem = int(i)
    print(site.getPosts()[elem])

    action = input("Delete [d], publish [p], exit [x] ")

    if action == "x":
        sys.exit()
    elif action == "p":
        if site.getBufferapp():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getBufferapp():
                    print("   getBuffer %s" % profile)
                    socialNetwork = (
                        profile,
                        site.getSocialNetworks()[profile],
                    )
                    title = site.getTitle(elem)
                    url = site.getLink(elem)
                    listPosts = []
                    listPosts.append((title, url))
                    site.buffer[socialNetwork].addPosts(listPosts)

        if site.getProgram():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getProgram():
                    print("   getProgram %s" % profile)

                    socialNetwork = (
                        profile,
                        site.getSocialNetworks()[profile],
                    )

                    listP = site.cache[socialNetwork].getPosts()
                    listPsts = site.obtainPostData(elem)
                    listP = listP + [listPsts]
                    # for i,l in enumerate(listP):
                    #    print(i, l)
                    # sys.exit()
                    site.cache[socialNetwork].posts = listP
                    site.cache[socialNetwork].updatePostsCache()
        t = moduleTumblr.moduleTumblr()
        t.setClient("fernand0")
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        t.publishPost(title, url, "")

    site.deletePost(site.getId(j), theChannel)
    # print(outputData['Slack']['pending'][elem][8])


if __name__ == "__main__":
    main()
