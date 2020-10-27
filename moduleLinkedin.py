#!/usr/bin/env python

import configparser
import logging
import os
import oauth2 as oauth
import pickle
import requests
import sys
import urllib.parse

from html.parser import HTMLParser
from linkedin_v2 import linkedin


from configMod import *
from moduleContent import *

class moduleLinkedin(Content):

    def __init__(self):
        super().__init__()
        self.service = 'Linkedin'
        self.user = None
        self.ln = None

    def setClient(self, linkedinAC=""):
        logging.info("    Connecting {} {}".format(self.service, 
            str(linkedinAC)))
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssLinkedin')
            if config.sections():
                if isinstance(linkedinAC, tuple): 
                    linkedinAC = linkedinAC[1][1]
                self.user = linkedinAC    

                self.CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY") 
                self.CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
                self.ACCESS_TOKEN = config.get("Linkedin", "ACCESS_TOKEN") 
                self.ln = linkedin.LinkedInApplication(token=self.ACCESS_TOKEN)
                self.URN = config.get("Linkedin", "URN")
            else:
                logging.warning("Account not configured") 
                if sys.exc_info()[0]: 
                    logging.warning("Unexpected error: {}".format( 
                        sys.exc_info()[0]))
                sys.exit(1)
        except:
            logging.warning("Account not configured")
            sys.exit(1)

    def authorize(self):
        try:
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
            print('https://www.linkedin.com/oauth/v2/authorization?'
                    + urllib.parse.urlencode(payload))

            access_token = input("Copy and paste the url in a browser and write here the reply url ")
            pos=access_token.find('code=')
            pos2=access_token.find('&',pos+10)
            print(pos, pos2)
            print(access_token[pos+5:pos2])
            access_token=access_token[pos+5:pos2] 



            url = 'https://www.linkedin.com/oauth/v2/accessToken'
            payload = {'grant_type':'authorization_code',
                    'code':access_token,
                    'redirect_uri':'http://localhost:8080/code',
                    'client_id': self.CONSUMER_KEY,
                    'client_secret': self.CONSUMER_SECRET}
            res = requests.post(url, data=payload)
            print(res.text)
            sys.exit()
        except:
            print("Some problem")
 

    def getClient(self):
        return None
 
    def setPosts(self):
        logging.info("  Setting posts")
        urn = self.URN
        author = f"urn:li:person:{urn}"        
        print(author,type(author))
        author = urllib.parse.quote(author)
        #url = 'https://api.linkedin.com/v2/originalArticles'#.format('{8822}')  
        #print(author)
        url = 'https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({})&sortBy=LAST_MODIFIED'.format(author)

        print(url)
        print(author)
        access_token = self.ln.authentication.token.access_token
        headers = {'X-Restli-Protocol-Version': '2.0.0',
           'Content-Type': 'application/json',
           'Authorization': f'Bearer {access_token}'}

        # b'{"serviceErrorCode":100,"message":"Not enough permissions to access: GET-authors /ugcPosts","status":403}'
        res = requests.get(url,headers=headers,data={'q':author})
        self.posts = res

    def publishPost(self, post, link, comment):

        try: 
            # Function submit_share added on my own repo:
            # https://github.com/fernand0/python-linkedin-v2
            # Do not install with pip, install with 
            # > python setup.py install
            res = self.ln.submit_share(comment=comment, title=post,
                    description=None, submitted_url=link, 
                    submitted_image_url=None, urn=self.URN, 
                    visibility_code='anyone')
            logging.info("    Reply %s"%str(res))
        except:
            logging.info("Error publishing!")
            logging.warning(self.report(self.service, post, link, sys.exc_info()))

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

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleLinkedin

    ln = moduleLinkedin.moduleLinkedin()

    ln.setClient('fernand0')
    if True: 
        ln.authorize()


    print(ln.ln.get_profile())

    ln.publishPost("Testing", 'https://github.com/fernand0/socialModules/blob/master/moduleLinkedin.py','')

    sys.exit(1)
    import moduleSlack
    slack = moduleSlack.moduleSlack()

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    site = moduleSlack.moduleSlack()
    section = "Blog7"

    url = config.get(section, "url")
    site.setUrl(url)

    SLACKCREDENTIALS = os.path.expanduser(CONFIGDIR + '/.rssSlack')
    site.setSlackClient(SLACKCREDENTIALS)

    CHANNEL = 'links' 
    theChannel = site.getChanId(CHANNEL)  
    print("the Channel %s" % theChannel)
    site.setPosts()
    post = site.getNumPostsData(1,len(site.getPosts()))[0]
    title = post[0]
    link = post[1]
    print(title, link)
    ln.publishPost(title, link,'')




    sys.exit()
    print(ln.publishPost("Probando á é í ó ú — ",'',''))

    import time
    time.sleep(10)
    sys.exit()
    print(ln.publishPost("El mundo es Imperfecto",'http://elmundoesimperfecto.com/',''))

if __name__ == '__main__':
    main()

