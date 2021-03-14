import configparser
import logging
import sys

import pytumblr

from configMod import *
from moduleContent import *
from moduleQueue import *

# Configuration
#
# [Buffer1]
# consumer_key:
# consumer_secret:
# oauth_token:
# oauth_secret:


class moduleTumblr(Content, Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.tc = None
        self.service = 'Tumblr'

    def getKeys(self, config):
        consumer_key = config.get("Buffer1", "consumer_key")
        consumer_secret = config.get("Buffer1", "consumer_secret")
        oauth_token = config.get("Buffer1", "oauth_token")
        oauth_secret = config.get("Buffer1", "oauth_secret")

        return (consumer_key, consumer_secret, oauth_token, oauth_secret)

    def initApi(self, keys):
        client = pytumblr.TumblrRestClient(keys[0], keys[1], keys[2], keys[3])
        tumblr = self.user
        if isinstance(tumblr, str):
            self.url = f"https://{tumblr}.tumblr.com/"
        elif isinstance(tumblr[1], str):
            self.url = f"https://{tumblr[1]}.tumblr.com/"
        elif isinstance(tumblr, tuple):
            self.url = f"https://{tumblr[1][1]}.tumblr.com/"
        logging.info(f"Url: {self.url}")

        return client

    def getBlogName(self):
        name = self.getUrl().split('/')[2]
        return name

    def setApiPosts(self):
        posts = self.setApiPublished()
        return posts

    def setApiPublished(self):
        posts = self.getClient().posts(self.getUrl().split('/')[2])
        if 'posts' in posts:
            posts = posts['posts']
        else:
            posts = []

        return (posts)

    def setApiDrafts(self):
        drafts = self.getClient().drafts(self.getUrl().split('/')[2])
        if 'posts' in drafts:
            posts = drafts['posts']
        else:
            posts = []
        return (posts)

    def setApiQueue(self):
        queue = self.getClient().queue(self.getUrl().split('/')[2])
        if 'posts' in queue:
            posts = queue['posts']
        else:
            posts = []
        return(posts)

    def getPostTitle(self, post):
        logging.debug(f"getPostTitle {post}")
        title = ""
        if post:
            if 'summary' in post:
                title = post['summary']
        return title

    def getPostLink(self, post):
        logging.debug(f"getPostUrl {post}")
        url = ""
        if post:
            if 'post_url' in post:
                url = post['post_url']
        return url

    def getPostId(self, post):
        logging.debug(f"getPostId {post}")
        idPost = ""
        if post:
            if 'id' in post:
                idPost = post['id']
        return idPost

    def getPostState(self, post):
        logging.debug(f"getPostState {post}")
        state = ""
        if post:
            if 'state' in post:
                state = post['state']
        return state

    def processReply(self, reply):
        logging.info("Res: %s" % reply)
        res = reply
        if 'id' in reply:
            logging.info("Res: %s" % reply['id'])
            res = f"{self.getUrl()}{reply['id']}"
        return res

    def publishApiPost(self, postData):
        if self.getPostsType() == 'post':
            res = self.getClient().create_link(self.getBlogName(),
                                               state='queue',
                                               title=postData[0],
                                               url=postData[1],
                                               description=postData[2])
        elif self.getPostsType() == 'queue':
            idPost = postData[1].split('/')[-2]
            logging.debug(f"idPost {idPost}")
            res = self.editApiStateId(idPost, 'published')
        else:
            res = self.getClient().create_link(self.getBlogName(),
                                               state='queue',
                                               title=postData[0],
                                               url=postData[1],
                                               description=postData[2])

        return(res)

    def publish(self, j):
        # This is not publishing but changing state -> editing
        logging.info(f"Publishing {j}")
        logging.info(f"servicename {self.service}")
        if hasattr(self, 'getPostsType') and (self.getPostsType() == 'queue'):
            logging.info(f"Publishing queued state {j}")
            res = self.do_edit(j, newState='published')
        else:
            # Not tested
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks,
             content, links, comment) = self.obtainPostData(j)
            logging.info("Publishing {} {}".format(title, link))
            res = self.publishPost(title, link, comment)

        return(res)

    def editApiTitle(self, post, newTitle):
        idPost = post['id']
        typePost = post['type']
        res = self.getClient().edit_post(self.getBlogName(), id=idPost,
                                         type=typePost, title=newTitle)
        return res

    def editApiStateId(self, idPost, newState):
        res = self.getClient().edit_post(self.getBlogName(),
                                         id=idPost, state=newState)
        return (res)

    def editApiState(self, post, newState):
        idPost = post['id']
        res = self.editApiStateId(idPost, newState)
        return res

    def deleteApi(self, j):
        idPost = self.getId(j)
        logging.info("Deleting post %s" % idPost)
        return self.getClient().delete_post(self.getBlogName(), idPost)


def main():

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(message)s'
        )

    import moduleTumblr

    t = moduleTumblr.moduleTumblr()

    t.setClient('fernand0')
    t.setPostsType('posts')
    t.setPosts()
    print(t.getPosts())
    sys.exit()

    t.setPostsType('queue')

    t.setPosts()
    i = 0
    print(t.getPosts())
    for i, p in enumerate(t.getPosts()):
        print(i, t.getPostTitle(p), t.getPostLink(p))
    print(len(t.getPosts()))
    print(t.getPostTitle(t.getPosts()[i]))
    print(t.getPostLink(t.getPosts()[i]))
    print(t.getPostId(t.getPosts()[i]))
    print(t.publish(i))
    sys.exit()

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    section = 'Blog2'
    url = config.get(section, "url")
    rssFeed = config.get(section, "rss")
    logging.info(f" Blog RSS: {rssFeed}")
    import moduleRss
    blog = moduleRss.moduleRss()
    # It does not preserve case
    blog.setRssFeed(rssFeed)
    blog.setUrl(url)
    blog.setPosts()
    post = blog.obtainPostData(1)

    title = post[0]
    link = post[1]
    content = post[7]
    links = post[8]
    t.publishPost(title, link, content)


if __name__ == '__main__':
    main()
