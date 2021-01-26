#!/usr/bin/env python

import configparser
import datetime
import json
import logging
import os
import requests
import sys
import time
import urllib

from moduleContent import *
from moduleQueue import *

import tmdbsimple as tmdb

class moduleImdb(Content,Queue):

    def __init__(self):
        super().__init__()
        self.service = 'Imdb'
        self.client = None
        self.url=None
        self.fileTV = '/tmp/tv.json'
        self.gen = 'Cine'
        self.cache = False
        self.channels = None
        self.posts = []
        
    def setClient(self, init=()):
        logging.info("Setting client")
        logging.info(f"Setting client {str(init)}")
        date = time.strftime('%Y-%m-%d')
        if isinstance(init,str): 
            self.url = init 
        elif isinstance(init[2],str):
            self.url = init[2].format(date)
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
        # This does not belong here it is the source of the data
        self.data = []
        logging.info("Reading data...") 
        if os.path.exists(self.fileTV): 
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
            request = urllib.request.urlopen(self.url) 
            json_data = request.read().decode() 
            f = open(self.fileTV, 'w') 
            f.write(json_data) 
            f.close() 

        data = json.loads(json_data) 
        logging.info("Data read...")
        for i in data['data'].keys(): 
            if i[:-5] in self.channels: 
                cadName = data['data'][i]['DATOS_CADENA']['NOMBRE'] 
                for j in range(len(data['data'][i]['PROGRAMAS'])): 
                    #print(j) 
                    genero = data['data'][i]['PROGRAMAS'][j]['GENERO'] 
                    if genero == self.gen:
                        title = data['data'][i]['PROGRAMAS'][j]['TITULO'] 
                        horaIni = data['data'][i]['PROGRAMAS'][j]['HORA_INICIO']
                        horaFin = data['data'][i]['PROGRAMAS'][j]['HORA_FIN'] 
                        self.data.append((horaIni,horaFin, title, '-', cadName, genero)) 

    def setPosts(self):
        logging.info(" Setting posts")

        self.setInfoData() 

        hh = time.strftime('%H:00') 
        firstPost = True
        useCache = False
        for post in self.data: 
            if (hh <= post[0]): 
                res = self.setPostMoreData(post)
                logging.debug("More data: {}".format(str(res)))
                if res: 
                    post = post[:3] + (res[0], ) + post[4:] + res[1:]
                else:
                    post = post[:3] + ('-', ) + post[4:] 
                #if firstPost and self.posts and (self.posts[0][2] != post [2]): 
                if firstPost: # and (self.posts and self.posts[0][2] != post [2]): 
                    # We have old data
                    self.posts = []
                    firstPost = False
                    useCache = False
                if not useCache:
                    self.posts.append(post) 
                    logging.info("Post more {}".format(str(post)))

        if not useCache:
            self.posts.sort()


    def getPostTitle(self, post):
        logging.debug("getPostTitle {}".format(post))
        if post:
            return(post[2])
        else:
            return("")

    def getPostLink(self, post):
        return ""

    def getPostCode(self, post):
        if post:
            return(post[4])
        else:
            return("")

    def getPostLine(self, post): 
        logging.info("Post line {}".format(post))
        line = '> [{}] - ({}) {}-{}: {}'.format(post[3], post[4], 
                post[0], post[1], post[2])
        logging.info("Post line formatted {}".format(line))

        return line

    def getPostAvg(self, post):
        if post:
            return(post[3])
        else:
            return("")

    def getPostTimeIni(self, post):
        if post:
            return(post[0])
        else:
            return("")

    def setPostMoreData(self, post):
        postMore = None 
        mySearch = self.getClient().Search() 
        title = self.getPostTitle(post)
        response = mySearch.movie(query=title) 
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
        if post:
            return(post[1])
        else:
            return("")

    def getPostId(self, post):
        idPost = -1
        if hasattr(self, 'ts'):
            idPost = post['ts']
        return(idPost)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

        if i < len(self.getPosts()):
            post = self.getPosts()[i]
            logging.info("Post --- {}".format(str(post)))
            theTitle = self.getPostTitle(post)
            theLink = None #self.getPostLink(post)
            code = self.getPostCode(post) 
            average = self.getPostAvg(post) 
            comment = '[{}] - ({}) {}-{}'.format(average, code, 
                    self.getPostTimeIni(post),
                    self.getPostTimeEnd(post))
            theContent = ""
            if len(post)>6 :
                theContent = '\n{}\n{}\n{} ({})'.format(post[5+2], 
                    post[5+4], post[5+1], post[5+3])
            logging.info("Post content {}".format(theContent))

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    config = configparser.ConfigParser()
    config.read(CONFIGDIR+'/.rssBlogs')

    url = config.get('Blog23', 'url')
    import moduleImdb

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
