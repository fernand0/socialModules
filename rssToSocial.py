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
import moduleSocial
import moduleSlack
import moduleForum
import moduleGmail
import moduleWordpress
import moduleImgur
import moduleImdb
import modulePocket
import moduleMastodon
import moduleTwitter

import configparser
import logging
import sys
import time

# # sudo pip install buffpy version does not work
# # Better use:
# # git clone https://github.com/vtemian/buffpy.git
# # cd buffpy
# # sudo python setup.py install
# from buffpy.api import API
# from buffpy.managers.profiles import Profiles
# from buffpy.managers.updates import Update

from configMod import *


def readConfig(checkBlog):
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + "/.rssBlogs")

    blogs = []

    logging.info("Configured blogs:")

    for section in config.sections():
        blog = None
        url = config.get(section, "url")
        msgLog = f"Section: {section} | Url: {url}"

        if "hold" in config.options(section):
            msgLog = msgLog + " (In hold state)"
            logMsg(msgLog, 1, 1)
            continue
        logMsg(msgLog, 1, 1)
        if (not checkBlog) or (checkBlog.upper() == section.upper()):
            if "rss" in config.options(section):
                rssFeed = config.get(section, "rss")
                logging.info(" Blog RSS: {}".format(rssFeed))
                blog = moduleRss.moduleRss()
                # It does not preserve case
                blog.setRssFeed(rssFeed)
            elif url.find("slack") > 0:
                logging.info(" Blog Slack: {}".format(url))
                blog = moduleSlack.moduleSlack()
                blog.setClient(url)
                blog.setChannel("links")
            elif url.find("imgur") > 0:
                logging.info(" Blog ImgUr: {}".format(url))
                blog = moduleImgur.moduleImgur()
                if "imgur" in config.options(section):
                    imgur = config.get(section, "imgur")
                else:
                    imgur = url.split("/")[-1]
                logging.info(" ImgUr: {}".format(imgur))
                blog.setClient(imgur)
            elif "forum" in config.options(section):
                forum = config.get(section, "forum")
                logging.info(" Forum: {}".format(forum))
                blog = moduleForum.moduleForum()
                blog.setClient(forum)
            elif "gmail" in config.options(section):
                mail = config.get(section, "gmail")
                logging.info(" Gmail: {}".format(mail))
                blog = moduleGmail.moduleGmail()
                blog.setClient(("gmail", mail))
            elif "wordpress" in config.options(section):
                wordpress = config.get(section, "wordpress")
                logging.info(" Wordpress: {}".format(wordpress))
                blog = moduleWordpress.moduleWordpress()
                blog.setClient(wordpress)
            elif "imdb" in config.options(section):
                imdb = config.get(section, "imdb")
                logging.info(" Imdb: {}".format(imdb))
                blog = moduleImdb.moduleImdb()
                # blog.setClient((url,config.get(section,'channels').split(',')))
            elif url.find("pocket") >= 0:
                pocket = config.get(section, "url")
                logging.info(" Pocket: {}".format(pocket))
                blog = modulePocket.modulePocket()
                blog.setClient(pocket)

                # If checkBlog is empty it will add all of them
            elif url.find("mastodon") >= 0:
                mastodon = config.get(section, "url")
                logging.info(" Mastodon: {}".format(mastodon))
                blog = moduleMastodon.moduleMastodon()
                blog.setClient(mastodon.split("@")[-1])
            elif url.find("twitter") >= 0:
                twitter = config.get(section, "url")
                logging.info(" Twitter: {}".format(twitter))
                blog = moduleTwitter.moduleTwitter()
                blog.setClient(twitter.split("/")[-1])

            blog.setUrl(url)

            if "linksToAvoid" in config.options(section):
                blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
            if "time" in config.options(section):
                blog.setTime(config.get(section, "time"))
            if "postaction" in config.options(section):
                blog.setPostAction(config.get(section, "postaction"))
            if "numposts" in config.options(section):
                blog.setNumPosts(config.get(section, "numposts"))
            else:
                blog.setNumPosts(1)

            blog.setSocialNetworks(config[section])

            if "max" in config.options(section):
                blog.setMax(config.get(section, "max"))
            elif "buffermax" in config.options(section):
                blog.setBufMax(config.get(section, "buffermax"))
            else:
                blog.setBufMax(1)

            if "cache" in config.options(section):
                blog.setProgram(config.get(section, "cache"))
            if "posts" in config.options(section):
                blog.setPostsType(config.get(section, "posts"))
                if blog.getPostsType() == "search":
                    blog.setSearch(config.get(section, "search"))
            else:
                blog.setPostsType("posts")

            blogs.append(blog)

    return blogs


