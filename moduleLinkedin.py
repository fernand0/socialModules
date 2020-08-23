#!/usr/bin/env python

import configparser
import logging
import os
import pickle
import requests
import sys

from html.parser import HTMLParser
from linkedin_v2 import linkedin

import oauth2 as oauth



from configMod import *
from moduleContent import *

class moduleLinkedin(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.ln = None

    def setClient(self, linkedinAC=""):
        logging.info("    Connecting Linkedin")
        if True:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssLinkedin')

            self.user = linkedinAC    

            self.CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY") 
            self.CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET") 
            self.ACCESS_TOKEN = config.get("Linkedin", "ACCESS_TOKEN") 
            self.ln = linkedin.LinkedInApplication(token=self.ACCESS_TOKEN)
            #self.USER_TOKEN = config.get("Linkedin", "USER_TOKEN") 
            #self.USER_SECRET = config.get("Linkedin", "USER_SECRET") 
            #self.RETURN_URL = config.get("Linkedin", "RETURN_URL")
            #self.ACCESS_TOKEN = config.get("Linkedin", "ACCESS_TOKEN")
            self.URN = config.get("Linkedin", "URN")

        else:
            logging.warning("Account not configured")

    def authorize(self):
        if True:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssLinkedin')
            self.CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY") 
            self.CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET") 

            import requests
            payload = {'response_type':'code',
                    'client_id': self.CONSUMER_KEY,
                    'client_secret': self.CONSUMER_SECRET,
                    'redirect_uri': 'http://localhost:8080/code',
                    'state':'33313134',
                    'scope': 'r_liteprofile r_emailaddress w_member_social' }
            import urllib.parse
            print('https://www.linkedin.com/oauth/v2/authorization?'
                    + urllib.parse.urlencode(payload))

            access_token = input("Copy and paste the url in a browser and write here the access token ")

            url = 'https://www.linkedin.com/oauth/v2/accessToken'
            payload = {'grant_type':'authorization_code',
                    'code':access_token,
                    'redirect_uri':'http://localhost:8080/code',
                    'client_id': self.CONSUMER_KEY,
                    'client_secret': self.CONSUMER_SECRET}
            res = requests.post(url, data=payload)
            print(res.text)
            sys.exit()
 

    def getClient(self):
        return None
 
    def setPosts(self):
        logging.info("  Setting posts")
        urn = self.URN
        author = f"urn:li:person:{urn}"        
        url = 'https://api.linkedin.com/v2/originalArticles'#.format('{8822}')        
        print(url)
        access_token = self.ln.authentication.token.access_token
        headers = {'X-Restli-Protocol-Version': '2.0.0',
           'Content-Type': 'application/json',
           'Authorization': f'Bearer {access_token}'}

        res = requests.get(url,headers=headers,data={'q':author})
        self.posts = res

    def publishPost(self, post, link, comment):

        res = self.ln.submit_share(comment=comment, title=post,description=None,
                submitted_url=link, submitted_image_url=None, 
                urn=self.URN, visibility_code='anyone')
        logging.info("    Reply %s"%str(res))

        return res

        # Based on https://github.com/gutsytechster/linkedin-post
        access_token = self.ACCESS_TOKEN
        urn = self.URN

        author = f"urn:li:person:{urn}"

        headers = {'X-Restli-Protocol-Version': '2.0.0',
           'Content-Type': 'application/json',
           'Authorization': f'Bearer {access_token}'}

        api_url_base = 'https://api.linkedin.com/v2/'
        api_url = f'{api_url_base}ugcPosts'
    
        logging.info("    Publishing in LinkedIn...")
        if comment == None:
            comment = ''
        postC = comment + " " + post + " " + link
        h = HTMLParser()
        postC = h.unescape(post)
        try:
            logging.info("    Publishing in Linkedin: %s" % post)
            if link: 
                post_data = {
                    "author": author,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": comment
                            },
                            "shareMediaCategory": "ARTICLE",
                            "media": [
                                { "status": "READY",
                                    #"description": {
                                    #    "text": "El mundo es imperfecto"
                                    #    },
                                    "originalUrl": link,
                                    "title": {
                                        "text": post
                                    }
                               }
                            ]
                        },
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
                    },
                }
            else: 
                post_data = {
                     "author": author,
                     "lifecycleState": "PUBLISHED",
                     "specificContent": {
                         "com.linkedin.ugc.ShareContent": {
                             "shareCommentary": {
                                 "text": post
                             },
                             "shareMediaCategory": "NONE"
                         },
                     },
                     "visibility": {
                         "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
                     },
                }

            res = requests.post(api_url, headers=headers, json=post_data)
            logging.info("Res: %s" % res)
            if res.status_code == 201: 
                return("Success ") 
            else: 
                return(res.content)
        except:        
            return(self.report('LinkedIn', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        return post


def main():

    import moduleLinkedin

    ln = moduleLinkedin.moduleLinkedin()

    ln.setClient('fernand0')

    print(ln.ln.get_profile())

    print("Testing posts")
    ln.setPosts()
    for post in ln.getPosts():
        print(post)

    #print(ln.publishPost("Probando á é í ó ú — ",'',''))
    sys.exit()

    import time
    time.sleep(10)
    sys.exit()
    print(ln.publishPost("El mundo es Imperfecto",'http://elmundoesimperfecto.com/',''))

if __name__ == '__main__':
    main()

