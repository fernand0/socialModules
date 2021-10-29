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

import configparser, os
import pickle
import logging
import sys
import importlib
importlib.reload(sys)
from crontab import CronTab

from configMod import *
from moduleQueue import *
from moduleContent import *

class moduleCache(Content,Queue):
    
    def __init__(self):
        super().__init__()
        self.service = 'Cache'
        self.nick = None
        self.postaction = 'delete'
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def setClient(self, param):
        logging.info(f"    Connecting Cache {self.service}: {param}")
        self.postsType = 'posts'
        if isinstance(param, str):
            self.url = param
            self.user = param
            logging.warning("This is not possible!")
        elif isinstance(param[1], str):
            if param[0].find('http')>= 0:
                self.url = param[0]
            else:
                self.socialNetwork = param[0]
                self.service = param[0] 
            self.user = param[1]
            if self.user.find('\n')>=0:
                self.user = None
        else: 
            self.url = param[0]
            self.service = param[1][0] 
            self.user = param[1][1]

    def setApiDrafts(self):        
        # Every cache is the same, even the origin are drafts ??
        return(self.setApiPosts())

    def setApiPosts(self):        
        url = self.getUrl()
        if hasattr(self, "socialNetwork"):
            service = self.socialNetwork
        else: 
            service = self.getService()
        nick = self.getUser()
        logging.debug(f"Url: {url} service {service} nick {nick}")
        fileNameQ = fileNamePath(url, (service, nick)) + ".queue"
        logging.debug("File: %s" % fileNameQ)
        try:
            with open(fileNameQ,'rb') as f: 
                try: 
                    listP = pickle.load(f) 
                except: 
                    listP = [] 
        except:
            listP = []

        return(listP)

    #def getMax(self):
    #    return self.availableSlots()

    def getMax(self):
        maxVal = 0
        if hasattr(self, "max"): # and self.max:
            maxVal = int(self.max)
        self.setPosts()
        lenMax = len(self.getPosts()) 
        num = 1
        if maxVal > 1: 
            num = maxVal - lenMax 
        if num < 0:
            num = 0
        return num

    def getPosNextPost(self):
        # cache always shows the first item
        # Some standard contition?
        posts = self.getPosts()

        posLast = -1 

        if posts and (len(posts) > 0):
            posLast = 1

        # We will return a list for the case of returning more than one post
        return posLast


    def getHoursSchedules(self, command=None):
        return self.schedules[0].hour.render()

    def getSchedules(self, command=None):
        return self.schedules

    def setSchedules(self, command=None):
        self.setProfile(self.service)
        profile = self.getProfile()
        logging.debug("Profile %s" % profile)
    
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
        link = ''
        if listPosts:
            if not self.getPosts():
                self.setPosts()
            posts = self.getPosts()
            logging.debug(f"a Posts: {posts} listP: {listPosts}")
            for pp in listPosts:
                posts.append(pp)
            #for i, pp in enumerate(posts):
            #    print(i, pp)
            #    link = pp[1]
            self.assignPosts(posts)
            #for i,p in enumerate(posts):
            #    print(i, self.getPostTitle(p), self.getPostLink(p))
            self.updatePostsCache()
        link = listPosts[-1][1]
        return(link)

    def updatePostsCache(self):
        fileNameQ = fileNamePath(self.url, 
                (self.service, self.user)) + ".queue"

        with open(fileNameQ, 'wb') as f: 
            posts = self.getPosts()
            pickle.dump(posts, f)

        logging.debug("Writing in %s" % fileNameQ)
        logging.debug("Posts: {}".format(str(self.getPosts())))

        return 'Ok'

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

        if i < len(self.getPosts()):
            messageRaw = self.getPosts()[i]

            theTitle = messageRaw[0]
            theLink = messageRaw[1]

            theLinks = None
            content = messageRaw[4]
            theContent = None
            firstLink = theLink
            theImage = messageRaw[3]
            theSummary = content

            theSummaryLinks = content
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def getPostTitle(self, post):
        title = ''
        if post:
            title = post[0]
        return(title)

    def getPostLink(self, post):
        if post:
            link = post[1]
            return (link)
        return(None)

    def editApiLink(self, post, newLink=''):
        oldLink = self.getPostLink(post)
        idPost = self.getLinkPosition(oldLink)
        post = post[:1] + ( newLink, ) + post[2:]
        posts = self.getPosts()
        posts[idPost] = post
        self.assignPosts(posts)
        self.updatePostsCache()
        return(idPost)

    def editApiTitle(self, post, newTitle=''):
        logging.info(f"ApiTitle: {newTitle}. Post: {post}")
        oldLink = self.getPostLink(post)
        idPost = self.getLinkPosition(oldLink)
        oldTitle = self.getPostTitle(post)
        if not newTitle:
            newTitle = self.reorderTitle(oldTitle)
        post = (newTitle,) + post[1:]
        posts = self.getPosts()
        posts[idPost] = post
        self.assignPosts(posts)
        self.updatePostsCache()
        return(idPost)

    def insert(self, j, text):
        logging.info("Inserting %s", text)
        posts = self.getPosts()
        # We do not use j, Maybe in the future.
        logging.info(f"posts {posts}")
        if (j>=0) and (j<len(posts)):
            textS = text.split(' http')
            post = (textS[0], 'http'+textS[1], '','','','','','','','')
            self.assignPosts(posts[:j] + [ post ] + posts[j:])
            self.updatePostsCache()

    def publish(self, j):
        logging.info(">>>Publishing %d"% j)
        post = self.obtainPostData(j)
        logging.info(">>>Publishing {post[0]} in {self.service} user {self.nick}")
        api = getApi(self.service, self.nick)
        comment = ''
        title = post[0]
        link = post[1]
        comment = ''
        update = api.publishPost(title, link, comment)
        logging.info("Publishing title: %s" % title)
        logging.info("Social network: %s Nick: %s" % (self.service, self.nick))
        posts = self.getPosts()
        if (not isinstance(update, str) 
                or (isinstance(update, str) and update[:4] != "Fail")):
            self.assignPosts(posts[:j] + posts[j+1:])
            logging.debug("Updating %s" % posts)
            self.updatePostsCache()
            logging.debug("Update ... %s" % str(update))
            if ((isinstance(update, str) and ('text' in update))
                    or (isinstance(update, bytes) and (b'text' in update))):
                update = update['text']
            if type(update) == tuple:
                update = update[1]['id']
                # link: https://www.facebook.com/[name]/posts/[second part of id]
        logging.info("Update before return %s"% update)
        return(update) 

    def delete(self, j):
        # Not sure
        return self.deleteApi(j)

    def deleteApi(self, j):
        logging.info(f"Deleting: {j}")
        post = self.obtainPostData(j)
        posts = self.getPosts()
        posts = posts[:j] + posts[j+1:]
        self.assignPosts(posts)
        self.updatePostsCache()

        return("%s"% post[0])

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()

        if not posts:
            return None
        post = posts[i]
        return post

    def move(self, j, dest):
        k = int(dest)
        logging.info("Moving %d to %d"% (j, k))
        posts = self.getPosts()
        post = posts[j]
        logging.info("Moving %s"% post[0])
        if j > k:
            for i in range(j-1,k-1,-1):
                posts[i+1] = posts[i]
        elif j < k:
            for i in range(j, k):
                posts[i] = posts[i+1]

        posts[k] = post
        self.assignPosts(posts)
        self.updatePostsCache()
        logging.info("Moved %s"% post[0])
        return("%s"% post[0])
 
