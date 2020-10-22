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

def nextPost(blog, socialNetwork):
    #cacheName = 'Cache_'+socialNetwork[0]+'_'+socialNetwork[1]
    blog.cache[socialNetwork].setPosts()
    listP = blog.cache[socialNetwork].getPosts()

    if listP: 
        element = listP[0]
        listP = listP[1:] 
    elif type(listP) == type(()):
        element = listP
        listP = [] 
    else:
        logger.warning("This shouldn't happen")
        sys.exit()

    return(element,listP)

def publishDirect(blog, socialNetwork, i): 
    link = None
    if (i > 0): 
        profile = socialNetwork[0]
        nick = socialNetwork[1]
        (title, link, firstLink, image, summary, summaryHtml, 
                summaryLinks, content , links, comment) = (blog.obtainPostData(i - 1, False)) 
        logging.info("  Publishing directly\n") 
        serviceName = profile.capitalize() 
        print("   Publishing in %s %s" % (serviceName, title))
        if profile in ['telegram', 'facebook']:
            comment = summaryLinks
        elif profile == 'medium': 
            comment = summaryHtml
        else:
            comment = ''

        if (profile in ['twitter', 'facebook', 'telegram', 'mastodon', 
            'linkedin', 'pocket', 'medium', 'instagram']): 
            # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically 
            import importlib 
            mod = importlib.import_module('module'+serviceName) 
            cls = getattr(mod, 'module'+serviceName) 
            api = cls() 
            api.setClient(nick) 
            if profile in ['facebook']: 
                pos1= comment.find('http://fernand0.blogalia')
                if pos1 >=0:
                    pos2 = comment.find(' ',pos1+1)
                    pos3 = comment.find('\n',pos1+1)
                    pos2 = min(pos2, pos3)
                    logging.info(comment)
                    comment = "{}(Enlace censurado por Facebook){}".format(
                            comment[:pos1-1],
                            comment[pos2:])

                    logging.info(comment)
                else:
                    comment = None
                #url = link
                #apiurl = "http://tinyurl.com/api-create.php?url=" 
                #tinyurl = urllib.request.urlopen(apiurl + url).read() 
                #link = tinyurl.decode("utf-8")
            #print(link)
            result = api.publishPost(title, link, comment) 
            logging.debug(result) 
            if isinstance(result, str): 
                logging.info("Result %s"%str(result)) 
                if result[:4]=='Fail': 
                    logging.debug("Fail detected %s"%str(result)) 
                    if ((result.find('duplicate')>=0) or 
                            (result.find('abusive')>=0)): 
                        duplicate = True 
                        link='' 
                        logging.info("Posting failed") 
                elif result.find('Bad Request')>=0: 
                    link='' 
                    logging.info("Posting failed") 
    return link

def publishDelay(blog, socialNetwork, numPosts, timeSlots): 
    # We allow the rest of the Blogs to start

    for j in  range(numPosts): 
        tSleep = random.random()*timeSlots
        tSleep2 = timeSlots - tSleep

        element, listP = nextPost(blog,socialNetwork)

        logger.info("    %s -> %s: Waiting ... %.2f minutes" % 
                (urllib.parse.urlparse(blog.getUrl()).netloc.split('.')[0],
                    socialNetwork[0].capitalize(), 
                    tSleep/60))
        #logger.info("    %s: Waiting" % (blog.getUrl()))
        logger.info("     I'll publish %s" % element[0])
        print(" [d] Profile %s: waiting... %.2f minutes" 
                % (socialNetwork[0], tSleep/60))
        tNow = time.time()
        with open(fileNamePath(blog.getUrl(), 
            socialNetwork)+'.timeNext','wb') as f:
            pickle.dump((tNow,tSleep), f)
        time.sleep(tSleep) 

        # Things can have changed during the waiting
        element, listP = nextPost(blog,socialNetwork)

        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = element

        profile = socialNetwork[0]
        nick = socialNetwork[1]

        logger.info("    Publishing in: %s" % socialNetwork[0].capitalize())
        print(" [d] Publishing in: %s at %s" % (socialNetwork[0].capitalize(), 
            time.asctime()))

        result = None
        if profile in ['twitter', 'facebook', 'mastodon', 
                'imgur', 'wordpress','linkedin']: 
            # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
            try:
                import importlib
                mod = importlib.import_module('module'+profile.capitalize()) 
                cls = getattr(mod, 'module'+profile.capitalize())
                api = cls()
                api.setClient(nick)
                if profile in ['wordpress']: 
                    result = api.publishPost(title, link, comment, tags=links)
                else: 
                    result = api.publishPost(title, link, comment)
                logger.info("      Res: {}".format(result))
            except:
                logging.warning("Some problem in {}".format(socialNetwork[0].capitalize())) 
                logging.warning("Unexpected error:", sys.exc_info()[0]) 

            if isinstance(result, str):
                if result[:4]=='Fail':
                    link=''
                elif result[:21] == 'Wordpress API expired':
                    print(" [d] Not published: %s - %s" % (result, 'Fail'))
                    result = 'Fail!'
                else: 
                    print(" [d] Published: %s - %s" % (result, 'OK'))
                    result = 'OK'
        else: 
            try: 
                publishMethod = globals()['publish'+ profile.capitalize()]#()(self, )) 
                result = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
            except:
                logging.info(self.report('Social', text, sys.exc_info()))

        if result == 'OK':
            blog.cache[socialNetwork].posts = listP
            blog.cache[socialNetwork].updatePostsCache()
           
        if j+1 < numPosts:
            logger.info("Time: %s Waiting ... %.2f minutes to schedule next post in %s" % (time.asctime(), tSleep2/60, socialNetwork[0]))
            time.sleep(tSleep2) 
        logger.info("    Finished: {}".format(str(socialNetwork)))
        logger.info("    Finished: {}".format(str(urllib.parse.urlparse(blog.getUrl()).netloc.split('.'))))
        logger.info("    Finished: {}".format(str(socialNetwork[0].capitalize())))
        logger.info("    Finished: {}".format(str(urllib.parse.urlparse(blog.getUrl()).netloc.split('.')[0])))
        logger.info("    Finished: {} -> {}".format(urllib.parse.urlparse(blog.getUrl()).netloc.split('.')[0], socialNetwork[0].capitalize()))
        #logger.info("    %s: Finished" % (blog.getUrl()))
        print(" [d] Finished in: %s at %s" % (socialNetwork[0].capitalize(), 
            time.asctime()))

   
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


