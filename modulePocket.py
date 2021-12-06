#!/usr/bin/env python

import configparser
import os

from pocket import Pocket, PocketException

from configMod import *
from moduleContent import *
from moduleQueue import *

class modulePocket(Content,Queue):

    def __init__(self):
        super().__init__()
        self.postaction='archive'

    def getKeys(self, config):
        consumer_key = config.get("appKeys", "consumer_key")
        access_token = config.get("appKeys", "access_token")

        return(consumer_key, access_token)

    def initApi(self, keys):
        consumer_key, access_token = keys
        client = Pocket(consumer_key=consumer_key, access_token=access_token)
        return client

    def setApiPosts(self):
        posts = []
        dictPosts = self.client.retrieve()
        dictPosts = dictPosts['list']
        for post in dictPosts:
            posts.append(dictPosts[post])

        return(posts[:100])

    def processReply(self, reply):
        res = ''
        if reply:
            idPost = self.getPostId(reply)
            title = self.getPostTitle(reply)
            res = f"{title} https://getpocket.com/read/{idPost}"
        logging.info(f"     Res: {res}")
        return(res)

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            post, link, comment = args
            logging.debug(f"args: {args} in {self}")
        if kwargs:
            more = kwargs
            logging.debug(f"postData: {more} in {self}")

        # This belongs here?
        if not link.startswith('http'):
            logging.warning(f"Link that does not stat with < {link}")
            pos = link.find('http')
            link = link[pos:]
            pos = link.find(' ')
            if pos >=0:
                # Sometimes there are two links or something after the link
                link=link[:pos]
        res = self.getClient().add(link)
        return self.processReply(res)

    def publish(self, j):
        # This does not belong here
        logging.info("...Publishing %d"% j)
        #post = self.obtainPostData(j)
        #logging.info("Publishing %s"% post[0])
        update = ''
        title = self.getTitle(j)
        logging.info("Title: %s" % str(title))
        url = self.getLink(j)
        logging.info("Url: %s" % str(url))

        if self.getProgram():
            logging.info("getProgram")
            for profile in self.getSocialNetworks():
                nick = self.getSocialNetworks()[profile]
                logging.info("Social: {} Nick: {}".format(profile, nick))
                if ((profile[0] in self.getProgram()) or
                        (profile in self.getProgram())):
                    logging.info("Social: {} Nick: {}".format(profile, nick))
                    lenMax = self.len(profile)
                    socialNetwork = (profile, nick)

                    listP = self.cache[socialNetwork].setPosts()
                    listP = self.cache[socialNetwork].getPosts()
                    listPsts = self.obtainPostData(j)
                    listP = listP + [listPsts]
                    self.cache[socialNetwork].posts = listP
                    update = update + self.cache[socialNetwork].updatePostsCache()
                    logging.info("Uppdate: {}".format(update))
                    update = update + '\n'

        if  not self.getProgram(): #not self.getBuffer() and
            logging.info("Not getBuffer, getProgram {}".format(self.getSocialNetworks()))
            return ""
            delayedBlogs = []
            nowait = True
            for profile in self.getSocialNetworks():
                nick = self.getSocialNetworks()[profile]
                logging.info("Social: {} Nick: {}".format(profile, nick))
                listPosts = [ post ]
                socialNetwork = (profile, nick)
                link = self.addNextPosts(listPosts, socialNetwork)
                delayedBlogs.append((self, socialNetwork, 1, nowait, 0))

                import concurrent.futures
                import moduleSocial
                import time
                with concurrent.futures.ThreadPoolExecutor(
                        max_workers=len(delayedBlogs)) as executor:
                    delayedPosts = {executor.submit(moduleSocial.publishDelay,
                        *args):
                        args for args in delayedBlogs}
                    time.sleep(5)

                    for future in concurrent.futures.as_completed(delayedPosts):
                        dataBlog = delayedPosts[future]
                        try:
                            res = future.result()
                            if res:
                                print("  Published: %s"% str(res))
                                if not dataBlog[0].getProgram():
                                    posL = res.find('http')
                                    if posL>=0:
                                        link = res[posL:]
                                        if link:
                                            socialNetwork = dataBlog[1]
                                            updateLastLink(dataBlog[0].getUrl(),
                                                    link, socialNetwork)

                        except Exception as exc:
                            print('{} generated an exception: {}'.format(
                                str(dataBlog), exc))

    def archive(self, j):
        logging.info("Archiving %d"% j)
        client = self.client
        post = self.getPost(j)
        title = self.getPostTitle(post)
        logging.info("Post {}".format(str(post)))
        logging.info("Title {}".format(title))
        try:
            res = client.archive(int(self.getPostId(post)))
            res = client.commit()
            logging.info("Post id res {}".format(str(res)))
            logging.info("Post id res {}".format(str(res["action_results"])))
            if res['action_results']:
                rep = f"Archived {title}"
                self.posts = self.posts[:j] + self.posts[j+1:]
            else:
                rep = "Fail!"
        except:
            logging.warning("Archiving failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            rep = "Fail"
        return rep

    def delete(self, j):
        logging.info("Deleting %d"% j)
        client = self.client
        post = self.getPost(j)
        title = self.getPostTitle(post)
        logging.info("Post {}".format(str(post)))
        logging.info("Title {}".format(title))
        res = client.delete(int(self.getPostId(post)))
        res = client.commit()
        logging.info("Post id res {}".format(str(res)))
        logging.info("Post id res {}".format(str(res["action_results"])))
        if res['action_results']:
            rep = f"Deleted {title}"
        else:
            rep = "Fail!"
        return rep

    def getPostTitle(self, post):
        title = ''
        if 'resolved_title' in post:
            title = post['resolved_title']
            if not title and ('given_title' in post):
                title = post['given_title']
        #elif 'item' in post:
        #    if 'title' in post['item']:
        #        title = (post['item']['title'])
        if not title:
            title = self.getPostLink(post)
        return title

    def getPostId(self, post):
        if 'item' in post:
            if 'item_id' in post['item']:
                return(post['item']['item_id'])
        else:
            return ''

    def getPostLink(self, post):
        link = ''
        if 'resolved_url' in post:
            link = post['resolved_url']
            if not link and 'given_url' in post:
                link = post['given_url']
        return link


    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary,
                content, theSummaryLinks, theContent, theLinks, comment) = (
                        None, None, None, None, None,
                        None, None, None, None, None)

        if i < len(self.getPosts()):
            theTitle = self.getTitle(i)
            theLink = self.getLink(i)

            theLinks = None
            content = None
            theContent = None
            firstLink = theLink
            theImage = None
            theSummary = None

            theSummaryLinks = None
            comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.INFO,
            format='%(asctime)s %(message)s')

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs2')

    import modulePocket

    p = modulePocket.modulePocket()

    p.setClient('ftricas')
    p.setPostsType('posts')

    p.setPosts()
    print(p.getPosts())
    return

    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')
    sys.exit()

    for i, post in enumerate(p.getPosts()):
        print(i, p.getPostTitle(post), p.getPostLink(post))

    sys.exit()
    #i=7
    #print(i,p.getTitle(i))

    p.setSocialNetworks(config)
    print(p.getSocialNetworks())
    p.publish(99)

    sys.exit()

    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')

if __name__ == '__main__':
    main()

