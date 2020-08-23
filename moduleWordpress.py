import configparser
import logging
import requests
import json
import sys
from bs4 import BeautifulSoup
import urllib

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleWordpress(Content,Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.wp = None
        self.service = None
        self.tags = None
        self.oauth_base='https://public-api.wordpress.com/oauth2/authorize?'
        #self.api_auth='authorize'
        #self.api_token='token'
        self.api_auth = 'client_id={}&redirect_uri={}&response_type=token&blog={}'
        self.api_base='https://public-api.wordpress.com/rest/v1/'
        self.api_base2 = 'https://public-api.wordpress.com/wp/v2/'
        self.api_user='me'
        self.api_posts='sites/{}/posts'
        self.api_tags='sites/{}/tags'
        self.api_posts_search='?search={}'

    def setClient(self, user):
        logging.info("     Connecting Wordpress")
        self.service = 'Wordpress'
        try:
            config = configparser.RawConfigParser()
            config.read(CONFIGDIR + '/.rssWordpress')

            self.user = user
            try: 
                self.access_token =  config.get(user, "access_token")
            except:
                logging.warning("Access key does not exist!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
                logging.warning("Config file does not exists")
                logging.warning("Unexpected error:", sys.exc_info()[0])

        self.headers = {'Authorization':'Bearer '+self.access_token}
        self.my_site="{}.wordpress.com".format(user)

    def authorize(self): 
        # Firstly the data of the blog 
        config = configparser.ConfigParser()
        config.read(CONFIGDIR + '/.rssBlogs')
        url = config.get('Blog8','url')
        name = urllib.parse.urlparse(url).netloc.split('.')[0] 
        # Second the authentication data of the blog
        config = configparser.ConfigParser(interpolation=None) 
        configWordpress = CONFIGDIR + '/.rssWordpress'
        config.read(configWordpress)
        redirect_uri= config.get(name,'redirect_uri')
        client_id = config.get(name,'Client_ID')

        param=self.api_auth.format(client_id, 
                urllib.parse.quote(redirect_uri), url)
        print("Paste this URL in your browser and allow the application: {}{}".format(self.oauth_base,
            param)) 

        resUrl =  input('Paste the resulting URL: ') 
        splitUrl = urllib.parse.urlsplit(resUrl) 
        result = urllib.parse.parse_qsl(splitUrl.fragment)
        token = result[0][1]
        config.set(name, 'access_token', token)
        # Make a backup
        shutil.copyfile(configWordpress, '{}.bak'.format(configWordpress))
        with open(configWordpress, 'w') as configfile:
            config.write(configfile)

    def setPosts(self, morePosts=None): 
        logging.info("  Setting posts")
        self.posts = []
        try: 
            #print(self.api_base + self.api_posts.format(self.my_site))
            posts = requests.get(self.api_base + 
                    self.api_posts.format(self.my_site)+'?number=100', 
                    headers = self.headers).json()['posts']
            self.posts = posts
            if morePosts: 
                posts2 = requests.get(self.api_base + 
                    self.api_posts.format(self.my_site)+'?number=100&page=2', 
                    headers = self.headers).json()['posts']
                self.post.append(posts2)
        except KeyError:
            return(self.report('Wordpress API expired', '' , '', sys.exc_info()))
        except:
            return(self.report('Wordpress API', '' , '', sys.exc_info()))
        return('OK')

    def setTags(self): 
        res = requests.get(self.api_base + self.api_tags.format(self.my_site)) 
        if res.ok:
            self.tags = json.loads(res.text)

    def getTags(self): 
        return self.tags

    def checkTags(self, tags):
        idTags = []
        newTags = []
        if not self.tags:
            self.setTags()

        for tag in tags: 
            payload = {"name":tag}
            # I'm trying to create, if not possible, they exist
            res = requests.post(self.api_base 
                    + self.api_tags.format(self.my_site)+'/new', 
                    headers = self.headers,
                    data = payload)
            reply = json.loads(res.text)
            if 'ID' in reply:
                newTags.append(tag)
                idTags.append(reply['ID'])
            else:
                for ttag in self.tags['tags']:
                    if ttag['name'] == tag:
                        idTags.append(ttag['ID'])
            if newTags:
                # Update list of tags
                self.setTags()
                        
        return(idTags)

    def publishPost(self, post, link='', comment='', tags=[]):
        logging.debug("     Publishing in Wordpress...")
        title = post
        res = None
        try:
            logging.info("     Publishing: %s" % post)
            # The tags must be checked/added previously
            idTags = self.checkTags(tags)
            # They must be in a comma separated string
            idTags = ','.join(str(v) for v in idTags)
            payload = {"title":title,"content":comment,"status":'publish',#'draft', 
                    'tags':idTags}
            res = requests.post(self.api_base2 
                    + self.api_posts.format(self.my_site), 
                    headers = self.headers,
                    data = payload)
            if res.ok: 
                logging.info("Res: %s" % res)
                resJ = json.loads(res.text)
                logging.debug("Res text: %s" % resJ)
                logging.info("Res slug: %s" % resJ['generated_slug'])
                return("{} - \n https://{}/{}".format(title,
                    self.my_site,
                    resJ['generated_slug']))
        except:        
            logging.info("Fail!")
            logging.info(self.report('Wordpress', post, link, sys.exc_info()))
            return(self.report('Wordpress', post, link, sys.exc_info()))

        return 'OK'

    def getPostTitle(self, post):
        if 'title' in post:
            return(post['title'])
        else:
            return('')

    def getPostLink(self, post):    
        if 'URL' in post:
            return(post['URL'])
        else:
            return('')

    def extractImages(self, post): 
        res = []

        if 'content' in post:
            soup = BeautifulSoup(post['content'], 'lxml') 
            imgs = soup.find_all('img') 
            for img in imgs: 
                logging.debug(img)
                if img.has_attr('src'): 
                    res.append(img.get('src')) 
                else: 
                    res.append(img.get('data-large-file').split('?')[0])
        elif 'attachments' in post:
            for key in post['attachments']:
                if 'URL' in post['attachments'][key]:
                    res.append(post['attachments'][key]['URL'])
        else:
             logging.info("Fail image")
             logging.debug("Fail image %s", post)
             res = []
        return res
    
    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        post = self.getPost(i)
        
        if post:
            logging.debug("Post i: {}, {}".format(i,post))

            theTitle = self.getTitle(i)
            theLink = self.getLink(i)
            firstLink = theLink
            if 'content' in post: 
                content = post['content']
            else:
                content = theLink
            if 'excerpt' in post: 
                theSummary = post['excerpt']
            else:
                theSummary = content
            theSummaryLinks = content
            theImage=self.getImages(i)

            theContent=''
            comment = ''
            theSummaryLinks = ""

            if not content.startswith('http'):
                soup = BeautifulSoup(content, 'lxml')
                link = soup.a
                if link: 
                    firstLink = link.get('href')
                    if firstLink:
                        if firstLink[0] != 'h': 
                            firstLink = theLink

            if not firstLink: 
                firstLink = theLink

            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks
            
            theContent = ""
            theSummaryLinks = ""

            logging.debug("=========")
            logging.debug("Results: ")
            logging.debug("=========")
            logging.debug("Title:     ", theTitle)
            logging.debug("Link:      ", theLink)
            logging.debug("First Link:", firstLink)
            logging.debug("Summary:   ", content[:200])
            logging.debug("Sum links: ", theSummaryLinks)
            logging.debug("the Links"  , theLinks)
            logging.debug("Comment:   ", comment)
            logging.debug("Image;     ", theImage)
            logging.debug("Post       ", theTitle + " " + theLink)
            logging.debug("==============================================")
            logging.debug("")


            return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)
        else:
            logging.info("No post")
            return (None, None, None, None, None, None, None, None, None, None)

def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')
    import moduleWordpress

    wp = moduleWordpress.moduleWordpress()
    wp.setClient('avecesunafoto')
    res = wp.setPosts()
    if res[:4] == 'Fail':
       wp.authorize()
    sys.exit()

    print("Testing tags")
    wp.setTags()
    print(wp.getTags())
    #print(wp.checkTags(['test']))

    print("Testing posts")
    wp.setPosts()
    for i,post in enumerate(wp.getPosts()):
        print("{}) {} {}".format(i, wp.getPostTitle(post), 
            wp.getPostLink(post)))
        print(wp.obtainPostData(i))


    sel = input('Select one ')
    pos =  int(sel)
    post = wp.getPosts()[pos]
    print("{}) {} {}".format(pos, wp.getPostTitle(post), 
            wp.getPostLink(post)))
    sys.exit()


    #pos = wp.getLinkPosition('https://avecesunafoto.wordpress.com/2020/03/10/gamoncillo/')
    #img = wp.obtainPostData(pos)
    #print(img)
    #if img[3]:
    #    print(img[3])
    #    print(len(img[3]))
    ##for i in img[3]:
    #    #resizeImage(i)
    #    #input('next?')

    print("Testing posting")
    print(title, post)

    sys.exit()
    wp.publishPost(post, '', title)


    sys.exit()
    for i, post in enumerate(wp.getPosts()):
        print("p",i, ") ", post)
        #print("@%s: %s" %(tweet[2], tweet[0]))

    print(pos)
    print(wp.getPosts()[pos])
    title = wp.obtainPostData(pos)
    sys.exit()
    print("Testing title and link")
    
    for i, post in enumerate(wp.getPosts()):
        title = wp.getPostTitle(post)
        link = wp.getPostLink(post)
        #url = tw.getPostUrl(post)
        print("{}) Title: {}\nLink: {}\nUrl:{}\n".format(i,title,link,link))


    print("Testing obtainPostData")
    for (i,post) in enumerate(wp.getPosts()):
        print(i,") ",wp.obtainPostData(i))

    sys.exit()

if __name__ == '__main__':
    main()

