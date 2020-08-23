#!/usr/bin/env python
# encoding: utf-8

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
#sys.setdefaultencoding("UTF-8")
from crontab import CronTab

from configMod import *
from moduleQueue import *
from moduleContent import *

class moduleCache(Content,Queue):
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.nick = None
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def setClient(self, param):
        url = param[0]
        socialNetwork = param[1]
        self.url = url
        self.service = socialNetwork[0]
        self.nick = socialNetwork[1]

    def getSocialNetwork(self):
        return (self.service, self.nick)

    def getService(self):
        return(self.service)

    def setPosts(self):        
        logging.debug("Service %s Nick %s" % (self.service, self.nick))
        fileNameQ = fileNamePath(self.url, 
                (self.service, self.nick)) + ".queue"
        logging.debug("File %s" % fileNameQ)
        try:
            with open(fileNameQ,'rb') as f: 
                try: 
                    listP = pickle.load(f) 
                except: 
                    listP = [] 
        except:
            listP = []

        self.posts = listP

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
            self.posts = self.posts + listPosts
            self.updatePostsCache()
            link = listPosts[len(listPosts) - 1][1]
        return(link)

    def updatePostsCache(self):
        fileNameQ = fileNamePath(self.url, (self.service, self.nick)) + ".queue"

        with open(fileNameQ, 'wb') as f:
            pickle.dump(self.posts, f)
        logging.debug("Writing in %s" % fileNameQ)

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

    def getTitle(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            title = post[0]
            return (title)
        return(None)

    def getLink(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            link = post[1]
            return (link)
        return(None) 
    
    def getPostTitle(self, post):
        if post:
            title = post[0]
            return (title)
        return(None)

    def getPostLink(self, post):
        if post:
            link = post[1]
            return (link)
        return(None)

    #def isForMe(self, args):
    #    logging.info("isForMe %s" % str(self.service))
    #    return ((self.service[0].capitalize() in args.split()[0])
    #           or (args[0] == '*'))

    def editl(self, j, newLink=''):
        logging.info("New link %s", newLink)
        thePost = self.obtainPostData(j)
        oldLink = thePost[1]
        thePost = thePost[:1] + ( newLink, ) + thePost[2:]
        print(thePost)
        self.posts[j] = thePost
        logging.info("Service Name %s" % self.name)
        self.updatePostsCache()
        update = "Changed "+oldLink+" with "+newLink
        return(update)

    def edit(self, j, newTitle=''):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        if not newTitle:
            newTitle = self.reorderTitle(oldTitle)
        thePost = thePost[1:]
        thePost = (newTitle,) + thePost
        self.posts[j] = thePost
        logging.info("Service Name %s" % self.name)
        self.updatePostsCache()
        update = "Changed "+oldTitle+" with "+newTitle
        return(update)

    def insert(self, j, text):
        logging.info("Inserting %s", text)
        print(j)
        print(text)
        # We do not use j, Maybe in the future.
        textS = text.split(' http')
        post = (textS[0], 'http'+textS[1], '','','','','','','','')
        self.posts.append(post)
        self.updatePostsCache()

    def publish(self, j):
        logging.info("Publishing %d"% j)
        post = self.obtainPostData(j)
        logging.info("Publishing %s"% post[0])
        import importlib
        serviceName = self.service.capitalize()
        mod = importlib.import_module('module' + serviceName) 
        cls = getattr(mod, 'module' + serviceName)
        api = cls()
        api.setClient(self.nick)
        comment = ''
        title = post[0]
        link = post[1]
        comment = ''
        update = api.publishPost(title, link, comment)
        logging.info("Publishing title: %s" % title)
        logging.info("Social network: %s Nick: %s" % (self.service, self.nick))
        if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
            self.posts = self.posts[:j] + self.posts[j+1:]
            logging.debug("Updating %s" % self.posts)
            self.updatePostsCache()
            logging.info("Update ... %s" % str(update))
            if 'text' in update:
                update = update['text']
            if type(update) == tuple:
                update = update[1]['id']
                # link: https://www.facebook.com/[name]/posts/[second part of id]
        logging.info("Update before return %s"% update)
        return(update)
    
    def delete(self, j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        logging.info("Deleted %s"% post[0])
        return("%s"% post[0])

    def move(self, j, dest):
        k = int(dest)
        logging.info("Moving %d to %d"% (j, k))
        post = self.posts[j]
        if j > k:
            logging.info("Moving %s"% post[0])
            for i in range(j-1,k-1,-1):
                self.posts[i+1] = self.posts[i]
            self.posts[k] = post

            self.updatePostsCache()
            logging.info("Moved %s"% post[0])
        return("%s"% post[0])
 
def main():
    import moduleCache
    import moduleSlack

    cache = moduleCache.moduleCache()
    cache.setClient(('http://fernand0-errbot.slack.com/', 
            ('twitter', 'fernand0')))
    cache.setPosts()
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
