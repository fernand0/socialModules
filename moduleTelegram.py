#!/usr/bin/env python

import configparser
import os
import telepot
import sys

from configMod import *
from moduleContent import *

class moduleTelegram(Content):

    def __init__(self):
        super().__init__()

    def setClient(self, channel):
        logging.info("     Connecting Telegram")
        try:
            config = configparser.ConfigParser() 
            config.read(CONFIGDIR + '/.rssTelegram') 
            
            TOKEN = config.get("Telegram", "TOKEN") 
            
            try: 
                bot = telepot.Bot(TOKEN) 
                meMySelf = bot.getMe() 
            except: 
                logging.warning("Telegram authentication failed!") 
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except: 
            logging.warning("Account not configured") 
            bot = None

        self.tc = bot
        self.user = meMySelf
        self.channel = channel

    def getClient(self):
        return self.tc

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        self.posts = self.tc.getUpdates(allowed_updates='message')

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in Telegram...")
        bot = self.tc
        title = post
        content = comment
        links = ""
        channel = self.channel

        from html.parser import HTMLParser
        h = HTMLParser()
        title = h.unescape(title)
        content = content.replace('<','&lt;')
        text = '<a href="'+link+'">'+title+ "</a>\n" + content + '\n\n' + links
        textToPublish2 = ""
        if len(text) < 4090:
            textToPublish = text
            links = ""
        else:
            text = '<a href="'+link+'">'+title + "</a>\n" + content
            textToPublish = text[:4080] + ' ...'
            textToPublish2 = '... '+ text[4081:]

        logging.info("Publishing (text to )"+ textToPublish)
        logging.info("Publishing (text to 2)"+ textToPublish2)

        try:
            bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 
        except:
            return(self.report('Telegram', textToPublish, link, sys.exc_info()))

        if textToPublish2:
            try:
                bot.sendMessage('@'+channel, textToPublish2[:4090], parse_mode='HTML') 
            except:
                bot.sendMessage('@'+channel, "Text is longer", parse_mode='HTML') 
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
    import moduleTelegram

    tel = moduleTelegram.moduleTelegram()

    tel.setClient('testFernand0')

    print("Testing posts")
    tel.setPosts()
    for post in tel.getPosts():
        print(post)

    print("Testing title and link")

    for post in tel.getPosts():
        print(post)
        title = tel.getPostTitle(post)
        link = tel.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))

if __name__ == '__main__':
    main()

