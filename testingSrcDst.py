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

    # def publishDelay(self, src, more, action, 
    #                 noWait, timeSlots, simmulate, name=""): 

    #     path = "/home/ftricas/usr/src/socialModules" 
    #     sys.path.append(path)
    #     from configMod import logMsg

    #     indent = f" {name}"+" "

    #     msgLog = (f"{indent}Sleeping to launch all processes")
    #     logMsg(msgLog, 1, 0)
    #     time.sleep(2)
    #     msgAction = (f"{action[0]} {action[3]}@{action[2]} "
    #                  f"({action[1]})")
    #     msgLog = (f"{indent}Source: {src[2]} ({src[3]}) -> "
    #             f"Action: {msgAction})")

    #     logMsg(msgLog, 1, 0)
    #     textEnd = (f"{msgLog}")

    #     # Destination

    #     apiSrc = self.readConfigSrc(indent, src, more)
    #     apiDst = self.readConfigDst(indent, action, more)

    #     # getSocialNetwork() ?
    #     profile = action[2]
    #     nick = action[3]


    #     socialNetwork = (profile, nick)
    #     msgLog = (f"{indent}socialNetwork: {socialNetwork}")
    #     logMsg(msgLog, 2, 0)

    #     numAvailable = len(apiSrc.getPosts())

    #     indent = f"{indent} "

    #     apiDst.setUrl(apiSrc.getUrl())
    #     apiDst.setUser(nick)

    #     num = apiDst.getMax()
    #     try: 
    #         if action[0] == "cache": 
    #             num = apiDst.availableSlots()
    #     except: 
    #         msgLog = (f"{indent}Except!") 
    #         logMsg(msgLog, 1, 1)
    #     if num < 0: 
    #         num = 0

    #     myLastLink, lastTime = apiDst.getLastTime()
    #     myTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lastTime))
    #     lastLink = myLastLink

    #     # Maybe this should be in moduleContent ?
    #     if isinstance(lastLink, list):
    #         if len(lastLink) > 0:
    #             myLastLink = lastLink[0]
    #         else:
    #             myLastLink = ""
    #     else:
    #         myLastLink = lastLink

    #     if (src[0] in ['twitter','mastodon','gmail', 'cache']):
    #         i = 1
    #         myLastLink = ''
    #     else:
    #         i = apiSrc.getLinkPosition(myLastLink)

    #     indent = f"{indent}  "

    #     if myLastLink:
    #         msgLog = (f"{indent}Last time: {myTime}")
    #         logMsg(msgLog, 1, 1)
    #         msgLog = (f"{indent}Last link: {myLastLink}")
    #         logMsg(msgLog, 1, 1)

    #     msgLog = (f"{indent}DstMax: {apiDst.getMax()}"
    #             f" num: {num} i: {i}"
    #             f" Available: {numAvailable}"
    #             f" Max: {apiDst.getMax()}")
    #     logMsg(msgLog, 1, 1)

    #     msgLog = (f"apiSrc: {apiSrc}")
    #     logMsg(msgLog, 2, 0)
    #     msgLog = (f"apiDst: {apiDst}")
    #     logMsg(msgLog, 2, 0)

    #     listPosts = []

    #     # return ("ok")
    #     if num>0:
    #         diffTime = time.time() - lastTime
    #         msgLog = (f"{indent}Src time: {apiSrc.getTime()} "
    #                 f"Dst time: {apiDst.getTime()}")
    #         logMsg(msgLog, 2, 0)
    #         hours = float(apiDst.getTime())*60*60

    #     if (num > 0) and (noWait or (diffTime>hours)): 
    #         tSleep = random.random()*float(timeSlots)*60
    #         tNow = time.time()

    #         if ((i>0) and (numAvailable>0) and (action[0] not in ['cache'])):
    #                 #and (src[2] != f"{action[2]}@{action[3]}")): 
    #             fileNameNext = setNextTime(apiDst, socialNetwork, tNow, tSleep)
    #             msgLog = (f"{indent}apiSrc: {apiSrc} apiDst: {apiDst}")
    #             logMsg(msgLog, 1, 0)
    #             
    #             text = (f"{indent}Source: {more['url']} ({src[3]}) -> " 
    #                     f"\n{indent}Source: {src[2]} ({src[3]}) -> " 
    #                     f"Action: {msgAction})")
    #             logMsg(text, 1, 0)
    #             msgLog = (f"{indent}{fileNameNext}")
    #             logMsg(text, 1, 0)
    #             with open(fileNameNext,'wb') as f: 
    #                 pickle.dump((tNow,tSleep), f)

    #         if (tSleep>0.0):
    #             # time.sleep(1)
    #             msgLog= f"{indent}Waiting {tSleep/60:2.2f} minutes" 
    #         else:
    #             msgLog= f"{indent}No Waiting"
    #         msgLog = f"{msgLog} for action: {msgAction}"
    #         logMsg(msgLog, 1, 1)

    #         time.sleep(tSleep)

    #         msgLog = (f"{indent}Go!\n"
    #                   f"{indent}└-> Action: {msgAction}")
    #         logMsg(msgLog, 1, 1)


    #         # The source of data can have changes while we were waiting
    #         apiSrc.setPosts()

    #         listPosts = apiSrc.getNumPostsData(num, i, lastLink)

    #         if listPosts and listPosts[0][1]: 
    #             msgLog = f"{indent}Would schedule in {msgAction} ..."
    #             logMsg(msgLog, 1, 1)
    #             indent = f"{indent} "
    #             msgLog = (f"{indent}listPosts: {listPosts}")
    #             logMsg(msgLog, 2, 0)
    #             [ logMsg(f"{indent}- {post[0][:200]}", 1, 1) 
    #                         for post in listPosts 
    #             ]

    #             indent = f"{indent[:-1]}"

    #             # Only the last one.
    #             title = listPosts[-1][0]
    #             link = listPosts[-1][1]
    #             llink = ''
    #             firstLink = listPosts[-1][2]
    #             summaryLinks = listPosts[-1][6]
    #             comment = listPosts[-1][-1]
    #             tags = listPosts[-1][-2]

    #             if profile in ['telegram', 'facebook']: 
    #                 comment = summaryLinks 
    #             elif profile not in 'wordpress':
    #                 comment = ''
    #             if profile == 'pocket': 
    #                 if firstLink: 
    #                     link, llink = firstLink, link

    #             msgLog = (f"{indent}title: {title}")
    #             logMsg(msgLog, 2, 0)
    #             msgLog = (f"{indent}link: {link}")
    #             logMsg(msgLog, 2, 0)
    #             msgLog = (f"{indent}i: {i}")
    #             logMsg(msgLog, 2, 0)

    #             if tags: 
    #                 msgLog = (f"{indent}Tags {tags}")
    #                 logMsg(msgLog, 2, 0)

    #             msgLog = (f"{indent}I'll publish: {title} - {link}")
    #             logMsg(msgLog, 1, 1)

    #             if not simmulate:
    #                 if action[0] == "cache": 
    #                     apiDst.setPosts()
    #                     res = apiDst.addPosts(listPosts)
    #                 else: 
    #                     res = None
    #                     if hasattr(apiDst, 'service'):
    #                         clsService = getModule(apiDst.service)
    #                         if hasattr(apiDst, "publishPost"):
    #                             if profile in ['tumblr']: 
    #                                 # For the cache we use the origin's url
    #                                 # but sometimes we need the url of the
    #                                 # service
    #                                 print(f"url: {apiDst.getUrl()}")
    #                                 apiDst.setUrl(
    #                                     f"https://{apiDst.user}.tumblr.com/")
    #                                 print(f"url: {apiDst.getUrl()}")
    #                             elif profile in ['wordpress']: 
    #                                 res = apiDst.publishApiPost((title, link, 
    #                                                             comment, tags))
    #                             else: 
    #                                 res = apiDst.publishPost(title, link, 
    #                                                             comment) 
    #                         else: 
    #                             res = apiDst.publish(i) 
    #                 indent = f"{indent[:-1]}"

    #                 if (not res) or (res and not ('Fail!' in res)): 
    #                     msgLog = (f"{indent}End publish, reply: {res}")
    #                     logMsg(msgLog, 1, 1)

    #                     if llink:
    #                         link = llink
    #                     if link and (src[0] not in ['cache']):  
    #                         if isinstance(lastLink, list):
    #                             link = "\n".join(
    #                                 [
    #                                     "{}".format(post[1])
    #                                     for post in reversed(listPosts)
    #                                 ]
    #                             )
    #                             link = link + "\n" + "\n".join(lastLink)
    #                         updateLastLink(apiDst.getUrl(), link, socialNetwork)
    #                 else:
    #                     msgLog = (f"{indent}End publish, reply: {res}")
    #                     logMsg(msgLog, 1, 1)
    #             else:
    #                 msgLog = (f"{indent}This is a simmulation")
    #                 logMsg(msgLog, 1, 1)
    #                 msgLog = (f"{indent}I'd record link: {link}")
    #                 logMsg(msgLog, 1, 1)
    #                 fN = fileNamePath(apiDst.getUrl(), socialNetwork)
    #                 msgLog = (f"{indent}in file ", f"{fN}.last")
    #                 logMsg(msgLog, 1, 1)

    #             postaction = apiSrc.getPostAction()
    #             if (not postaction) and (src[0] in ["cache"]):
    #                 postaction = "delete"
    #             if postaction:
    #                 msgLog = (f"{indent} Post Action {postaction}")
    #                 logMsg(msgLog, 1, 1)

    #             if (not simmulate) and (not res or 
    #                     (res and not ('Fail!' in res))):
    #                 try:
    #                     cmdPost = getattr(apiSrc, postaction)
    #                     msgLog = (f"[indent]Post Action {postaction} "
    #                               f"command {cmdPost}")
    #                     logMsg(msgLog, 1, 0)
    #                     res = cmdPost(i - 1)
    #                     msgLog = (f"{indent}End {postaction}, reply: {res}")
    #                     logMsg(msgLog, 1, 1)
    #                 except:
    #                     msgLog = (f"{indent}No postaction or wrong one")
    #                     logMsg(msgLog, 1, 1)
    #             
    #             msgLog = (f"{indent}Available {len(apiSrc.getPosts())-1}")
    #             logMsg(msgLog, 1, 1)
    #         else:
    #             msgLog = f"{indent}Empty listPosts or some problem {listPosts}"
    #             # Sometimes the module (moduleGmail) returns a list of None
    #             # values
    #             logMsg(msgLog, 1, 1)
    #     else:
    #         if (num<=0):
    #             msgLog = (f"{indent}No posts available")
    #             logMsg(msgLog, 1, 1)
    #         elif (diffTime<=hours):
    #             msgLog = (f"{indent}Not enough time passed")
    #             logMsg(msgLog, 1, 1)
 
    #     return textEnd

    def readArgs(self):

        import argparse

        parser = argparse.ArgumentParser(
            description="Improving command line call", allow_abbrev=True
        )
        parser.add_argument(
            "--timeSlots",
            "-t",
            default=50,  # 50 minutes
            help=("How many time slots we will have for publishing "
                 f"(in minutes)"),
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

    command, args = input("Which command? ").split(' ')

    print(f"Command: {command}")
    print(f"Args: {args}")


    rul = None

   
    # rul = ('tumblr', 'set', 'fernand0', 'queue')
    # rul = ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
    # rul = ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
    # rul = ('pocket', 'set', '@ftricas', 'posts') 
    # rul = ('cache',  'set', 
    #         ('http://fernand0-errbot.slack.com/', ('tumblr', 'fernand0')),
    #         'posts')
    # rul = ('cache',  'set', 
    #         ('http://fernand0-errbot.slack.com/', ('twitter', 'fernand0')),
    #         'posts')
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
            print(f"Action: {action}")
            if action[0] == 'cache':
                apiDst = getApi('cache', (action[1], (action[2], action[3]))) 
                logging.info(apiDst)
                apiDst.addPosts( [apiSrc.obtainPostData(j), ])
            else:
                apiDst = getApi(action[2], action[3]) 
                apiDst.setPostsType(rul[3])
                logging.info(apiDst)
                apiDst.setPostsType('posts')
                apiDst.setPosts()
                # print(apiDst.getPosts())
                print(f"I'll publish: {title} - {link}")
                apiDst.publishPost(title, link, '')
        if rul[0] in ['slack']:
            # postaction !!
            idPost = apiSrc.getPostId(post)
            apiSrc.deleteApiPosts(idPost)
        elif rul[0] in ['pocket']:
            apiSrc.archive(j)
        elif rul[0] in ['cache']:
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
            msgLog = (f"{elem} {params}")
            logMsg(msgLog, 2, 0)
            site = getApi(elem, params[1])
            if hasattr(site, 'setPostsType'):
                site.setPostsType(params[2])
            site.setPosts()
            msgLog = (f"Posts: {site.getPosts()}")
            logMsg(msgLog, 2, 0)
            if elem == "forum":
                break


if __name__ == "__main__":
    main()
