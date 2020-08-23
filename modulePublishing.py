# This module provides infrastructure for publishing content in different
# places It stores in a convenient and consistent way the content in order to
# be used in other programs

import configparser
import os
import logging

from configMod import *

class Publisher:

    def __init__(self):
        self.content = None

        
    #def isForMe(self, args):
    #    serviceName =  self.content.socialNetwork[0].capitalize()
    #    if (serviceName[0] in args) or ('*' in args): 
    #       return True
    #    return False
    
    def showPost(self, args):
        logging.info("To show %s" % args)
    
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1] #self.name.capitalize()
            logging.debug(self.postsFormatted)
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            if title:
                return(title+' '+link)
            else:
                return("")
        return("")
    
    def publishPost(self, args):
        #return(self.interpretAndExecute(args,'publish'))
        logging.info("To publish %s" % args)
    
        udpate = None
        if self.isForMe(args):
            j = int(args[-1])
            service = self.content.socialNetwork[0]
            nick = self.content.socialNetwork[1]
            serviceName = 'Cache_'+service+'_'+nick
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.content.getPostsFormatted[serviceName]['pending'][j])
            publishMethod = getattr(moduleSocial, 
                    'publish'+ self.socialNetwork[0].capitalize())
            logging.info("Publishing title: %s" % title)
            logging.info("Social network: %s Nick: %s" % (serviceName, nick))
            update = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
            if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
                self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
                logging.debug("Updating %s" % self.postsFormatted)
                #logging.info("Blog %s" % cache['blog'])
                self.updatePostsCache()
                logging.info("UUpdate ... %s" % str(update))
                if 'text' in update:
                    update = update['text']
                if type(update) == tuple:
                    update = update[1]['id']
                    # link: https://www.facebook.com/[name]/posts/[second part of id]
            logging.info("Update before return", update)
    
            return(update)
        return ""
    
    def deletePost(self, args):
        #return(self.interpretAndExecute(args,'delete'))
        logging.info("To Delete %s" % args)
    
        udpate = ""
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1] #self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            update = "Deleted: "+ title
            logging.debug("Posts %s" % self.postsFormatted[serviceName]['pending'])
            self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
            logging.debug("-Posts %s" % self.postsFormatted[serviceName]['pending'])
            logging.info("social network %s - %s" 
                    % (self.socialNetwork[0], self.socialNetwork[1]))
            self.updatePostsCache()
            return(update)
    
        return("")
    
    def editPost(self, args, newTitle):
        #return(self.interpretAndExecute(args,'edit', newTitle))
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)
    
        udpate = None
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1] #self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            self.postsFormatted[serviceName]['pending'][j] = (newTitle, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
            self.updatePostsCache()
            update = "Changed "+title+" with "+newTitle
        else:
            update = ""

        return(update)
    
   
    
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
    

