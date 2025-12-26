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
        content = ""
        title = ""
        link = ""

        if args and len(args) == 3:
            title, link, comment = args
            if comment:
                content = comment
        elif kwargs:
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

        if not title and not link:
            self.res_dict["error_message"] = "No title or link to publish."
            return self.res_dict

        bot = self.getClient()
        channel = self.user
        text = f'<a href="{link}">{title}</a>\n'

        from html import unescape

        title = unescape(title)
        if content:
            content = content.replace("<", "&lt;")
            text += content

        try:
            # Telegram messages have a size limit of 4096 characters
            res = bot.sendMessage("@" + channel, text[:4096], parse_mode="HTML")
            self.res_dict["raw_response"] = res
            if res and "message_id" in res:
                self.res_dict["success"] = True
                self.res_dict["post_url"] = (
                    f"https://t.me/{channel}/{res['message_id']}"
                )
            else:
                self.res_dict["error_message"] = f"Telegram API error: {res}"
        except Exception as e:
            self.res_dict["error_message"] = self.report(
                "Telegram", text[:100], link, sys.exc_info()
            )
            self.res_dict["raw_response"] = e

        return self.res_dict

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
