import configparser
import json
import logging
import sys
import time

from imgurpython import ImgurClient

from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleQueue import *


class moduleImgur(Content, Queue):

    def __init__(self):
        super().__init__()
        self.service = 'Imgur'

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
        client_id = keys[0]
        client_secret = keys[1]
        access_token = keys[2]
        refresh_token = keys[3]

        try:
            client = ImgurClient(client_id, client_secret,
                             access_token, refresh_token)
        except:
            client = None
            reply = self.report(self.service, apiSrc, sys.exc_info())

        return client

    def setApiPosts(self):
        posts = []
        client = self.getClient()
        logging.debug(f"Client: {client} {self.user} ")
        if self.user.find('https')>=0:
            user = self.user.split('/')[-1]
        else:
            user = self.user

        logging.debug(f"User: {user}")

        if client:
            for album in client.get_account_albums(user):
                logging.debug(f"Title: {time.ctime(album.datetime)} "
                              f"{album.title}")
                if album.in_gallery:
                    posts.append(album)
            else:
                logging.warning('No client configured!')
        return (posts)

    def setApiDrafts(self):
        posts = []
        client = self.getClient()
        logging.debug(f"Client: {client}")
        logging.debug(f"User: {self.user}")

        if client:
            if self.user.find('http')>= 0:
                user = self.user.split('/')[-1]
            else:
                user = self.user

            logging.debug(f"User: {user}")
            for album in client.get_account_albums(user):
                info = f"{time.ctime(album.datetime)} {album.title}"
                logging.info(f"Info: {info}")
                if not album.in_gallery:
                    posts.append(album)
                    # logging.info(f"Draft: {info}")
        else:
            logging.warning('No client configured!')

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
        return post.title

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
            return post.link

    def getPostImage(self, post):
        # FIXME. Need rethinking
        return self.getPostId(post)

    def getPostId(self, post):
        print(f"Post: {post}")
        return post.id

    def processReply(self, reply):
        res = ''
        if reply:
            if not ('Fail!' in reply):
                logging.info(f"Reply: {reply}")
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
        logging.info(f"    Publishing next post from {apiSrc} in "
                    f"{self.service}")
        try:
            post = apiSrc.getNextPost()
            if post:
                res = self.publishApiPost(api=apiSrc, post=post)
                reply = self.processReply(res)
            else:
                reply = "Fail! No posts available"
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
        print(f"post: {post}")
        print(f"api: {api}")
        # print(f"api: {api.auxClass}")
        print(f"tit: {title} id: {idPost}")
        # This method publishes (as public post) some gallery that is in draft
        # mode
        logging.info("     Publishing in: {}".format(self.service))
        logging.info("      {}".format(str(post)))
        api = self.getClient()
        # idPost = self.getPostId(post)
        try:
            res = api.share_on_imgur(idPost, title, terms=0)
            logging.info(f"      Res: {res}")
            if res:
                return(OK)
        except:
            logging.info(self.report('Imgur', post, idPost, sys.exc_info()))
            return(self.report('Imgur', post, idPost, sys.exc_info()))

        return(FAIL)

    def delete(self, j):
        logging.info(f"Deleting {j}")
        post = self.obtainPostData(j)
        logging.info(f"Deleting {post[0]}")
        idPost = self.posts[j].id
        logging.info(f"id {idPost}")
        logging.info(self.getClient().album_delete(idPost))
        sys.exit()
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        logging.info(f"Deleted {post[0]}")
        return(f"{post[0]}")

    def extractImages(self, post):
        theTitle = self.getPostTitle(post)
        data = self.getClient().get_album_images(self.getPostId(post))

        res = []
        title = theTitle
        for img in data:
            logging.debug(f"Img: {img}")
            if img.type == 'video/mp4':
                logging.info("Es vídeo")
                urlImg = img.mp4
            else:
                logging.info("Es imagen")
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
                    logging.warning(f"Name in different format {img.name}")
            res.append((urlImg, title, description, tags))
        return res

    def getNumPostsData(self, num, i, lastLink):
        listPosts = []
        posts = self.getPosts()
        logging.debug(f"Eo posts: {posts}")
        logging.debug(f"Eo posts last: {lastLink}")
        num = 1
        # Only one post each time
        j = 0
        logging.info(f"i: {i}, len: {len(posts)}")
        for ii in range(min(i, len(posts)), 0, -1):
            logging.info(f"iii: {ii}")
            ii = ii - 1
            if (ii < 0):
                break
            idPost = self.getPostId(posts[ii])
            logging.info(f"idPost: {idPost}")
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

    testingEditLink = False
    if testingEditLink:
        apiSrc.setPosts()
        print(f"Posts: {apiSrc.getPosts()}")

        return

    testingDrafts = False
    if testingDrafts:
        apiSrc.setPosts()
        lastLink = 'https://imgur.com/a/q5zyNtS'
        # img.lastLinkPublished = lastLink
        # i = img.getLinkPosition(lastLink)
        # num = 1
        listPosts = apiSrc.getPosts()
        print(listPosts)
        listPosts2 = apiSrc.getNumNextPost(1)
        print(listPosts2)
        print(f"post: {apiSrc.getNextPost()}")
        print(f"Title: {apiSrc.getPostTitle(apiSrc.getNextPost())}")
        print(f"Id: {apiSrc.getPostId(apiSrc.getNextPost())}")
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

    extractImages = True
    if extractImages:
        apiSrc.setPostsType('posts')
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