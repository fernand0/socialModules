#!/usr/bin/env python

import configparser
import logging
import sys
import time

from slack_sdk import WebClient

from socialModules.moduleContent import *

# from socialModules.moduleQueue import *

# from slack_sdk.errors import SlackApiError

# https://slack.dev/python-slack-sdk/v3-migration/


class moduleSlack(Content):  # , Queue):
    def getKeys(self, config):
        slack_token = config.get(self.service, "oauth-token")
        user_slack_token = config.get(self.service, "user-oauth-token")
        return (slack_token, user_slack_token)

    def initApi(self, keys):
        self.indent = f"{self.indent} "
        msgLog = f"{self.indent} Start initApi"
        logMsg(msgLog, 2, False)
        self.slack_token = None
        self.user_slack_token = None
        self.channel = None
        self.postaction = None
        self.service = "Slack"

        msgLog = f"{self.indent} Nick: {self.nick}"
        logMsg(msgLog, 2, False)
        self.setUser(self.nick)
        # if self.user and self.user.find('/')>=0:
        #    self.name = self.user.split('/')[2].split('.')[0]
        #    self.nick = self.user.split('/')[2]
        # else:
        #    self.name = self.user
        # if self.user.find('@')>=0:
        #    channel, user = self.user.split('@')
        #    self.user = user
        #    #self.setChannel(channel)

        client = WebClient(keys[0])
        self.slack_token = keys[0]
        self.user_slack_token = keys[1]

        msgLog = f"{self.indent} End initApi"
        logMsg(msgLog, 2, False)
        self.indent = self.indent[:-1]
        return client

    def getChannels(self):
        response = self.getClient().conversations_list()
        conversations = response.get("channels", "")
        return conversations

    def setNick(self, nick=None):
        if not nick:
            nick = self.getUrl()
        #    nick = nick.split("/")[2].split(".")[0]
        self.nick = nick

    def setUser(self, user=""):
        self.user = user
        self.setNick()

    # def setNick(self, nick=""):
    #     if not nick:
    #         nick = self.getUrl()
    #         if nick and nick.find("/") >= 0:
    #             nick = nick.split("/")[2].split(".")[0]
    #         elif nick and nick.find("@") >= 0:
    #             channel, nick = nick.split("@")
    #             # self.setChannel(channel)
    #         self.nick = nick

    def setChannel(self, channel=""):
        # setPage in Facebook
        if not channel:
            listChannels = self.getChannels()[3]
            # FIXME. There should be a better way
            msgLog = f"{self.indent} List of channels: {listChannels}"
            logMsg(msgLog, 2, False)
            channel = listChannels.get("name", "")
        theChannel = self.getChanId(channel)
        self.channel = theChannel

    def getChannel(self):
        return self.channel

    def setSlackClient(self, slackCredentials):
        config = configparser.ConfigParser()
        if not slackCredentials:
            slackCredentials = CONFIGDIR + "/.rssSlack"
        config.read(slackCredentials)

        self.slack_token = config["Slack"].get("oauth-token")
        self.user_slack_token = config["Slack"].get("user-oauth-token")

        try:
            self.sc = WebClient(self.slack_token)
        except:
            self.report("Slack", "", "", sys.exc_info())
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
            # logging.info("getProgram {}".format(str(self.getProgram())))

    def getSlackClient(self):
        return self.sc

    def setApiPosts(self):
        msgLog = f"{self.indent} Service {self.service} Start setApiPosts"
        logMsg(msgLog, 2, False)
        if not hasattr(self, "channel") or not self.channel:
            # FIXME
            # Can we improve this in mosuleSlack and moduleFacebook?
            self.setChannel("links")
        posts = []
        theChannel = self.getChannel()
        self.getClient().token = self.slack_token
        data = {"limit": 1000, "channel": theChannel}
        history = self.getClient().api_call("conversations.history", data=data)
        try:
            posts = history["messages"]
        except:
            posts = []

        msgLog = f"{self.indent} Service {self.service} End setApiPosts"
        logMsg(msgLog, 2, False)
        # logging.debug(f"Posts: {posts}")
        return posts

    def processReply(self, reply):
        # FIXME: Being careful with publishPost, publishPosPost, publishNextPost, publishApiPost
        res = reply
        # if isinstance(reply, dict):
        #     res = reply.get("ok", "Fail!")
        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, link, comment = args
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            # comment = api.getPostComment(title)
        else:
            self.res_dict["error_message"] = "Not enough arguments for publication."
            return self.res_dict

        chan = self.getChannel()
        if not chan:
            self.setChannel()
            chan = self.getChannel()
        msgLog = f"{self.indent} Service {self.service} Channel: {chan}"
        logMsg(msgLog, 2, False)

        try:
            self.getClient().token = self.user_slack_token
            data = {"channel": chan, "text": f"{title} {link}"}
            result = self.getClient().api_call("chat.postMessage", data=data)
            logMsg(f"Result api: {result}")
            self.getClient().token = self.slack_token

            self.res_dict["raw_response"] = result
            if result["ok"]:
                self.res_dict["success"] = True
                self.res_dict["post_url"] = self.getAttribute(result, 'post_url')
                # Construct post_url if possible
                if "channel" in result and "ts" in result:
                    self.res_dict["post_url"] = self.getApiPostUrl(result)
            else:
                self.res_dict["error_message"] = (
                    f"Slack API error: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            self.res_dict["error_message"] = f"Exception during Slack API call: {e}"
            self.res_dict["raw_response"] = sys.exc_info()

        return self.res_dict

    def editApiPost(self, post, newContent):
        theChan = self.getChannel()
        idPost = self.getPostId(post)

        result = None
        self.getClient().token = self.user_slack_token
        data = {"channel": theChan, "ts": idPost, "text": newContent}
        result = self.getClient().api_call("chat.update", data=data)
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

    def editApiLink(self, post, newLink):
        # oldLink = self.getPostLink(post)
        # idPost = self.getLinkPosition(oldLink)
        # oldTitle = self.getPostTitle(post)
        self.setPostLink(post, newLink)
        self.updatePostsCache()

    def setPostLink(self, post, newLink):
        logMsg(f"Post: {post}", 1, False)
        if "attachments" in post:
            post["attachments"][0]["original_url"] = newLink
        else:
            text = post["text"]
            if text.startswith("<") and text.count("<") == 1:
                logMsg("Starts", 2, False)
                # The link is the only text
                post["text"][1:-1] = newLink
            elif text.find("<h") >= 0:
                logMsg("<h", 2, False)
                pos = text.rfind("<h")
                # text[pos + 1 : -1] = newLink
                text = f"{text[:pos]} {newLink} (n)"
                post["text"] = text
            else:
                logMsg("http", 2, False)
                logMsg(f"text: {text}", 2, False)
                pos = text.rfind("http")
                logMsg(f"text pos: {pos}", 2, False)
                text = f"{text[:pos]} {newLink}"
                logMsg(f"textt: {text}", 2, False)
                post["text"] = text
            msgLog = f"PPost: {post}"
            logMsg(msgLog, 2, False)

    def getPost(self, i):
        self.indent = f"{self.indent} "
        msgLog = f"{self.indent} Start getPost pos {i}."
        logMsg(msgLog, 2, False)
        post = None
        posts = self.getPosts()
        if posts and (i >= 0) and (i < len(posts)):
            post = posts[i]
        elif posts and (i < 0):
            post = posts[len(posts) - 1]

        msgLog = f"{self.indent} End getPost"
        logMsg(msgLog, 2, False)
        self.indent = self.indent[:-1]
        return post

    def getPostId(self, post):
        return post.get("ts", "")

    def editApiTitle(self, post, newTitle):
        # This method will reconstruct the post content with the new title
        # and then call editApiPost.
        original_text = post.get("text", "")
        original_link = self.getPostLink(post)
        print(f"Orig: {original_text}")
        print(f"Orig l : {original_link}")

        # Create a temporary post dictionary to get the new text with the updated title
        temp_post = post.copy()
        temp_post = self.setPostTitle(temp_post, newTitle)
        new_text_with_title = temp_post.get("text", "")
        print(f"New : {new_text_with_title}")

        # If there was an original link, ensure it's still part of the new text
        if original_link and original_link not in new_text_with_title:
            # This is a simplified approach. A more robust solution might parse
            # the original text to correctly insert the new title while preserving
            # the link's position and formatting.
            new_content = f"{new_text_with_title.strip()} {original_link}"
        else:
            new_content = new_text_with_title

        return self.editApiPost(post, new_content)

    def setPostTitle(self, post, newTitle):
        if ("attachments" in post) and ("title" in post["attachments"][0]):
            post["attachments"][0]["title"] = newTitle
        elif "text" in post:
            text = post["text"]
            if text.startswith("<"):
                if "|" in text:
                    title = text.split("|")[1]
                else:
                    title = text
                titleParts = title.split(">")
                title = newTitle
                if (len(titleParts) > 1) and (titleParts[1].find("<") >= 0):
                    # There is a link
                    title = title + " " + titleParts[1].split("<")[0]
            else:
                if text.find("<h") >= 0:
                    pos = text.find("<h")
                else:
                    pos = text.rfind("http")
                logMsg(f"text pos: {pos}", 2, False)
                if pos >= 0:
                    title = newTitle + " " + text[pos:]
                else:
                    title = newTitle

            post["text"] = title
        else:
            return "No title"

        return post

    def getPostTitle(self, post):
        # print(f"Post: {post}")
        if ("attachments" in post) and ("title" in post["attachments"][0]):
            return post["attachments"][0]["title"]
        elif "text" in post:
            text = post["text"]
            if text.startswith("<"):
                if "|" in text:
                    title = text.split("|")[1]
                else:
                    title = text
                titleParts = title.split(">")
                title = titleParts[0]
                if (len(titleParts) > 1) and (titleParts[1].find("<") >= 0):
                    # There is a link
                    title = title + titleParts[1].split("<")[0]
            elif text.find("<h") >= 0:
                pos = text.find("<")
                if pos >= 0:
                    title = text[:pos]
                else:
                    title = text
            else:
                pos = text.rfind("http")
                title = text[:pos]
            msgLog = f"{self.indent} Post text: {text}"
            logMsg(msgLog, 2, False)
            return title
        else:
            return "No title"

    def getApiPostUrl(self, post):
        return (
            f"https://{self.getUser()}.slack.com/archives/"
            f"{self.getChannel()}/p{self.getPostId(post)}"
        )

    def getPostContent(self, post):
        return self.getPostContentHtml(post)

    def getPostContentHtml(self, post):
        if "attachments" in post:
            text = post.get("attachments", [{}])[0].get("text", "")
        else:
            text = post.get("text", "")
        return text

    def getApiPostLink(self, post):
        link = ""
        if "attachments" in post:
            link = post["attachments"][0]["original_url"]
        else:
            text = post["text"]
            if text.startswith("<") and text.count("<") == 1:
                # The link is the only text
                link = post["text"][1:-1]
            elif text.find("<h") >= 0:
                # Some people include URLs in the title of the page
                pos = text.rfind("<")
                link = text[pos + 1 :]
                pos = link.find(">")
                link = link[:pos]

            else:
                pos = text.rfind("http")
                link = text[pos:-1]
        return link

    def getPostImage(self, post):
        return post.get("attachments", [{}])[0].get("image_url", "")

    def getChanId(self, name):
        msgLog = f"{self.indent} Service {self.service} Start getChanId"
        logMsg(msgLog, 2, False)

        self.getClient().token = self.user_slack_token
        chanList = self.getClient().api_call("conversations.list")["channels"]
        self.getClient().token = self.slack_token
        for channel in chanList:
            if channel["name_normalized"] == name:
                return channel["id"]
        return None

    def getBots(self, channel="tavern-of-the-bots"):
        # FIXME: this does not belong here
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
        msgLog = "{self.indent} Searching in Slack..."
        logMsg(msgLog, 1, False)
        try:
            self.getClient().token = self.slack_token
            data = {"query": text}
            res = self.getClient().api_call(
                "search.messages", data=data
            )  # , query=text)

            if res:
                self.report(self.service, "", "", sys.exc_info())
                return res
        except:
            return self.report("Slack", text, sys.exc_info())

    def register_specific_tests(self, tester):
        tester.add_test("Search test", self.test_search)
        tester.add_test("List channels test", self.test_list_channels)

    def get_user_info(self, client):
        response = client.auth_test()
        return f"{response['user']} ({response['team']})"

    def get_post_id_from_result(self, result):
        if isinstance(result, dict) and "ts" in result:
            return result["ts"]
        return None

    def test_search(self, apiSrc):
        query = input("Enter search query: ").strip()
        if not query:
            print("No query provided")
            return

        results = apiSrc.search(apiSrc.getChannel(), query)
        if results and "messages" in results and "matches" in results["messages"]:
            matches = results["messages"]["matches"]
            print(f"Found {len(matches)} messages:")
            for i, msg in enumerate(matches[:5]):
                print(f"\n{i+1}. {msg.get('text', 'No text')}")
                print(f"   by @{msg.get('user', 'Unknown user')}")
                print(f"   Link: {msg.get('permalink', 'No link')}")
        else:
            print("No results found.")

    def test_list_channels(self, apiSrc):
        channels = apiSrc.getChannels()
        if channels:
            print("Available channels:")
            for i, channel in enumerate(channels):
                print(f"{i+1}. {channel.get('name', 'No name')}")
        else:
            print("No channels found.")


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    slack_module = moduleSlack()
    tester = ModuleTester(slack_module)
    tester.run()


if __name__ == "__main__":
    main()
