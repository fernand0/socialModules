# This module provides infrastructure for managing content in different 
# queues: local cache, buffer, Gmail, ... 

import configparser
import os
import logging
import re

class Queue:

    def __init__(self):
        self.name = None
        self.service = None
        self.nick = None
        self.socialNetwork = None
        self.posts = None
        self.postsFormatted = None

    def getProfiles(self):
        if not self.profiles:
            self.setProfiles()
        return(self.profiles)
 
    def getPostsFormatted(self):    
        return(self.postsFormatted)

    def lenMax(self): 
        return(len(self.getPosts()))

    def reorderTitle(self, oldTitle):            
        p = re.compile('\w')
        newTitle = ''
        for word in oldTitle.split():
            if not p.search(word):
                word = ' '+word+' '
                newTitle = word.join(oldTitle.split(word)[::-1])
                break
        if not newTitle:
            newTitle = oldTitle
        return(newTitle)

    def extractDataMessage(self, i):
        logging.info("extract queue")
        if hasattr(self, 'getPostsType'):
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPosts()
        if i < len(posts):
            post = posts[i]
            logging.info("Post: %s"% post)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLink(post)
        else:
            theTitle = None
            theLink = None
        return (theTitle, theLink, None, None, None, None, None, None, None, None)

    def obtainPostData(self, i, debug=False):
        logging.info("Obtain post data Service %s"% self.service)
        return (self.extractDataMessage(i))

    def selectAndExecute(self, command, args):
        # FIXME Does this go here?
        logging.info(f"Selecting {command} with {args} in {self.getService()}")
        argsCont = ''
        pos = args.find(' ')
        j = -1
        if pos > 0: 
            argsIni = args[:pos]
            argsCont = args[pos+1:]
            logging.debug(f"Args {argsIni}-{argsCont}")
            if (argsCont and len(argsCont)>1): 
                if argsCont[0].isdigit() and (argsCont[1] == ' '): 
                    j = int(argsCont[0])
                    argsCont = argsCont[2:]
        else: 
            argsIni = args
            logging.info(f"Args {argsIni}")

        pos = argsIni.find('*')
        if pos == 0: 
            """ If the first character of the argument is a '*' the following
            ones are the number. But we are supposing that they start at the
            third character, so we move the string one character to the right
            """
            argsIni=' {}'.format(argsIni)

        reply = ""

        if len(argsIni) > 2:
            j = int(argsIni[2:]) 
        logging.debug(f"Argscont {argsCont} j {j}")
        logging.debug(f"Self: {self}")
        cmd = getattr(self, command)
        logging.debug(f"Cmd: {cmd}")
        if (j>=0):
            logging.info("Command %s %d"% (command, j))
            if argsCont:
                reply = reply + str(cmd(j, argsCont))
            else: 
                reply = reply + str(cmd(j))
        else:
            logging.info("Missing argument %s %d"% (command, j))
            reply = "Missing argument"

        logging.info(f"Reply: {reply}")
        return(reply)

    def showR(self, j):
        if j < len(self.getPosts()):
            post = self.getPosts()[j]
            reply = f"Post: {post}"
        return reply

    #FIXME should we put here related commands or move this one to
    # moduleContent?  
    def show(self, j):
        if j < len(self.getPosts()):
            logging.info("To show post %d" % j)

            post = self.getPosts()[j]
            title = self.getPostTitle(post)
            link = self.getPostLink(post)
            content = self.getPostContent(post)
            if (title == content):
                content = ''

            reply = ''
            logging.info("title %s"%title)
            if title:
                reply = reply + ' ' + title 
            if content:
                reply = reply + ' ' + content
            if link: 
                reply = reply + '\n' + link 
        else:
            reply = ''

        return(reply)

    def publish(self, j):
        """A command to publish some update"""
        logging.info(f"To publish post {j}")
        if j < len(self.getPosts()):
            post = self.getPost(j)
            logging.debug(f"Post: {post}")
            client = self.client
            logging.debug(f"Clients: {client}")
            #available = self.available
            rules = self.rules
            logging.debug(f"Rules: {rules}")

            logging.info(f"Publishing {args}")
            RES = ""

            logging.debug(f"Avail: {available}")
            dst = (
                available[args[0].lower()]["name"],
                "set",
                available[args[0].lower()]["data"][int(args[1])]['src'][1],
                available[args[0].lower()]["data"][int(args[1])]['src'][2],
            )
            src = (dst[0], dst[2])
            logging.info(f"Src: {src}")
            logging.info(f"Dst: {dst}")
            logging.debug(f"Rules: {rules}")

        return post

        # clients = self.clients
        # logging.debug(f"Clients: {clients}")
        # available = self.available
        # rules = self.rules

        # logging.info(f"Publishing {args}")
        # yield (f"Publishing {args}")
        # res = ""

        # # yield(f"Avail: {available}")
        # logging.debug(f"Avail: {available}")
        # dst = (
        #     available[args[0].lower()]["name"],
        #     "set",
        #     available[args[0].lower()]["data"][int(args[1])]['src'][1],
        #     available[args[0].lower()]["data"][int(args[1])]['src'][2],
        # )
        # src = (dst[0], dst[2])
        # # yield(f"Src: {src}")
        # # yield(f"Dst: {dst}")
        # logging.info(f"Src: {src}")
        # logging.info(f"Dst: {dst}")
        # logging.debug(f"Rules: {rules}")
        # if isinstance(dst[2], tuple):
        #     nickSn = f"{dst[2][1][0]}@{dst[2][1][1]}"
        #     dst2 = dst[:2]+ (nickSn,)+('posts', )
        # else:
        #     dst2 = dst
        # logging.debug(f"Dst2: {dst2}")
        # actions = rules[dst2]
        # apiSrc = getApi(src[0], src[1])
        # # yield apiSrc
        # apiSrc.setPostsType(dst[3])
        # apiSrc.setPosts()
        # j = int(args[2:])
        # post = apiSrc.getPost(j)
        # title = apiSrc.getPostTitle(post)
        # link = apiSrc.getPostLink(post)
        # logging.debug(f"Title: {title}")
        # logging.debug(f"Link: {link}")
        # logging.debug(f"Actions: {actions}")

        # published = False
        # for i, action in enumerate(actions):
        #     if post: 
        #         logging.info(f"Action {i}: {action} with post: {post}")
        #     if action[0] == "cache":
        #         apiDst = getApi("cache", (src[1], (action[2], action[3])))
        #         # FIXME
        #         apiDst.socialNetwork=action[2]
        #         apiDst.nick=action[3]
        #         res = apiDst.addPosts(
        #             [
        #                 apiSrc.obtainPostData(j),
        #             ]
        #         )
        #     else:
        #         apiDst = getApi(action[2], action[3])
        #         apiDst.setPostsType(action[1])
        #         if 'tumblr' in dst2[0]:
        #             # Dirty trick. The publishing method checks data which
        #             # comes from source. Not OK
        #             apiDst.setPostsType('queue')
        #         elif 'gmail' in dst2[0]:
        #             # Needs some working
        #             apiDst.setPostsType('drafts')
        #         yield (f"I'll publish {title} - {link} ({action[1]})")
        #         if not published:
        #             if hasattr(apiDst, "publishApiPost"):
        #                 res = apiDst.publishPost(title, link, "")
        #             else:
        #                 res = apiDst.publish(j)
        #             if not ('Fail' in res):
        #                 published = True
        #         else:
        #             res = "Other action published before"
        #         # res = apiDst.publishPost(title, link, '')
        #     yield (f"Published, reply: {res}")

        # postaction = apiSrc.getPostAction()
        # if (not postaction) and (src[0] in ["cache","slack"]):
        #     # Different from batch process because we do not want the item to
        #     # reappear in scheduled sending. There can be problems if the link
        #     # is in some cache.
        #     postaction = "delete"
        # logging.debug(f"Post Action {postaction}")
        # try:
        #     cmdPost = getattr(apiSrc, postaction)
        #     yield (f"Post Action: {postaction}")
        #     res = cmdPost(j)
        #     yield (f"End {postaction}, reply: {res}")
        # except:
        #     res = "No postaction or wrong one"
        #     yield (res)
        # yield end()


    
    #######################################################
    # These need work
    #######################################################
    
    def movePost(self, args):
        # Moving posts, we identify the profile by the first letter. We can use
        # several letters and if we put a '*' we'll move the posts in all the
        # social networks
        logging.info("To move %s to %s" % (toMove,toWhere))
    
        i = 0
        profMov = ""
        return(args)
        while toMove[i].isalpha():
            profMov = profMov + toMove[i]
            i = i + 1
    
        profiles = cache['profiles']
        for profile in profiles: 
            logging.info("Social Network %s" % profile)
            logging.info("profMov %s", profMov)
            if 'socialNetwork' in profile:
                logging.info("socialNetwork %s", profile['socialNetwork'])
    
                serviceName = profile['socialNetwork'][0].capitalize()
                nick = profile['socialNetwork'][1]
                if (serviceName[0] in profMov) or toMove[0]=='*': 
                    logging.info("to Move %s to %s" % (toMove, toWhere))
                    j = int(toMove[-1])
                    k = int(toWhere[-1])
                    postI = (posts[serviceName]['pending'][i])
                    postJ = (posts[serviceName]['pending'][j])
                    posts[serviceName]['pending'][i] = postJ
                    posts[serviceName]['pending'][j] = postI
                    updatePostsCache(profile['socialNetwork'])
    
        return(posts[serviceName]['pending'][i][0]+' '+ 
                  posts[serviceName]['pending'][j][0])
    
    def copyPost(self, api, log, profiles, toCopy, toWhere):
        logging.info(toCopy+' '+toWhere)
    
        profCop = toCopy[0]
        ii = int(toCopy[1])
    
        j = 0
        profWhe = ""
        i = 0
        while i < len(toWhere):
            profWhe = profWhe + toWhere[i]
            i = i + 1
        
        log.info(toCopy,"|",profCop, ii, profWhe)
        for i in range(len(profiles)):
            serviceName = profiles[i].formatted_service
            log.info("ii: %s" %i)
            updates = getattr(profiles[j].updates, 'pending')
            update = updates[ii]
            if ('media' in update): 
                if ('expanded_link' in update.media):
                    link = update.media.expanded_link
                else:
                    link = update.media.link
            else:
                link = ""
           
            if (serviceName[0] in profCop):
                for j in range(len(profiles)): 
                    serviceName = profiles[j].formatted_service 
                    if (serviceName[0] in profWhe):
                        profiles[j].updates.new(urllib.parse.quote(update.text + " " + link).encode('utf-8'))
    

