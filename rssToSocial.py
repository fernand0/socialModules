#!/usr/bin/env python
# encoding: utf-8
#
# Very simple Python program to publish RSS entries of a set of feeds
# in available social networks.
#
# It has a configuration file with a number of blogs with:
#    - The RSS feed of the blog
#    - The Twitter account where the news will be published
#    - The Facebook page where the news will be published
#    - Other social networks
# It uses a configuration file that has two sections:
#      - The oauth access token
#
# And more thins. To be done.
#

import moduleRss
# https://github.com/fernand0/scripts/blob/master/moduleRss.py
import moduleXmlrpc
# https://github.com/fernand0/scripts/blob/master/moduleXmlrpc.py
import moduleSocial
# https://github.com/fernand0/scripts/blob/master/moduleSocial.py
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py
import moduleBuffer
# https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
import moduleSlack
# https://github.com/fernand0/scripts/blob/master/moduleSlack.py
import moduleForum
# https://github.com/fernand0/scripts/blob/master/moduleForum.py
import moduleGmail
# https://github.com/fernand0/scripts/blob/master/moduleGmail.py
import moduleWordpress
# https://github.com/fernand0/scripts/blob/master/moduleImgur.py
import moduleImgur
import moduleImdb

import configparser
import os
import logging
import random
import threading
import feedparser
import facebook
from twitter import *
from medium import Client
from html.parser import HTMLParser
import telepot
import re
import sys
import time
import datetime
import pickle
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from bs4 import Doctype
import importlib
import urllib.parse
# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update

from configMod import *

def test():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    # We can publish the last entry of a blog in Medium as a draft
    blog = moduleRss.moduleRss()
    blog.setRssFeed('http://fernand0.blogalia.com/rss20.xml')
    blog.getBlogPostsRss()
    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(0))
    publishMedium("", title, link, summary, summaryHtml, summaryLinks, image)


    print("Configured blogs:")

    feed = []
    # We are caching the feeds in order to use them later

    i = 1
    recentPosts = {}

    for section in config.sections():
        rssFeed = config.get(section, "rss")
        feed.append(feedparser.parse(rssFeed))
        lastPost = feed[-1].entries[0]
        print('%s) %s %s (%s)' % (str(i), section,
                                  config.get(section, "rss"),
                                  time.strftime('%Y-%m-%d %H:%M:%SZ',
                                  lastPost['published_parsed'])))
        lastLink = checkLastLink(self.url, config.get(section, "rss"))
        print(lastLink)
        lenCmp = min(len(lastLink),len(lastPost['link']))

        recentPosts[section] = {}
        recentPosts[section]['posts'] = feed[-1].entries[0]

    for i in recentPosts.keys():
         print("post",i,recentPosts[i]['posts']['title'])
         print("post",i,recentPosts[i]['posts']['link'])
         if 'content' in recentPosts[i]['posts']:
             content = recentPosts[i]['posts']['content'][0]['value']
         else:
             content = recentPosts[i]['posts']['summary']
         print("post content",i,content)
         soup = BeautifulSoup(content)
         theSummary = soup.get_text()
         theSummaryLinks = blog.extractLinks(soup)
         print("post links",i,theSummaryLinks)

    return recentPosts

