#!/usr/bin/env python

# This module is used as a infrastructure for publishing in several social
# networks using their APIs via different available python modules. 
#
# It uses several configuration files to store credentials such as:
# 
# .rssBlogs
# It can contain as many blogs as desired, with different parameters for each
# one (a blog can have, for example a twtter account, but not Telegram account
# and  so on).  
# The structure for one of these blogs is
# [Blog]
#     url:
#     rssFeed:
#     xmlrpc:
#     twitterAC:
#     pageFB:
#     telegramAC:
#     mediumAC:
#     linksToAvoid:
#      
# .rssTwitter 
# We can store the configuration of the app (CONSUMER_KEY and CONSUMER_SECRET)
# and the configuration for each Twitter account. For just only one Twitter
# account it could be:
# [appKeys]
#CONSUMER_KEY:
#CONSUMER_SECRET:
#[user1]
#TOKEN_KEY:
#TOKEN_SECRET:
# 
# There can be more lines for more Twitter accounts
# We can store the configuration for publishing in a Facebook page.
# 
#
# .rssFacebook
# We can store the configuration of the user. The user has to have permission
# for publishing in the page that will be selected by the program using the
# module. It has been tested with just one user account and several pages. If
# you need more than one user account some changes could be needed.
#[Facebook]
#oauth_access_token:
#
# .rssLinkedin
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
# Parameters.
#[Linkedin]
#CONSUMER_KEY:
#CONSUMER_SECRET:
#USER_TOKEN:
#USER_SECRET:
#RETURN_URL:http://localhost:8080/code
# .rssTelegram
# We can store the configuration of the bot. If you need more than one user
# account some changes could be needed.
#[Telegram]
#TOKEN:
#
# .rssMedium
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
#[appKeys]
#ClientID:
#ClientSecret:
#access_token:
#
# .rssBuffer
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
#[appKeys]
#client_id:
#client_secret:
#redirect_uri:urn:ietf:wg:oauth:2.0:oob
#access_token:
#

import logging
import random
import sys
import time
import pickle

from configMod import *

logger = logging.getLogger(__name__)

def listNextPosts(blog, socialNetwork):
    listP = ""
    if blog.getProgram():
        if socialNetwork in blog.cache:
            blog.cache[socialNetwork].setPosts()
            listP = blog.cache[socialNetwork].getPosts()
    else:
        listP = blog.getNextPosts(socialNetwork)
        logging.debug("listP {}".format(listP))
    return listP

def nextPost(blog, socialNetwork, listP):
    if listP: 
        element = listP[0]
        listP = listP[1:] 
    elif type(listP) == type(()):
        element = listP
        listP = [] 
    else:
        element = None
        logger.info("Empty list")

    return(element,listP)