def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleCache

    queues = []
    for fN in os.listdir(f"{DATADIR}"):
        if fN.find('queue')>=0:
            queues.append(fN)

    for i, fN in enumerate(queues):
        print(f"{i}) {fN}")

    sel = input('Select one ')

    fN = queues[int(sel)]
    url, sN, nick = fN.split('_')
    nick = nick[:-len('.queue')]

    print(f"url: {url} social network: {sN} nick: {nick}")
    fNP = f"{DATADIR}/{fN}"
    import time
    fileT = time.strftime("%Y-%m-%d %H:%M:%S", 
            time.localtime(os.path.getmtime(fNP)))
    print(f"File name: {fNP} Date: {fileT}")

    action = input(f"Actions: (D)elete, (S)how (T)itles ")



    if action.upper()in ['S','T']: 
        url = f"https://{url}/"

        site = moduleCache.moduleCache()
        site.setClient((url, (sN, nick)))
        site.setPosts()
        if action.upper() == 'T': 
            [ print(f"- {post[0]}") for post in site.getPosts() ]
        else: 
            print(site.getPosts())
    elif action.upper() in ['D']:
        fileDelete = f"{fNP}"
        ok = input(f"I'll delete {fileDelete} ")
        os.remove(fileDelete)


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
        print(cache.selectAndExecute('insert', 'A2 Do You Really Have a Right to be “Forgotten”? - Assorted Stuff https://www.assortedstuff.com/do-you-really-have-a-right-to-be-forgotten/'))
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
    # It has 10 elements
    print(cache.obtainPostData(0))
    print(cache.selectAndExecute('show', 'T0'))
    print(cache.selectAndExecute('show', 'M0'))
    print(cache.selectAndExecute('show', 'F1'))
    print(cache.selectAndExecute('show', '*2'))
    print(cache.selectAndExecute('show', 'TM3'))
    print(cache.selectAndExecute('show', 'TM6'))
    print(cache.selectAndExecute('move', 'T5 0'))
    #print(cache.selectAndExecute('editl', 'T1 https://www.pagetable.com/?p=1152'))
    #print(cache.selectAndExecute('delete', 'F7'))
    #print(cache.selectAndExecute('edit', 'T3'))
    #print(cache.selectAndExecute('edit', 'T0'))
    #print(cache.selectAndExecute('publish', 'T1'))
    sys.exit()

    blog.cache.setPosts()
    print('T0', blog.cache.selectAndExecute('show', 'T0'))
    print('T3', blog.cache.selectAndExecute('show', 'T3'))
    print('TF2', blog.cache.selectAndExecute('show', 'TF2'))
    print('F4', blog.cache.selectAndExecute('show', 'F4'))
    print('*3', blog.cache.selectAndExecute('show', '*3'))
    #print('F0', blog.cache.selectAndExecute('delete', 'F0'))
    #print('edit F0', blog.cache.selectAndExecute('edit', 'F0'+' '+'LLVM 8.0.0 Release.'))
    #print('edit F0', blog.cache.editPost('F0', 'Así es Guestboard, un "Slack" para la organización de eventos.'))
    #print('publish T0', blog.cache.publishPost('T0'))
    #ca.movePost('T4 T3')
    #ca.editPost('T4', "My Stepdad's Huge Dataset.") 
    #ca.editPost('F5', "¡Sumate al datatón y a WiDS 2019! - lanacion.com")
    sys.exit()
    print(ca.editPost('F1', 'Alternative Names for the Tampon Tax - The Belladonna Comedy'))
    sys.exit()
    print(cache.editPost(postsP, 'F1', '10 Tricks to Appear Smart During Meetings – The Cooper Review – Medium...'))
    sys.exit()

    publishPost(api, profiles, ('F',1))

    posts.update(postsP)
    print("-> Posts",posts)
    #print("Posts",profiles)
    print("Keys",posts.keys())
    print("Pending",type(profiles))
    profiles = listSentPosts(api, "")
    print("Sent",type(profiles))


    if profiles:
       toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
       #publishPost(api, profiles, toPublish)


if __name__ == '__main__':
    main()
