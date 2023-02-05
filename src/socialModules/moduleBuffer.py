#!/usr/bin/env python
# encoding: utf-8

#
# - This module comes from https://github.com/fernand0/err-buffer.git
#
# - The second one includes the secret data of the buffer app [~/.rssBuffer]
# [appKeys]
# client_id:XXXXXXXXXXXXXXXXXXXXXXXX
# client_secret:XXXXXXXXXXXXXXXXXXXXXXXXXXXxXXXX
# redirect_uri:XXXXXXXXXXXXXXXXXXXXXXXXX
# access_token:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# 
# These data can be obtained registering an app in the bufferapp site.
# Follow instructions at:
# https://bufferapp.com/developers/api
# 
# - The third one contains the last published URL [~/.rssBuffer.last]
# It contains just an URL which is the last one published. 
# At this moment it only considers one blog
# 
# We are adding now the ability to read a local queue. It is stored in the
# following way:
#
# Queue files name is composed of a dot, followed by the path of the URL,
# followed by the name of the social network and the name of the user for
# posting there.
# The filename ends in .queue
# For example:
#    .my.blog.com_twitter_myUser.queue
# This file stores a list of pending posts stored as an array of posts as
# returned by moduleBlog
# (https://github.com/fernand0/scripts/blob/master/moduleBlog.py)
#  obtainPostData method.
# For the moment, it will read the filenames from
#  .rssProgram
# One file at each line


import configparser
import importlib
import logging
import os
import sys
import time
import urllib

importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")

import buffpy
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Updates
from buffpy.models import Update
# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from colorama import Fore

from configMod import *
from moduleContent import *
# from moduleQueue import *

# We can put as many items as the service with most items allow
# The limit is ten.
# Get all pending updates of a social network profile