def main():

    print("====================================")
    print("Launched at %s" % time.asctime())
    print("====================================")
    print("")
        
    isDebug = False


    import argparse
    parser = argparse.ArgumentParser(description='Improving command line call',
            allow_abbrev=True)
    parser.add_argument('--timeSlots', '-t', default=55*60, # 55 minutes
                    help='How many time slots we will have for publishing')
    parser.add_argument('checkBlog', default="",
            metavar='Blog', type=str, nargs='?',
                    help='you can select just a blog')
    parser.add_argument('--simmulate', '-s',default=False,
            action='store_true', help='simulate which posts would be added')
    parser.add_argument('--noWait', '-n', default=False,
            action='store_true', help='no wait for time restrictions')
    args = parser.parse_args()

    checkBlog = args.checkBlog
    timeSlots = int(args.timeSlots)
    simmulate = args.simmulate
    nowait = args.noWait


    loggingLevel = logging.INFO
    logging.basicConfig(filename = LOGDIR + "/rssSocial_.log", 
            level=loggingLevel, 
            format='%(asctime)s [%(filename).12s] %(message)s', 
            datefmt='%Y-%m-%d %H:%M')

    logging.info("Launched at %s" % time.asctime())
    logging.debug("Parameters %s, %d" % (sys.argv, len(sys.argv)))
    logging.info("Configured blogs:")

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    blogs = []
    delayedPosts = []
    delayedBlogs = []

    for section in config.sections():
        blog = None
        logging.info("Section: %s"% section)
        url = config.get(section, "url")
        print("Section: %s %s"% (section, url))
        if ("rss" in config.options(section)):
            rssFeed = config.get(section, "rss")
            logging.info(" Blog RSS: {}".format(rssFeed))
            blog = moduleRss.moduleRss()
            # It does not preserve case
            blog.setRssFeed(rssFeed)
        elif url.find('slack')>0:
            logging.info(" Blog Slack: {}".format(url))
            blog = moduleSlack.moduleSlack()
            blog.setSlackClient(os.path.expanduser(CONFIGDIR+'/.rssSlack'))
        elif url.find('imgur')>0:
            logging.info(" Blog ImgUr: {}".format(url))
            blog = moduleImgur.moduleImgur()
            if 'imgur' in config.options(section): 
                imgur = config.get(section,'imgur') 
            else: 
                imgur = url.split('/')[-1]
            logging.info(" ImgUr: {}".format(imgur))
            blog.setClient(imgur)
        elif 'forum' in config.options(section):
            forum = config.get(section,'forum')
            logging.info(" Forum: {}".format(forum))
            blog = moduleForum.moduleForum()
            blog.setClient(forum)
        elif 'gmail' in config.options(section):
            mail = config.get(section,'gmail')
            logging.info(" Gmail: {}".format(mail))
            blog = moduleGmail.moduleGmail()
            blog.setClient(('gmail',mail))
        elif 'wordpress' in config.options(section):
            wordpress = config.get(section,'wordpress')
            logging.info(" Wordpress: {}".format(wordpress))
            blog = moduleWordpress.moduleWordpress()
            blog.setClient(wordpress)
        elif 'imdb' in config.options(section):
            imdb = config.get(section,'imdb')
            logging.info(" Imdb: {}".format(imdb))
            blog = moduleImdb.moduleImdb()
            #blog.setClient((url,config.get(section,'channels').split(',')))
        blog.setUrl(url)

        if (not checkBlog) or (checkBlog.upper() == section.upper()):
            # If checkBlog is empty it will add all of them
            if ("linksToAvoid" in config.options(section)):
                blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
            if ("time" in config.options(section)):
                blog.setTime(config.get(section, "time"))

            blog.setSocialNetworks(config, section)

            if ('buffer' in config.options(section)): 
                blog.setBufferapp(config.get(section, "buffer")) 

            if('max' in config.options(section)):
                blog.setMax(config.get(section, "max")) 

            if ('cache' in config.options(section)): 
                blog.setProgram(config.get(section, "cache"))

            if ('buffermax' in config.options(section)): 
                blog.setBufMax(config.get(section, "buffermax"))
            else:
                blog.setBufMax(9)
            if ('posts' in config.options(section)): 
                blog.setPostsType(config.get(section, "posts"))
            else:
                blog.setPostsType("posts")


            bufferMax = int(blog.getBufMax())
            #print(bufferMax)

            socialNetworks = blog.getSocialNetworks()
            if socialNetworks:
                logging.info(" Looking for pending posts") 
                print("   Looking for pending posts ... " )
                blog.setPosts()
            else:
                logging.info(" No social networks configured") 
                print("   No social networks configured ... " )

            for profile in socialNetworks:
                lenMax = 0
                i = 0
                link= ""

                nick = blog.getSocialNetworks()[profile]
                socialNetwork = (profile, nick)
                nameProfile = profile + '_' + nick

                if ((blog.getBufferapp() 
                        and (profile[0] in blog.getBufferapp())) 
                        or (blog.getProgram() 
                            and (profile[0] in blog.getProgram()))): 
                    lenMax = blog.len(profile)


                logging.info("  Service %s" % profile)
                print("  Service %s" % profile)
                logging.debug("  Service %s Lenmax %d" % (profile, lenMax))

                num = bufferMax - lenMax

                lastLink, lastTime = checkLastLink(url, socialNetwork)
                if hasattr(blog, 'getPostsType'): 
                    if blog.getPostsType() == 'drafts': 
                        i = 1
                    else: 
                        i = blog.getLinkPosition(lastLink)
 
                if (i == 0):
                    logging.info("    No new posts")
                    print("    No new posts")
                hours = blog.getTime() 
                if lastLink and isinstance(lastLink, list):
                    myLastLink = lastLink[0]
                else:
                    myLastLink = lastLink
                logging.info("    %s Last link %s"% 
                        (time.strftime('%Y-%m-%d %H:%M:%S', 
                            time.localtime(lastTime)), myLastLink))
                print("     %s Last link %s" %
                        (time.strftime('%Y-%m-%d %H:%M:%S', 
                            time.localtime(lastTime)), myLastLink))
                logging.debug("bufferMax - lenMax = num %d %d %d"%
                        (bufferMax, lenMax, num)) 

                if ((not nowait) and 
                        (hours and 
                            (((time.time() - lastTime) 
                                - round(float(hours)*60*60)) < 0))): 
                    logging.info("  Not publishing because time restriction") 
                    print("     Not publishing because time restriction (Last time: %s)"% time.ctime(lastTime)) 
                else:
                    listPosts = []
                    if 'max' in blog.__dir__():
                        num = int(blog.getMax())


                    if ((num > 0) and (blog.getBufferapp() or blog.getProgram())
                            or not (blog.getBufferapp() or blog.getProgram())):

                        logging.debug("   Profile %s"% profile)
                        link = ""
                        listPosts = blog.getNumPostsData(num, i)

                    if simmulate:
                        print(listPosts)


                    if (blog.getBufferapp() 
                            and (profile[0] in blog.getBufferapp())): 
                        print("   Buffered")
                        link = blog.buffer[socialNetwork].addPosts(listPosts)

                    if ((blog.getProgram() 
                            and isinstance(blog.getProgram(), list)
                            and profile in blog.getProgram()) or 
                        (blog.getProgram() 
                            and isinstance(blog.getProgram(), str) 
                            and (profile[0] in blog.getProgram()))):
                        print("   Delayed")
                        link = blog.cache[socialNetwork].addPosts(listPosts)

                        time.sleep(1)
                        print(link)
                        delayedBlogs.append((blog, socialNetwork, 1, timeSlots))


                    if not (blog.getBufferapp() or blog.getProgram()):
                        link = moduleSocial.publishDirect(blog, 
                                socialNetwork, i) 
                        logging.info("  Link reply %s"%str(link)) 

                    if link:
                         logging.info("    Updating link %s %s" % 
                                 (profile, link))
                         if isinstance(lastLink, list):
                             link = link + '\n' + '\n'.join(lastLink)
                         updateLastLink(blog.url, link, socialNetwork) 
                         logging.debug("listPosts: %s"% listPosts)

            time.sleep(2)
        else:
            print("    Skip")

    print("====================================")
    print("Finished at %s" % time.asctime())
    print("====================================")

    if delayedBlogs:

        print("======================================")
        print("Starting delayed at %s" % time.asctime())
        print("======================================")

        import concurrent.futures 
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(delayedBlogs)) as executor:
            delayedPosts = {executor.submit(moduleSocial.publishDelay, *args): args for args in delayedBlogs}
            time.sleep(5)
            print("")
            for future in concurrent.futures.as_completed(delayedPosts):
                dataBlog = delayedPosts[future]
                try:
                    res = future.result()
                    print("Res: %s"% str(res))
                except Exception as exc:
                    print('%r generated an exception: %s' % (str(dataBlog), exc))
                #else:
                #    print('Blog %s' % str(dataBlog))
    

        print("======================================")
        print("Finished delayed at %s" % time.asctime())
        print("======================================")

    logging.info("Finished at %s" % time.asctime())

if __name__ == '__main__':
    main()

