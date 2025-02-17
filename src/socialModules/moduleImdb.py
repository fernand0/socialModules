#!/usr/bin/env python

import configparser
import datetime
import json
import logging
import os
import sys
import time
import urllib

import requests
import tmdbsimple as tmdb

from socialModules.moduleContent import *
# from socialModules.moduleQueue import *


class moduleImdb(Content): #,Queue):

    def setClient(self, init=()):
        self.service = 'Imdb'
        self.client = None
        self.url=None
        self.fileTV = '/tmp/tv.html'
        self.gen = 'CN'
        self.cache = False
        self.channels = None
        self.posts = []
        
        logging.info(f"{self.indent} Setting client")
        logging.info(f"{self.indent} Setting client {str(init)}")
        # logging.info(f"Url {self.getUrl()}")
        date = time.strftime('%Y-%m-%d')
        if isinstance(init,str): 
            self.url = init 
        elif isinstance(init[1],str):
            self.url = init[1].format(date)
        else:
            self.url = init[1][2].format(date)
        try:
            try:
                config = configparser.ConfigParser()
                config.read(CONFIGDIR+'/.rssTMDb')
            except:
                logging.info("Some problem with configuration file")

            tmdb.API_KEY = config.get('TMDb', 'api_key')
            self.client = tmdb
            self.channels = config.get('TMDb', 'channels').split(',')
        except:
            logging.info("Fail")

    def setInfoData(self): 
        # This does not belong here; it is the source of the data
        posts = []
        self.data = []
        logging.info("Reading data...") 
        if os.path.exists(self.fileTV): 
            import time
            timeNow = time.time() 
            timeFile = os.path.getmtime(self.fileTV)
            dateFile = datetime.datetime.fromtimestamp(timeFile) 
            dateFile = str(dateFile)[:10] 
            dateToday = str(datetime.datetime.fromtimestamp(timeNow))[:10] 
            if ((timeNow - timeFile)/(60*60) < 20) and (dateFile == dateToday): 
                logging.info("Using cache") 
                json_data=open(self.fileTV).read() 
                self.cache = True 

        if not self.cache: 
            logging.info("Downloading data {}".format(self.url)) 
            req = urllib.request.Request(self.url, headers={
                      "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84"
                      }) 
            request = urllib.request.urlopen(req)
            json_data = request.read().decode() 
            f = open(self.fileTV, 'w') 
            f.write(json_data) 
            f.close() 

        soup = BeautifulSoup(json_data, features="lxml")
        logging.info("Data read...")
        links = []
        for link in soup.find_all("div", { "class" : "mc-image"}): 
            links.append(link)
        titles = []
        for title in soup.find_all("div", { "class" : "mtitle"}): 
            titles.append(title)
        channels = []
        for link in soup.find_all("div", { "class" : "canal-badge"}):
            channels.append(link)
        times = []
        for time in soup.find_all("div", { "class" : "triangle-badge"}):
            times.append(time)

        for i, link in enumerate(links): 
            e = {}
            cadName = channels[i].contents[1]['title']
            genero = titles[i].contents[3].replace(' ', '')
            title = titles[i].contents[0].contents[0]
            theLink = link.contents[1]['href']
            cadYear = titles[i].contents[1]#.contents
            posY = cadYear.find('(')
            year =  cadYear[posY+1:posY+5]
            hini = times[i].contents[0].contents[0].contents[0]
            hfin = ""
            e['release_date'] = year
            e['t'] = title
            e['URL'] = theLink
            e['CADENA'] = cadName
            e['hi'] = hini
            e['d'] = ""
            e['GENERO'] = genero
            posts.append(e)

            self.data.append((hini, hfin, title, '-', cadName, genero))

            #if cadName in self.channels:
            #    for e in i['events']:
            #    # for j in range(len(data['data'][i]['PROGRAMAS'])): 
            #        #print(j) 
            #        # genero = data['data'][i]['PROGRAMAS'][j]['GENERO'] 
            #        genero = e['g']
            #        if ('Cine' in e['t'] or genero == self.gen):
            #            # title = data['data'][i]['PROGRAMAS'][j]['TITULO'] 
            #            title = e['t']
            #            if not genero:
            #                e['g'] = self.gen
            #                genero = self.gen
            #            # horaIni = data['data'][i]['PROGRAMAS'][j]['HORA_INICIO']
            #            # horaFin = data['data'][i]['PROGRAMAS'][j]['HORA_FIN'] 
            #            hini = datetime.datetime.fromtimestamp(e['hi']) 
            #            hfin = datetime.datetime.fromtimestamp(e['hf'])
            #            # self.data.append((horaIni,horaFin, title, '-', cadName, genero)) 
            #            self.data.append((hini,hfin, title, '-', cadName, genero)) 
            #            # FIXME: ¿Todos o sólo estos?
            #            posts.append(e)
            #            posts[-1]['CADENA'] = cadName
        return posts

    def setPosts(self):
        logging.info(f"{self.indent} Setting posts")

        posts = self.setInfoData() 
        # print(f"Posts: {posts}")

        hh = time.strftime('%H:00') 
        dd = time.strftime('%d') 
        firstPost = True
        useCache = False
        j = 0
        for i, post in enumerate(posts): 
            hhIni = self.getPostTimeIni(post)
            # hhIni, ddIni = hhIni.hour, hhIni.day
            #ddIni = ""
            # if ((dd == str(ddIni) and hh <= str(hhIni))
            #         and (post['g'] == self.gen)):
            #     try:
            res = self.setPostMoreDataNew(post)
            #    except:
            #        res = ""
            j = j + 1
        # self.posts = sorted(posts, key = lambda d: d['HORA_INICIO'])
        # logging.info(f"Posts: {posts}")
        self.posts = sorted(posts, key = lambda d: d['hi'])

    def getPostTitle(self, post):
        logging.debug("getPostTitle {}".format(post))
        if isinstance(post, tuple):
            if post:
                return(post[2])
            else:
                return("")
        else:
            return post.get('t','')

    def getPostLink(self, post):
        if isinstance(post, dict):
            return post.get('URL', '')
        return ""

    def getPostCode(self, post):
        if isinstance(post, dict):
            return post.get('CADENA', '')
        if post:
            return(post[4])
        else:
            return("")

    def getPostContent(self, post):
        content = (
                  f"({self.getPostDate(post)}) {self.getPostCode(post)} "
                  f"[{self.getPostAvg(post)}] "
                  f"{self.getPostTimeIni(post)}-{self.getPostTimeEnd(post)} "
                  f"\n{self.getPostPlot(post)}\n "
                  f" {self.getPostStars(post)}" )
        return content

    def getPostLine(self, post): 
        # logging.info(f"Post: {post}")
        if post['g'] == 'CN': #True: #post['GENERO'] == 'Cine':
            logging.info("Post line {}".format(post))
            hini = datetime.datetime.fromtimestamp(self.getPostTimeIni(post))
            hini = f"{hini.hour}:{hini.minute}"
            hfin = datetime.datetime.fromtimestamp(self.getPostTimeEnd(post))
            hfin = f"{hfin.hour}:{hfin.minute}"
            line = (f"> [{self.getPostAvg(post)}] - "
                   f"({self.getPostCode(post)}) "
                   f"{hini}-{hfin}: "
                   f"{self.getPostTitle(post)}")
            logging.info("Post line formatted {}".format(line))

            return line

    def getPostAvg(self, post):
        if isinstance(post, dict):
            if 'RESULT' in post:
                return post.get('RESULT')[0].get('vote_average', '')
            else:
                return ''
        if post:
            return(post[3])
        else:
            return("")

    def getPostTimeIni(self, post):
        if isinstance(post, dict):
            return post.get('hi', '')
        if post:
            return(post[0])
        else:
            return("")

    def getPostDate(self, post):
        if isinstance(post, dict):
            if 'RESULT' in post:
                return post.get('RESULT')[0].get('release_date', '')
            else:
                return ''
        if post:
            return(post[8])
        else:
            return("")

    def getPostPlot(self, post):
        if isinstance(post, dict):
            if 'd' in post:
                return post.get('d')
            else:
                return ''
        if post:
            return(post[7])
        else:
            return("")

    def getPostStars(self, post):
        if isinstance(post, dict):
            if 'movie' in post:
                data = post.get('movie')
                director = ''
                if data and ('crew' in data['credits']):
                    for cred in data['credits']['crew']:
                        if cred['department'] == 'Directing':
                            director = cred['name']
                            break
                cast = []
                if 'credits' in data:
                    for name in data['credits']['cast'][:4]: 
                        cast.append(name['name'])
                return f"[{director}] {', '.join(cast)}"
            else:
                return ''
        if post:
            return(post[9])
        else:
            return("")

    def setPostMoreDataNew(self, post):
        postMore = None 
        mySearch = self.getClient().Search() 
        title = self.getPostTitle(post)
        logging.info(f"Post: {post}")
        logging.info(f"Title: {title}")
        import hashlib
        m = hashlib.md5()
        m.update(title.encode())
        titleHash = m.hexdigest()
        print(f"Hash: {titleHash}")
        fileNamePath = "/tmp/movies"
        fileNameHash = f"{fileNamePath}/{titleHash}"
        movieData = {}
        dataUpdate = {}
        if not os.path.exists(fileNamePath):
            try:
                os.mkdir(fileNamePath)
            except OSError:
                print ("Creation of the directory %s failed" % path)
        if os.path.exists(fileNameHash):
            with open(fileNameHash, 'r') as fHash:
                data = fHash.read()
                if data:
                    dataUpdate = json.loads(data)
        else:
            response = mySearch.movie(query=title) 
            print (f"ResSearch: {response}")
            if len(mySearch.results) > 0: 
                movie = tmdb.Movies(mySearch.results[0]['id']) 
                movieData['info'] = movie.info()
                movieData['credits'] = movie.credits()
                dataUpdate.update({'RESULT': mySearch.results})
                dataUpdate.update({'movie': movieData})
                if os.path.exists(fileNameHash):
                    with open(fileNameHash, 'w') as fHash:
                        fHash.write(json.dumps(dataUpdate))

        post.update(dataUpdate)
 
    def setPostMoreData(self, post):
        postMore = None 
        mySearch = self.getClient().Search() 
        title = self.getPostTitle(post)
        response = mySearch.movie(query=title) 
        print (f"ResSearch: {response}")
        if len(mySearch.results) > 0: 
            average = mySearch.results[0]['vote_average'] 
            overview = mySearch.results[0]['overview'] 
            movie = tmdb.Movies(mySearch.results[0]['id']) 
            director = None
            if 'crew' in movie.credits():
                for cred in movie.credits()['crew']:
                    if cred['department'] == 'Directing':
                        director = cred['name']
                        break
            genreList=[] 
            for genre in movie.info()['genres']: 
                genreList.append(genre['name']) 

            cast=[] 
            for name in movie.credits()['cast'][:4]: 
                cast.append(name['name'])

            release = movie.info()['release_date']

            logging.debug("Genre: {}".format(', '.join(genreList)))
            logging.debug("Overview: {}".format(movie.info()['overview']))
            logging.debug("Release: {}".format(release))
            logging.debug("Vote: {}".format(movie.info()['vote_average']))
            logging.debug('Cast: {}'.format(', '.join(cast)))
            if director:
                logging.debug('Director: {}'.format(director))
                postMore = (average, ', '.join(genreList), 
                    overview, release,'[{}] '.format(director)+ ', '.join(cast)) 
            else:
                postMore = (average, ', '.join(genreList), 
                    overview, release,', '.join(cast)) 

        return(postMore)

    def getPostTimeEnd(self, post):
        if isinstance(post, dict):
            return post.get('hf', '')
        if post:
            return(post[1])
        else:
            return("")

    def getPostId(self, post):
        if isinstance(post, dict):
            if 'RESULT' in post:
                return post.get('RESULT')[0].get('id', '')
            else:
                return ''
        idPost = -1
        if hasattr(self, 'ts'):
            idPost = post['ts']
        return(idPost)

    # def extractDataMessage(self, i):
    #     logging.info("Service %s"% self.service)
    #     (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

    #     if i < len(self.getPosts()):
    #         post = self.getPosts()[i]
    #         logging.info("Post --- {}".format(str(post)))
    #         theTitle = self.getPostTitle(post)
    #         theLink = None #self.getPostLink(post)
    #         code = self.getPostCode(post) 
    #         average = self.getPostAvg(post) 
    #         comment = '[{}] - ({}) {}-{}'.format(average, code, 
    #                 self.getPostTimeIni(post),
    #                 self.getPostTimeEnd(post))
    #         theContent = ""
    #         if len(post)>6 :
    #             theContent = '\n{}\n{}\n{} ({})'.format(post[5+2], 
    #                 post[5+4], post[5+1], post[5+3])
    #         logging.info("Post content {}".format(theContent))

    #     return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    # 
    # Src: ('imdb', 'set', 'http://www.movistarplus.es/programacion-tv/?v=json', 'posts')
    # 
    # More: {'url': 'http://www.movistarplus.es/programacion-tv/?v=json', 'service': 'imdb', 'imdb': 'fernand0', 'posts': 'posts', 'search': 'http://www.movistarplus.es/programacion-tv/{}/?v=json', 'direct': 'gmail', 'gmail': 'fernand0+tv@elmundoesimperfecto.com', 'hold': 'yes'}

    MODULE = 'imdb'

    indent = ""
    for src in rules.rules.keys():
        if src[0] == MODULE:
            print(f"Src: {src}")
            more = rules.more[src]
            break
    apiSrc = rules.readConfigSrc(indent, src, more)

    testingPosts = True
    if testingPosts:
        print("Testing posts")
        apiSrc.setPostsType("posts")
        apiSrc.setPosts()

        print("Testing title and link")

        for i, post in enumerate(apiSrc.getPosts()):
            if True: #post['GENERO'] == 'Cine':
                print(f"Post: {post}")
                title = apiSrc.getPostTitle(post)
                link = apiSrc.getPostLink(post)
                print(f"DAte: ({apiSrc.getPostDate(post)})")
                print(f"Code: {apiSrc.getPostCode(post)} ")
                print(f"Avg: [{apiSrc.getPostAvg(post)}] ")
                print(f"Ini-fin: {apiSrc.getPostTimeIni(post)}-{apiSrc.getPostTimeEnd(post)} ")
                print(f"plot: {apiSrc.getPostPlot(post)}\n ")
                print(f"Stars: {apiSrc.getPostStars(post)}" )
 
                url = apiSrc.getPostUrl(post)
                theId = apiSrc.getPostId(post)
                summary = apiSrc.getPostContent(post)
                image = apiSrc.getPostImage(post)
                print(f"{i}) Title: {title}\n"
                      f"Link: {link}\n"
                      f"Url: {url}\nId: {theId}\n"
                      f"Content: {summary} {image}")
                if ('Molly' in title):
                    return

        return



    return

    site = moduleImdb.moduleImdb()
    site.setClient((url, None))
    print("Testing set posts")
    site.setPosts()
    print("Testing get posts")
    #print(site.getPosts())
    for i,post in enumerate(site.getPosts()[-10:]):
        print(post)

    sys.exit()

    print("post",site.setPostMoreData(site.getPosts()[0]))

    #print(site.getPosts()[2])
    #print(site.setPostMoreData(2))


if __name__ == '__main__':
    main()
