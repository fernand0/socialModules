#!/usr/bin/env python

import configparser
import json
import sys
import urllib.parse
from html.parser import HTMLParser

import oauth2 as oauth
import requests
from linkedin_api.clients.restli.client import RestliClient

from socialModules.configMod import *
from socialModules.moduleContent import *

# git@github.com:fernand0/python-linkedin-v2.git
# python setup.py install


class moduleLinkedin(Content):
    POSTS_RESOURCE = "/posts"

    def getKeys(self, config):
        CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY")
        CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
        ACCESS_TOKEN = config.get("Linkedin", "ACCESS_TOKEN")
        URN = config.get("Linkedin", "URN")
        RETURN_URL = config.get("Linkedin", "return_url")

        return (CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, URN, RETURN_URL)

    def initApi(self, keys):
        self.URN = keys[3]
        self.TOKEN = keys[2]
        self.API_VERSION = "202501"
        client = RestliClient()
        return client

    def authorize(self):
        # Needs some cleaning
        try:
            config = configparser.ConfigParser()
            configLinkedin = CONFIGDIR + "/.rssLinkedin"
            config.read(configLinkedin)
            keys = self.getKeys(config)
            self.CONSUMER_KEY = keys[0]
            self.CONSUMER_SECRET = keys[1]
            self.state = config.get("Linkedin", "state")

            payload = {
                "response_type": "code",
                "client_id": self.CONSUMER_KEY,
                "client_secret": self.CONSUMER_SECRET,
                "redirect_uri": keys[4],
                "state": self.state,
                "scope": "r_liteprofile r_emailaddress w_member_social r_member_social",
            }
            print(
                "https://www.linkedin.com/oauth/v2/authorization?"
                + urllib.parse.urlencode(payload)
            )

            # auth_client = AuthClient(
            #                         client_id=self.CONSUMER_KEY,
            #                         client_secret=self.CONSUMER_SECRET,
            #                         redirect_url='localhost:3000')
            # print(f"{auth_client.generate_member_auth_url(scopes=['r_liteprofile']}")
            resUrl = input(
                "Copy and paste the url in a browser and write here the access token "
            )

            splitUrl = urllib.parse.urlsplit(resUrl)
            result = urllib.parse.parse_qsl(splitUrl.query)
            access_token = result[0][1]
            token_response = auth_client.exchange_auth_code_for_access_token(auth_code)
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            payload = {
                "grant_type": "authorization_code",
                "code": access_token,
                "redirect_uri": "http://localhost:8080/code",
                "client_id": self.CONSUMER_KEY,
                "client_secret": self.CONSUMER_SECRET,
            }

            res = requests.post(url, data=payload)
            print(res.text)
            config.set("Linkedin", "ACCESS_TOKEN", json.loads(res.text)["access_token"])
            shutil.copyfile(configLinkedin, "{}.bak".format(configLinkedin))
            with open(configLinkedin, "w") as configfile:
                config.write(configfile)

            restli_client = RestliClient()
            sys.exit()
        except:
            print("Some problem")

    def setProfile(self):
        me_response = self.getClient().get(resource_path="/me", access_token=self.TOKEN)
        self.profile = me_response

    def getProfile(self):
        profile = None
        if hasattr(self, "profile"):
            profile = self.profile
        return profile

    def setApiPosts(self):
        urn = self.URN
        author = f"urn:li:person:{urn}"
        author = urllib.parse.quote(author)
        posts = []
        # posts =  self.getClient().get_posts(urn=self.URN)
        # print(posts)
        # url = 'https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({})&sortBy=LAST_MODIFIED'.format(author)

        # access_token = self.client.authentication.token.access_token
        # headers = {'X-Restli-Protocol-Version': '2.0.0',
        #   'Content-Type': 'application/json',
        #   'Authorization': f'Bearer {access_token}'}

        # posts = requests.get(url,headers=headers,data={'q':author})
        # print(posts)
        return posts

    def processReply(self, reply):
        # logging.info(f"Res {reply}")
        if isinstance(reply, bytes):
            res = json.loads(reply)
        else:
            res = reply
        # if (('message' in res) and ('expired' in res['message'])):
        #    reply = f"Fail! {self.service} token expired"
        # if (('message' in res) and ('duplicate' in res['message'])):
        #    reply = f"Fail! {self.service} Status is a duplicate."
        # elif ('message' in res):
        if hasattr(res, "entity_id"):
            reply = f"https://www.linkedin.com/feed/update/{res.entity_id}/"
        else:
            reply = res
        # logging.info(f"Res: {reply}")

        return reply

    def publishApiImage(self, *args, **kwargs):
        # Does not work?
        res = ""
        if len(args) == 2:
            title, imageName = args
            more = kwargs
            if imageName:
                with open(imageName, "rb") as imagefile:
                    imagedata = imagefile.read()

                try:
                    res = self.getClient().submit_share(
                        comment=None,
                        title=title,
                        description=None,
                        submitted_url=None,
                        submitted_image_url=imageName,
                        urn=self.URN,
                        visibility_code="anyone",
                    )
                except:
                    logging.info(f"Exception {sys.exc_info()}")
                    res = self.report("Linkedin", title, link, sys.exc_info())
        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3 and args[0]:
            title, link, comment = args
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)[:250]
            link = api.getPostLink(post)
            comment = api.getPostComment(title)
        else:
            self.res_dict["error_message"] = "Not enough arguments for publication."
            return self.res_dict

        msgLog = f"{self.indent} Publishing: {title} - {link} - {comment}"
        logMsg(msgLog, 1, False)

        try:
            me_response = self.getClient().get(resource_path="/me", access_token=self.TOKEN)
            self.res_dict["raw_response"] = me_response

            if "id" not in me_response.entity:
                self.res_dict["error_message"] = "Could not get user ID for publishing."
                return self.res_dict

            author_urn = f"urn:li:person:{me_response.entity['id']}"
            entity = {
                "author": author_urn,
                "commentary": f"{title}",
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
            }

            if link:
                entity["content"] = {"article": {"source": link, "title": title}}

            res = self.getClient().create(
                resource_path=self.POSTS_RESOURCE,
                entity=entity,
                version_string=self.API_VERSION,
                access_token=self.TOKEN,
            )
            self.res_dict["raw_response"] = res

            if res.status_code == 201:
                self.res_dict["success"] = True
                # The post URN is in the x-restli-id header
                post_urn = res.headers.get('x-restli-id')
                if post_urn:
                    self.res_dict["post_url"] = f"https://www.linkedin.com/feed/update/{post_urn}/"
            else:
                if "message" in res.entity:
                    self.res_dict["error_message"] = res.entity['message']
                else:
                    self.res_dict["error_message"] = f"LinkedIn API error: {res.entity}"
        except Exception as e:
            self.res_dict["error_message"] = self.report("Linkedin", title, link, sys.exc_info())
            self.res_dict["raw_response"] = e

        return self.res_dict

    def deleteApiPosts(self, idPost):
        result = self.getClient().delete_post(idPost, urn=self.URN)
        logging.info(f"Res: {result}")
        return result

    def getApiPostLink(self, post):
        link = ''
        if ('link' in post.data):
            # whatever
            link = post.data.get('link')
        return post

    def getApiPostUrl(self, post):
        link = ''
        if ('link' in post.data):
            # whatever
            link = post.data.get('link')
        return post

    def getApiPostTitle(self, post):
        title = ''
        if ('text' in post.data):
            # whatever
            title = post.data.get('text')
        return post

    def register_specific_tests(self, tester):
        pass

    def get_user_info(self, client):
        # client is the module Linkedin instance
        me_response = client.getClient().get(resource_path="/me", access_token=client.TOKEN)
        if me_response.entity:
            firstName = me_response.entity.get('localizedFirstName', '')
            lastName = me_response.entity.get('localizedLastName', '')
            return f"{firstName} {lastName}"
        return "Could not get user info"

    def get_post_id_from_result(self, result):
        if isinstance(result, str) and 'linkedin.com' in result:
            return result.split('/')[-2]
        return None


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    linkedin_module = moduleLinkedin()
    tester = ModuleTester(linkedin_module)
    tester.run()


if __name__ == "__main__":
    main()
