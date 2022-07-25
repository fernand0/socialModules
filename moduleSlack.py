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
        self.postaction = None
        self.service = "Slack"

    def getKeys(self, config):
        slack_token = config.get(self.service, "oauth-token")
        user_slack_token = config.get(self.service, "user-oauth-token")
        return (slack_token, user_slack_token)

    def initApi(self, keys):
        logging.info("     Connecting {}".format(self.service))
        if self.user and self.user.find('/')>=0:
            self.name = self.user.split('/')[2].split('.')[0]
        else:
            self.name = self.user
        if self.user.find('@')>=0:
            channel, user = self.user.split('@')
            self.user = user
            #self.setChannel(channel)

        client = WebClient(keys[0])
        self.slack_token = keys[0]
        self.user_slack_token = keys[1]
        return client

    def getChannels(self):
        response = self.getClient().conversations_list()
        conversations = response.get("channels", '')
        return conversations

    def setChannel(self, channel=''):
        # setPage in Facebook
        if not channel:
            channel = self.getChannels()[0].get('name','')
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
            # FIXME
            # Can we improve this in mosuleSlack and moduleFacebook?
            self.setChannel('links')
        posts = []
        theChannel = self.getChannel()
        self.getClient().token = self.slack_token
        data = {"limit": 1000, "channel": theChannel}
        history = self.getClient().api_call("conversations.history", data=data)
        try:
            posts = history["messages"]
        except:
            posts = []

        logging.debug(f"Posts: {posts}")
        return posts

    def processReply(self, reply):
        # FIXME: Being careful with publishPost, publishPosPost, publishNextPost, publishApiPost
        res = reply
        if isinstance(reply, dict):
           res = reply.get('ok','Fail!')
        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, link, comment = args
        if kwargs:
            more = kwargs
        chan = self.getChannel()
        if not chan:
            self.setChannel()
            chan = self.getChannel()
        self.getClient().token = self.user_slack_token
        data = {"channel": chan, "text": f"{title} {link}"}
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

    def getPostId(self, post):
        return (post.get('ts',''))

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
                    title = title + ' ' + titleParts[1].split("<")[0]
            else:
                pos = text.find("<")
                if pos>=0:
                    title = newTitle + ' ' + text[pos:]
                else:
                    title = newTitle

            # Last space
            posSpace = text.rfind(' ')
            post["text"] = title + text[posSpace:]
            print(f"Title: {post['text']}")
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
            else:
                pos = text.find("<")
                if pos>=0:
                    title = text[:pos]
                else:
                    title = text
            return title
        else:
            return "No title"

    def getPostUrl(self, post):
        return (
            f"{self.getUser()}archives/"
            f"{self.getChannel()}/p{self.getPostId(post)}"
        )

    def getPostContent(self, post):
        return self.getPostContentHtml(post)

    def getPostContentHtml(self, post):
        if "attachments" in post:
            text = post.get("attachments", [{}])[0].get('text', '')
        else:
            text = post.get('text', '')
        return text

    def getPostLink(self, post):
        link = ''
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

    def getPostImage(self, post):
        return post.get('attachments',[{}])[0].get('image_url', '')

    def getChanId(self, name):
        logging.debug("getChanId %s" % self.service)

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

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format="%(asctime)s %(message)s"
    )

    import moduleSlack

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    # 
    # src: ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
    #
    # More: {'url': 'http://fernand0-errbot.slack.com/', 'service': 'slack', 'cache': 'linkedin\ntwitter\nfacebook\nmastodon\ntumblr', 'twitter': 'fernand0Test', 'facebook': 'Fernand0Test', 'mastodon': '@fernand0@mastodon.social', 'linkedin': 'Fernando Tricas', 'tumblr': 'fernand0', 'buffermax': '9'}
    # It can be empty: {}
    
    indent = ""
    for src in rules.rules.keys():
        if src[0] == 'slack':
            print(f"Src: {src}")
            more = rules.more[src]
            break
    apiSrc = rules.readConfigSrc(indent, src, more)

    apiSrc.setChannel("links")

    testingInit = False
    if testingInit:
        import moduleRules
        src = ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
        rules = moduleRules.moduleRules()
        more = {}
        indent = ''
        apiSrc = rules.readConfigSrc(indent, src, more)
        logging.info(f"User: {apiSrc.getUser()}")
        logging.info(f"Name: {apiSrc.getName()}")
        logging.info(f"Nick: {apiSrc.getNick()}")
        return

    testingPublishing = False
    if testingPublishing:
        links  = [
                'https://www.johndcook.com/blog/2021/12/11/fraud-sloppiness-and-statistics/',
                'https://nadh.in/blog/open-source-is-not-broken/',
                'https://medium.com/geekculture/madridss-modular-metro-733abaaaf429',
                'https://blog.filippo.io/professional-maintainers/',
                'https://christine.website/blog/open-source-broken-2021-12-11',
                'https://solar.lowtechmagazine.com/power.html',
                'https://nakedsecurity.sophos.com/2021/12/13/log4shell-explained-how-it-works-why-you-need-to-know-and-how-to-fix-it/',
                'https://vaceituno.medium.com/must-read-books-for-cybersecurity-professionals-486f81075c83'
                'https://georgecouros.ca/blog/archives/13412',
                'https://ariadne.space/2021/12/11/to-secure-the-supply-chain-you-must-properly-fund-it/',
                'https://aws.amazon.com/message/12721/',
                ]
        site.setChannel('links')
        for link in links:
            site.publishPost('', link, '')
        return

    testingEditTitle = False
    if testingEditTitle:
        print("Testing edit posts")
        site.setPostsType("posts")
        site.setPosts()
        print(site.getPostTitle(site.getPosts()[0]))
        print(site.getPostLink(site.getPosts()[0]))
        input("Edit? ")
        site.setPostTitle(site.getPosts()[0], "prueba")
        print(site.getPostTitle(site.getPosts()[0]))
        print(site.getPostLink(site.getPosts()[0]))
        return


    testingPosts = False
    if testingPosts:
        print("Testing posts")
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('links')
        apiSrc.setPosts()

        print("Testing title and link")

        for i, post in enumerate(apiSrc.getPosts()):
            # print(f"Post: {post}")
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            url = apiSrc.getPostUrl(post)
            theId = apiSrc.getPostId(post)
            summary = apiSrc.getPostContentHtml(post)
            image = apiSrc.getPostImage(post)
            print(f"{i}) Title: {title}\n"
                  f"Link: {link}\n"
                  f"Url: {url}\nId: {theId}\n"
                  f"Content: {summary} {image}")

        if input("All? (y/n) ") == 'y':
            print(f"Channels: {apiSrc.getChannels()}")
            for channel in apiSrc.getChannels():
                print(f"Name: {channel['name']}")
                apiSrc.setChannel(channel['name'])
                apiSrc.setPosts()
                for i, post in enumerate(apiSrc.getPosts()):
                    print(f"{i}) Title: {apiSrc.getPostTitle(post)}\n"
                          f"Link: {apiSrc.getPostLink(post)}\n")
                print(f"Name: {channel['name']}")
                input("More? (any key to continue) ")

        return

    testingDeleteLast = False
    if testingDeleteLast:
        site.setPostsType("posts")
        site.setPosts()
        print(f"Testing delete last")
        post = site.getPosts()[0]
        input(f"Delete {site.getPostTitle(post)}? ")
        site.delete(0)
        return
        
    testingDelete = False
    if testingDelete:
        # print("Testing posting and deleting")
        res = site.publishPost(
            "FOSDEM 2022 - FOSDEM 2022 will be online",
            "https://fosdem.org/2022/news/2021-10-22-fosdem-online-2022/", ""
        )
        print("res", res)
        # idPost = res
        # print(idPost)
        # input("Delete? ")
        # site.deletePostId(idPost)
        # sys.exit()

        i = 0
        post = site.getPost(i)
        title = site.getPostTitle(post)
        link = site.getPostLink(post)
        url = site.getPostUrl(post)
        print(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
        print(f"Content: {site.getPostContentHtml(post)}\n")
        input("Delete?")
        site.delete(i)
        return

    myChan = None
    channels = []
    testingChannels = True
    if testingChannels:
        for i, chan in enumerate(apiSrc.getChannels()):
            channels.append(chan.get('name',''))
            print(f"{i}) Chan: {chan.get('name','')}")


        select = input("Which one? ")
        if select.isdigit():
            channels = [ channels[int(select)], ]

    testingDelete = True
    if testingDelete:
        for chan in channels:
            apiSrc.setChannel(chan)

            apiSrc.setPosts()

            [ print(f"{i}) {apiSrc.getPostTitle(post)}")
                    for i, post in enumerate(apiSrc.getPosts()) ]
            pos = input("Which post to delete (a for all)? ")
            if pos.isdigit():
                post = apiSrc.getPost(int(pos))
                apiSrc.deletePost(post)
            else:
                for pos, post in enumerate(apiSrc.getPosts()):
                    apiSrc.deletePost(post)

        return

    testingCleaning = False
    if testingCleaning:
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('tavern-of-the-bots')
        apiSrc.setPosts()
        ipList = {}
        for i, post in enumerate(apiSrc.getPosts()):
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            url = apiSrc.getPostUrl(post)
            print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
            # if 'Rep' in link:
            # if 'foto' in link:
            # if '"args": ""' in link:
            if 'Hello' in title:
                posIni = title.find('IP')+4
                posFin = title.find(' ', posIni) - 1
                if title[posIni:posFin] not in ipList:
                    print(title[posIni:posFin])
                    ipList[title[posIni:posFin]] = 1
                    print(ipList)
                else:
                    print(f"{link[posIni:posFin]}")
                    input("Delete? ")
                    print(f"Deleted {apiSrc.delete(i)}")

            # time.sleep(5)

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

    sys.exit()

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