#[{'_Profile__schedules': None, u'formatted_service': u'Twitter', u'cover_photo': u'https://pbs.twimg.com/profile_banners/62983/1355263933', u'verb': u'tweet', u'formatted_username': u'@fernand0', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 10862, u'drafts': 0}, u'service_username': u'fernand0', u'id': u'4ed35f97512f7ebb5d00000b', u'disconnected': False, u'statistics': {u'followers': 5736}, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://pbs.twimg.com/profile_images/487165212391256066/DFRGycds_normal.jpeg', u'service': u'twitter', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'09:10', u'09:45', u'10:09', u'10:34', u'11:10', u'11:45', u'12:07', u'13:29', u'15:15', u'16:07', u'16:42', u'17:07', u'17:40', u'18:10', u'18:33', u'19:05', u'19:22', u'20:15', u'21:30', u'22:45', u'23:10', u'23:25', u'23:45']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'http://pbs.twimg.com/profile_images/487165212391256066/DFRGycds_normal.jpeg', u'service_type': u'profile', u'service_id': u'62983', u'_id': u'4ed35f97512f7ebb5d00000b', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'LinkedIn', u'cover_photo': u'https://d3ijcis4e2ziok.cloudfront.net/default-cover-photos/blurry-blue-background-iii_facebook_timeline_cover.jpg', u'verb': u'post', u'timezone_city': u'Madrid - Spain', u'formatted_username': u'Fernando Tricas', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 4827, u'drafts': 0}, u'service_username': u'Fernando Tricas', u'id': u'4f4606ec512f7e0766000003', u'disconnected': False, u'statistics': {u'connections': 500}, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://media.licdn.com/mpr/mprx/0_zVbmG3KX1MsA8cT9vyLgGCt5Ay0Aucl9BjPAGC1ZaMIhPPQnMpBCuGbn0-xffrKVqJ5KDLD_G-D1', u'service': u'linkedin', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'01:46', u'05:52', u'07:13', u'08:54', u'09:27', u'10:13', u'10:49', u'11:58', u'12:03', u'12:03', u'12:41', u'13:05', u'15:23', u'16:35', u'16:57', u'17:23', u'18:02', u'18:37', u'19:58', u'20:17', u'21:13', u'22:00', u'23:05', u'23:07', u'23:49']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://media.licdn.com/mpr/mprx/0_zVbmG3KX1MsA8cT9vyLgGCt5Ay0Aucl9BjPAGC1ZaMIhPPQnMpBCuGbn0-xffrKVqJ5KDLD_G-D1', u'service_type': u'profile', u'service_id': u'x4Eu0cqIhj', u'_id': u'4f4606ec512f7e0766000003', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'Facebook', u'cover_photo': u'https://scontent.xx.fbcdn.net/hphotos-xfp1/t31.0-8/s720x720/904264_10151421662663264_1461180243_o.jpg', u'verb': u'post', u'timezone_city': u'Zaragoza - Spain', u'formatted_username': u'Fernando Tricas', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'pending': 0, u'sent': 5971, u'drafts': 0}, u'service_username': u'Fernando Tricas', u'id': u'5241b3f0351ff0a83500001b', u'disconnected': False, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://scontent.xx.fbcdn.net/hprofile-xpf1/v/t1.0-1/c0.0.50.50/p50x50/10500300_10152337396498264_6509296623992251600_n.jpg?oh=1870d57d20aa70388bed86f1383051f2&oe=578BF216', u'service': u'facebook', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'00:58', u'07:53', u'09:06', u'09:44', u'10:03', u'10:30', u'11:07', u'11:37', u'12:16', u'13:04', u'13:40', u'16:02', u'16:32', u'16:51', u'17:18', u'17:38', u'18:03', u'18:44', u'19:14', u'23:02', u'23:41']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://scontent.xx.fbcdn.net/hprofile-xpf1/v/t1.0-1/c0.0.50.50/p50x50/10500300_10152337396498264_6509296623992251600_n.jpg?oh=1870d57d20aa70388bed86f1383051f2&oe=578BF216', u'service_type': u'profile', u'service_id': u'503403263', u'_id': u'5241b3f0351ff0a83500001b', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'Google+ Page', u'cover_photo': u'https://d3ijcis4e2ziok.cloudfront.net/default-cover-photos/blurry-blue-background-iii_facebook_timeline_cover.jpg', u'verb': u'post', u'formatted_username': u'Reflexiones e Irreflexiones', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/London', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 0, u'drafts': 0}, u'service_username': u'Reflexiones e Irreflexiones', u'id': u'521f6df14ddfcbc91600004a', u'disconnected': False, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://lh6.googleusercontent.com/-yAIEsEEQ220/AAAAAAAAAAI/AAAAAAAAAC8/Q8K1Li_kZSY/photo.jpg?sz=50', u'service': u'google', u'default': False, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'10:50', u'17:48']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://lh6.googleusercontent.com/-yAIEsEEQ220/AAAAAAAAAAI/AAAAAAAAAC8/Q8K1Li_kZSY/photo.jpg?sz=50', u'service_type': u'page', u'service_id': u'117187804556943229940', u'_id': u'521f6df14ddfcbc91600004a', u'utm_tracking': u'enabled', u'disabled_features': []}]


