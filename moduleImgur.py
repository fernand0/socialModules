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
        client_id = config.get(self.user, 'client_id')
        client_secret = config.get(self.user, 'client_secret')
        access_token = config.get(self.user, 'access_token')
        refresh_token = config.get(self.user, 'refresh_token')

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
        if client:
            for album in client.get_account_albums(self.user):
                logging.debug(f"{time.ctime(album.datetime)} {album.title}")
                if album.in_gallery:
                    posts.append(album)
            else:
                logging.warning('No client configured!')
        return (posts)

    def setApiDrafts(self):
        posts = []
        client = self.getClient()

        if client:
            for album in client.get_account_albums(self.user):
                info = f"{time.ctime(album.datetime)} {album.title}"
                logging.debug(info)
                if not album.in_gallery:
                    posts.append(album)
                    logging.debug(f"Draft: {info}")
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

    def getLinkPosition(self, link):
        if self.getPostsType() == 'posts':
            return len(self.getPosts())
        else:
            return Content.getLinkPosition(self, link)

    def getPostLink(self, post):
        if self.getPostsType() == 'cache':
            return post[1]
        else:
            return post.link

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
            theTitle = None
            theLink = None
            thePost = None
            theTags = None

        return (theTitle,  theLink, theLink, theId,
                None, None, None, None, theTags, thePost)

    def publishPost(self, post, idPost, comment=''):
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
            urlImg = 'https://i.imgur.com/{}.jpg'.format(img.id)
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
        num = 1
        # Only one post each time
        j = 0
        for ii in range(min(i, len(posts)), 0, -1):
            ii = ii - 1
            if (ii < 0):
                break
            idPost = self.getPostId(posts[ii])
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

    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format='%(asctime)s %(message)s')

    import moduleImgur

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    accounts = ["Blog20", "Blog21"]
    for acc in accounts:
        print("Account: {}".format(acc))
        img = moduleImgur.moduleImgur()
        section = acc
        url = config.get(acc, 'url')
        img.setUrl(url)
        name = url.split('/')[-1]
        img.setClient(name)
        if 'posts' in config[acc]:
            print("si")
            img.setPostsType(config.get(acc, 'posts'))
        img.setPostsType('posts')
        print(img.getPostsType())
        img.setPosts()
        # lastLink, lastTime = checkLastLink(img.getUrl(), socialNetwork)
        for i, p in enumerate(img.getPosts()):
            link = img.getPostLink(p)
            print(i, img.getPostTitle(p), img.getPostLink(p))
        i = 5
        p = img.getPost(i)
        print(i, img.getPostTitle(p), img.getPostLink(p))
        print(img.editApiTitle(p, 'No se su nombre'))

        selection = input("Which one? ")
        print(selection)
        break

        if ('cache' in config.options(section)):
            img.setProgram(config.get(section, "cache"))
            cache = config.get(acc, 'cache')
            user = config.get(acc, cache)
        img.setCache()
        img.setClient(name)
        img.setUrl(url)
        if 'posts' in config.options(acc):
            img.setPostsType(config.get(acc, 'posts'))
        img.setPosts()
        for i, im in enumerate(img.getPosts()):
            print(i, img.getPostTitle(im))
        lastLink = None
        i = 1
        if 'wordpress' in img.getSocialNetworks():
            socialNetwork = ('wordpress', img.getSocialNetworks()['wordpress'])
            lastLink, lastTime = checkLastLink(url, socialNetwork)

            print(f"lastLink {lastLink[0]}")
            pos = img.getLinkPosition(lastLink[0])
            print(f"pos {pos}")
            i = pos
        print()
        num = int(selection)
        listPosts = img.getNumPostsData(num, i, lastLink)
        print(f"listPosts: {listPosts}")
        continue
        # Code from this point is not expected to work, but in some cases can
        # serve as an example.

        if cache == 'wordpress':
            import moduleWordpress
            wp = moduleWordpress.moduleWordpress()
            wp.setClient(user)
            continue
            wp.publishPost(title, link, comment, tags=links)
            continue
        else:
            socialNetwork = ('imgur', img.getSocialNetworks()['imgur'])
            lastLink, lastTime = checkLastLink(url, socialNetwork)
            i = 1
            listPosts = img.getNumPostsData(1, i)
            print(listPosts)
            continue

        sys.exit()
        imgs = img.getClient().get_album_images(img.getPosts()[-1].id)
        print("imgs", imgs)
        for iimg in imgs:
            print(f"id {iimg.id}")
            print(f"title {iimg.title}")
            print(f"descr {iimg.description}")
            print(f"name {iimg.name}")
        print(img.extractImages(img.getPosts()[-2]))
        print(img.getImagesCode(-1))
        continue

        print("---- Posts ----")
        for i, post in enumerate(img.getPosts()):
            print(img.getPostTitle(post))
            print(img.getPostLink(post))
            print(img.getPostId(post))
            print(img.obtainPostData(i))
        print("---- Drafts ----")
        for i, post in enumerate(img.getDrafts()):
            print(img.getPostTitle(post))
            print(img.getPostLink(post))
            print(img.obtainPostData(i))
        print("----")
        time.sleep(2)
    pos = int(selection)

    post = img.getImages(pos)
    postWP = img.getImagesCode(pos)
    title = img.getPostTitle(img.getPosts()[pos])
    tags = img.getImagesTags(pos)
    print("---post images ----")
    print(post)
    print("---title----")
    print(title)
    print("---postWP----")
    print(postWP)
    print("---tags----")
    print(tags)

    publishCache = False
    if publishCache:
        listPosts = img.getNumPostsData(1, pos, '')
        print(listPosts)
        input("Add? ")

        import moduleCache
        cache = moduleCache.moduleCache()
        cache.setClient(('https://imgur.com/user/ftricas', 
                        ('wordpress', 'avecesunafoto')))
        cache.setPosts()
        print(cache.getPosts())
        cache.addPosts(listPosts)

    sys.exit()

    # Testing Wordpress publishing
    img.setSocialNetworks(config)
    print(img.getSocialNetworks())
    service = 'wordpress'
    socialNetwork = (service, img.getSocialNetworks()[service])

    publishWordpress = False
    if publishWordpress:
        import moduleWordpress
        wp = moduleWordpress.moduleWordpress()
        wp.setClient('avecesunafoto')

        print(wp.publishPost(title, '', postWP, tags=post[-1]))
 
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
