import configparser
import sys
import time

from imgurpython import ImgurClient

from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class moduleImgur(Content): #, Queue):

    def getKeys(self, config):
        if self.user.find('http')>=0:
            user = self.user.split('/')[-1]
        else:
            user = self.user
        client_id = config.get(user, 'client_id')
        client_secret = config.get(user, 'client_secret')
        access_token = config.get(user, 'access_token')
        refresh_token = config.get(user, 'refresh_token')

        return (client_id, client_secret, access_token, refresh_token)

    def initApi(self, keys):
        self.service = 'Imgur'

        self.nick = self.user.split('/')[-1]
        client_id = keys[0]
        client_secret = keys[1]
        access_token = keys[2]
        refresh_token = keys[3]

        try:
            client = ImgurClient(client_id, client_secret,
                             access_token, refresh_token)
        except:
            client = None
            reply = self.report(self.service, '', '', sys.exc_info())

        return client

    def setApiPosts(self):
        posts = []
        client = self.getClient()
        # msgLog = (f"{self.indent} Client: {client} {self.user} ")
        # logMsg(msgLog, 2, 0)
        if self.user.find('https')>=0:
            # FIXME. This should be a method
            user = self.user.split('/')[-1]
        else:
            user = self.user

        # msgLog = (f"{self.indent} User: {user}")
        # logMsg(msgLog, 2, 0)

        if client:
            albums = None
            try:
                albums = client.get_account_albums(user)
            except:
                msgLog = (f"{self.indent} Failed connection")
                logMsg(msgLog, 1, 1)

            if albums:
                for album in albums:
                    # msgLog = (f"{self.indent} Title: "
                    #           f"{time.ctime(album.datetime)} "
                    #           f"{album.title}")
                    # logMsg(msgLog, 2, 0)
                    if album.in_gallery:
                        posts.append(album)
        else:
            msgLog = (f'{self.indent} setApiPosts No client configured!')
            logMsg(msgLog, 3, 0)
        return (posts)

    def setApiDrafts(self):
        posts = []
        client = self.getClient()
        # msgLog = (f"{self.indent} Client: {client}")
        # logMsg(msgLog, 2, 0)
        # msgLog = (f"{self.indent} User: {self.user}")
        # logMsg(msgLog, 2, 0)

        if client:
            if self.user.find('http')>= 0:
                user = self.user.split('/')[-1]
            else:
                user = self.user

            # msgLog = (f"{self.indent} User: {user}")
            # logMsg(msgLog, 2, 0)
            try:
                albums = client.get_account_albums(user)
            except:
                msgLog = (f"{self.indent} Error getting albums")
                logMsg(msgLog, 3, 1)
                albums = []

            for album in albums:
                # info = f"{time.ctime(album.datetime)} {album.title}"
                # msgLog = (f"{self.indent} Info: {info}")
                # logMsg(msgLog, 2, 0)
                if not album.in_gallery:
                    info = f"{time.ctime(album.datetime)} {album.title}"
                    msgLog = (f"{self.indent} Info: {info}")
                    posts.append(album)
                    # logging.info(f"Draft: {info}")
        else:
            msgLog = (f'{self.indent} setApiDrafts No client configured!')
            logMsg(msgLog, 3, 0)

        return (posts)

    def editApiTitle(self, post, newTitle):
        idPost = self.getPostId(post)
        fields = {'ids': None, 'title': newTitle}
        # 'ids' parameter is optional but in the Python package check for it
        return self.getClient().update_album(idPost, fields)

    def setPostTitle(self, post, newTitle):
        post.title = newTitle

    def getPostTitle(self, post):
        print(f"Post: {post}")
        try:
            title = post.title
        except:
            title = ''
        return title

    def getPostContentHtml(self, post):
        content = ''
        if post.description:
            content = post.description
        return content

    def getPostContentLink(self, post):
        return post.link

    def editApiLink(self, post, newLink):
        post.link = newLink

    def setPostLink(self, post, newLink):
        post.link = newLink

    def getPostLink(self, post):
        if self.getPostsType() == 'cache':
            return post[1]
        else:
            try:
                link = post.link
            except:
                link = ''
            return link

    def getPostImage(self, post):
        # FIXME. Need rethinking
        return self.getPostId(post)

    def getPostId(self, post):
        idPost = ''
        if post:
            idPost = post.id
        return idPost

    def processReply(self, reply):
        res = ''
        if reply:
            if not ('Fail!' in reply):
                msgLog = (f"{self.indent} Reply: {reply}")
                logMsg(msgLog, 2, 0)
                # idPost = reply.get('id','')
                # title = reply.get('title')
                res = f"Published {reply}"
            else:
                res = reply
                if ('Image already in gallery.' in res):
                    res = res + ' SAVELINK'
        return(res)

    def publishNextPost(self, apiSrc):
        # We just store the post, we need more information than the title,
        # link and so on.
        reply = ''
        msgLog = (f"{self.indent} Publishing next post from {apiSrc} in "
                    f"{self.service}")
        logMsg(msgLog, 1, 0)
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "No posts available"
        except:
            reply = self.report(self.service, apiSrc, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, idPost, comment = args
        if kwargs:
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            idPost = api.getPostId(post)
        # print(f"post: {post}")
        # print(f"api: {api}")
        # print(f"api: {api.auxClass}")
        # print(f"tit: {title} id: {idPost}")
        # # This method publishes (as public post) some gallery that is in draft
        # mode
        msgLog = (f"{self.indent} Publishing in: {self.service}")
        logMsg(msgLog, 1, 0)
        msgLog = (f"{self.indent}  Post: {post}")
        logMsg(msgLog, 1, 0)
        api = self.getClient()
        # idPost = self.getPostId(post)
        try:
            res = api.share_on_imgur(idPost, title, terms=0)
            msgLog = (f"{self.indent} Res: {res}")
            logMsg(msgLog, 2, 0)
            if res:
                return(OK)
        except:
            res = self.report('Imgur', post, idPost, sys.exc_info())
            return(res)

        return(FAIL)

    def delete(self, j):
        msgLog = (f"{self.indent} Deleting {j}")
        logMsg(msgLog, 1, 0)
        post = self.obtainPostData(j)
        msgLog = (f"{self.indent} Deleting {post[0]}")
        logMsg(msgLog, 1, 0)
        post = self.obtainPostData(j)
        idPost = self.posts[j].id
        msgLog = (f"{self.indent} id {idPost}")
        logMsg(msgLog, 2, 0)
        post = self.obtainPostData(j)
        msgLog = (f"{self.indent} {self.getClient().album_delete(idPost)}")
        logMsg(msgLog, 2, 0)
        #FIXME is this ok?
        sys.exit()
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        msgLog = (f"{self.indent} Deleted {post[0]}")
        logMsg(msgLog, 2, 0)
        return(f"{post[0]}")

    def extractImages(self, post):
        theTitle = self.getPostTitle(post)
        data = self.getClient().get_album_images(self.getPostId(post))

        res = []
        title = theTitle
        for img in data:
            # msgLog = (f"{self.indent} Img: {img}")
            # logMsg(msgLog, 2, 0)
            if img.type == 'video/mp4':
                # msgLog = (f"{self.indent} Es vídeo")
                # logMsg(msgLog, 2, 0)
                urlImg = img.mp4
            else:
                # msgLog = (f"{self.indent} Es imagen")
                # logMsg(msgLog, 2, 0)
                urlImg = img.link
            # import inspect
            # loggin.debug(inspect.getmembers(img)[2][1])
            # urlImg = 'https://i.imgur.com/{}.jpg'.format(img.id)
            titleImg = img.description
            if titleImg:
                description = titleImg.split('#')
                description, tags = description[0], description[1:]
                aTags = []
                while tags:
                    aTag = tags.pop().strip()
                    aTags.append(aTag)
                tags = aTags
            else:
                description = ""
                tags = []
            if img.name:
                try:
                    from dateutil.parser import parse
                    myDate = str(parse(img.name.split('_')[1])).split(' ')[0]
                    tags.append(myDate)
                    if description:
                        description = '{} ({})'.format(description, myDate)
                    else:
                        description = '({})'.format(myDate)
                except:
                    msgLog = (f"{self.indent} Name in different format "
                              f"{img.name}")
                    logMsg(msgLog, 3, 0)

            res.append((urlImg, title, description, tags))
        return res

    def getNumPostsData(self, num, i, lastLink):
        listPosts = []
        posts = self.getPosts()
        msgLog = (f"{self.indent} Eo posts: {posts}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Eo posts last: {lastLink}")
        logMsg(msgLog, 2, 0)
        num = 1
        # Only one post each time
        j = 0
        msgLog = (f"{self.indent} i: {i}, len: {len(posts)}")
        logMsg(msgLog, 2, 0)
        for ii in range(min(i, len(posts)), 0, -1):
            # logging.info(f"iii: {ii}")
            ii = ii - 1
            if (ii < 0):
                break
            idPost = self.getPostId(posts[ii])
            # logging.info(f"idPost: {idPost}")
            if (not ((idPost in lastLink)
                     or ('https://imgur.com/a/'+idPost in lastLink))):
                # Only posts that have not been posted previously. We
                # check by link (post[1]) We don't use this code here.
                post = self.obtainPostData(ii)
                listPosts.append(post)

                j = j + 1
                if j == num:
                    break

        return(listPosts)


def main():

    import logging
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format='%(asctime)s %(message)s')
    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    #
    # src: ('imgur', 'set', 'https://imgur.com/user/ftricas', 'drafts')
    #
    # More: Src {'url': 'https://imgur.com/user/ftricas', 'service': 'imgur', 'posts': 'drafts', 'cache': 'imgur', 'imgur': 'ftricas', 'time': '23.1', 'max': '1'}
    print(rules.rules.keys())

    indent = ""
    mySrc = None
    for src in rules.rules.keys():
        if src[0] == 'imgur':
            print(f"Src: {src}")
            more = rules.more[src]
            mySrc = src
            # break
    apiSrc = rules.readConfigSrc(indent, mySrc, more)

    testingImages = True
    if testingImages:
        apiSrc.setPostsType('posts')
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"Title: {apiSrc.getPostTitle(post)}")
            print(f"Link: {apiSrc.getPostLink(post)}")
            print(f"Text: {apiSrc.getImagesCode(i)}")

        return

    testingDrafts = False
    if testingDrafts:
        apiSrc.setPostsType('drafts')
        apiSrc.setPosts()
        print(f"Posts: {apiSrc.getPosts()}")
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"{i}) {apiSrc.getPostTitle(post)} - {apiSrc.getPostLink(post)}")

        return

    testingPosts = False
    if testingPosts:
        apiSrc.setPosts()
        print(f"Posts: {apiSrc.getPosts()}")

        return

    testingDrafts = False
    if testingDrafts:
        apiSrc.setPostsType('drafts')
        apiSrc.setPosts()
        lastLink = 'https://imgur.com/a/plNolxs'
        # img.lastLinkPublished = lastLink
        # i = img.getLinkPosition(lastLink)
        # num = 1
        listPosts = apiSrc.getPosts()
        print(listPosts)
        for i, post in enumerate(listPosts):
            print(f"{i}) {apiSrc.getPostTitle(post)}"
                  f" {apiSrc.getPostLink(post)}")
        #listPosts2 = apiSrc.getNumNextPost(1)
        #print(listPosts2)
        #print(f"post: {apiSrc.getNextPost()}")
        #print(f"Title: {apiSrc.getPostTitle(apiSrc.getNextPost())}")
        #print(f"Id: {apiSrc.getPostId(apiSrc.getNextPost())}")
        return

    publishCache = False
    if publishCache:
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"{i}) {apiSrc.getPostTitle(post)}")
        pos = int(input("Which post? "))
        post = apiSrc.getPost(pos)
        print(f"Post: {post}")
        print(f"Title: {apiSrc.getPostTitle(post)}")
        input("Add? ")

        import moduleCache
        cache = moduleCache.moduleCache()
        # cache.setClient(('https://imgur.com/user/ftricas',
        #                 ('wordpress', 'avecesunafoto')))
        # cache.setClient(('https://imgur.com/user/ftricas',
        #                 ('imgur', 'ftricas')))
        cache.setClient((('imgur', 'https://imgur.com/user/ftricas'),
                'imgur@ftricas', 'posts'))
        cache.socialNetwork = 'imgur'
        cache.nick = 'ftricas'
        apiSrc.socialNetwork = 'imgur'
        apiSrc.nick = 'ftricas'
        apiSrc.user = 'https://imgur.com/user/ftricas'
        cache.fileName = cache.fileNameBase(apiSrc)
        cache.setPostsType('posts')
        cache.setPosts()
        print(cache.getPosts())
        cache.publishPost(api=apiSrc, post=post)
        return

    extractImages = False
    if extractImages:
        apiSrc.setPostsType('drafts')
        apiSrc.setPosts()

        for i, post in enumerate(apiSrc.getPosts()[:25]):
            print(f"{i}) {apiSrc.getPostTitle(post)}")
        pos = int(input("Position? "))
        res = apiSrc.extractImages(apiSrc.getPosts()[pos])
        print(res)

        return


    publishWordpress = False
    # Testing Wordpress publishing
    if publishWordpress:
        apiSrc.setPostsType('posts')
        apiSrc.setPosts()

        for i, post in enumerate(apiSrc.getPosts()[:25]):
            print(f"{i}) {apiSrc.getPostTitle(post)}")
        pos = int(input("Position? "))
        service = 'wordpress'
        nick = 'avecesunafoto'
        socialNetwork = (service, nick) #img.getSocialNetworks()[service])
        for src in rules.rules.keys():
            if (src[0] == 'imgur') and (rules.rules[src][0][2] == 'wordpress'):
                action = rules.rules[src][0]
                more = rules.more[src]
                break

        apiDst = rules.readConfigDst("", action, more, apiSrc)
        rules.executePublishAction("", "", apiSrc, apiDst, False , False, pos)

        return
    img = moduleImgur.moduleImgur()
    acc = "Blog20"
    url = config.get(acc, 'url')
    img.setUrl(url)
    name = url.split('/')[-1]
    img.setClient(name)
    img.setPostsType(config.get(acc, 'posts'))
    img.setPosts()
    img.setSocialNetworks(config)
    print(img.getSocialNetworks())

    input("Go?")
    service = 'wordpress'
    nick = 'avecesunafoto'
    socialNetwork = (service, nick) #img.getSocialNetworks()[service])

    img.setPostsType('posts')
    img.setPosts()

    for i, post in enumerate(img.getPosts()[:6]):
        print(f"{i}) {img.getPostTitle(post)}")
    pos = int(input("Position? "))+1

    if publishWordpress:
        listPosts = img.getNumPostsData(1, pos, '')
        print(listPosts[0])
        post = listPosts[0]
        title = post[0]
        postWP = post[-1]
        tags = post[-2]
        print(title)
        print(postWP)
        print(tags)
        input("Publish? ")
        import moduleWordpress
        wp = moduleWordpress.moduleWordpress()
        wp.setClient('avecesunafoto')

        print(wp.publishPost(title, '', postWP, tags=tags))

    sys.exit()
    for service in img.getSocialNetworks():
        socialNetwork = (service, img.getSocialNetworks()[service])

        linkLast, lastTime = checkLastLink(img.getUrl(), socialNetwork)
        print("linkLast {} {}".format(socialNetwork, linkLast))
        i = img.getLinkPosition(linkLast)
        print(i)
        print(img.getNumPostsData(2, i))

    sys.exit()
    fileName = fileNamePath(img.url)
    urls = getLastLink(fileName)
    thePost = None
    for i, post in enumerate(img.getPosts()):
        print(f"{i}) {img.getPostTitle(post)} {img.getPostLink(post)}")
        if not img.getPostTitle(post).startswith('>'):
            if not (img.getPostLink(post).encode() in urls[0]):
                print("--->", img.getPostTitle(post))
                thePost = post

    if thePost:
        res = downloadUrl(img.getPostLink(thePost))

        print()
        print(res)
        sys.exit()

        print(f"Wordpressing! {res[0][2]}")
        import moduleWordpress
        wp = moduleWordpress.moduleWordpress()
        wp.setClient('avecesunafoto')
        title = res[0][2]
        text = ''
        for iimg in res:
            text = '{}\n<p><a href="{}"><img class="alignnone size-full '\
                          'wp-image-3306" src="{}" alt="" width="776" '\
                          'height="1035" /></a></p>'.format(text,
                                                            iimg[0],
                                                            iimg[1])

        print('----')
        print(title)
        print(text)

        theUrls = [img.getPostLink(thePost).encode(), ] + urls[0]
        wp.publishPost(text, '', title)

        updateLastLink(img.url, theUrls)

        text = ''
        for img in res:
            text = '{}\n<p><a href="{}"><img class="alignnone size-full '\
                                        'wp-image-3306" src="{}" alt="" '\
                                        'width="776" height="1035" /></a>'\
                                        '</p>'.format(text, img[0], img[1])

        print("---")
        print(text)


if __name__ == '__main__':
    main()