def updateCaches(blog, socialNetworks, simmulate):
    msgLog = " Updating Caches"
    logMsg(msgLog, 1, 1)

    blog.setPosts()
    # for i, pp in enumerate(blog.getPosts()):
    #    print(i,blog.getPostTitle(pp),
    #            #blog.getPostLink(pp),
    #            blog.getPostLinks(pp)[0])
    # sys.exit()

    bufferMax = blog.getBufMax()

    for profile in socialNetworks:
        lenMax = 0
        i = 0
        link = ""

        nick = socialNetworks[profile]
        socialNetwork = (profile, nick)
        msgLog = "  Service: {} Nick: {}".format(profile, nick)
        logMsg(msgLog, 1, 1)

        if blog.getProgram() and (profile in blog.getProgram()):
            lenMax = blog.len(profile)
        elif bufferMax:
            lenMax = bufferMax
        else:
            lenMax = 1

        msgLog = f"   BufferMax {bufferMax} Lenmax {lenMax}"
        logMsg(msgLog, 1, 0)
        num = blog.getMax()
        if not num:
            num = bufferMax - lenMax
            if num < 0:
                num = 0
        # if lenMax <= num:
        #    #num = lenMax
        # #else:
        #    num = lenMax
        lastLink, lastTime = checkLastLink(blog.getUrl(), socialNetwork)

        if isinstance(lastLink, list):
            if len(lastLink) > 0:
                myLastLink = lastLink[0]
            else:
                myLastLink = ""
        else:
            myLastLink = lastLink

        # if lastLink and isinstance(lastLink, list):
        #    myLastLink = lastLink[0]
        # else:
        #    myLastLink = lastLink

        i = blog.getLinkPosition(myLastLink)

        msgLog = "    Last time: {}".format(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lastTime))
        )
        logMsg(msgLog, 1, 1)

        msgLog = "    Last link: {}".format(myLastLink)
        logMsg(msgLog, 1, 1)

        msgLog = f"    Available {len(blog.getPosts())}"
        logMsg(msgLog, 1, 1)

        msgLog = f"    Would add {num} posts"
        logMsg(msgLog, 1, 1)

        if i == 0:
            msgLog = "    No new posts."
        else:
            msgLog = "    New posts."

        logMsg(msgLog, 1, 1)

        # hours = blog.getTime()

        # msgLog = "    Profile {}".format(profile.capitalize())
        # logMsg(msgLog, 2, 0)

        # msgLog = "bufferMax - lenMax =
        #           num %d %d %d"% (bufferMax, lenMax, num)
        # logMsg(msgLog, 2, 0)

        listPosts = []

        # print(num)
        # print(i)
        # print(lastLink)
        if num > 0:

            link = ""
            listPosts = blog.getNumPostsData(num, i, lastLink)
            # print(num)
            # for i, pp in enumerate(listPosts):
            #    print(i, pp[0])
            # sys.exit()

            if listPosts:
                print("      Would schedule ...")
                logging.info("      Would schedule ...")
                [print("       - {}".format(post[0])) for post in listPosts]
                [
                    logging.info("     - {}".format(post[0]))
                    for post in listPosts
                ]

            if simmulate:
                print("Simmulation {}".format(str(listPosts)))
            elif (
                blog.getProgram()
                and isinstance(blog.getProgram(), list)
                and profile in blog.getProgram()
            ) or (
                blog.getProgram()
                and isinstance(blog.getProgram(), str)
                and (profile[0] in blog.getProgram())
            ):
                # msgLog = "      Delayed"
                # logMsg(msgLog, 1, 1)
                if listPosts:
                    msgLog = "      Adding posts"
                    logMsg(msgLog, 1, 1)
                    link = blog.cache[socialNetwork].addPosts(listPosts)
                else:
                    link = ""

                if link:
                    logging.info("    Updating link %s %s" % (profile, link))
                    if isinstance(lastLink, list):
                        # print(lastLink)
                        link = "\n".join(
                            [
                                "{}".format(post[1])
                                for post in reversed(listPosts)
                            ]
                        )
                        link = link + "\n" + "\n".join(lastLink)

                    updateLastLink(blog.getUrl(), link, socialNetwork)
                    msgLog = "listPosts: {}".format(str(listPosts))
                    logMsg(msgLog, 2, 0)
            else:
                if listPosts:
                    link = blog.addNextPosts(listPosts, socialNetwork)


