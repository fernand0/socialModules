#!/usr/bin/env python

import configparser
import os
import pickle
import sys
import time
import urllib

import click
import gitterpy
import gitterpy.client
import requests
from bs4 import BeautifulSoup

from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class moduleGitter(Content): #,Queue):

    def getKeys(self, config):
        token = config.get(self.service, "token")
        oauth_key = config.get(self.service, "oauth_key")
        oauth_secret = config.get(self.service, "oauth_secret")

        return (token, oauth_key, oauth_secret)

    def initApi(self, keys):
        self.service = None
        self.client = None
        self.channel = None
        self.keys = []
        self.service = 'Gitter'

        self.token = keys[0]
        # logging.info("     Connecting {}".format(self.service))
        try:
            client = gitterpy.client.GitterClient(self.token)
        except:
            msgLog = ("Account not configured")
            logMsg(msgLog, 3, 0)
            if sys.exc_info()[0]:
                # logging.warning("Unexpected error: {}".format(
                #     sys.exc_info()[0]))
                self.report(self.service, "", "", sys.exc_info())
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)
            # logging.info(self.report('Slack', text, sys.exc_info()))
            client = slack.WebClient(token=self.slack_token)
        return client

    def getChannels(self):
        return self.getClient().rooms.rooms_list

    def setChannel(self, channel=''):
        if not channel:
            # The first one
            channel = self.getChannels()[0].get('name','')
        # setPage in Facebook
        # We should follow more the model there
        self.channel = channel

    def getChannel(self):
        return self.channel

    def setApiPosts(self):
        if not self.channel:
            # It will set the owner channel by default
            msgLog = (f"No channel defined, setting the first one (if any)")
            logMsg(msgLog, 3, 0)
            self.setChannel()
        posts = []
        try:
            if self.getClient():
                history = self.getClient().messages.list(self.getChannel())
                posts = history
        except:
            self.report(self.service, "", "", sys.exc_info())

        return posts

    # Duplicate code? Available in moduleContent
    # def getIdPosition(self, idPost):
    #     posts = self.getPosts()
    #     if posts:
    #         for i, entry in enumerate(posts):
    #             idS = idPost
    #             myIdPost = self.getPostId(entry)
    #             if idS == myIdPost:
    #                 pos = i
    #         return (pos)
    #     else:
    #         return -1

    def getPostContentHtml(self, post):
        return post.get('html', '')

    def editApiLink(self, post, newLink):
        #FIXME. To be done
        pass

    def setPostTitle(self, post, newTitle):
        # Only in local memory
        pos = post.get('text','').rfind('http')
        title = newTitle
        if pos>=0:
            title = f"{title} {post.get('text','')[pos:]}"
            post['text'] = title

    def getApiPostTitle(self, post):
        title = post.get("text", "")
        pos = title.rfind("http")
        if pos >= 0:
            title = title[:pos]
        return title

    def getApiPostLink(self, post):
        link = ''
        text = post.get('text','')
        pos = text.rfind('http')
        if pos>=0:
            link = text[pos:]
        return link

    def getPostId(self, post):
        idPost = post.get('id','')
        return (idPost)

    def deleteApiPosts(self, idPost):
        result = self.deteleGitter(idPost, self.getChannel())
        # logging.info(f"Res: {result}")
        return(result)

    def deleteGitter(self, idPost, idChannel):
        # This does not belong here
        # '/v1/rooms/:roomId/chatMessages/:chatMessageId"
        # call = f"https://api.gitter.im/v1/{api_meth}"
        #api_meth = 'rooms/{}/chatMessages/{}'.format(room_id, idPost)
        api_meth  = self.getClient().get_and_update_msg_url(idChannel, idPost)
        result = self.getClient().delete(api_meth)
        # logging.info("Result: {}".format(str(result)))
        return result

    def deleteApiPosts(self, idPost):
        theChan = self.getChannel()
        # idChannel = self.getChanId(theChan)
        # logging.info(f"Chan: {theChan}")
        idChannel = theChan
        res = self.deleteGitter(idPost, idChannel)
        return res

    # def deletePost(self, idPost, idChannel):
    #     #theChannel or the name of the channel?
    #     logging.info("Deleting id %s from %s" % (idPost, idChannel))
    #     logging.info(f"Chan: {idChannel}")
    #     # idChannel = self.getChanId(idChannel)
    #     # logging.info(f"Chan: {idChannel}")
    #     try:
    #         result = self.deleteGitter(idPost, idChannel)
    #     except:
    #         logging.info(self.report('Gitter',
    #                         "Error deleting", "", sys.exc_info()))
    #         result= ""
    #     logging.debug(result)
    #     return(result)

    def getChanId(self, name):
        msgLog = ("{self.indent} getChanId {self.service}")
        logMsg(msgLog, 2, 0)

        chanList = self.getClient().rooms.rooms_list
        for channel in chanList:
            if channel.get('name', '').endswith(name):
                return(channel['id'])
        return(None)

    # def extractDataMessage(self, i):
    #     logging.info(f"extract gitt {i}")
    #     logging.info("Extract Service %s"% self.service)
    #     (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None)

    #     if i < len(self.getPosts()):
    #         post = self.getPosts()[i]
    #         theTitle = self.getPostTitle(post)
    #         theLink = self.getPostLink(post)
    #         print("The title: {theTitle}")

    #         theLinks = ''
    #         content = ''
    #         theContent = ''
    #         firstLink = theLink
    #         theImage = ''
    #         theSummary = ''

    #         theSummaryLinks = ''
    #         comment = ''

    #     print (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)
    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


    def processReply(self, reply):
        # logging.info(reply)
        reply = reply.get('id', '')
        return reply

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, link, comment = args
        if kwargs:
            more = kwargs

            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            comment = api.getPostComment(title)

        chan = self.getChannel()
        result = self.getClient().messages.send(chan, f"{title} {link}")
        return(result)

    def getBots(self, channel='tavern-of-the-bots'):
        # FIXME: this does not belong here
        if not self.posts:
            self.setPosts(channel)
        msgs = {}
        for msg in self.getPosts():
            if msg['text'].find('Hello')>=0:
                posN = msg['text'].find('Name:')+6
                posFN = msg['text'].find('"',posN)
                posI = msg['text'].find('IP:')+4
                posFI = msg['text'].find(' ',posI+1)-1
                posC = msg['text'].find('[')
                name = msg['text'][posN:posFN]
                ip = msg['text'][posI:posFI]
                command = msg['text'][posC+1:posC+2]
                if name not in msgs:
                    theTime = msg['sent'][:10]
                    msgs[name] = (ip, command, theTime)
        theBots = []
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a,b,c,name))
        return(theBots)

