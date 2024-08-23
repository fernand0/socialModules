# Queue [cache] files name is composed of a dot, followed by the path of the
# URL, followed by the name of the social network and the name of the user for
# posting there.
# The filename ends in .queue
# For example:
#    .my.blog.com_twitter_myUser.queue
# This file stores a list of pending posts stored as an array of posts as
# returned by moduleRss
# (https://github.com/fernand0/scripts/blob/master/moduleRss
#  obtainPostData method.

import configparser
import importlib
import os
import pickle
import sys

importlib.reload(sys)
from crontab import CronTab

import socialModules
from socialModules.configMod import *
from socialModules.moduleContent import *
#from socialModules.moduleQueue import *


class moduleCache(Content): #,Queue):

    def __init__(self, indent=''):
        super().__init__(indent)
        self.postaction = 'delete'

    def getApiDst(self):
        api = self.apiDst
        # if hasattr(self, 'auxClass'):
        #     myModule = f"module{self.auxClass.capitalize()}"
        #     importlib.import_module(myModule)
        #     mod = sys.modules.get(myModule)
        #     cls = getattr(mod, myModule)
        #     myModule = f"{self.indent} {cls}"
        #     api = cls()
        return api

    def getUser(self):
        user = ''
        if hasattr(self, 'apiSrc'):
            user = self.apiSrc.getUser()
        return user

    def getProfileR(self, rule):
        msgLog = (f"{self.indent} getProfileR {rule}")
        logMsg(msgLog, 2, 0)
        return rule[2:]

    def setPostsType(self, postsType):
        # FIXME. Is this ok?
        if postsType == 'posts':
            self.postsType = 'cache'
        else:
            self.postsType = postsType

    def getPostsType(self):
        return 'posts'

    def fileNameBase(self, dst=None):
        self.indent = f"{self.indent} "
        msgLog = (f"{self.indent} Start fileNameBase (c)")
        logMsg(msgLog, 2, 0)
        myDst = dst
        if hasattr(self, 'fileName') and self.fileName:
            fileName =  self.fileName
        else:
            src = self
            typeSrc = 'posts'
            typeDst = 'posts'

            #nameSrc = type(src).__name__
            nameSrc = src.getNameModule()

            # self.setNick()
            #user = self.getNick()
            user = self.apiSrc.getNick()
            # logging.info(f"Userrrrrrr: {user} - {self.getUser()}")
            # self.setServiceAux()
            service = self.apiSrc.getService()

            userD = self.apiDst.getUser()
            serviceD = self.apiDst.getService()
            # userD = self.src[1][3]
            # serviceD = self.src[1][2]
            nameDst = serviceD.capitalize()

            fileName = (f"{nameSrc}_{typeSrc}_"
                        f"{user}_{service}__"
                        f"{nameDst}_{typeDst}_"
                        f"{userD}_{serviceD}")
            fileName = (f"{DATADIR}/{fileName.replace('/','-').replace(':','-')}")
            self.fileName = fileName

        msgLog = (f"{self.indent} End fileNameBase")
        logMsg(msgLog, 2, 0)
        self.indent = f"{self.indent[:-1]}"
        return fileName

    def initApi(self, keys):
        self.service = 'Cache'
        self.postaction = 'delete'
        self.postsType = 'posts'
        self.url = ""
        self.socialNetwork = ""
        self.user = self.src[2]
        self.nick = self.user
        self.apiDst = getModule(self.src[1][2], f"{self.indent}  (c)")
        self.apiDst.setUser(self.src[1][3])
        self.apiSrc = getModule(self.src[0], f"{self.indent}  (c)")
        # logging.info(f"{self.indent} srcClass: {self.apiSrc}")
        self.apiSrc.setUrl(self.src[2])
        self.apiSrc.setUser()
        self.apiSrc.setNick()
        # logging.info(f"{self.indent} Dst: {self.apiDst.getUser()}")
        # logging.info(f"{self.indent} Dst: {self.apiDst.getNick()}")
        # logging.info(f"{self.indent} Dst: {self.apiDst.getName()}")
        # logging.info(f"{self.indent} Src: {self.apiSrc.getUser()}")
        # logging.info(f"{self.indent} Src: {self.apiSrc.getNick()}")
        # logging.info(f"{self.indent} Src: {self.apiSrc.getName()}")
        # logging.info(f"{self.indent} Src: {self.apiSrc.getUrl()}")
        #FIXME. Do we need three?

        # We are instatiating (but not configuring) the aux api
        self.fileName = ""

        return self

    def getKeys(self, config):
        return None

    def setApiDrafts(self):
        msgLog = f"{self.indent} setApiDrafts"
        # Every cache is the same, even the origin are drafts ??
        return(self.setApiPosts())

    def setApiCache(self):
        return(self.setApiPosts())

    def setApiPosts(self):
        self.indent = f"{self.indent} "
        msgLog = f"{self.indent} Start setApiPosts"
        logMsg(msgLog, 2, 0)
        # fileNameQ = ''
        # service = self.getService()
        # nick = self.getNick()
        # if hasattr(self, 'fileName'):
        #     fileNameQ = self.fileName
        # elif hasattr(self, "socialNetwork"):
        #     service = self.socialNetwork
        #     nick = self.nick
        # else:
        #     service = self.getService()
        #     nick = self.getUser()
        # # msgLog = f"{self.indent} Url: {url} service {service} nick {nick}"
        # # logMsg(msgLog, 2, 0)
        # nick = self.getNick()
        fileNameQ = f"{self.fileNameBase(self.apiDst)}.queue"
        msgLog = (f"{self.indent} File: %s" % fileNameQ)
        logMsg(msgLog, 2, 0)
        listP = []
        try:
            msgLog = checkFile(fileNameQ, f"{self.indent} ")
            logMsg(f"{self.indent}  {msgLog}", 2, 0)
            if "OK" in msgLog:
                with open(fileNameQ,'rb') as f:
                    try:
                        listP = pickle.load(f)
                    except:
                        msgLog = f"Problem loading data"
                        self.report(self.service, msgLog, '', '')
            else:
                self.report(self.service, msgLog, '', '')
        except:
            msgLog = f"Some problem with file {fileNameQ}"
            self.report(self.service, msgLog, '', sys.exc_info())
            listP = []

        # msgLog = f"{self.indent} listP: {listP}"
        # logMsg(msgLog, 2, 0)

        msgLog = f"{self.indent} End setApiPosts"
        logMsg(msgLog, 2, 0)
        self.indent = self.indent[:-1]

        return(listP)

    def getMax(self):
        maxVal = 0
        if hasattr(self, "max"): # and self.max:
            maxVal = int(self.max)
        # msgLog = f"{self.indent} maxVal {maxVal}"
        # logMsg(msgLog, 2, 0)
        self.setPosts()
        lenMax = len(self.getPosts())
        # msgLog = f"{self.indent} len {lenMax}"
        # logMsg(msgLog, 2, 0)
        num = 1
        if maxVal > 1:
            num = maxVal - lenMax
        if num < 0:
            num = 0
        # msgLog = f"{self.indent} num {num}"
        # logMsg(msgLog, 2, 0)
        return num

    def getPosNextPost(self, apiDst=None):
        # cache always shows the first item
        # Some standard contition?
        posLast = 1
        return posLast

    def getHoursSchedules(self, command=None):
        return self.schedules[0].hour.render()

    def getSchedules(self, command=None):
        return self.schedules

    def setSchedules(self, command=None):
        self.setProfile(self.service)
        profile = self.getProfile()
        msgLog = ("Profile %s" % profile)
        logMsg(msgLog, 2, 0)

        profile.id = profile['id']
        profile.profile_id = profile['service_id']
        schedules = profile.schedules
        if schedules:
            self.schedules = schedules
        else:
            self.schedules = None
        #print(self.schedules[0]['times'])
        #print(len(self.schedules[0]['times']))

    def setSchedules(self, command):
        schedules = CronTab(user=True)
        self.crontab = schedules
        self.schedules = []
        schedules = schedules.find_command(command)
        for sched in schedules:
            #print(sched.minute, sched.hour)
            self.schedules.append(sched)

    def addSchedules(self, times):
       myTimes = self.schedules[0].hour
       print("sched", self.schedules[0].render())
       for time in times:
           print(time)
           hour = time.split(':')[0]
           if int(hour) not in myTimes:
               myTimesS = str(myTimes)
               print(myTimes)
               myTimesS = myTimesS + ',' + str(hour)
               self.schedules[0].hour.also.on(str(hour))
           self.crontab.write()

    def delSchedules(self, times):
        myTimes = self.schedules[0].hour
        timesI = []
        for time in times:
            timesI.append(int(time.split(':')[0]))
        print("my",myTimes)
        print("myI",timesI)

        myNewTimes = []
        for time in myTimes:
            print("time",time)
            if time not in timesI:
                myNewTimes.append(time)

        print("myN",myNewTimes)
        self.schedules[0].hour.clear()
        for time in myNewTimes:
            self.schedules[0].hour.also.on(str(time))
        print(self.schedules[0].hour)
        self.crontab.write()

    def addPosts(self, listPosts):
        # FIXME validate the type of date of the posts we are adding.
        link = ''
        if listPosts:
            if not self.getPosts():
                self.setPosts()
            posts = self.getPosts()
            # logging.info(f"a Posts: {posts} listP: {listPosts}")
            for pp in listPosts:
                posts.append(pp)
            #for i, pp in enumerate(posts):
            #    print(i, pp)
            #    link = pp[1]
            self.assignPosts(posts)
            #for i,p in enumerate(posts):
            #    print(i, self.getPostTitle(p), self.getPostLink(p))
            self.updatePostsCache()
        link = self.getPostLink(listPosts[-1])
        return(link)

    def updatePosts(self, src):
        if self.fileName:
            fileName = self.fileName
        else:
            fileName = self.fileNameBase(self)
        fileNameQ = f"{fileName}.queue"

        with open(fileNameQ, 'wb') as f:
            posts = self.getPosts()
            pickle.dump(posts, f)

        msgLog = (f"{self.indent} Writing in {fileNameQ}")
        logMsg(msgLog, 2, 0)
        #msgLog = ("Posts: {}".format(str(self.getPosts())))

        return 'Ok'

    def updatePostsCache(self):
        # fileNameQ = fileNamePath(self.url,
        #         (self.socialNetwork, self.nick)) + ".queue"
        fileNameQ = f"{self.fileNameBase(None)}.queue"

        #if hasattr(self, 'fileName'):
        #    fileNameQ = f"{self.fileName}.queue"
        #elif hasattr(self, "socialNetwork"):
        #    url = self.getUrl()
        #    service = self.socialNetwork
        #    nick = self.nick
        #else:
        #    service = self.getService()
        #    nick = self.getUser()

        # msgLog = (f"{self.indent} Url: {url} service {service} nick {nick}")
        # logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} File Queue: {fileNameQ}")
        logMsg(msgLog, 2, 0)
        # msgLog = ("Posts antes: {}".format(str(self.getPosts())))

        msgLog = (f"{self.indent} Writing in {fileNameQ}")
        logMsg(msgLog, 2, 0)

        with open(fileNameQ, 'wb') as f:
            posts = self.getPosts()
            msgLog = f"{self.indent} Posts updating {self.service} {posts}"
            logMsg(msgLog, 2, 0)
            pickle.dump(posts, f)

        # msgLog = (f"Posts: {str(self.getPosts())}")

        return 'Ok'

    # def extractDataMessage(self, i):
    #     logging.info("Service %s"% self.service)
    #     (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         messageRaw = self.getPosts()[i]

    #         theTitle = messageRaw[0]
    #         theLink = messageRaw[1]

    #         theLinks = None
    #         content = messageRaw[4]
    #         theContent = None
    #         firstLink = theLink
    #         theImage = messageRaw[3]
    #         theSummary = content

    #         theSummaryLinks = content
    #         comment = None

    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def setPostLink(self, post, newLink):
        logging.info(f"{self.indent} setPostLink ")
        #FIXME. This should be similar to setPostTitle
        if post:
            post = self.apiSrc.setPostLink(post, newLink)
            # if hasattr(self, 'auxClass'):
            #     myModule = f"module{self.auxClass.capitalize()}"
            #     importlib.import_module(myModule)
            #     mod = sys.modules.get(myModule)
            #     cls = getattr(mod, myModule)
            #     api = cls(self.indent)
            #     apiCmd = getattr(api, 'setPostLink')
            #     post  = apiCmd(post, newLink)
            # # else:
            # #     # Old style
            # #     title = post[0]
            return post

    def setPostTitle(self, post, newTitle):
        if post:
            post = self.apiSrc.setPostTitle(post, newTitle)
            # if hasattr(self, 'auxClass'):
            #     myModule = f"module{self.auxClass.capitalize()}"
            #     import importlib
            #     importlib.import_module(myModule)
            #     mod = sys.modules.get(myModule)
            #     cls = getattr(mod, myModule)
            #     api = cls(self.indent)
            #     apiCmd = getattr(api, 'setPostTitle')
            #     post  = apiCmd(post, newTitle)
            # # else:
            # #     # Old style
            # #     title = post[0]
            return post

    def getPostTitle(self, post):
        # self.indent = f"{self.indent} "
        # msgLog = (f"{self.indent} Start getPostTitle.")
        # logMsg(msgLog, 2, 0)
        title = ''
        if post:
            title = self.apiSrc.getPostTitle(post)
            # if hasattr(self, 'auxClass'):
            #     # msgLog = (f"{self.indent} auxClass: {self.auxClass}")
            #     # logMsg(msgLog, 2, 0)
            #     if isinstance(self.auxClass, str):
            #         myModule = f"module{self.auxClass.capitalize()}"
            #         import importlib
            #         importlib.import_module(myModule)
            #         mod = sys.modules.get(myModule)
            #         cls = getattr(mod, myModule)
            #         api = cls(self.indent)
            #     else:
            #         api = self.auxClass
            #     logging.debug(f"  Api: {api}")
            #     logging.debug(f"  Post: {post}")
            #     apiCmd = getattr(api, 'getPostTitle')
            #     title  = apiCmd(post)
            # else:
            #     # Old style
            #     title = post[0]
        # msgLog = (f"{self.indent} End getPostTitle.")
        # logMsg(msgLog, 2, 0)
        # self.indent = self.indent[:-1]
        return(title)

    def getPostLink(self, post):
        # self.indent = f"{self.indent} "
        # msgLog = (f"{self.indent} Start getPostLink.")
        # logMsg(msgLog, 2, 0)
        link = ''
        if post:
            link = self.apiSrc.getPostLink(post)
            # if hasattr(self, 'auxClass'):
            #     if isinstance(self.auxClass, str):
            #         myModule = f"module{self.auxClass.capitalize()}"
            #         import importlib
            #         importlib.import_module(myModule)
            #         mod = sys.modules.get(myModule)
            #         cls = getattr(mod, myModule)
            #         api = cls(self.indent)
            #     else:
            #         api = self.auxClass
            #     apiCmd = getattr(api, 'getPostLink')
            #     link = apiCmd(post)
            # else:
            #     link = post[1]
        # msgLog = (f"{self.indent} End getPostLink.")
        # logMsg(msgLog, 2, 0)
        # self.indent = self.indent[:-1]
        return (link)

    def getPostContentHtml(self, post):
        content = ''
        if post:
            content = self.apiSrc.getPostContentHtml(post)
            #if hasattr(self, 'auxClass'):
            #    myModule = f"module{self.auxClass.capitalize()}"
            #    import importlib
            #    importlib.import_module(myModule)
            #    mod = sys.modules.get(myModule)
            #    cls = getattr(mod, myModule)
            #    api = cls(self.indent)
            #    apiCmd = getattr(api, 'getPostContentHtml')
            #    content  = apiCmd(post)
            #else:
            #    content = post[4]
        return content

    def editApiLink(self, post, newLink=''):
        oldLink = self.getPostLink(post)
        idPost = self.getLinkPosition(oldLink)
        oldTitle = self.getPostTitle(post)
        self.setPostLink(post, newLink)
        self.updatePostsCache()
        # if hasattr(self, 'auxClass'):
        #     myModule = f"module{self.auxClass.capitalize()}"
        #     import importlib
        #     importlib.import_module(myModule)
        #     mod = sys.modules.get(myModule)
        #     cls = getattr(mod, myModule)
        #     api = cls(self.indent)
        #     apiCmd = getattr(api, 'editApiLink')
        #     content  = apiCmd(post, newLink)
        # else:
        #     post = post[:1] + ( newLink, ) + post[2:]

    def editApiTitle(self, post, newTitle=''):
        oldLink = self.getPostLink(post)
        idPost = self.getLinkPosition(oldLink)
        oldTitle = self.getPostTitle(post)
        if not newTitle:
            newTitle = self.reorderTitle(oldTitle)
        self.setPostTitle(post, newTitle)
        self.updatePostsCache()
        # FIXME. Twice?

    def insert(self, j, text):
        msgLog = (f"{self.indent} Inserting {text}")
        logMsg(msgLog, 2, 0)
        posts = self.getPosts()
        # We do not use j, Maybe in the future.
        # logging.info(f"posts {posts}")
        if (j>=0) and (j<len(posts)):
            textS = text.split(' http')
            post = (textS[0], 'http'+textS[1], '','','','','','','','')
            self.assignPosts(posts[:j] + [ post ] + posts[j:])
            self.updatePostsCache()

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ''
        msgLog = (f"{self.indent} publishing next post in {self.service}")
        logMsg(msgLog, 1, 0)
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=self, post=post)
                reply = self.processReply(res)
            else:
                reply = "No posts available"
        except:
            reply = self.report(self.service, apiSrc, post, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        if args and len(args)==3:
            title, link, comment = args
        if kwargs:
            more = kwargs
            api = more['api']
            post = more['post']
        # logging.debug(f"more: {more}")
        self.setPosts()
        posts = self.getPosts()
        # logging.debug(f"pppposts: {posts}")
        posts.append(more['post'])
        self.assignPosts(posts)
        self.updatePosts(more['api'])
        return "OK. Published!"

    def getPostId(self, post):
        idPost = ''
        if post:
            idPost = self.apiSrc.getPostId(post)
            #if hasattr(self, 'auxClass'):
            #    myModule = f"module{self.auxClass.capitalize()}"
            #    import importlib
            #    importlib.import_module(myModule)
            #    mod = sys.modules.get(myModule)
            #    cls = getattr(mod, myModule)
            #    api = cls(self.indent)
            #    apiCmd = getattr(api, 'getPostId')
            #    idPost  = apiCmd(post)
            #else:
            #    # Old style
            #    link = self.getPostLink(post)
            #    idPost = self.getLinkPosition(link)
        return idPost

    def deleteApiCache(self, idPost):
        # In caches drafts == posts
        # There is a problem because the origin is a draft in some cases and
        # posts in others. #FIXME ?
        return self.deleteApiPosts(idPost)

    def deleteApiDrafts(self, idPost):
        # In caches drafts == posts
        # There is a problem because the origin is a draft in some cases and
        # posts in others. #FIXME ?
        return self.deleteApiPosts(idPost)

    def deleteApiPosts(self, idPost):
        # FIXME ??
        if isinstance(idPost, str):
            # FIXME
            idPost = self.getIdPosition(idPost)

        # msgLog = (f"{self.indent} id: {idPost}")
        # logMsg(msgLog, 2, 0)
        self.deleteApi(idPost)
        return f"OK. Deleted post {idPost}"

    def deleteApiNextPost(self):
        i = 0
        self.deleteApi(i)
        return f"OK. Deleted post {i}"

    # def publishh(self, j):
    #     logging.info(">>>Publishing %d"% j)
    #     post = self.obtainPostData(j)
    #     logging.info(">>>Publishing {post[0]} in {self.service} user {self.nick}")
    #     api = getApi(self.service, self.nick)
    #     comment = ''
    #     title = post[0]
    #     link = post[1]
    #     comment = ''
    #     update = api.publishPost(title, link, comment)
    #     logging.info("Publishing title: %s" % title)
    #     logging.info("Social network: %s Nick: %s" % (self.service, self.nick))
    #     posts = self.getPosts()
    #     if (not isinstance(update, str)
    #             or (isinstance(update, str) and update[:4] != "Fail")):
    #         self.assignPosts(posts[:j] + posts[j+1:])
    #         logging.debug("Updating %s" % posts)
    #         self.updatePostsCache()
    #         logging.debug("Update ... %s" % str(update))
    #         if ((isinstance(update, str) and ('text' in update))
    #                 or (isinstance(update, bytes) and (b'text' in update))):
    #             update = update['text']
    #         if type(update) == tuple:
    #             update = update[1]['id']
    #             # link: https://www.facebook.com/[name]/posts/[second part of id]
    #     logging.info("Update before return %s"% update)
    #     return(update)

    def delete(self, j):
        # Not sure
        return self.deleteApi(j)

    def deleteApi(self, j):
        # msgLog = (f"{self.indent} Deleting: {j}")
        # logMsg(msgLog, 1, 0)
        posts = self.getPosts()
        # logging.debug(f"Posts antes: {posts}")
        # logging.debug(f"Posts .antes: {self.getPosts()}")
        posts = posts[:j] + posts[j+1:]
        # logging.debug(f"Posts despues: {posts}")
        # logging.debug(f"Posts .despues: {self.getPosts()}")
        self.assignPosts(posts)
        # logging.debug(f"Posts + despues: {posts}")
        # logging.debug(f"Posts + .despues: {self.getPosts()}")
        self.updatePostsCache()

        return(f"Deleted: {j}")

     # def obtainPostData(self, i, debug=False):
     #     if not self.posts:
     #         self.setPosts()

     #     posts = self.getPosts()

     #     if not posts:
     #         return None
     #     post = posts[i]
     #     return post

    def copy(self, j, dest):
        msgLog = (f"{self.indent} Copying {j} to {dest}")
        logMsg(msgLog, 1, 0)
        posts = self.getPosts()
        post = posts[j:j+1]
        msgLog = (f"Copying: {self.getPostTitle(post)}")
        logMsg(msgLog, 1, 0)
        msgLog = (f"Destination: {dest}")
        logMsg(msgLog, 1, 0)
        # msgLog = (f"Posts: {posts}")
        # msgLog = (f"Post: {post}")

        #yield f"src: {src}"

        return("%s"% dest.addPosts(post))

        if j > k:
            for i in range(j-1,k-1,-1):
                posts[i+1] = posts[i]
        elif j < k:
            for i in range(j, k):
                posts[i] = posts[i+1]

        posts[k] = post
        self.assignPosts(posts)
        self.updatePostsCache()
        msgLog = (f"{self.indent} Moved {self.getPostTitle(post)}")
        logMsg(msgLog, 1, 0)
        return("%s"% self.getPostTitle(post))

    def move(self, j, dest):
        k = int(dest)
        msgLog = (f"{self.indent} Moving %d to %d"% (j, k))
        logMsg(msgLog, 1, 0)
        posts = self.getPosts()
        post = posts[j]
        msgLog = (f"{self.indent} Moving {self.getPostTitle(post)}")
        logMsg(msgLog, 1, 0)
        if j > k:
            for i in range(j-1,k-1,-1):
                posts[i+1] = posts[i]
        elif j < k:
            for i in range(j, k):
                posts[i] = posts[i+1]

        posts[k] = post
        self.assignPosts(posts)
        self.updatePostsCache()
        msgLog = (f"{self.indent} Moved {self.getPostTitle(post)}")
        logMsg(msgLog, 1, 0)
        return(f"{self.getPostTitle(post)}")

def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleCache
    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    name = nameModule()
    print(f"Name: {name}")

    rulesList = rules.selectRule(name)
    for i, rule in enumerate(rulesList):
        print(f"{i}) {rule}")

    sel = int(input(f"Which one? "))
    src = rulesList[sel]
    print(f"Selected: {src}")
    more = rules.more[src]
    indent = ""
    apiSrc = rules.readConfigSrc(indent, src, more)
    print(f"Url: {apiSrc.getUrl()}")
    print(f"apiDst: {apiSrc.getApiDst()}")
    print(f"User apiDst: {apiSrc.getApiDst().getUser()}")
    print(f"User: {apiSrc.getUser()}")
    print(f"User src: {apiSrc.apiSrc.getUser()}")
    print(f"User src: {apiSrc.apiSrc.getNick()}")

    testingFiles = False

    if testingFiles:
        import socialModules.moduleCache
        import socialModules.moduleRules
        rules = socialModules.moduleRules.moduleRules()
        rules.checkRules()

        queues = []
        for fN in os.listdir(f"{DATADIR}"):
            if (fN[0].isupper() and fN.find('queue')>=0):
                queues.append(fN)

        for i, fN in enumerate(queues):
            print(f"{i}) {fN}")

        sel = input('Select one ')

        fN = queues[int(sel)]
        try:
            url, sN, nick = fN.split('_')
            nick = nick[:-len('.queue')]
        except:
            url = ''
            sN = ''
            nick = ''
            sN = fN.split('__')[0]
            sN = sN.split('_')[-1]
            myModule = f"module{sN.capitalize()}"
            print(f"{myModule}")
            import importlib
            importlib.import_module(myModule)
            mod = sys.modules.get(myModule)
            cls = getattr(mod, myModule)
            api = cls()

            apiCmd = getattr(api, 'getPostTitle')

        print(f"url: {url} social network: {sN} nick: {nick}")
        fNP = f"{DATADIR}/{fN}"
        import time
        fileT = time.strftime("%Y-%m-%d %H:%M:%S",
                time.localtime(os.path.getmtime(fNP)))
        print(f"File name: {fNP} Date: {fileT}")

        action = input(f"Actions: (D)elete, (S)how (T)itles (L)inks ")

        if action.upper()in ['S','T', 'L']:
            url = f"https://{url}/"

            site = socialModules.moduleCache.moduleCache()
            print(f"File: {fNP}")
            service = fNP.split('__')[0].split('_')[-1].lower()
            url = fNP.split('__')[0].split('_')[2].replace('---','://').replace('-','/')
            user = url.split('/')[-1]

            indent = ""
            src = ('cache', (service, url), f"{service}@{user}", 'posts')
            more = {}
            apiSrc = rules.readConfigSrc(indent, src, more)
            apiSrc.setPosts()
            posts = site.getPosts()
            if not posts:
                with open(fNP,'rb') as f:
                    try:
                        listP = pickle.load(f)
                    except:
                        listP = []
                posts = listP

            print()
            if action.upper() == 'T':
                [ print(f"{i}) {apiCmd(post)}") for i, post in enumerate(posts) ]
            elif action.upper() == 'L':
                apiCmd = getattr(api, 'getPostLink')
                [ print(f"{i}) {apiCmd(post)}") for i, post in enumerate(posts) ]
            else:
                print(posts)
            print()
        elif action.upper() in ['D']:
            fileDelete = f"{fNP}"
            ok = input(f"I'll delete {fileDelete} ")
            os.remove(fileDelete)
        return

    dataSources = {'S0': {'sn':'slack',
                          'nick':'http://fernand0-errbot.slack.com/'},
                   'G0': {'sn':'gitter',
                          'nick':'https://gitter.im/fernand0errbot/'},
                   }

    dataCaches = {'S0': {'sn':'slack', 'nick':'http://fernand0-errbot.slack.com/'},
                  'H0': {'sn':'linkedin', 'nick':'Fernando Tricas'},
                  'H1': {'sn':'twitter', 'nick':'fernand0'},
                  'H2': {'sn':'facebook', 'nick':'Enlaces de fernand0'},
                  'H3': {'sn':'mastodon', 'nick':'@fernand0@mastodon.social'},
                  'H4': {'sn':'tumblr', 'nick':'fernand0'},
                  'H5': {'sn':'imgur', 'nick':'ftricas'},
                  'H6': {'sn':'twitter', 'nick':'fernand0Test'},
                  'H7': {'sn':'facebook', 'nick':'Fernand0Test'},
                  'H8': {'sn':'telegram', 'nick':'testFernand0'},
                  }

    testingPublishPos = False
    if testingPublishPos:
        url = 'http://fernand0-errbot.slack.com/'
        cache = input("Which source? ").capitalize()
        nickDst = dataSources[cache]['nick']
        snDst = dataSources[cache]['sn']
        site = getApi(snDst, nickDst)
        site.setPosts()
        [ print(f"{i}) {site.getPostTitle(post)}")
         for i, post in enumerate(site.getPosts()) ]
        pos = int(input("Which post? "))
        for cache in dataCaches.keys():
            print(f"Cache: {cache}) - {dataCaches[cache]}")
            reply = input("Publish? ")
            if reply != 'y':
                continue
            nickDst = dataCaches[cache]['nick']
            snDst = dataCaches[cache]['sn']
            siteDst = getApi('cache', (site, (snDst, nickDst)))
            siteDst.socialNetwork = snDst
            siteDst.nick = nickDst
            siteDst.setPostsType('posts')
            siteDst.setPosts()
            siteDst.publishPosPost(site, pos)
        return

    testingEditPos = False
    if testingEditPos:
        print("Testing edit Posts")
        apiSrc.setPosts()

        [ print(f"{i}) {apiSrc.getPostTitle(post)}")
         for i, post in enumerate(apiSrc.getPosts()) ]
        pos = int(input("Which post? "))
        post = apiSrc.getPost(pos)
        print(apiSrc)
        newTitle = input("New title? ")
        newPosts = apiSrc.editApiTitle(post, newTitle)
        # FIXME. It has been recorded
        # posts = apiSrc.getPosts()
        # posts[pos] = newPost
        print(f"new: {newPosts}")
        #apiSrc.assignPosts(posts)
        print(apiSrc.updatePostsCache())

        return

    testingEditLink = True
    if testingEditLink:
        print("Testing edit Post link")
        apiSrc.setPosts()

        [ print(f"{i}) {apiSrc.getPostTitle(post)} - {apiSrc.getPostLink(post)}")
         for i, post in enumerate(apiSrc.getPosts()) ]
        pos = int(input("Which post? "))
        post = apiSrc.getPost(pos)
        print(apiSrc)
        newLink = input("New link? ")
        newPosts = apiSrc.editApiLink(post, newLink)
        # FIXME. It has been recorded
        # posts = apiSrc.getPosts()
        # posts[pos] = newPost
        print(f"new: {newPosts}")
        #apiSrc.assignPosts(posts)
        # print(apiSrc.updatePostsCache())

    testingPosts = True
    if testingPosts:
        print("Testing Posts")
        cmd = getattr(apiSrc, 'setApiPosts')
        posts = cmd
        posts = cmd()
        for i, post in enumerate(posts):
            print(f"{i}) {apiSrc.getPostTitle(post)} - {apiSrc.getPostLink(post)}")
        return
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"{i}) {apiSrc.getPostTitle(post)}")

        return


    testingPublishPos = True
    if testingPublishPos:
        snDst = 'facebook'
        nickDst = 'Enlaces de fernand0'
        url = 'http://fernand0-errbot.slack.com/'
        siteDst = getApi(snDst, nickDst)
        siteDst.setPage(nickDst)
        site = getApi('cache', ('slack', url, f"{snDst}@{nickDst}"))
        site.socialNetwork = snDst
        site.nick = nickDst
        site.setPostsType('posts')
        site.auxClass = 'slack'
        site.setPosts()
        pos = int(input("Which post? "))
        print(siteDst.publishPosPost(site, pos))

        return


    try:
        config = configparser.ConfigParser()
        config.read(CONFIGDIR + '/.rssBlogs')

        section = "Blog7"
        url = config.get(section, 'url')
        cache = config[section]['cache']
        for sN in cache.split('\n'):
            nick = config[section][sN]
            print('- ', sN, nick)
            site = moduleCache.moduleCache()
            site.setClient((url, (sN, nick)))
            site.setPosts()
            print(len(site.getPosts()))
            posts = site.getPosts()[:8]
            for i, post in enumerate(posts):
                print(i, site.getPostTitle(post))
                link = site.getPostLink(post)
                print(link)
                #updateLastLink(url, link, (sN, nick))
            return
            site.posts = posts
            #site.updatePostsCache()

            print(checkLastLink(url, (sN, nick)))

    except:
        cache = moduleCache.moduleCache()
        cache.setClient(('http://fernand0-errbot.slack.com/',
                ('twitter', 'fernand0')))
        cache.setPosts()
        print(len(cache.getPosts()))
        sys.exit()
        print(cache.getPostTitle(cache.getPosts()[0]))
        print(cache.getPostLink(cache.getPosts()[0]))
        # print(cache.selectAndExecute('insert', 'A2 Do You Really Have a Right to be “Forgotten”? - Assorted Stuff https://www.assortedstuff.com/do-you-really-have-a-right-to-be-forgotten/'))
        print(cache.getPostTitle(cache.getPosts()[9]))
        print(cache.getPostLink(cache.getPosts()[9]))
        cache.setPosts()
        print(cache.getPostTitle(cache.getPosts()[9]))
        sys.exit()
        cache.setSchedules('rssToSocial')
        print(cache.schedules)
        cache.addSchedules(['9:00','20:15'])
        print(cache.schedules)
        cache.delSchedules(['9:00','20:15'])
    sys.exit()

    print(cache.getPosts())
    print(cache.getPosts()[0])
    print(len(cache.getPosts()[0]))
    # # It has 10 elements
    # print(cache.obtainPostData(0))
    # print(cache.selectAndExecute('show', 'T0'))
    # print(cache.selectAndExecute('show', 'M0'))
    # print(cache.selectAndExecute('show', 'F1'))
    # print(cache.selectAndExecute('show', '*2'))
    # print(cache.selectAndExecute('show', 'TM3'))
    # print(cache.selectAndExecute('show', 'TM6'))
    # print(cache.selectAndExecute('move', 'T5 0'))
    # #print(cache.selectAndExecute('editl', 'T1 https://www.pagetable.com/?p=1152'))
    # #print(cache.selectAndExecute('delete', 'F7'))
    # #print(cache.selectAndExecute('edit', 'T3'))
    # #print(cache.selectAndExecute('edit', 'T0'))
    # #print(cache.selectAndExecute('publish', 'T1'))
    # sys.exit()

    # blog.cache.setPosts()
    # print('T0', blog.cache.selectAndExecute('show', 'T0'))
    # print('T3', blog.cache.selectAndExecute('show', 'T3'))
    # print('TF2', blog.cache.selectAndExecute('show', 'TF2'))
    # print('F4', blog.cache.selectAndExecute('show', 'F4'))
    # print('*3', blog.cache.selectAndExecute('show', '*3'))
    # #print('F0', blog.cache.selectAndExecute('delete', 'F0'))
    # #print('edit F0', blog.cache.selectAndExecute('edit', 'F0'+' '+'LLVM 8.0.0 Release.'))
    # #print('edit F0', blog.cache.editPost('F0', 'Así es Guestboard, un "Slack" para la organización de eventos.'))
    # #print('publish T0', blog.cache.publishPost('T0'))
    # #ca.movePost('T4 T3')
    # #ca.editPost('T4', "My Stepdad's Huge Dataset.")
    # #ca.editPost('F5', "¡Sumate al datatón y a WiDS 2019! - lanacion.com")
    # sys.exit()
    # print(ca.editPost('F1', 'Alternative Names for the Tampon Tax - The Belladonna Comedy'))
    # sys.exit()
    # print(cache.editPost(postsP, 'F1', '10 Tricks to Appear Smart During Meetings – The Cooper Review – Medium...'))
    # sys.exit()

    # publishPost(api, profiles, ('F',1))

    # posts.update(postsP)
    # print("-> Posts",posts)
    # #print("Posts",profiles)
    # print("Keys",posts.keys())
    # print("Pending",type(profiles))
    # profiles = listSentPosts(api, "")
    # print("Sent",type(profiles))


    # if profiles:
    #    toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
    #    #publishPost(api, profiles, toPublish)


if __name__ == '__main__':
    main()
