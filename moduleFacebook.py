#!/usr/bin/env python

import configparser
import sys

from bs4 import BeautifulSoup
from bs4 import Tag
from html.parser import HTMLParser

import facebook

from configMod import *
from moduleContent import *
from moduleQueue import *

# We are using facebook-sdk 
# You can find the way to obtain tokens and so on at:
# https://facebook-sdk.readthedocs.io/
# 
# Config file
# [Facebook]
# oauth_access_token: #<- We only need this one
# client_token:
# app_token:
# app_id:

class moduleFacebook(Content,Queue):

    def __init__(self):
        super().__init__()

    def getKeys(self, config): 
        oauth_access_token = config.get(self.service, "oauth_access_token")
        return ((oauth_access_token,))

    def initApi(self, keys):
        graph = facebook.GraphAPI(keys[0], version='3.0') 
        #self.setPage(self.user)
        return graph 

    def setPage(self, facebookAC='me'):
        perms = ['publish_actions','manage_pages','publish_pages'] 
        pages = self.getClient().get_connections("me", "accounts") 
        self.pages = pages

        if (facebookAC != 'me'): 
            for i in range(len(pages['data'])): 
                logging.debug("Selecting %s %s"% (pages['data'][i]['name'], facebookAC)) 
                if (pages['data'][i]['name'] == facebookAC): 
                    logging.info("     Selected... %s"% pages['data'][i]['name']) 
                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token']) 
                    self.page = graph2
                    self.pageId = pages['data'][i]['id']
                    break
                else: 
                    # Publishing as me 
                    self.page = facebookAC 

    def setApiPosts(self):
        posts = []
        postsF = self.page.get_connections(self.pageId, connection_name='posts') 
        if 'data' in postsF: 
            for post in postsF['data']: 
                postt = self.page.get_connections(post['id'], 
                        connection_name='attachments') 
                if 'data' in postt:
                    # We need to merge the two dictionaries to have the id and
                    # the other data
                    posts.append({**postt['data'][0] , **post})

        return posts
        #outputData = {}
        #serviceName = 'Facebook'
        #outputData[serviceName] = {'sent': [], 'pending': []}
        #for post in self.getPosts():
        #    (page, idPost) = post['id'].split('_')
        #    url = 'https://facebook.com/' + page + '/posts/' + idPost
        #    outputData[serviceName]['sent'].append((post['message'], url, 
        #            '', post['created_time'], '','','','',''))

        #self.postsFormatted = outputData

    def getUrlId(self, post):
        return (post.split('/')[-1])

    def processReply(self, reply): 
        res = reply
        if reply: 
            logging.debug("Res: %s" % reply) 
            if 'id' in reply: 
                res = 'https://www.facebook.com/{}'.format(reply['id'])
                logging.info("     Link: {}".format(res)) 
        return(res)
 
    def publishApiPost(self, postData):
        post, link, comment, plus = postData
        post = self.addComment(post, comment)

        res = "Fail!"
        if (not isinstance(self.page, str)):
            res = self.page.put_object('me', "feed", message=post, link=link)
        return res

    def deleteApiPosts(self, idPost): 
        result = self.page.delete_object(idPost)
        logging.info(f"Res: {result}")
        return(result)

    def getPostId(self, post):
        result = self.getAttribute(post, 'id')
        return result

    #def getUrlId(self, post):
    #    return (post.split('/')[-1])

    def getPostTitle(self, post):
        return self.getAttribute(post, 'title')

    def getPostUrl(self, post):
        idPost = self.getPostId(post)
        return f"https://facebook.com/{idPost}"
        #return f'https://twitter.com/{self.user}/status/{idPost}'

    def getPostLink(self, post):
        result = self.getAttribute(post, 'url')
        pos = result.find('=')
        pos2 = result.find('&',pos)
        import urllib.parse
        return urllib.parse.unquote(result[pos+1:pos2])

    def getPostImages(self,idPost):
        res = []
        post = self.client.get_object('me',fields='id')
        myId = post['id']
        field='attachments'
        post = self.client.get_object('{}_{}'.format(myId,idPost),fields=field)
        res.append(post['attachments']['data'][0]['media']['image']['src'])
        subAttach = post['attachments']['data'][0]['subattachments']
        for img in subAttach['data']:
            res.append(img['media']['image']['src'])

        return(res)

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleFacebook
    fc = moduleFacebook.moduleFacebook()

    fc.setClient('me')
    fc.setPage('Enlaces de fernand0')
    #print("Testing posting and deleting")
    #res = fc.publishPost("Prueba borrando 7", "http://elmundoesimperfecto.com/", '')
    #print("Res",res)
    #idPost = fc.getUrlId(res)
    #print("id",idPost)
    #input('Delete? ')
    #fc.deletePostId(idPost)
    #sys.exit() 
    fc.setPostsType('posts')
    fc.setPosts()
    for i, post in enumerate(fc.getPosts()):
        title = fc.getPostTitle(post)
        link = fc.getPostLink(post)
        url = fc.getPostUrl(post)
        theId = fc.getPostId(post)
        print(f"{i}) Title: {title}\nLink: {link}\nUrl: {url}\nId: {theId}\n")
    sys.exit()
    fc.publishPost("Prueba")
    print(fc.user)
    sys.exit()
    images = fc.getPostImages('10157835018558264')
    print(images)
    print(len(images))
    images = fc.getPostImages('10157761305288264')
    print(images)
    print(len(images))
    sys.exit()
    print(fc.get_object(id='me'))

    print("Listing pages")
    for page in fc.pages['data']:
        print(page['name'], page)

    fc.setPosts()
    for post in fc.getPosts():
        print(post)
        #print("@%s: %s" %(tweet[2], tweet[0]))
    sys.exit()

    print("Testing title and link")
    
    for post in fc.getPosts():
        print(post)
        title = fc.getPostTitle(post)
        link = fc.getPostLink(post)
        print("Title: {}\nLink: {}\n".format(title,link))

 
    sys.exit()


    fc.setPosts()
    posts = fc.getPosts()
    for post in posts:
        print(post)
        #print("%s: %s" %(post[0], post[1]))


if __name__ == '__main__':
    main()