def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.INFO,
            format='%(asctime)s %(message)s')

    import moduleGitter
    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    # src: ('gitter', 'set', 'https://gitter.im/fernand0errbot/', 'posts')
    # more: {'url': 'https://gitter.im/fernand0errbot/', 'service': 'gitter', 'cache': 'twitter\nfacebook\ntelegram', 'twitter': 'fernand0Test', 'facebook': 'Fernand0Test', 'telegram': 'testFernand0', 'buffermax': '9'}
    # Not needed, it can be {}

    indent = ""
    for src in rules.rules.keys():
        if src[0] == 'gitter':
            more = rules.more[src]
            break
    apiSrc = rules.readConfigSrc(indent, src, more)

    apiSrc.setUser(apiSrc.getClient().auth.get_my_id['name'])

    testingSetTitle = False
    if testingSetTitle:
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('fernand0errbot/links')
        apiSrc.setPosts()
        if apiSrc.getPosts():
            print(f"Title: {apiSrc.getPostTitle(apiSrc.getPost(0))}")
            newTitle = input(f"New title? ")
            apiSrc.setPostTitle(apiSrc.getPost(0), newTitle)
            print(f"Title: {apiSrc.getPostTitle(apiSrc.getPost(0))}")

        return

    testingPosts = False
    if testingPosts:
        print("Testing posts")
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('fernand0errbot/links')
        apiSrc.setPosts()

        print("Testing title and link")

        for i, post in enumerate(apiSrc.getPosts()):
            print(f"Post: {post}")
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            url = apiSrc.getPostUrl(post)
            theId = apiSrc.getPostId(post)
            summary = apiSrc.getPostContentHtml(post)
            image = apiSrc.getPostImage(post)
            print(f"{i}) Title: {title}\n"
                  f"Link: {link}\n"
                  f"Url: {url}\nId: {theId}\n"
                  f"Content: {summary} {image}")

        if input("All? (y/n) ") == 'y':
            for channel in apiSrc.getChannels():
                print(f"Name: {channel['name']}")
                apiSrc.setChannel(channel['name'])
                apiSrc.setPosts()
                for i, post in enumerate(apiSrc.getPosts()):
                    print(f"{i}) Title: {apiSrc.getPostTitle(post)}\n"
                          f"Link: {apiSrc.getPostLink(post)}\n")
                input("More? (any key to continue) ")

        return

    testingDelete = True
    if testingDelete:
        print(f"Channels")
        [ print(f"{i}) {channel.get('name','')}")
            for i, channel in enumerate(apiSrc.getChannels()) ]
        pos = input("Which channel (number)? ")
        apiSrc.setChannel(apiSrc.getChannels()[int(pos)].get('name',''))

        apiSrc.setPosts()

        [ print(f"{i}) {apiSrc.getPostTitle(post)}")
                for i, post in enumerate(apiSrc.getPosts()) ]
        pos = input("Which post to delete? ")
        post = apiSrc.getPost(int(pos))
        apiSrc.deletePost(post)

        return

    return

    testingSlack = False
    if testingSlack:
        import moduleSlack

        siteS = moduleSlack.moduleSlack()
        try:
            # My own config settings
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + "/.rssBlogs")

            section = "Blog7"
            url = config.get(section, "url")
            siteS.setSocialNetworks(config)
            print(f"social: {siteS.getSocialNetworks()}")
        except:
            url = "http://fernand0-errbot.slack.com/"
        siteS.setClient(url)
        siteS.setChannel("links")
        siteS.setPosts()
        for post in reversed(siteS.getPosts()):
            link = siteS.getPostLink(post)
            title = siteS.getPostTitle(post)
            print(f"Link: {link} {title}")
            print(f"Reply: {site.publishPost(title, link, '')}")
            time.sleep(5)
        sys.exit()

    testingDeleteGitter = False
    if testingDeleteGitter:
        site.setPosts()
        for post in site.getPosts():
            print(f"Post: {post} {site.getChannel()}")
            input("Delete? ")
            site.deletePost(site.getPostId(post), site.getChannel())
        sys.exit()

    testingPostDelete = True
    if testingPostDelete:
        rep = site.publishPost(CHANNEL, 'helloo')

        site.setPosts()
        print(len(site.getPosts()))
        post = site.getPosts()[-1]
        print(post)
        print("----------------")
        print("title {}".format(site.getPostTitle(post)))
        link = site.getPostLink(post)
        print("link {}".format(link))
        print(site.getLinkPosition(link))
        input("Delete? ")
        site.deletePost(site.getPostId(post), CHANNEL)
        return

    site.setPosts()
    post = site.getPosts()[-1]
    print("----------------")
    print("title {}".format(site.getPostTitle(post)))
    link = site.getPostLink(post)
    print("link {}".format(link))
    print(site.getLinkPosition(link))

    sys.exit()

    print(CHANNEL)
    site.deletePost(site.getPostId(post), site.getChanId(CHANNEL))
    rep = site.publishPost(CHANNEL, 'helloo')
    print(rep)

    print(site.extractDataMessage(4))

    sys.exit()
    res=site.search('links', 'https://www.pine64.org/2020/01/24/setting-the-record-straight-pinephone-misconceptions/a')
    print("res",res)
    print("res",res['messages']['total'])
    print(site.getPosts())
    post = site.getPosts()[0]
    print(site.getPostTitle(post))
    print(site.getPostLink(post))
    rep = site.publishPost('tavern-of-the-bots', 'hello')
    wait = input('Delete %s?' % rep)
    theChan = site.getChanId('tavern-of-the-bots')
    rep = site.deletePost(rep['ts'], theChan)

    sys.exit()

    site.setPosts('links')
    site.setPosts('tavern-of-the-bots')
    print(site.getPosts())
    print(site.getBots())
    print(site.getClient().api_call('channels.list'))
    sys.exit()
    rep = site.publishPost('tavern-of-the-bots', 'hello')
    site.deletePost(rep['ts'], theChan)
    sys.exit()

    site.setSocialNetworks(config)

    if ('buffer' in config.options(section)):
        site.setBufferapp(config.get(section, "buffer"))

    if ('cache' in config.options(section)):
        site.setProgram(config.get(section, "cache"))

    theChannel = site.getChanId("links")

    i = 0
    listLinks = ""

    lastUrl = ''
    for i, post in enumerate(site.getPosts()):
        url = site.getLink(i)
        if urllib.parse.urlparse(url).netloc == lastUrl:
            listLinks = listLinks + "%d>> %s\n" % (i, url)
        else:
            listLinks = listLinks + "%d) %s\n" % (i, url)
        lastUrl = urllib.parse.urlparse(url).netloc
        print(site.getTitle(i))
        print(site.getLink(i))
        print(site.getPostTitle(post))
        print(site.getPostLink(post))
        i = i + 1

    numEntries = i
    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == 'x':
        sys.exit()

    elem = int(i)
    print(site.getPosts()[elem])

    action = input("Delete [d], publish [p], exit [x] ")

    if action == 'x':
        sys.exit()
    elif action == 'p':
        if site.getBufferapp():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getBufferapp():
                    lenMax = site.len(profile)
                    print("   getBuffer %s" % profile)
                    socialNetwork = (profile,site.getSocialNetworks()[profile])
                    title = site.getTitle(elem)
                    url = site.getLink(elem)
                    listPosts = []
                    listPosts.append((title, url))
                    site.buffer[socialNetwork].addPosts(listPosts)

        if site.getProgram():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getProgram():
                    lenMax = site.len(profile)
                    print("   getProgram %s" % profile)

                    socialNetwork = (profile,site.getSocialNetworks()[profile])

                    listP = site.cache[socialNetwork].getPosts()
                    #site.cache[socialNetwork].posts = site.cache[socialNetwork].posts[:8]
                    #listP = site.cache[socialNetwork].getPosts()
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #site.cache[socialNetwork].updatePostsCache()
                    listPsts = site.obtainPostData(elem)
                    listP = listP + [listPsts]
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #sys.exit()
                    site.cache[socialNetwork].posts = listP
                    site.cache[socialNetwork].updatePostsCache()
        t = moduleTumblr.moduleTumblr()
        t.setClient('fernand0')
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        t.publishPost(title, url, '')

    site.deletePost(site.getId(j), theChannel)
    #print(outputData['Slack']['pending'][elem][8])


if __name__ == '__main__':
    main()
