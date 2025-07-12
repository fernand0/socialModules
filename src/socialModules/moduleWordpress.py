import configparser
import json
import logging
import shutil
import sys
import urllib
import urllib.parse

import requests
from bs4 import BeautifulSoup

from socialModules.configMod import CONFIGDIR
from socialModules.moduleContent import Content


class moduleWordpress(Content):  # ,Queue):
    def getKeys(self, config):
        access_token = config[self.user]["access_token"]
        return (access_token,)

    def initApi(self, keys):
        # self.user = None
        self.wp = None
        self.service = "Wordpress"
        self.tags = None
        self.oauth_base = "https://public-api.wordpress.com/oauth2/authorize?"
        # self.api_auth='authorize'
        # self.api_token='token'
        self.api_auth = "client_id={}&redirect_uri={}&response_type=token&blog={}"
        self.api_base = "https://public-api.wordpress.com/rest/v1/"
        self.api_base2 = "https://public-api.wordpress.com/wp/v2/"
        self.api_user = "me"
        self.api_posts = "sites/{}/posts"
        self.api_tags = "sites/{}/tags"
        self.api_posts_search = "?search={}"
        self.my_site = None
        self.headers = None
        self.access_token = None

        self.access_token = keys[0]
        self.headers = {"Authorization": "Bearer " + self.access_token}
        self.my_site = "{}.wordpress.com".format(self.user)

        return "client"

    def setNick(self, nick=None):
        if not nick:
            nick = self.getUrl()
            nick = nick.split("/")[2].split(".")[0]
        self.nick = nick

    # def setClient(self, user):
    #    logging.info(f"     Connecting Wordpress {user}")
    #    if isinstance(user, str):
    #        self.user = user
    #    elif isinstance(user[1], str):
    #        self.user = user[1]
    #    else:
    #        self.user = user[1][1]

    #    try:
    #        config = configparser.RawConfigParser()
    #        config.read(CONFIGDIR + '/.rssWordpress')

    #        try:
    #            self.access_token =  config.get(self.user, "access_token")
    #            logging.info(f"     Connected {user}")
    #        except:
    #            logging.info(f"     Not Connected {user}")
    #            logging.warning("Access key does not exist!")
    #            logging.warning("Unexpected error:", sys.exc_info()[0])
    #    except:
    #            logging.info(f"     Not Not Connected {user}")
    #            logging.warning("Config file does not exists")
    #            logging.warning("Unexpected error:", sys.exc_info()[0])

    #    self.headers = {'Authorization':'Bearer '+self.access_token}
    #    self.my_site="{}.wordpress.com".format(self.user)

    def authorize(self):
        url = f"https://{self.user}.wordpress.com/"
        name = self.user
        # Second the authentication data of the blog
        config = configparser.ConfigParser(interpolation=None)
        configWordpress = CONFIGDIR + "/.rssWordpress"
        config.read(configWordpress)
        try:
            redirect_uri = config.get(name, "redirect_uri")
            client_id = config.get(name, "Client_ID")
            param = self.api_auth.format(
                client_id, urllib.parse.quote(redirect_uri), url
            )
            print(
                f"Paste this URL in your browser and allow the application: "
                f"{self.oauth_base}{param}"
            )

            resUrl = input("Paste the resulting URL: ")
            splitUrl = urllib.parse.urlsplit(resUrl)
            print(f"split: {splitUrl}")
            print(f"split: {splitUrl.fragment}")
            result = urllib.parse.parse_qsl(splitUrl.fragment)
            print(f"result: {result}")
            result = urllib.parse.parse_qsl(splitUrl.fragment)
            token = urllib.parse.unquote(result[0][1])
            print(f"token: {token}")
            print(f"name: {name}")
            config.set(name, "access_token", token)
            # Make a backup
            shutil.copyfile(configWordpress, "{}.bak".format(configWordpress))
            with open(configWordpress, "w") as configfile:
                config.write(configfile)
        except:
            logging.info("No config file or not adequate fields")

    def setApiPosts(self, morePosts=False):
        posts = []
        numPosts = 100
        try:
            result = requests.get(
                self.api_base
                + self.api_posts.format(self.my_site)
                + f"?number={numPosts}",
                headers=self.headers,
            ).json()
            if "posts" in result:
                posts = result["posts"]
            if morePosts:
                posts2 = requests.get(
                    self.api_base
                    + self.api_posts.format(self.my_site)
                    + "?number=100&page=2",
                    headers=self.headers,
                ).json()["posts"]
                posts.append(posts2)
        except KeyError:
            logging.warning("KeyError probably API Key expired")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            return self.report(f"{self.service} API expired", "", "", sys.exc_info())
        except:
            return self.report(f"{self.service} API", "", "", sys.exc_info())
        return posts

    # def setPosts(self, morePosts=None):
    #    logging.info("  Setting posts")
    #    self.posts = []
    #    try:
    #        #print(self.api_base + self.api_posts.format(self.my_site))
    #        posts = requests.get(self.api_base +
    #                self.api_posts.format(self.my_site)+'?number=100',
    #                headers = self.headers).json()['posts']
    #        self.posts = posts
    #        if morePosts:
    #            posts2 = requests.get(self.api_base +
    #                self.api_posts.format(self.my_site)+'?number=100&page=2',
    #                headers = self.headers).json()['posts']
    #            self.post.append(posts2)
    #    except KeyError:
    #        logging.warning("KeyError probably API Key expired")
    #        logging.warning("Unexpected error:", sys.exc_info()[0])
    #        return(self.report('Wordpress API expired', '' , '', sys.exc_info()))
    #    except:
    #        return(self.report('Wordpress API', '' , '', sys.exc_info()))
    #    return('OK')

    def setTags(self):
        res = requests.get(
            self.api_base + self.api_tags.format(self.my_site) + "?number=1000"
        )
        if res.ok:
            self.tags = json.loads(res.text)

    def getTags(self):
        return self.tags

    def checkTags(self, tags):
        if isinstance(tags, dict):
            tags = tags["tags"]
        idTags = []
        newTags = []
        if not self.tags:
            self.setTags()

        for tag in tags:
            payload = {"name": tag}
            # I'm trying to create, if not possible, they exist
            res = requests.post(
                self.api_base + self.api_tags.format(self.my_site) + "/new",
                headers=self.headers,
                data=payload,
            )
            reply = json.loads(res.text)

            if "ID" in reply:
                newTags.append(tag)
                idTags.append(reply["ID"])
            else:
                for ttag in self.tags["tags"]:
                    if ttag["name"] == tag:
                        idTags.append(ttag["ID"])
            if newTags:
                # Update list of tags
                self.setTags()

        return idTags

    def processReply(self, reply):
        res = reply
        logging.info("Res: %s" % res)
        if res.ok:
            resJ = json.loads(res.text)
            logging.debug("Res text: %s" % resJ)
            logging.debug("Res slug: %s" % resJ["generated_slug"])
            title = resJ["title"]["raw"]
            res = "{} - \n https://{}/{}".format(
                title, self.my_site, resJ["generated_slug"]
            )
        else:
            res = self.report(
                self.service, self, "", f"Res: {res} Fail! Failed authentication."
            )
        return res

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ""
        logging.info(f"    Publishing next post from {apiSrc} in " f"{self.service}")
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "Fail! No posts available"
        except:
            reply = self.report(self.service, apiSrc, "", sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        print(f"Args: {args} kwargs: {kwargs}")
        tags = []
        # if args and len(args)>3:
        #     tags = postData[3]
        if args and len(args) >= 3:
            try:
                title, link, comment, more = args
            except:
                title, link, comment = args
        if kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            pos = api.getLinkPosition(link)
            comment = api.getImagesCode(pos)
            tags = api.getImagesTags(pos)
            print(f"Comment: {comment}")

        if tags:
            idTags = self.checkTags(tags)
            logging.info("     Tags: {idTags}")
            idTags = ",".join(str(v) for v in idTags)
        else:
            idTags = ""
        print(f"title: {title}")
        print(f"link: {link}")
        print(f"content: {comment}")
        print(f"tags: {tags}")

        payload = {
            "title": title,
            "content": comment,
            "status": "publish",
            # One of: publish, future, draft, pending, private
            "tags": idTags,
        }
        res = requests.post(
            self.api_base2 + self.api_posts.format(self.my_site),
            headers=self.headers,
            data=payload,
        )
        print(f"Resss: {res}")
        return res

    # def publishPostt(self, post, link='', comment='', tags=[]):
    #     logging.debug("     Publishing in Wordpress...")
    #     title = post
    #     res = None
    #     try:
    #         logging.info("     Publishing: %s %s" % (post,str(tags)))
    #         print("     Publishing: %s %s" % (post,str(tags)))
    #         # The tags must be checked/added previously
    #         idTags = self.checkTags(tags)
    #         logging.info("     Publishing: %s %s" % (post,str(idTags)))
    #         print("     Publishing: %s %s" % (post,str(idTags)))
    #         # They must be in a comma separated string
    #         idTags = ','.join(str(v) for v in idTags)
    #         print("co",comment)
    #         payload = {"title":title,"content":comment,
    #                 "status":'publish',
    #                 # One of: publish, future, draft, pending, private
    #                 'tags':idTags}
    #         res = requests.post(self.api_base2
    #                 + self.api_posts.format(self.my_site),
    #                 headers = self.headers,
    #                 data = payload)
    #         print(res)
    #         if res.ok:
    #             logging.info("Res: %s" % res)
    #             resJ = json.loads(res.text)
    #             logging.debug("Res text: %s" % resJ)
    #             logging.info("Res slug: %s" % resJ['generated_slug'])
    #             return("{} - \n https://{}/{}".format(title,
    #                 self.my_site,
    #                 resJ['generated_slug']))
    #         else:
    #             tres = type(res)
    #             logging.info(f"Res: {res} type {tres}")
    #             print(f"Res: {res} type {tres}")
    #             return("Fail!")
    #     except KeyError:
    #         logging.info("Fail!")
    #         logging.info(self.report('KeyError Wordpress', post, link, sys.exc_info()))
    #         return(self.report('Wordpress', post, link, sys.exc_info()))
    #     except:
    #         logging.info("Fail!")
    #         logging.info(self.report('Wordpress', post, link, sys.exc_info()))
    #         return(self.report('Wordpress', post, link, sys.exc_info()))

    #     return 'OK'

    def getPostTitle(self, post):
        if "title" in post:
            return post["title"]
        else:
            return ""

    def getPostLink(self, post):
        if "URL" in post:
            return post["URL"]
        else:
            return ""

    def extractImages(self, post):
        res = []

        if "content" in post:
            soup = BeautifulSoup(post["content"], "lxml")
            imgs = soup.find_all("img")
            for img in imgs:
                logging.debug(f"extract img: {img}")
                src = img.get("src","")
                alt = img.get("alt","")
                if '(' in alt and ')' in alt:
                    posI = alt.find('(')
                    posF = alt.find(')')+1
                    title = alt[posI:posF]
                    res.append((src, src, title, alt))
                else:
                    res.append(img.get("data-large-file").split("?")[0])
        elif "attachments" in post:
            for key in post["attachments"]:
                if "URL" in post["attachments"][key]:
                    res.append(post["attachments"][key]["URL"])
        else:
            logging.info("Fail image")
            logging.debug("Fail image %s", post)
            res = []
        return res

    # def obtainPostData(self, i, debug=False):
    #     if not self.posts:
    #         self.setPosts()

    #     post = self.getPost(i)

    #     if post:
    #         logging.debug("Post i: {}, {}".format(i,post))

    #         theTitle = self.getTitle(i)
    #         theLink = self.getLink(i)
    #         firstLink = theLink
    #         if 'content' in post:
    #             content = post['content']
    #         else:
    #             content = theLink
    #         if 'excerpt' in post:
    #             theSummary = post['excerpt']
    #         else:
    #             theSummary = content
    #         theSummaryLinks = content
    #         theImage=self.getImages(i)

    #         theContent=''
    #         comment = ''
    #         theSummaryLinks = ""

    #         if not content.startswith('http'):
    #             soup = BeautifulSoup(content, 'lxml')
    #             link = soup.a
    #             if link:
    #                 firstLink = link.get('href')
    #                 if firstLink:
    #                     if firstLink[0] != 'h':
    #                         firstLink = theLink

    #         if not firstLink:
    #             firstLink = theLink

    #         theLinks = theSummaryLinks
    #         theSummaryLinks = theContent + theLinks

    #         theContent = ""
    #         theSummaryLinks = ""

    #         logging.debug("=========")
    #         logging.debug("Results: ")
    #         logging.debug("=========")
    #         logging.debug("Title:     ", theTitle)
    #         logging.debug("Link:      ", theLink)
    #         logging.debug("First Link:", firstLink)
    #         logging.debug("Summary:   ", content[:200])
    #         logging.debug("Sum links: ", theSummaryLinks)
    #         logging.debug("the Links"  , theLinks)
    #         logging.debug("Comment:   ", comment)
    #         logging.debug("Image;     ", theImage)
    #         logging.debug("Post       ", theTitle + " " + theLink)
    #         logging.debug("==============================================")
    #         logging.debug("")

    #         return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)
    #     else:
    #         logging.info("No post")
    #         return (None, None, None, None, None, None, None, None, None, None)


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    import moduleWordpress

    wp = moduleWordpress.moduleWordpress()
    wp.setClient("avecesunafoto")
    wp.setPostsType("posts")
    wp.setPosts()
    res = wp.getPosts()
    print(f"Res: {res}")
    if (not res) or (res[:4] == "Fail"):
        wp.authorize()
    res = wp.getPosts()

    return
    print("Testing tags")
    wp.setTags()
    print(wp.getTags())
    # print(wp.checkTags(['test']))

    print("Testing posts")
    wp.setPostsType("posts")
    wp.setPosts()
    for i, post in enumerate(wp.getPosts()):
        print("{}) {} {}".format(i, wp.getPostTitle(post), wp.getPostLink(post)))
        print(wp.obtainPostData(i))

    sel = input("Select one ")
    pos = int(sel)
    post = wp.getPost(pos)
    print("{}) {} {}".format(pos, wp.getPostTitle(post), wp.getPostLink(post)))
    wp.publishPost(wp.getPostTitle(post), wp.getPostLink(post), "")
    sys.exit()

    # wp.publishPost(post, '', title)

    # pos = wp.getLinkPosition('https://avecesunafoto.wordpress.com/2020/03/10/gamoncillo/')
    # img = wp.obtainPostData(pos)
    # print(img)
    # if img[3]:
    #    print(img[3])
    #    print(len(img[3]))
    ##for i in img[3]:
    #    #resizeImage(i)
    #    #input('next?')

    print("Testing posting")
    # print(title, post)

    sys.exit()

    sys.exit()
    for i, post in enumerate(wp.getPosts()):
        print("p", i, ") ", post)
        # print("@%s: %s" %(tweet[2], tweet[0]))

    print(pos)
    print(wp.getPosts()[pos])
    title = wp.obtainPostData(pos)
    sys.exit()
    print("Testing title and link")

    for i, post in enumerate(wp.getPosts()):
        title = wp.getPostTitle(post)
        link = wp.getPostLink(post)
        # url = tw.getPostUrl(post)
        print("{}) Title: {}\nLink: {}\nUrl:{}\n".format(i, title, link, link))

    print("Testing obtainPostData")
    for i, post in enumerate(wp.getPosts()):
        print(i, ") ", wp.obtainPostData(i))

    sys.exit()


if __name__ == "__main__":
    main()
