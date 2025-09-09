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
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)[:250]
            # Title/content/article must be of lenght 0...400
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        msgLog = f"{self.indent} Publishing: {title} - {link} - {comment}"
        logMsg(msgLog, 1, 0)
        try:
            try:
                # me_response = self.getClient().get(resource_path=ME_RESOURCE,
                me_response = self.getClient().get(
                    resource_path="/me", access_token=self.TOKEN
                )

                msgLog = f"{self.indent} Response: {me_response}"
                logMsg(msgLog, 2, 0)
                POSTS_RESOURCE = "/posts"
                if link and "id" in me_response.entity:
                    entity = {
                        "author": f"urn:li:person:{me_response.entity['id']}",
                        "commentary": f"{title}",
                        "visibility": "PUBLIC",
                        "distribution": {
                            "feedDistribution": "MAIN_FEED",
                            "targetEntities": [],
                            "thirdPartyDistributionChannels": [],
                        },
                        "content": {
                            "article": {"source": f"{link}", "title": f"{title}"}
                        },
                        "lifecycleState": "PUBLISHED",
                    }

                    res = self.getClient().create(
                        resource_path=POSTS_RESOURCE,
                        entity=entity,
                        version_string=self.API_VERSION,
                        access_token=self.TOKEN,
                    )
                else:
                    res = self.getClient().create(
                        resource_path=POSTS_RESOURCE,
                        entity={
                            "author": f"urn:li:person:{me_response.entity['id']}",
                            "visibility": "PUBLIC",
                            "commentary": f"{title}",
                            "distribution": {
                                "feedDistribution": "MAIN_FEED",
                                "targetEntities": [],
                                "thirdPartyDistributionChannels": [],
                            },
                            "lifecycleState": "PUBLISHED",
                        },
                        version_string=self.API_VERSION,
                        access_token=self.TOKEN,
                    )
            except:
                logging.info(f"Linkedin. Not authorized.")
                logging.info(f"Exception {sys.exc_info()}")
                res = self.report("Linkedin", title, link, sys.exc_info())
            # self.getClient().get_profile()
            # try:
            #     res = self.getClient().submit_share(comment=comment,
            #                                         title=title,
            #                                         description=None,
            #                                         submitted_url=link,
            #                                         submitted_image_url=None,
            #                                         urn=self.URN,
            #                                         visibility_code='PUBLIC')
            # except:
            #     logging.info(f"Linkedin. Not authorized.")
            #     logging.info(f"Exception {sys.exc_info()}")
            #     res = self.report('Linkedin', title, link, sys.exc_info())
        except:
            logging.info(f"Linkedin. Other problems.")
            logging.info(f"Exception {sys.exc_info()}")
            res = self.report("Linkedin", title, link, sys.exc_info())

        # logging.debug(f"Code return: {res}")
        # logging.debug(f"Code return: {res.__dir__()}")
        # logging.debug(f"Code return: {res.status_code}")
        # logging.debug(f"Code return: {res.response}")
        # logging.debug(f"Code return entity: {res.entity}")
        # logging.debug(f"Code return: {res.entity_id}")
        # logging.debug(f"Code return headers: {res.headers}")
        # logging.debug(f"Code return headers: {res.url}")
        # logging.debug(f"Code return type: {type(res)}")
        if isinstance(res, bytes) and ("201".encode() not in res):
            # FIXME: Logic? Conditional management?
            res = f"Fail!\n{res}"
        else:
            code = res.status_code
            # msgLog = f"{self.indent} return code: {code}"
            # logMsg(msgLog, 1, 0)
            if code and (code != 201):
                if "message" in res.entity:
                    res = f"Fail! {res.entity['message']}"
                else:
                    res = f"Fail! {res.entity}"
        return res

    def deleteApiPosts(self, idPost):
        result = self.getClient().delete_post(idPost, urn=self.URN)
        logging.info(f"Res: {result}")
        return result

    def getPostTitle(self, post):
        # Not  developed
        return post


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    import moduleLinkedin

    ln = moduleLinkedin.moduleLinkedin()

    ln.setClient("fernand0")
    try:
        print(ln.getClient().get(resource_path="/me", access_token=ln.TOKEN))
    except:
        logging.info("Not authorized, re-authorizing")
        ln.authorize()

    testingMe = False
    if testingMe:
        ln.setProfile()
        profile = ln.getProfile()
        if profile and profile.status_code == 200:
            print(f"Profile: {profile.__dir__()}")
            print(f"Profile: {profile.entity}")

        return

    testingPost = True
    if testingPost:
        res = ln.publishPost("A ver otro", "https://elmundoesimperfecto.com/", "")
        print(f"res: {res}")
        if "Fail" in res:
            ln.authorize()
        return
    # sys.exit()
    # print(ln.deleteApiPosts('6764243697006727168'))
    # sys.exit()

    testingPostImages = False
    if testingPostImages:
        image = "/tmp/E8dCZoWWQAgDWqX.png"
        title = "Prueba imagen"
        ln.publishImage(title, image)
        return

    testingPosts = True
    if testingPosts:
        print("Testing posts")
        ln.setProfile()
        LIST_POSTS_RESOURCE = "/ugcPosts"
        QUERY_PARAMS = {
            "q": "authors",
            "authors": "List({urn:li:person:'"
            + f"{ln.getProfile().entity['id']}"
            + "})",
            "sortBy": "LAST_MODIFIED",
            "projection": "(elements*(...))",
        }

        print(f"url: {LIST_POSTS_RESOURCE}")
        print(f"url: {QUERY_PARAMS}")
        posts = ln.getClient().get(
            resource_path=LIST_POSTS_RESOURCE,
            access_token=ln.TOKEN,
            query_params=QUERY_PARAMS,
        )
        print(f"Posts: {posts.__dir__()}")
        print(f"Posts: {posts.entity}")

        # q=authors&authors=List({encoded personUrn})&sortBy=LAST_MODIFIED&projection=(elements*(...))

        return

        ln.setPostsType("posts")
        ln.setPosts()
        for post in ln.getPosts():
            print(post)
        return

    sys.exit()

    import moduleSlack

    slack = moduleSlack.moduleSlack()

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + "/.rssBlogs")

    site = moduleSlack.moduleSlack()
    section = "Blog7"

    url = config.get(section, "url")
    site.setUrl(url)

    SLACKCREDENTIALS = os.path.expanduser(CONFIGDIR + "/.rssSlack")
    site.setSlackClient(SLACKCREDENTIALS)

    CHANNEL = "links"
    theChannel = site.getChanId(CHANNEL)
    print("the Channel %s" % theChannel)
    site.setPosts()
    post = site.getNumPostsData(1, len(site.getPosts()))[0]
    title = post[0]
    link = post[1]
    print(title, link)
    ln.publishPost(title, link, "")

    sys.exit()
    print(ln.publishPost("Probando á é í ó ú — ", "", ""))

    import time

    time.sleep(10)
    sys.exit()
    print(
        ln.publishPost("El mundo es Imperfecto", "http://elmundoesimperfecto.com/", "")
    )


if __name__ == "__main__":
    main()
