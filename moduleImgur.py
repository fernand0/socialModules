import configparser
import json
import logging
import sys
import time

from imgurpython import ImgurClient

from moduleContent import *
from moduleQueue import *
from configMod import *

class moduleImgur(Content,Queue):

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

    #def setClientt(self, idName):

    #    if isinstance(idName, str): 
    #        self.name = idName
    #    elif isinstance(idName[1], str):
    #        self.name = idName[1]
    #    else:
    #        # Deprecated
    #        self.name = idName[1][1]

    #    try:
    #        config = configparser.ConfigParser()
    #        config.read(CONFIGDIR + '/.rssImgur') 

    #        if config.sections(): 
    #            self.client_id=config.get(self.name, 'client_id') 
    #            self.client_secret=config.get(self.name, 'client_secret') 
    #            self.access_token=config.get(self.name, 'access_token') 
    #            self.refresh_token=config.get(self.name, 'refresh_token')

    #            self.client = ImgurClient(self.client_id, self.client_secret, 
    #                    self.access_token, self.refresh_token)
    #        else:
    #            logging.warning("Some problem with configuration file!")
    #            self.client = None
    #    except:
    #        logging.warning("User not configured!")
    #        logging.warning("Unexpected error:", sys.exc_info()[0])

    def setApiCache(self, numPosts=20): 
        import moduleCache
        cache = moduleCache.moduleCache()
        cache.setClient((self.url, (self.service, self.user, 'posts')))
        cache.setPosts()
        return cache.getPosts()


    def setApiPosts(self, numPosts=20): 
        posts = []
        client = self.getClient() 
        if client:
            for album in client.get_account_albums(self.user):
                logging.debug("{} {}".format(time.ctime(album.datetime),
                    album.title))
                text = ""
                if album.in_gallery: 
                    posts.append(album)
            else:
                logging.warning('No client configured!')
        return (posts[:numPosts])
 
    def setApiDrafts(self, numPosts=20): 
        posts = []
        client = self.getClient()

        if client:
            for album in client.get_account_albums(self.user):
                logging.debug("{} {}".format(time.ctime(album.datetime),
                    album.title))
                text = ""
                if not album.in_gallery: 
                    posts.append(album)
                    logging.debug("Draft {} {}".format(time.ctime(album.datetime), 
                        album.title))
        else:
            logging.warning('No client configured!')

        return (posts)
 
    #def setPosts(self, numPosts=20): 
    #    self.posts = []
    #    self.drafts = []
    #    if self.getPostsType() == 'file':
    #        # cache setPosts()
    #        fileNameQ = fileNamePath(self.getUrl(), (self.service[0].lower() +
    #            self.service[1:], self.user))+'.queue'
    #        try:
    #            with open(fileNameQ,'rb') as f: 
    #                try: 
    #                    listP = pickle.load(f) 
    #                except: 
    #                    listP = [] 
    #        except:
    #            listP = []
    #        for post in listP:
    #            self.posts = [ post ] + self.posts
    #    else:
    #        client = self.getClient()
    #        if client:
    #            for album in client.get_account_albums(self.user):
    #                logging.debug("{} {}".format(time.ctime(album.datetime),
    #                    album.title))
    #                text = ""
    #                if album.in_gallery: 
    #                    #self.posts.insert(0,album)
    #                    self.posts.append(album)
    #                else:
    #                    #self.drafts.insert(0,album)
    #                    self.drafts.append(album)
    #        else:
    #            logging.warning('No client configured!')
    #    self.drafts = self.drafts[0:numPosts]
    #    self.posts = self.posts[0:numPosts]
    #    # We set some limit
                    
    def getPostTitle(self, post):
        return post.title

    def getPostLink(self,post):
        if self.getPostsType() == 'cache':
            return post[1]
        else: 
            return post.link

    def getPostId(self,post):
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
        print("s",self)
        print("sc",self.client)
        api = self.getClient() 
        print("c",api)
        idPost = idPost.split('/')[-1]
        try: 
            res = api.share_on_imgur(idPost, post, terms=0)            
            logging.info("      Res: %s" % res) 
            if res: 
                return(OK) 
        except: 
            logging.info(self.report('Imgur', post, idPost, sys.exc_info()))
            return(self.report('Imgur', post, idPost, sys.exc_info()))

        return(FAIL)

    def publish(self, j):
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service)
        (title, link, firstLink, image, summary, summaryHtml, 
                summaryLinks, content, links, comment) = self.obtainPostData(j)
        logging.info("Publishing {} {}".format(title, link))
        idPost = link
        logging.info("Publishing {} {}".format(title, idPost))
        logging.info("Publishing getP {}".format(self.getProgram()))
        
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
            return update
        else:
            api = self.getClient()
            try:
                res = api.share_on_imgur(idPost, title, terms=0)            
                logging.info("Res: %s" % res)
                return(res)
            except:
                post = title
                link = idPost
                logging.info(self.report('Imgur', post, link, sys.exc_info()))
                return(FAIL)

        return("%s"% title)

    def delete(self,j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        idPost = self.posts[j].id
        logging.info("id %s"% idPost)
        logging.info(self.getClient().album_delete(idPost))
        sys.exit()
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        logging.info("Deleted %s"% post[0])
        return("%s"% post[0])

    def extractImages(self, post):
        theTitle = self.getPostTitle(post)
        theLink = self.getPostLink(post) 
        data = self.getClient().get_album_images(self.getPostId(post))

        res = []
        title = theTitle
        for img in data:
            urlImg = 'https://i.imgur.com/{}.jpg'.format(img.id)
            titleImg = img.description
            if titleImg:
                description = titleImg.split('#')
                description, tags = description[0], description[1:]
                aTags= []
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
                    logging.warning("Name in different format {}".format(img.name))
            res.append((urlImg,title, description, tags))
        return res

    def extractImagesOld(self, post):
        theTitle = self.getPostTitle(post)
        theLink = self.getPostLink(post) 
        page = urlopen(theLink).read() 
        soup = BeautifulSoup(page,'lxml') 

        res = []
        script = soup.find_all('script')
        pos = script[9].text.find('image')
        pos = script[9].text.find('{',pos+1)
        pos2 = script[9].text.find('\n',pos+1)
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
                    aTags= []
                    while tags: 
                        aTag = tags.pop().strip()
                        aTags.append(aTag) 
                    tags = aTags
                else:
                    description = ""
                    tags = []
            else:
                titleImg = ""
            res.append((urlImg,title, description, tags))
        return res

    def getNumPostsData(self, num, i, lastLink): 
        listPosts = []
        posts = self.getPosts()
        #if True: #self.getPostsType() == 'posts':
        j = 0
        #for k,p in enumerate(posts):
        #    print(k,self.getPostTitle(p), self.getPostLink(p))
        for ii in range(min(i,len(posts)),0,-1):
            ii = ii - 1
            if (ii < 0): break
            idPost = self.getPostId(posts[ii])
            title = self.getPostTitle(posts[ii])
            print(ii, idPost, title)
            if not (idPost in lastLink): 
                # Only posts that have not been posted previously. We
                # check by link (post[1]) We don't use this code here.
                post = self.obtainPostData(ii) 
                listPosts.append(post)

                j = j + 1
                if j == num:
                    break
        #listPosts = reversed(listPosts)
        #else: 
        #    # here we can use the general method, starting at the first
        #    # post
        #    #i = 1 
        #    i = len(posts)
        #    listPosts = Content.getNumPostsData(self, num, i, lastLink)

        return(listPosts)


def main(): 

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
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
        print(img.getPostsType())
        img.setPosts()
        for i,p in enumerate(img.getPosts()):
            print(i, img.getPostTitle(p), img.getPostLink(p))
        continue
        img.setSocialNetworks(config)
            


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

            #print("lastLink",lastLink)
            print("lastLink",lastLink[0])
            pos = img.getLinkPosition(lastLink[0])
            print("pos {}".format(pos))
            i = pos
        num = 5
        listPosts = img.getNumPostsData(num, i, lastLink)
        print("listPosts:")
        print(listPosts)
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
            listPosts = img.getNumPostsData(1,i)
            print(listPosts)
            continue


        sys.exit()
        #img.publishPost(img.getPosts()[5],img.getPostLink(img.getPosts()[0]))
        #print(dir(img.getPosts()[0]))
        #for method in img.getPosts()[0].__dir__():
        #    print(method)
        #    #print(img.method())
        #print("datetime",img.getPosts()[0].datetime)
        imgs = img.getClient().get_album_images(img.getPosts()[-1].id)
        print("imgs",imgs)
        for iimg in imgs:
            print("id",iimg.id)
            print("title",iimg.title)
            print("descr",iimg.description)
            print("name",iimg.name)
        print(img.extractImages(img.getPosts()[-2]))
        print(img.getImagesCode(-1))
        continue 

        #print(img.getImages(0))


        print("---- Posts ----")
        for i, post in enumerate(img.getPosts()):
            print(img.getPostTitle(post))
            print(img.getPostLink(post))
            print(img.getPostId(post))
            print(img.obtainPostData(i))
            #print(img.getImagesCode(i))
        print("---- Drafts ----")
        for i, post in enumerate(img.getDrafts()):
            print(img.getPostTitle(post))
            print(img.getPostLink(post))
            print(img.obtainPostData(i))
        print("----")
        time.sleep(2)
    sys.exit()
    pos=3
    post = img.getImages(pos)
    postWP = img.getImagesCode(pos)
    title = img.getPostTitle(img.getPosts()[pos])
    tags = img.getImagesTags(pos)
    print("---post images ----")
    print(post)
    print("---title----")
    print (title)
    print("---postWP----")
    print(postWP)
    print("---tags----")
    print(tags)

    # Testing Wordpress publishing
    img.setSocialNetworks(config)
    print(img.getSocialNetworks())
    service='wordpress'
    socialNetwork = (service, img.getSocialNetworks()[service])

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
        print(img.getNumPostsData(2,i))
 
    sys.exit()
    txt = ''
    fileName = fileNamePath(img.url)
    urls = getLastLink(fileName)
    thePost=None
    for i, post in enumerate(img.getPosts()):
        print("{}) {} {}".format(i, img.getPostTitle(post), 
            img.getPostLink(post)))
        #print(img.getPosts()[i])
        if not img.getPostTitle(post).startswith('>'):
            if not (img.getPostLink(post).encode() in urls[0]):
                print("--->",img.getPostTitle(post))
                thePost = post


    if thePost:
        res = downloadUrl(img.getPostLink(thePost))

        print()
        print(res)
        sys.exit()


        #sel = input('Publish? (p/w) ') 

        #if sel == 'p':
        #    print('pubishing! {}'.format(res [0][2]))
        #    print(img.publish(pos))
        #elif sel == 'w':
        print('Wordpressing! {}'.format(res [0][2]))
        import moduleWordpress 
        wp = moduleWordpress.moduleWordpress() 
        wp.setClient('avecesunafoto') 
        title = res [0][2]
        text = '' 
        for iimg in res: 
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,iimg[0],iimg[1])

        print('----') 
        print(title) 
        print(text) 

        theUrls = [img.getPostLink(thePost).encode(), ] + urls[0]
        wp.publishPost(text, '', title)

        updateLastLink(img.url, theUrls)
        #elif sel == 's':
        #    import pprint
        #    pprint.pprint(img.getPosts()[pos])
        #    pprint.pprint(img.getPosts()[pos].views)
        #    pprint.pprint(time.ctime(img.getPosts()[pos].datetime))
        #    pprint.pprint(img.getPosts()[pos].section)
        #    #pprint.pprint(dir(img.getPosts()[pos]))

        text = ''
        for img in res:
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,img[0],img[1])

        print("---")
        print(text)



        #print(img.publish(0))
        #img.delete(8)

if __name__ == '__main__':
    main()
