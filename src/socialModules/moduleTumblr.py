import configparser
import sys

import pytumblr

from socialModules.configMod import CONFIGDIR, logMsg
from socialModules.moduleContent import Content

# from socialModules.moduleQueue import *

# Configuration
#
# [Buffer1]
# consumer_key:
# consumer_secret:
# oauth_token:
# oauth_secret:


class moduleTumblr(Content):  # , Queue):
    def getKeys(self, config):
        consumer_key = config.get("Buffer1", "consumer_key")
        consumer_secret = config.get("Buffer1", "consumer_secret")
        oauth_token = config.get("Buffer1", "oauth_token")
        oauth_secret = config.get("Buffer1", "oauth_secret")

        return (consumer_key, consumer_secret, oauth_token, oauth_secret)

    def initApi(self, keys):
        self.service = "Tumblr"

        client = pytumblr.TumblrRestClient(keys[0], keys[1], keys[2], keys[3])
        # print(f"client: {client}")
        tumblr = self.user
        msgLog = f"{self.indent} Service {self.service} user {self.user}"
        logMsg(msgLog, 1, False)
        if isinstance(tumblr, str):
            self.url = f"https://{tumblr}.tumblr.com/"
        elif isinstance(tumblr[1], str):
            self.url = f"https://{tumblr[1]}.tumblr.com/"
        elif isinstance(tumblr, tuple):
            self.url = f"https://{tumblr[1][1]}.tumblr.com/"
        # msgLog = (f"{self.indent} Url: {self.url}")
        # logMsg(msgLog, 2, False)

        return client

    def getBlogName(self):
        name = self.getUrl().split("/")[2]
        return name

    def setNick(self, nick=None):
        if not nick:
            nick = self.getUrl()
            nick = nick.split("/")[2].split(".")[0]
        self.nick = nick

    def setApiPosts(self):
        posts = self.setApiPublished()
        return posts

    def setApiPublished(self):
        posts = self.getClient().posts(self.getUrl().split("/")[2])
        if "posts" in posts:
            posts = posts["posts"]
        else:
            posts = []

        return posts

    def setApiDrafts(self):
        drafts = self.getClient().drafts(self.getUrl().split("/")[2])
        if "posts" in drafts:
            posts = drafts["posts"]
        else:
            posts = []
        return posts

    def setApiQueue(self):
        posts = []
        if self.getClient():
            queue = self.getClient().queue(self.getUrl().split("/")[2])
            if "posts" in queue:
                posts = queue["posts"]

        return posts

    def getPostAction(self):
        # We won't delete posts from tumblr
        postaction = ""
        if hasattr(self, "postaction"):
            postaction = self.postaction
        return postaction

    def getApiPostTitle(self, post):
        msgLog = f"{self.indent} getPostTitle {post}"
        logMsg(msgLog, 2, False)
        title = ""
        if post:
            if "summary" in post:
                title = post["summary"]
        return title

    def getApiPostLink(self, post):
        link = ""
        if post and 'url' in post:
            link = self.getAttribute(post, "url")

        return link

    def getPostContent(self, post):
        result = ""
        if post and "body" in post:
            result = self.getAttribute(post, "body")
        return result

    def getApiPostUrl(self, post):
        url = ""
        if post:
            if "post_url" in post:
                url = post["post_url"]
        return url

    def getPostId(self, post):
        msgLog = f"{self.indent} getPostId {post}"
        logMsg(msgLog, 2, False)
        idPost = ""
        if post:
            if "id" in post:
                idPost = post["id"]
        return idPost

    def getPostState(self, post):
        msgLog = f"{self.indent} getPostState {post}"
        logMsg(msgLog, 2, False)
        state = ""
        if post:
            if "state" in post:
                state = post["state"]
        return state

    def processReply(self, reply):
        msgLog = f"{self.indent} Res: %s" % reply
        logMsg(msgLog, 2, False)
        res = reply
        if "id" in reply:
            try:
                # msgLog = (f"{self.indent} Res: {reply['id']}")
                # logMsg(msgLog, 2, False)
                res = f"OK! https://{self.service}.com/{self.user}/{reply['id']}"
            except:
                msgLog = f"{self.indent} Temporal: error {reply}"
                logMsg(msgLog, 3, False)
        elif "errors" in reply:
            res = f"failed! {res.get('errors','')} {reply}"
        elif ("meta" in reply and 'status' in reply['meta']
              and 'Forbidden' in reply['meta']['msg']):
            res = f"Fail! {res.get('meta','')} {reply}"

        return res

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ""
        msgLog = (
            f"{self.indent} Publishing next post from {apiSrc} in " f"{self.service}"
        )
        logMsg(msgLog, 2, False)
        try:
            post = apiSrc.getNextPost()
            msgLog = f"{self.indent} Next post from {apiSrc} is {post}"
            logMsg(msgLog, 2, False)
            if post:
                reply = self.publishApiPost(api=apiSrc, post=post)
            else:
                reply = "No posts available"
        except:
            reply = self.report(self.service, post, apiSrc, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        title, link, comment, idPost = "", "", "", None

        if args and len(args) == 3 and args[0]:
            title, link, comment = args
            api = self
            idPost = link.split("/")[-2] if link else None
        elif kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = more.get("comment", "")
            idPost = api.getPostId(post)

        try:
            res = None
            if api.getPostsType() == "posts":
                logMsg(f"Creating link post: Title: {title} Link: {link} Comment: {comment}", 1, 0)
                res = self.getClient().create_link(
                    self.getUser(), state="queue", title=title, url=link, description=comment, type='link'
                )
            elif api.getPostsType() == "queue" and idPost:
                logMsg(f"Publishing from queue: {idPost}", 1, 0 )
                res = self.editApiStateId(idPost, "published")
            elif title and link:
                logMsg(f"Creating default link post: Title: {title} Link: {link} Comment: {comment}", 1, 0)
                res = self.getClient().create_link(
                    self.getUser(), state="queue", title=title, url=link, description=comment
                )
            else:
                self.res_dict["error_message"] = "Not enough information to publish."
                return self.res_dict

            self.res_dict["raw_response"] = res
            if res and ('id' in res or 'posts' in res):
                self.res_dict["success"] = True
                # Tumblr API doesn't consistently return a direct post URL here
                # The blog name and post ID are available to construct one if needed.
                # For now, we'll leave post_url empty.
            else:
                 self.res_dict["error_message"] = f"Tumblr API error: {res}"

        except ConnectionError as e:
            self.res_dict["error_message"] = self.report("Tumblr", post, link, sys.exc_info())
            self.res_dict["raw_response"] = e
        except Exception as e:
            self.res_dict["error_message"] = f"An unexpected error occurred: {e}"
            self.res_dict["raw_response"] = e

        return self.res_dict

    def publishh(self, j):
        # This is not publishing but changing state -> editing
        # logging.info(f"Publishing {j}")
        # logging.info(f"servicename {self.service}")
        res = ""
        if hasattr(self, "getPostsType") and (self.getPostsType() == "queue"):
            msgLog = f"Publishing queued state {j}"
            logMsg(msgLog, 1, False)

            # res = self.do_edit(j, newState='published')
        else:
            # Not tested
            (
                title,
                link,
                firstLink,
                image,
                summary,
                summaryHtml,
                summaryLinks,
                content,
                links,
                comment,
            ) = self.obtainPostData(j)
            # logging.info("Publishing {} {}".format(title, link))
            # res = self.publishPost(title, link, comment)

        return res

    def editApiTitle(self, post, newTitle):
        idPost = post["id"]
        typePost = post["type"]
        res = self.getClient().edit_post(
            self.getBlogName(), id=idPost, type=typePost, title=newTitle
        )
        return res

    def editApiStateId(self, idPost, newState):
        res = self.getClient().edit_post(self.getBlogName(), id=idPost, state=newState)
        return res

    def editApiState(self, post, newState):
        idPost = post["id"]
        res = self.editApiStateId(idPost, newState)
        return res

    def deleteApi(self, j):
        idPost = self.getId(j)
        msgLog = f"{self.indent} Deleting post %s" % idPost
        logMsg(msgLog, 1, False)
        return self.getClient().delete_post(self.getBlogName(), idPost)

    def deleteApiQueue(self, idPost):
        msgLog = "{self.indent} Deleting from queue %s" % idPost
        logMsg(msgLog, 1, False)
        return self.getClient().delete_post(self.getBlogName(), idPost)

    def register_specific_tests(self, tester):
        tester.add_test("View dashboard", self.test_view_dashboard)

    def get_user_info(self, client):
        return client.info()['user']['name']

    def get_post_id_from_result(self, result):
        return result['id']

    def test_view_dashboard(self, apiSrc):
        posts = apiSrc.getClient().dashboard()['posts']
        for i, post in enumerate(posts[:5]):
            print(f"\n{i+1}. {post['blog_name']} - {post.get('summary', 'No summary')}")
            print(f"   Link: {post['post_url']}")

def main():
    import logging
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    tumblr_module = moduleTumblr()
    tester = ModuleTester(tumblr_module)
    tester.run()


if __name__ == "__main__":
    main()
