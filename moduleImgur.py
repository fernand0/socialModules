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

    def setClient(self, idName):
        if isinstance(idName, str): 
            self.name = idName
        else:
            self.name = idName[1][1]

        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssImgur') 

            if config.sections(): 
                self.client_id=config.get(self.name, 'client_id') 
                self.client_secret=config.get(self.name, 'client_secret') 
                self.access_token=config.get(self.name, 'access_token') 
                self.refresh_token=config.get(self.name, 'refresh_token')

                self.client = ImgurClient(self.client_id, self.client_secret, 
                        self.access_token, self.refresh_token)
            else:
                logging.warning("Some problem with configuration file!")
                self.client = None
        except:
            logging.warning("User not configured!")
            logging.warning("Unexpected error:", sys.exc_info()[0])

        self.service = 'Imgur'

    def getClient(self):
        return self.client

    def setPosts(self): 
        self.posts = []
        self.drafts = []
        client = self.getClient()
        if client:
            for album in client.get_account_albums(self.name):
                logging.debug("{} {}".format(time.ctime(album.datetime),
                    album.title))
                text = ""
                if album.in_gallery: 
                    self.posts.insert(0,album)
                else:
                    self.drafts.insert(0,album)
        else:
            logging.warning('No client configured!')
        self.drafts = self.drafts[-20:]
        self.posts = self.posts[-20:]
        # We set some limit
                    
    def getPostTitle(self, post):
        return post.title

    def getPostLink(self,post):
        return post.link

    def getPostId(self,post):
        return post.id

    def extractDataMessage(self, i):
        posts = self.getPosts()
        if i < len(posts):
            post = posts[i]
            logging.info("Post: %s"% post)
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

        return (theTitle, theId, theLink, None, None, None, None, None, theTags, thePost)

       
    def publishPost(self, post, idPost, comment=''):
        # This method publishes (as public post) some gallery that is in draft
        # mode
        logging.info("     Publishing in Imgur...")
        api = self.getClient() 
        if True: 
            res = api.share_on_imgur(idPost, post, terms=0)            
            logging.info("      Res: %s" % res) 
            if res: 
                return(OK) 
        else: 
            logging.info(self.report('Imgur', post, idPost, sys.exc_info()))
            return(self.report('Imgur', post, idPost, sys.exc_info()))

        return(FAIL)

    def publish(self, j):
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service)
        idPost = self.posts[j].id
        title = self.getPostTitle(self.posts[j])
        idPost = self.getPostId(self.posts[j])
        
        api = self.getClient()
        try:
            res = api.share_on_imgur(idPost, title, terms=0)            
            logging.info("Res: %s" % res)
            return(res)
        except:
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
            #print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(img.datetime)))
            #print("n",img.name)
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
        url = config.get(acc, 'url')
        name = config.get(acc, 'imgur')
        img.setClient(name)
        img.setUrl(url)
        if 'posts' in config.options(acc):
            img.setPostsType(config.get(acc, 'posts'))
        print("Type",img.getPostsType())
        img.setPosts()
        #print(img.getPosts())
        #import inspect 
        #print(inspect.getmembers('img'))
        #img.publishPost(img.getPosts()[0],img.getPostLink(img.getPosts()[0]))
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
        sys.exit()
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
    img.setSocialNetworks(config, section)
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
