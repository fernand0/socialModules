import configparser
import inspect
import logging
import os
import random
import sys
import time
import urllib.parse

path = f"{os.path.expanduser('~')}/usr/src/socialModules"
sys.path.append(path)
import moduleRules
from configMod import *


class srcDst:
    def readArgs(self):
        import argparse

        parser = argparse.ArgumentParser(
            description="Improving command line call", allow_abbrev=True
        )
        parser.add_argument(
            "--timeSlots",
            "-t",
            default=50,  # 50 minutes
            help=("How many time slots we will have for publishing " f"(in minutes)"),
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

        return args


def main():
    logging.basicConfig(
        filename=LOGDIR + "/rssSocial.log",
        level=logging.INFO,
        format="%(asctime)s [%(filename).12s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    msgLog = "Launched at %s" % time.asctime()
    logMsg(msgLog, 1, 2)

    rules = moduleRules.moduleRules()
    srcs, dsts, ruls, impRuls = rules.checkRules()

    local = srcDst()
    args = local.readArgs()

    rules.executeRules(args)

    return

    command, args = input("Which command? ").split(" ")

    print(f"Command: {command}")
    print(f"Args: {args}")

    rul = None

    if rul:
        apiSrc = getApi(rul[0], rul[2])
        apiSrc.setPostsType(rul[3])
        apiSrc.setPosts()
        j = 0
        post = apiSrc.getPost(j)
        title = apiSrc.getPostTitle(post)
        link = apiSrc.getPostLink(post)
        # print(title)
        # print(link)
        for action in ruls[rul]:
            # print(f"Action: {action}")
            if action[0] == "cache":
                apiDst = getApi("cache", (action[1], (action[2], action[3])))
                logging.info(apiDst)
                apiDst.addPosts(
                    [
                        apiSrc.obtainPostData(j),
                    ]
                )
            else:
                apiDst = getApi(action[2], action[3])
                apiDst.setPostsType(rul[3])
                logging.info(apiDst)
                apiDst.setPostsType("posts")
                apiDst.setPosts()
                # print(apiDst.getPosts())
                print(f"I'll publish: {title} - {link}")
                apiDst.publishPost(title, link, "")
        if rul[0] in ["slack"]:
            # postaction !!
            idPost = apiSrc.getPostId(post)
            apiSrc.deleteApiPosts(idPost)
        elif rul[0] in ["pocket"]:
            apiSrc.archive(j)
        elif rul[0] in ["cache"]:
            apiSrc.delete(j)

        # We can delete here because we have the data, but ... What happens if
        # something goes wrong? Deleting depends on the source. Sometimes is
        # not possible

    # rules
    sys.exit()

    # rules.printList(ruls, "Rules")
    # rules.printList(impRuls, "Implicit Rules")
    available = {}
    for src in srcs:
        if not (src[0] in available):
            available[src[0]] = [src[1:]]
        else:
            available[src[0]].append(src[1:])

    # import pprint
    # pprint.pprint(available)
    # rules.printList(available, "A ver")
    myKeys = {}
    myIniKeys = []
    print("Available list")
    for i, key in enumerate(available):
        print(f"{i}) {key} - {len(available[key])}")
    print("Testing posts")
    for elem in available:
        iniK, nameK = rules.getIniKey(elem, myKeys, myIniKeys)
        myIniKeys.append(iniK)
        logging.info(f"{elem} ({iniK}) - {len(available[elem])}")
        for params in available[elem]:
            msgLog = f"{elem} {params}"
            logMsg(msgLog, 2, 0)
            site = getApi(elem, params[1])
            if hasattr(site, "setPostsType"):
                site.setPostsType(params[2])
            site.setPosts()
            msgLog = f"Posts: {site.getPosts()}"
            logMsg(msgLog, 2, 0)
            if elem == "forum":
                break


if __name__ == "__main__":
    main()
