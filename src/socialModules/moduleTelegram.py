#!/usr/bin/env python

import configparser
import json
import logging
import sys

import telepot

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleTelegram(Content):
    def get_user_info(self, client):
        return f"{self.user}"

    def get_post_id_from_result(self, result):
        return result.id

    def getKeys(self, config):
        print(config)
        print(config.get("Telegram", "TOKEN"))
        TOKEN = config["Telegram"]["TOKEN"]
        print(TOKEN)
        return (TOKEN,)

    def initApi(self, keys):
        self.service = "Telegram"
        # logging.info("     Connecting {self.service}")
        TOKEN = keys[0]
        # logging.info("     token: {TOKEN}")
        try:
            bot = telepot.Bot(TOKEN)
            logging.info("     token: {TOKEN}")

            meMySelf = bot.getMe()
        except:
            logging.warning("Telegram authentication failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])

        # self.user = meMySelf
        # self.channel = channel
        return bot

    def setClient(self, channel):
        msgLog = f"{self.indent} Start setClient account: {channel}"
        logMsg(msgLog, 1, False)
        self.indent = f"{self.indent} "
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssTelegram")

            if channel in config:
                TOKEN = config.get(channel, "TOKEN")
            else:
                TOKEN = config.get("Telegram", "TOKEN")
            try:
                bot = telepot.Bot(TOKEN)
            except:
                logging.warning("Telegram authentication failed!")
                # logging.warning("Unexpected error:", sys.exc_info())
        except:
            logging.warning("Account not configured")
            bot = None

        self.client = bot
        self.user = channel
        self.channel = channel
        self.indent = self.indent[:-1]
        msgLog = f"{self.indent} End setClientt"
        logMsg(msgLog, 1, False)

    def setChannel(self, channel):
        self.channel = channel

    def publishApiImage(self, *args, **kwargs):
        msgLog = (
            f"{self.indent} Service {self.service} publishing args "
            f"{args}: kwargs {kwargs}"
        )
        logMsg(msgLog, 2, False)
        post, image = args
        more = kwargs

        bot = self.getClient()
        channel = self.user
        if True:
            bot.sendPhoto("@" + channel, photo=open(image, "rb"), caption=post)
        else:
            return self.report("Telegram", post, sys.exc_info())

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ""
        logging.info(f"    Publishing next post from {apiSrc} in " f"{self.service}")
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "No posts available"
        except:
            reply = self.report(self.service, apiSrc, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        rep = "Fail!"
        content = ""
        if args and len(args) == 3:
            title, link, comment = args
            if comment:
                content = comment
        if kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            if post:
                contentHtml = api.getPostContentHtml(post)
                soup = BeautifulSoup(contentHtml, "lxml")
                (theContent, theSummaryLinks) = api.extractLinks(soup, "")
                content = f"{theContent}\n{theSummaryLinks}"

        bot = self.getClient()

        links = ""
        channel = self.user

        logging.info(f"{self.service}: Title: {title} Link: {link}")
        text = '<a href="' + link + '">' + title + "</a>\n"
        logging.debug(f"{self.service}: Text: {text}")
        # FIXME: This code needs improvement
        textToPublish = text
        textToPublish2 = ""
        from html import unescape

        title = unescape(title)
        if content:
            content = content.replace("<", "&lt;")
            text = text + content + "\n\n" + links

        textToPublish = text
        while textToPublish:
            try:
                res = bot.sendMessage(
                    "@" + channel, textToPublish[:4080], parse_mode="HTML"
                )
                textToPublish = textToPublish[4080:]
            except:
                return self.report("Telegram", textToPublish, link, sys.exc_info())

            if links:
                bot.sendMessage("@" + channel, links, parse_mode="HTML")
            rep = res

        return rep

    def processReply(self, reply):
        res = ""
        if not isinstance(reply, list):
            origReply = [
                reply,
            ]
        else:
            origReply = reply
        for rep in origReply:
            if isinstance(rep, str):
                rep = rep.replace("'", '"')
                rep = json.loads(rep)
            else:
                rep = reply
            if "message_id" in rep:
                idPost = rep["message_id"]
                res = f"{res} https://t.me/{self.user}/{idPost}"
        return res

    def getApiPostTitle(self, post):
        if "channel_post" in post:
            if "text" in post["channel_post"]:
                return post["channel_post"]["text"]
            else:
                return ""
        else:
            return ""


def main():
    import logging
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    telegram_module = moduleTelegram()
    tester = ModuleTester(telegram_module)
    tester.run()


if __name__ == "__main__":
    main()
