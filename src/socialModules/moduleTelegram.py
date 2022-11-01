#!/usr/bin/env python

import configparser
import logging
import sys

import telepot

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleTelegram(Content):

    def __init__(self):
        super().__init__()
        self.service = 'Telegram'

    def getKeys(self, config):
        print(config)
        print(config.get('Telegram', 'TOKEN'))
        TOKEN = config['Telegram']['TOKEN']
        print(TOKEN)
        return((TOKEN, ))

    def initApi(self, keys):
        logging.info("     Connecting Telegram")
        TOKEN = keys[0]
        logging.info("     token: {TOKEN}")
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
        logging.info(f"     Connecting Telegram, channel: {channel}")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTelegram')

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

    def setChannel(self, channel):
        self.channel = channel

    def publishApiImage(self, *args, **kwargs):
        post, image = args
        more = kwargs

        bot = self.getClient()
        channel = self.user
        if True:
            bot.sendPhoto('@'+channel, photo=open(image, 'rb'), caption=post)
        else:
            return(self.report('Telegram', post, sys.exc_info()))

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ''
        logging.info(f"    Publishing next post from {apiSrc} in "
                    f"{self.service}")
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "Fail! No posts available"
        except:
            reply = self.report(self.service, apiSrc, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        content = ''
        if args and len(args) == 3:
            title, link, comment = args
        if kwargs:
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            if post:
                contentHtml = api.getPostContentHtml(post)
                soup = BeautifulSoup(contentHtml,'lxml')
                (theContent, theSummaryLinks) = api.extractLinks(soup, "")
                content = f"{theContent}\n{theSummaryLinks}"

        bot = self.getClient()

        links = ""
        channel = self.user

        logging.info(f"{self.service}: Title: {title} Link: {link}")
        text = ('<a href="'+link+'">' + title+ "</a>\n")
        #FIXME: This code needs improvement
        textToPublish = text
        textToPublish2 = ""
        from html.parser import HTMLParser
        h = HTMLParser()
        title = h.unescape(title)
        if content:
            content = content.replace('<', '&lt;')
            text = (text + content + '\n\n' + links)
            textToPublish2 = ""
            if len(text) < 4090:
                textToPublish = text
                links = ""
            else:
                textToPublish = text[:4080] + ' ...'
                textToPublish2 = '... ' + text[4081:]

            logging.info("Publishing (text to )" + textToPublish)
            logging.info("Publishing (text to 2)" + textToPublish2)

        if textToPublish:
            try:
                bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML')
            except:
                return(self.report('Telegram', textToPublish,
                    link, sys.exc_info()))

            if textToPublish2:
                try:
                    bot.sendMessage('@'+channel, textToPublish2[:4090],
                            parse_mode='HTML')
                except:
                    bot.sendMessage('@'+channel, "Text is longer",
                            parse_mode='HTML')
            if links:
                bot.sendMessage('@'+channel, links, parse_mode='HTML')

    def getPostTitle(self, post):
        if 'channel_post' in post:
            if 'text' in post['channel_post']:
                return(post['channel_post']['text'])
            else:
                return ''
        else:
            return ''


def main():

    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
            format='%(asctime)s %(message)s')

    import moduleTelegram

    tel = moduleTelegram.moduleTelegram()

    tel.setClient('testFernand0')
    # tel.setChannel('testFernand0')

    testingImage = False
    if testingImage:
        res = tel.publishImage("Prueba imagen", "/tmp/prueba.png")
        return

    testingPost = True
    if testingPost:
        res = tel.publishPost("Prueba texto", "https://t.me/testFernand0", '')
                #api = 'lala' , post = 'lele')
        return
    # print("Testing posts")
    # tel.setPosts()

    # for post in tel.getPosts():
    #     print(post)

    # print("Testing title and link")

    # for post in tel.getPosts():
    #     print(post)
    #     title = tel.getPostTitle(post)
    #     link = tel.getPostLink(post)
    #     print("Title: {}\nLink: {}\n".format(title, link))

    sys.exit()


if __name__ == '__main__':
    main()