def publishDelay(blog, socialNetwork, numPosts, nowait, timeSlots): 
    # We allow the rest of the Blogs to start

    result = ''

    profile = socialNetwork[0]
    nick = socialNetwork[1]

    listP = listNextPosts(blog, socialNetwork)

    # element, listP = nextPost(blog, socialNetwork)
    # We need to separate nextPost from getting the list of 'cached' posts
    if not listP:
        listP = []

    #numPosts = min(numPosts, len(listP)+1)
    #print(numPosts)
    llink = None
    tSleep = random.random()*timeSlots
    tSleep2 = timeSlots - tSleep
    
    listP = listNextPosts(blog, socialNetwork)
    element, listP = nextPost(blog, socialNetwork, listP)

    if element:
        tNow = time.time()

        lastTime = getNextTime(blog, socialNetwork)
        lastTime = float(lastTime[0])

        hours = float(blog.getTime())*60*60
        diffTime = time.time() - lastTime #- round(float(hours)*60*60)

        if (nowait or diffTime > hours):
            msgLog = " {} -> {} ({}): waiting... {:.2f} minutes".format(
                    urllib.parse.urlparse(blog.getUrl()).netloc.split('.')[0], 
                    profile, nick , tSleep/60) 
            fileNameNext = setNextTime(blog, socialNetwork, tNow, tSleep)
            logMsg(msgLog, 1, 1)

            logger.debug("     I'll publish %s" % element[0])
            time.sleep(tSleep) 

            # Things can have changed during the waiting
            listP = listNextPosts(blog, socialNetwork)
            element, listP = nextPost(blog,socialNetwork, listP)

            if element:
                (title, link, firstLink, image, summary, summaryHtml, 
                        summaryLinks, content, links, comment) = element

                msgLog = " Publishing in: {} ({}) at {}".format(
                        profile.capitalize(), nick, time.asctime())
                logMsg(msgLog, 1, 1)

                result = None

                # Destination
                if profile in ['twitter', 'facebook', 'mastodon', 
                        'imgur', 'wordpress','linkedin', 'tumblr',
                        'pocket', 'medium','telegram','kindle']: 
                    if profile in ['telegram', 'facebook']: 
                        comment = summaryLinks 
                    if profile in ['facebook']: 
                        pos1 = 0
                        while pos1>=0:
                            pos1 = comment.find(
                                    'http://fernand0.blogalia',pos1) 
                            if pos1 >=0: 
                                pos2 = comment.find(' ',pos1+1) 
                                pos3 = comment.find('\n',pos1+1) 
                                pos2 = min(pos2, pos3) 
                                logging.info(comment) 
                                comment = "\n{}(Enlace censurado por Facebook){}".format( comment[:pos1-1], comment[pos2:]) 
                                logging.debug(comment) 
                                pos1=pos2
                    elif profile == 'medium': 
                        comment = summaryHtml 
                    elif profile == 'pocket': 
                        if firstLink: 
                            link, llink = firstLink, link
                        idPost = element[-1]
                    elif profile == 'kindle': 
                        myLink = links[0]
                        idPost = element[-1]
                        llink = idPost
                        profile = 'html'

                try: 
                    api = getApi(profile, nick) 
                    if profile in ['wordpress']: 
                        result = api.publishPost(title, link, 
                                comment, tags=links)
                    elif profile in ['html']: 
                        result = api.click(myLink)
                    else: 
                        result = api.publishPost(title, link, comment)
                except:
                    logging.warning("Some problem in {}".format(
                        profile.capitalize())) 
                    logging.warning("Unexpected error:", sys.exc_info()[0]) 

                logging.info("Result: {}".format(str(result)))
                #sys.exit()
                if  isinstance(result, int):
                    result = str(result)
                if isinstance(result, str):
                    if ((result[:4]=='Fail') or
                            (result[:21] == 'Wordpress API expired')):
                        print(" Not published: {} ({}) - Res: {}".format(
                            profile.capitalize(), nick, result))
                        link = ''
                        result = 'Fail!'
                    else: 
                        print(" Published in: {} ({}):\n  Res: {}".format( 
                            profile.capitalize(), nick, result))
                        result = 'OK'
                else:
                    result = 'OK'
 
                if result == 'OK':
                    if blog.getPostAction(): 
                        logging.info("Postaction: {}".format(str(idPost)))
                        print("del",blog.deletePostId(idPost))
                    with open(fileNameNext,'wb') as f:
                        pickle.dump((tNow,tSleep), f)
                    if hasattr(blog, 'cache') and blog.cache:
                        blog.cache[socialNetwork].posts = listP
                        blog.cache[socialNetwork].updatePostsCache()
                    elif hasattr(blog, 'nextPosts'): 
                        blog.nextPosts[socialNetwork] = listP
                        blog.updatePostsCache(socialNetwork)
                    else:
                        print("What happened?")

                msgLog = " Finished in: {} ({}) at {}".format(
                        profile.capitalize(), nick, time.asctime())
                logMsg(msgLog, 1, 1)
            else: 
                result == ''
    else: 
        logging.info("There are no new posts in {}".format(blog.getUrl()))

    if result == 'OK':
        if llink:
            link = llink
    else:
        link = ''

    return link
   
def cleanTags(soup):
    tags = [tag.name for tag in soup.find_all()]
    validtags = ['b', 'strong', 'i', 'em', 'a', 'code', 'pre']

    quotes = soup.find_all('blockquote')
    for quote in quotes:
        quote.insert_before('«')
        quote.insert_after( '»')

    for tag in tags:
        if tag not in validtags:
            for theTag in soup.find_all(tag):
                theTag.unwrap()
        elif (tag == 'strong') or (tag == 'b'):
            # We want to avoid problems with links nested inside these tags.
            for theTag in soup.find_all(tag):
                if theTag.find('a'):
                    theTag.unwrap()

    code = [td.find('code') for td in soup.findAll('pre')]
    # github.io inserts code tags inside pre tags
    for cod in code:
        cod.unwrap()

    tags = soup.findAll(text=lambda text:isinstance(text, Doctype))
    if (len(tags)>0):
        tags[0].extract()
    # <!DOCTYPE html> in github.io


if __name__ == "__main__":

    import moduleSocial
    import moduleRss

    blog = moduleRss.moduleRss()
    url = 'http://fernand0.tumblr.com/'
    rssFeed= 'rss'
    blog.setUrl(url)
    blog.setRssFeed(rssFeed)
    blog.addSocialNetwork(('facebook', 'Fernand0Test'))        
    #blog.addSocialNetwork(('telegram', 'Fernand0Test'))        
    blog.addSocialNetwork(('twitter', 'fernand0Test'))        
    blog.setPostsRss()
    blog.getPostsRss()
    lastLink, lastTime = checkLastLink(blog.url,('twitter', 'fernand0Test'))
    i = blog.getLinkPosition(lastLink) 
    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (blog.obtainPostData(i - 1))
    fbPage = blog.getSocialNetworks()['facebook']
    #telegram = blog.getSocialNetworks()['telegram']
    #medium = blog.getSocialNetworks()['medium']
    num = 4
    listPosts= []
    for j in range(num, 0, -1):
        if (i == 0):
            break
        i = i - 1
        listPosts.append(blog.obtainPostData(i - 1))
        timeSlots = 60*60
    if listPosts:
        moduleSocial.publishDelayTwitter(blog, listPosts ,'fernand0Test', timeSlots)