def prepareUpdates(blogs, simmulate, nowait, timeSlots):
    msgLog = "Preparing updates"
    logMsg(msgLog, 1, 2)

    delayedBlogs = []

    for blog in blogs:
        msgLog = "Updates for site: {}".format(blog.getUrl())
        logMsg(msgLog, 1, 2)

        socialNetworks = blog.getSocialNetworks()

        if socialNetworks:
            msgLog = "Looking for pending posts in {}".format(
                ", ".join(mySN.capitalize() for mySN in socialNetworks.keys())
            )
            logMsg(msgLog, 1, 1)

            updateCaches(blog, socialNetworks, simmulate)
            delayedBlogs = delayedBlogs + prepareUpdatesBlog(
                blog, socialNetworks, simmulate, nowait, timeSlots
            )

        else:
            msgLog = " No social networks configured"
            logMsg(msgLog, 1, 1)

    return delayedBlogs


def prepareUpdatesBlog(blog, socialNetworks, simmulate, nowait, timeSlots):
    # msgLog = " Preparing Updates"
    # logMsg(msgLog, 1, 1)

    delayedBlogs = []

    for profile in socialNetworks:
        nick = socialNetworks[profile]
        socialNetwork = (profile, nick)
        if simmulate:
            msgLog = " Simmulation"
            logMsg(msgLog, 1, 1)
        else:
            if (
                blog.getProgram()
                and isinstance(blog.getProgram(), list)
                and profile in blog.getProgram()
            ) or (
                blog.getProgram()
                and isinstance(blog.getProgram(), str)
                and (profile[0] in blog.getProgram())
            ):

                delayedBlogs.append(
                    (
                        blog,
                        socialNetwork,
                        int(blog.getNumPosts()),
                        nowait,
                        timeSlots,
                    )
                )
            else:
                delayedBlogs.append(
                    (blog, socialNetwork, int(blog.getNumPosts()), nowait, 0)
                )

    return delayedBlogs


def startPublishing(delayedBlogs):
    msgLog = " Starting delayed at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(delayedBlogs)
    ) as executor:
        delayedPosts = {
            executor.submit(moduleSocial.publishDelay, *args): args
            for args in delayedBlogs
        }
        time.sleep(5)
        messages = []
        for future in concurrent.futures.as_completed(delayedPosts):
            dataBlog = delayedPosts[future]
            try:
                res = future.result()
                if res:
                    messages.append(
                        f"  Published in: {dataBlog[1][0]} {dataBlog[1][1]}:"
                        f"\n   {res}"
                    )
                    if not dataBlog[0].getProgram():
                        posL = res.find("http")
                        if posL >= 0:
                            link = res[posL:]
                            if link:
                                socialNetwork = dataBlog[1]
                                updateLastLink(
                                    dataBlog[0].getUrl(), link, socialNetwork
                                )

            except Exception as exc:
                print(
                    "{} generated an exception: {}".format(str(dataBlog), exc)
                )

    msgLog = " Finished delayed at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    for msgLog in messages:
        logMsg(msgLog, 1, 1)


def main():

    loggingLevel = logging.INFO
    logging.basicConfig(
        filename=LOGDIR + "/rssSocial_.log",
        level=loggingLevel,
        format="%(asctime)s [%(filename).12s] %(message)s",
        datefmt="%Y-%m-%d %H:%M",
    )

    msgLog = "Launched at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    import argparse

    parser = argparse.ArgumentParser(
        description="Improving command line call", allow_abbrev=True
    )
    parser.add_argument(
        "--timeSlots",
        "-t",
        default=50,  # 55 minutes
        help="How many time slots we will have for publishing (in minutes)",
    )
    parser.add_argument(
        "checkBlog",
        default="",
        metavar="Blog",
        type=str,
        nargs="?",
        help="you can select just a blog",
    )
    parser.add_argument(
        "--simmulate",
        "-s",
        default=False,
        action="store_true",
        help="simulate which posts would be added",
    )
    parser.add_argument(
        "--noWait",
        "-n",
        default=False,
        action="store_true",
        help="no wait for time restrictions",
    )
    args = parser.parse_args()

    checkBlog = args.checkBlog
    timeSlots = 60 * int(args.timeSlots)
    simmulate = args.simmulate
    nowait = args.noWait

    logging.info("Launched at %s" % time.asctime())
    logging.debug("Parameters %s, %d" % (sys.argv, len(sys.argv)))
    logging.info("Configured blogs:")

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + "/.rssBlogs")

    blogs = []
    delayedBlogs = []

    blogs = readConfig(checkBlog)
    delayedBlogs = prepareUpdates(blogs, simmulate, nowait, timeSlots)
    if not simmulate and delayedBlogs:
        startPublishing(delayedBlogs)

    msgLog = "Finished at %s" % time.asctime()
    logMsg(msgLog, 1, 2)


if __name__ == "__main__":
    main()
