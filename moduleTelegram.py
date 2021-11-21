#!/usr/bin/env python

import configparser
import logging
import telepot
import sys

from configMod import *
from moduleContent import *


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
        try:
            bot = telepot.Bot(TOKEN)
            meMySelf = bot.getMe()
        except:
            logging.warning("Telegram authentication failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])

        # self.user = meMySelf
        # self.channel = channel
        return bot

    def setClient(self, channel):
        logging.info("     Connecting Telegram")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTelegram')

            if channel in config:
                TOKEN = config.get(channel, "TOKEN")
            else:
                TOKEN = config.get("Telegram", "TOKEN")

            try:
                bot = telepot.Bot(TOKEN)
                meMySelf = bot.getMe()
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

    def publishApiImage(self, *postData):
        post, image, plus = postData

        bot = self.getClient()
        channel = self.user
        if True:
            bot.sendPhoto('@'+channel, photo=open(image, 'rb'), caption=post)
        else:
            return(self.report('Telegram', post, sys.exc_info()))

    # def publishApiPost(self, *args, **kwargs):
    #     title, link, comment = args
    #     more = kwargs
    #     print("...",title, link, comment, more)

    #     bot = self.getClient()
    #     content = comment
    #     links = ""
    #     channel = self.user

    #     from html.parser import HTMLParser
    #     h = HTMLParser()
    #     title = h.unescape(title)
    #     content = content.replace('<', '&lt;')
    #     text = ('<a href="'+link+'">'
    #             + title + "</a>\n" + content + '\n\n' + links)
    #     textToPublish2 = ""
    #     if len(text) < 4090:
    #         textToPublish = text
    #         links = ""
    #     else:
    #         text = '<a href="'+link+'">'+title + "</a>\n" + content
    #         textToPublish = text[:4080] + ' ...'
    #         textToPublish2 = '... ' + text[4081:]

    #     logging.debug("Publishing (text to )" + textToPublish)
    #     logging.debug("Publishing (text to 2)" + textToPublish2)


    #     try:
    #         bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML')
    #     except:
    #         return(self.report('Telegram', textToPublish,
    #             link, sys.exc_info()))

    #     if textToPublish2:
    #         try:
    #             bot.sendMessage('@'+channel, textToPublish2[:4090],
    #                             parse_mode='HTML')
    #         except:
    #             bot.sendMessage('@'+channel, "Text is longer",
    #                             parse_mode='HTML')
    #     if links:
    #         bot.sendMessage('@'+channel, links, parse_mode='HTML')

    def publishApiPost(self, *args): #, **kwargs):
        title, link, comment, more = args
        logging.info("    Publishing in Telegram...")
        bot = self.getClient()
        if 'post' in more:
            contentHtml = more['api'].getPostContentHtml(more['post'])
            print(f"contentHtml: {contentHtml}")
            soup = BeautifulSoup(contentHtml,'lxml')
            (theContent, theSummaryLinks) = more['api'].extractLinks(soup, "")
            content = f"{theContent}\n{theSummaryLinks}"
        else:
            content = comment
        links = ""
        channel = self.user
        print(f"content: {content}")

        logging.info(f"{self.service}: Title: {title} Link: {link}")
        text = ('<a href="'+link+'">' + title+ "</a>\n")
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
            print(f"text: {textToPublish}")
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

    testingPost = True
    if testingPost:
        more = {'api': 'lala', 'post': 'lele'}
        res = tel.publishPost("Prueba imagen", "/tmp/prueba.png", '', more) 
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
