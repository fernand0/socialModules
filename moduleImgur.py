import configparser
import json
import logging
import sys
import time

from imgurpython import ImgurClient

from moduleContent import *
from moduleQueue import *
from configMod import *


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

        client = ImgurClient(client_id, client_secret,
                             access_token, refresh_token)

        return client

    def setApiCache(self):
        import moduleCache
        cache = moduleCache.moduleCache()
        cache.setClient((self.url, (self.service, self.user, 'posts')))
        cache.setPosts()
        return cache.getPosts()

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
                logging.debug(f"{time.ctime(album.datetime)} {album.title}")
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

    def getPostTitle(self, post):
        return post.title

    def getPostContentHtml(self, post):
        content = ''
        if post.description:
            content = post.description
        return content

    def getPostContentLink(self, post):
        return post.link

    # def getLinkPosition(self, link):
    #     if self.getPostsType() == 'posts':
    #         return len(self.getPosts())
    #     else:
    #         return Content.getLinkPosition(self, link)

    def getPostLink(self, post):
        if self.getPostsType() == 'cache':
            return post[1]
        else:
            return post.link

    def getPostImage(self, post):
        # Need rethinking
        return self.getPostId(post)

    def getPostId(self, post):
        return post.id

    def extractDataMessage(self, i):
        posts = self.getPosts()
        if i < len(posts):
            if self.getPostsType() == 'cache':
                # Dirty?
                post = posts[0]
                return post
            else:
                post = posts[i]
                logging.debug(f"Post: {post}")
                theTitle = self.getPostTitle(post)
                theLink = self.getPostLink(post)
                theId = self.getPostId(post)
                thePost = self.getImagesCode(i)
                theTags = self.getImagesTags(i)
        else:
            theTitle = ''
            theLink = ''
            thePost = ''
            theTags = ''

        return (theTitle,  theLink, theLink, theId,
                '', '', '', theTags, thePost)

    def publishApiPost(self, *args, **kwargs):
        post, idPost, comment = args
        more = kwargs
        # This method publishes (as public post) some gallery that is in draft
        # mode
        logging.info("     Publishing in: {}".format(self.service))
        logging.info("      {}".format(str(post)))
        api = self.getClient()
        idPost = idPost.split('/')[-1]
        try:
            res = api.share_on_imgur(idPost, post, terms=0)
            logging.info(f"      Res: {res}")
            if res:
                return(OK)
        except:
            logging.info(self.report('Imgur', post, idPost, sys.exc_info()))
            return(self.report('Imgur', post, idPost, sys.exc_info()))

        return(FAIL)

    # def publish(self, j):
    #     logging.info(f"Publishing {j}")
    #     logging.info(f"servicename {self.service}")
    #     (title, link, firstLink, image, summary, summaryHtml,
    #      summaryLinks, content, links, comment) = self.obtainPostData(j)
    #     logging.info(f"Publishing {title} {link}")
    #     idPost = link
    #     logging.info(f"Publishing {title} {idPost}")
    #     logging.info(f"Publishing getP {self.getProgram()}")

    #     if self.getProgram():
    #         logging.info("getProgram")
    #         for profile in self.getSocialNetworks():
    #             nick = self.getSocialNetworks()[profile]
    #             logging.info(f"Social: {profile} Nick: {nick}")
    #             if ((profile[0] in self.getProgram()) or
    #                     (profile in self.getProgram())):
    #                 logging.info(f"Social: {profile} Nick: {nick}")
    #                 lenMax = self.len(profile)
    #                 socialNetwork = (profile, nick)

    #                 listP = self.cache[socialNetwork].setPosts()
    #                 listP = self.cache[socialNetwork].getPosts()
    #                 listPsts = self.obtainPostData(j)
    #                 listP = listP + [listPsts]
    #                 self.cache[socialNetwork].posts = listP
    #                 update = (update
    #                           + self.cache[socialNetwork].updatePostsCache())
    #                 logging.info(f"Update: {update}")
    #                 update = update + '\n'
    #         return update
    #     else:
    #         api = self.getClient()
    #         try:
    #             res = api.share_on_imgur(idPost, title, terms=0)
    #             logging.info("Res: %s" % res)
    #             return(res)
    #         except:
    #             post = title
    #             link = idPost
    #             logging.info(self.report('Imgur', post,
    #                                      link, sys.exc_info()))
    #             return(FAIL)
    #     return("%s"% title)

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

    def extractImagesOld(self, post):
        theTitle = self.getPostTitle(post)
        theLink = self.getPostLink(post)
        page = urlopen(theLink).read()
        soup = BeautifulSoup(page, 'lxml')

        res = []
        script = soup.find_all('script')
        pos = script[9].text.find('image')
        pos = script[9].text.find('{', pos + 1)
        pos2 = script[9].text.find('\n', pos + 1)
        data = json.loads(script[9].text[pos:pos2-1])
        import pprint
        pprint.pprint(data)
        sys.exit()
        title = data['title']
        for img in data['album_images']['images']:
            urlImg = 'https://i.imgur.com/{}.jpg'.format(img['hash'])
            if 'description' in img:
                titleImg = img['description']
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
            else:
                titleImg = ""
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

    import moduleImgur

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    testingDrafts = True
    if testingDrafts:
        img = moduleImgur.moduleImgur()
        acc = "Blog20"
        url = config.get(acc, 'url')
        img.setUrl(url)
        name = url.split('/')[-1]
        img.setClient(name)
        img.setPostsType(config.get(acc, 'posts'))
        img.setPosts()
        lastLink = 'https://imgur.com/a/q5zyNtS'
        img.lastLinkPublished = lastLink
        i = img.getLinkPosition(lastLink)
        num = 1
        listPosts = img.getNumPostsData(num, i, lastLink)
        print(listPosts)
        listPosts2 = img.getNumNextPost(1)
        print(listPosts2)
        print(f"{img.getPostTitle(img.getNextPost()[0])}")



    publishCache = False
    if publishCache:
        listPosts = img.getNumPostsData(1, pos, '')
        print(listPosts)
        input("Add? ")

        import moduleCache
        cache = moduleCache.moduleCache()
        # cache.setClient(('https://imgur.com/user/ftricas',
        #                 ('wordpress', 'avecesunafoto')))
        cache.setClient(('https://imgur.com/user/ftricas',
                        ('imgur', 'ftricas')))
        cache.setPosts()
        print(cache.getPosts())
        cache.addPosts(listPosts)


    publishWordpress = True
    # Testing Wordpress publishing
    img.setSocialNetworks(config)
    print(img.getSocialNetworks())
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