class moduleBuffer(Content,Queue):

    def __init__(self): #, url, socialNetwork, nick):
        super().__init__()
        self.service = None
        self.nick = None
        #self.buffer = None
        self.profiles = None
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def setClient(self, url, socialNetwork = None):
        if not socialNetwork:
            socialNetwork = url[1]
            url = url[0]
            logging.info("url %s" % url)
            logging.info("sN %s" % str(socialNetwork))
        config = configparser.ConfigParser()
        logging.debug("Config...%s" % CONFIGDIR)
        config.read(CONFIGDIR + '/.rssBuffer')
    
        clientId = config.get("appKeys", "client_id")
        clientSecret = config.get("appKeys", "client_secret")
        redirectUrl = config.get("appKeys", "redirect_uri")
        accessToken = config.get("appKeys", "access_token")
        
        # instantiate the api object 
        api = buffpy.api.API(client_id=clientId,
                  client_secret=clientSecret,
                  access_token=accessToken)
    
        self.client = api

        self.url = url
        self.service = socialNetwork[0]
        self.nick = socialNetwork[1]

    def setProfile(self, service=""):
        logging.info("  Checking services...")

        self.profile = None
        
        if (service == ""):
            logging.info("  All available in Buffer")
            try: 
                profiles = Profiles(api=self.client).all()
                self.profile = profiles[0]
            except:
                logging.info("   Something went wrong")
        else:
            logging.info("  Profile %s" % service)
            try: 
                profiles = Profiles(api=self.client).filter(service=service)
                self.profile = profiles[0]
            except:
                logging.info("   Something went wrong")

    def getProfile(self):
        return(self.profile)

    def setPosts(self):
        self.setProfile(self.service)
        profile = self.getProfile()
        logging.debug("Profile %s" % profile)
    
        for method in ['sent', 'pending']:
            if (profile 
                    and ('counts' in profile) 
                    and (profile.counts[method] > 0)):
                profile.id = profile['id']
                profile.profile_id = profile['service_id']
                updates = getattr(profile.updates, method)
                logging.debug("sent Profile %s" % updates)
                if method == 'pending': 
                    self.posts = updates
                else:
                    self.posted = updates

    def getHoursSchedules(self, command=None):
        return self.schedules[0]['times']

    def getSchedules(self, command=None):
        return self.schedules

    def setSchedules(self, command=None):
        """
        [{'days': ['sun'], 'times': ['09:27', '10:40', '11:50', '12:57', '16:11', '17:06', '18:37', '19:13']}, {'days': ['mon'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}, {'days': ['tue'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}, {'days': ['wed'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}, {'days': ['thu'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}, {'days': ['fri'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}, {'days': ['sat'], 'times': ['09:27', '10:40', '11:50', '12:17', '16:11', '17:06', '18:37', '19:13']}]
        """
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
    
    def isValidTime(self, time): 
        result = False
        if len(time) <= 5: 
            if time.find(':'): 
                for num in time.split(':'): 
                    if not num.isdigit():
                        result = False
                result =  True
        return result

    def addSchedules(self, times):
        toPost={'days':[], 'times':[]}
        myTimes = self.schedules[0]['times']
        logging.debug(myTimes)
        for time in times:
            if self.isValidTime(time): 
                if time not in myTimes: 
                    myTimes.append(time)
        myTimes.sort()

        for i, sched in enumerate(self.schedules): 
            if i == 7: break
            print(sched)
            toPost['days'].append(sched['days'][0])
        toPost['times'] = myTimes
        self.getProfile().schedules = toPost

    def delSchedules(self, times):
        toPost={'days':[], 'times':[]}
        myTimes = self.schedules[0]['times']
        for time in myTimes:
            if time not in times:
                toPost['times'].append(time)
        myTimes.sort()

        for i, sched in enumerate(self.schedules): 
            if i == 7: break
            print(sched)
            toPost['days'].append(sched['days'][0])
        self.getProfile().schedules = toPost

    def addPosts(self, listPosts):
        linkAdded = ''
        link=''
        logging.info("    Adding posts to %s" % self.service)
        for i, post in enumerate(listPosts): 
            title = self.getPostTitle(post)
            link = self.getPostLink(post)
            if self.service == 'instagram':
                img = self.getPostImg(post)
                #Crop the image and leave it on some server
                imgN = resizeImage(img)
                img = imgN
                print(img)
            else:
                img = ''
            textPost = title + " " + link
            logging.info("    Post: %s" % textPost)
            entry = textPost #urllib.parse.quote(textPost)
            try:
                if img: 
                    myMedia = {'photo':img}#,'description':title}
                    self.getProfile().updates.new(entry, shorten=False, media=myMedia)
                else:
                    myMedia = {'link':link}#,'description':title}
                    entry = title
                    self.getProfile().updates.new(entry, media=myMedia)
            except: 
                print("Buffer posting failed!") 
                logging.warning("Buffer posting failed!") 
                logging.warning("Unexpected error: %s"% sys.exc_info()[0]) 
                logging.warning("Unexpected error: %s"% sys.exc_info()[1]) 
                link = ''
                continue
            linkAdded = link
                
            time.sleep(2)
        logging.info("    Added posts to LinkedIn")

        return(linkAdded)

    # def extractDataMessage(self, i):
    #     logging.info("Service %s"% self.service)
    #     messageRaw = self.getPosts()[i]

    #     theTitle = messageRaw['text']
    #     theLink = ''
    #     content = ''
    #     if 'media' in messageRaw:
    #         if ('expanded_link' in messageRaw['media']):
    #             theLink = messageRaw['media']['expanded_link']
    #         elif 'link' in messageRaw['media']:
    #             theLink = messageRaw['media']['link']
    #         else:
    #             theLink = ''
    #         if ('description' in messageRaw['media']): 
    #             content = messageRaw['media']['description']

    #     theLinks = None
    #     theContent = content
    #     firstLink = theLink
    #     theImage = None
    #     theSummary = content

    #     theSummaryLinks = content
    #     comment = None

    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def getTitle(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            title = post['text']
            return (title)
        return(None)

    def getLink(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            link = post['media']['expanded_link']
            return (link)
        return(None) 
    
    def getPostTitle(self, post):
        if post:
            if 'text' in post:
                title = post['text']
            elif 'media' in post:
                if 'title' in post['media']:
                     title = post['media']['title']
                else:
                     title = 'None'
            else:
                title = post[0]
            return (title)
        return(None)

    def getPostLink(self, post):
        if post:
            if 'media' in post: 
                logging.debug("media %s"%str(post['media']))
                if ('expanded_link' in post['media']): 
                    link = post['media']['expanded_link'] 
                elif 'link' in post['media']:
                    link = post['media']['link']
                else:
                    link = ''
            else:
                link = post[1]
            return (link)
        return(None)

    def getPostImg(self, post):
        img = post[3]
        if img.find('?')>0: img = img.split('?')[0]
        return(img)

    #def isForMe(self, args):
    #    profile = self.getProfile()
    #    logging.info("isForMe %s" % str(profile['service']))
    #    return (profile['service'][0].capitalize() in args) or ('*' in args) 

    def editl(self, j, newLink=''):
        logging.info("New link %s", newLink)
        thePost = self.obtainPostData(j)
        oldLink = thePost[1]
        profile = self.getProfile()
        logging.info("servicename %s" %self.service)
        from buffpy.models.update import Update
        i=0
        update = Update(api=self.client, id=profile.updates.pending[j]['id']) 
        title = thePost[0]
        # media = {'original': newLink } 
        #update = update.edit(media={})
        print(title)
        self.delete(j)
        #update = update.edit(text=title+' '+newLink, media={})
        textPost = title + " " + newLink
        entry = textPost #urllib.parse.quote(textPost)
        update = self.getProfile().updates.new(entry)
        print(update)
        #return('Updated!  %s' % update)

        title = oldTitle
        update = "Changed "+title+" with "+newTitle

        logging.info("Res update %s" % update)

        return('Updated!  %s' % update)

    def edit(self, j, newTitle=''):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        if not newTitle:
            newTitle = self.reorderTitle(oldTitle)
        profile = self.getProfile()
        logging.info("servicename %s" %self.service)
        from buffpy.models.update import Update
        i=0
        update = Update(api=self.client, id=profile.updates.pending[j]['id']) 
        print(update)
        import urllib.parse
        update = update.edit(text=urllib.parse.quote(newTitle))

        title = oldTitle
        update = "Changed "+title+" with "+newTitle

        logging.info("Res update %s" % update)

        return(update)

    # def publishh(self, j):
    #     logging.info("Publishing %d"% j)
    #     post = self.obtainPostData(j)
    #     logging.info("Publishing %s"% post[0])
    #     profile = self.getProfile() 
    #     update = Update(api=self.client, id=profile.updates.pending[j]['id']) 
    #     res = update.publish()
    #     logging.info("Update before return %s"% res)
    #     if res:
    #         if 'message' in res: 
    #             return(res['message'])
    #         else:
    #             return(res)
    #     else:
    #         return("Published!")
    
    def delete(self, j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        profile = self.getProfile()
        from buffpy.models.update import Update
        update = Update(api=self.client, id=profile.updates.pending[j]['id']) 
        update = update.delete()

        logging.info("Update before return %s"% update)
        return(update['message'])

    def move(self, j, dest):
        k = int(dest)
        logging.info("Moving %d to %d"% (j, k))
        listPostIds = []
        for post in self.getPosts():
            listPostIds.append(post['id'])
        idPost = listPostIds[j]
        if j > k:
            logging.info("Moving %s"% idPost)
            for i in range(j-1,k-1,-1):
                listPostIds[i+1] = listPostIds[i]
            listPostIds[k] = idPost
        profile = self.getProfile()

        res = profile.updates.reorder(listPostIds)

        return(res)

 
def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')
    import moduleBuffer
        
    buf = moduleBuffer.moduleBuffer()
    buf.setClient('http://fernand0-errbot.slack.com/', 
            ('linkedin', 'Fernando Tricas'))
    buf.setClient('http://avecesunafoto.wordpress.com/', 
            ('instagram', 'a-veces-una-foto'))
    buf.setPosts()
    print(buf.getPosts())

    print(buf.getPostTitle(buf.getPosts()[0]))
    print(buf.getPostLink(buf.getPosts()[0]))
    sys.exit()
    buf.setSchedules()
    buf.addSchedules(['12:34','19:31'])
    buf.setSchedules()
    print(buf.schedules)
    buf.delSchedules(['12:34','19:31'])
    print(buf.schedules)
    sys.exit()
    print(buf.getPosts())
    print(buf.getPosts()[0])
    print(len(buf.getPosts()[0]))
    print(buf.getTitle(0))
    print(buf.getLink(0))
    post = buf.getPosts()[0]
    print("post")
    print(post)
    print(buf.getPostTitle(post))
    print(buf.getPostLink(post))
    post = buf.obtainPostData(0)
    print("post")
    print(post)
    print(buf.getPostTitle(post))
    print(buf.getPostLink(post))
    # # It has 30 elements
    # print(buf.obtainPostData(0))

    # print('F1', buf.selectAndExecute('show', 'F1'))
    # print('L3', buf.selectAndExecute('show', 'L3'))
    # print('TL2', buf.selectAndExecute('show', 'TL2'))
    # print('*4', buf.selectAndExecute('show', '*4'))
    # print('L4', buf.selectAndExecute('move', 'L9 0'))
    # sys.exit()
    # print('L0', buf.selectAndExecute('publish', 'L0'))
    # #print('edit L3', buf.selectAndExecute('editl', 'L3 http://www.danilat.com/weblog/2019/06/10/kpis-equipos-desarrollo-software'))
    # #print('edit L2', buf.selectAndExecute('edit', 'L2'+' '+'El tren del tambor.'))
    # #print('pub L0', buf.selectAndExecute('publish','L0'))
    # print('delete linkedin', buf.selectAndExecute('delete', 'L1'))
    # print("-> PostsP",postsP)
    # posts.update(postsP)
    # print("-> Posts",posts)
    # #print("Posts",profiles)
    # print("Keys",posts.keys())
    # sys.exit()
    # posts = listPendingPosts("")
    # print(profiles)
    # print("Pending",type(profiles))
    # print(profiles)
    # profiles = listSentPosts("")
    # print("Sent",type(profiles))
    # print(profiles)
    # print(type(profiles[1]),profiles[1])


    # if profiles:
    #    toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
    #    #publishPost(api, pp, profiles, toPublish)


if __name__ == '__main__':
    main()
