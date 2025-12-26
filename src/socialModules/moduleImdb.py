#!/usr/bin/env python

import configparser
import datetime
import json
import logging
import os
import sys
import time
import urllib

import tmdbsimple as tmdb
from bs4 import BeautifulSoup

from socialModules.moduleContent import *


class moduleImdb(Content):
    def setClient(self, init=()):
        self.service = "Imdb"
        self.client = None
        # self.url = None
        self.fileTV = "/tmp/tv.html"
        self.gen = "CN"
        self.cache = False
        self.channels = None
        self.posts = []

        logging.info(f"{self.indent} Setting client")
        logging.info(f"{self.indent} Setting client {str(init)}")
        # logging.info(f"Url {self.getUrl()}")
        date = time.strftime("%Y-%m-%d")
        if isinstance(init, str):
            self.url = init
        elif isinstance(init[1], str):
            self.url = init[1].format(date)
        else:
            self.url = init[1][2].format(date)
        try:
            try:
                config = configparser.ConfigParser()
                config.read(CONFIGDIR + "/.rssTMDb")
            except:
                logging.info("Some problem with configuration file")

            tmdb.API_KEY = config.get("TMDb", "api_key")
            self.client = tmdb
            self.channels = config.get("TMDb", "channels").split(",")
        except:
            logging.info("Fail")

    def setInfoData(self):
        # This does not belong here; it is the source of the data
        posts = []
        self.data = []
        logging.info(f"Reading data from {self.fileTV} ...")
        self.cache = False
        if os.path.exists(self.fileTV):
            import time

            timeNow = time.time()
            timeFile = os.path.getmtime(self.fileTV)
            dateFile = datetime.datetime.fromtimestamp(timeFile)
            dateFile = str(dateFile)[:10]
            dateToday = str(datetime.datetime.fromtimestamp(timeNow))[:10]
            if ((timeNow - timeFile) / (60 * 60) < 20) and (dateFile == dateToday):
                logging.info("Using cache")
                json_data = open(self.fileTV).read()
                self.cache = True

        if not self.cache:
            logging.info("Downloading data {}".format(self.url))
            req = urllib.request.Request(
                self.url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84"
                },
            )
            request = urllib.request.urlopen(req)
            json_data = request.read().decode()
            f = open(self.fileTV, "w")
            f.write(json_data)
            f.close()

        soup = BeautifulSoup(json_data, features="lxml")
        logging.info("Data read...")
        links = []
        for link in soup.find_all("div", {"class": "mc-image"}):
            links.append(link)
        titles = []
        for title in soup.find_all("div", {"class": "mtitle"}):
            titles.append(title)
        channels = []
        for link in soup.find_all("div", {"class": "canal-badge"}):
            channels.append(link)
        times = []
        for time in soup.find_all("div", {"class": "triangle-badge"}):
            times.append(time)

        for i, link in enumerate(links):
            e = {}
            cadName = channels[i].contents[1]["title"]
            genero = titles[i].contents[3].replace(" ", "")
            title = titles[i].contents[0].contents[0]
            theLink = link.contents[1]["href"]
            cadYear = titles[i].contents[1]  # .contents
            posY = cadYear.find("(")
            year = cadYear[posY + 1 : posY + 5]
            hini = times[i].contents[0].contents[0].contents[0]
            hfin = ""
            e["release_date"] = year
            e["t"] = title
            e["URL"] = urllib.parse.urljoin(self.url, theLink)
            e["CADENA"] = cadName
            e["hi"] = hini
            e["d"] = ""
            e["GENERO"] = genero
            e["g"] = genero
            posts.append(e)

            self.data.append((hini, hfin, title, "-", cadName, genero))

            # if cadName in self.channels:
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

        hh = time.strftime("%H:00")
        dd = time.strftime("%d")
        firstPost = True
        useCache = False
        j = 0
        for i, post in enumerate(posts):
            hhIni = self.getPostTimeIni(post)
            # hhIni, ddIni = hhIni.hour, hhIni.day
            # ddIni = ""
            # if ((dd == str(ddIni) and hh <= str(hhIni))
            #         and (post['g'] == self.gen)):
            #     try:
            res = self.setPostMoreDataNew(post)
            #    except:
            #        res = ""
            j = j + 1
        # self.posts = sorted(posts, key = lambda d: d['HORA_INICIO'])
        # logging.info(f"Posts: {posts}")
        self.posts = sorted(posts, key=lambda d: d["hi"])

    def getApiPostTitle(self, post):
        logging.debug("getPostTitle {}".format(post))
        if isinstance(post, tuple):
            if post:
                return post[2]
            else:
                return ""
        else:
            return post.get("t", "")

    def getApiPostLink(self, post):
        print(f"Post: {post}")
        print(f"Url: {self.url}")
        if isinstance(post, dict):
            return urllib.parse.urljoin(self.url, post.get("URL", ""))
        return ""

    def getPostCode(self, post):
        if isinstance(post, dict):
            return post.get("CADENA", "")
        if post:
            return post[4]
        else:
            return ""

    def getPostContent(self, post):
        content = (
            f"({self.getPostDate(post)}) {self.getPostCode(post)} "
            f"[{self.getPostAvg(post)}] "
            f"{self.getPostTimeIni(post)}-{self.getPostTimeEnd(post)} "
            f"\n{self.getPostPlot(post)}\n "
            f" {self.getPostStars(post)}"
        )
        return content

    def getPostLine(self, post):
        logging.info(f"Post: {post}")
        if True:  # post['g'] == 'CN': #True: #post['GENERO'] == 'Cine':
            logging.info("Post line {}".format(post))
            hini = self.getPostTimeIni(post)
            # hini = f"{hini}"
            hfin = self.getPostTimeEnd(post)
            # hfin = f"{hfin.hour}:{hfin.minute}"
            line = (
                f"> [{self.getPostAvg(post)}] - "
                f"({self.getPostCode(post)}) "
                f"{hini}-{hfin}: "
                f"{self.getPostTitle(post)}"
            )
            logging.info("Post line formatted {}".format(line))

            return line

    def getPostAvg(self, post):
        if isinstance(post, dict):
            if "RESULT" in post:
                return post.get("RESULT")[0].get("vote_average", "")
            else:
                return ""
        if post:
            return post[3]
        else:
            return ""

    def getPostTimeIni(self, post):
        if isinstance(post, dict):
            return post.get("hi", "")
        if post:
            return post[0]
        else:
            return ""

    def getPostDate(self, post):
        if isinstance(post, dict):
            if "RESULT" in post:
                return post.get("RESULT")[0].get("release_date", "")
            else:
                return ""
        if post:
            return post[8]
        else:
            return ""

    def getPostPlot(self, post):
        if isinstance(post, dict):
            if "d" in post:
                return post.get("d")
            else:
                return ""
        if post:
            return post[7]
        else:
            return ""

    def getPostStars(self, post):
        if isinstance(post, dict):
            if "movie" in post:
                data = post.get("movie")
                director = ""
                if data and ("crew" in data["credits"]):
                    for cred in data["credits"]["crew"]:
                        if cred["department"] == "Directing":
                            director = cred["name"]
                            break
                cast = []
                if "credits" in data:
                    for name in data["credits"]["cast"][:4]:
                        cast.append(name["name"])
                return f"[{director}] {', '.join(cast)}"
            else:
                return ""
        if post:
            return post[9]
        else:
            return ""

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
        logging.debug(f"Hash: {titleHash}")
        fileNamePath = "/tmp/movies"
        fileNameHash = f"{fileNamePath}/{titleHash}"
        logging.info(f"fileName: {fileNameHash}")
        movieData = {}
        dataUpdate = {}
        if not os.path.exists(fileNamePath):
            try:
                os.mkdir(fileNamePath)
            except OSError:
                print("Creation of the directory %s failed" % path)
        if os.path.exists(fileNameHash):
            with open(fileNameHash, "r") as fHash:
                data = fHash.read()
                if data:
                    dataUpdate = json.loads(data)
        else:
            response = mySearch.movie(query=title)
            logging.info(f"ResSearch: {response}")
            if len(mySearch.results) > 0:
                movie = tmdb.Movies(mySearch.results[0]["id"])
                movieData["info"] = movie.info()
                movieData["credits"] = movie.credits()
                dataUpdate.update({"RESULT": mySearch.results})
                dataUpdate.update({"movie": movieData})
                logging.info(f"Data: {dataUpdate}")
                if os.path.exists(fileNamePath):
                    with open(fileNameHash, "w") as fHash:
                        fHash.write(json.dumps(dataUpdate))

        post.update(dataUpdate)

    def setPostMoreData(self, post):
        postMore = None
        mySearch = self.getClient().Search()
        title = self.getPostTitle(post)
        response = mySearch.movie(query=title)
        print(f"ResSearch: {response}")
        if len(mySearch.results) > 0:
            average = mySearch.results[0]["vote_average"]
            overview = mySearch.results[0]["overview"]
            movie = tmdb.Movies(mySearch.results[0]["id"])
            director = None
            if "crew" in movie.credits():
                for cred in movie.credits()["crew"]:
                    if cred["department"] == "Directing":
                        director = cred["name"]
                        break
            genreList = []
            for genre in movie.info()["genres"]:
                genreList.append(genre["name"])

            cast = []
            for name in movie.credits()["cast"][:4]:
                cast.append(name["name"])

            release = movie.info()["release_date"]

            logging.debug("Genre: {}".format(", ".join(genreList)))
            logging.debug("Overview: {}".format(movie.info()["overview"]))
            logging.debug("Release: {}".format(release))
            logging.debug("Vote: {}".format(movie.info()["vote_average"]))
            logging.debug("Cast: {}".format(", ".join(cast)))
            if director:
                logging.debug("Director: {}".format(director))
                postMore = (
                    average,
                    ", ".join(genreList),
                    overview,
                    release,
                    "[{}] ".format(director) + ", ".join(cast),
                )
            else:
                postMore = (
                    average,
                    ", ".join(genreList),
                    overview,
                    release,
                    ", ".join(cast),
                )

        return postMore

    def getPostTimeEnd(self, post):
        if isinstance(post, dict):
            return post.get("hf", "")
        if post:
            return post[1]
        else:
            return ""

    def getPostId(self, post):
        if isinstance(post, dict):
            if "RESULT" in post:
                return post.get("RESULT")[0].get("id", "")
            else:
                return ""
        idPost = -1
        if hasattr(self, "ts"):
            idPost = post["ts"]
        return idPost

    def register_specific_tests(self, tester):
        pass

    def get_user_info(self, client):
        return ""

    def get_post_id_from_result(self, result):
        return None


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    imdb_module = moduleImdb()
    tester = ModuleTester(imdb_module)
    tester.run()


if __name__ == "__main__":
    main()
