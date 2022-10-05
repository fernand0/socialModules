#!/usr/bin/env python

import configparser
import logging
import sys
import time
import urllib

import click
from bs4 import BeautifulSoup
from slack_sdk import WebClient

from moduleContent import *
from moduleQueue import *

# from slack_sdk.errors import SlackApiError

# https://slack.dev/python-slack-sdk/v3-migration/




class moduleSlack(Content, Queue):

    def __init__(self):
        super().__init__()
        self.slack_token = None
        self.user_slack_token = None
        self.channel = None
        self.postaction = None
        self.service = "Slack"

    def getKeys(self, config):
        slack_token = config.get(self.service, "oauth-token")
        user_slack_token = config.get(self.service, "user-oauth-token")
        return (slack_token, user_slack_token)

    def initApi(self, keys):
        logging.info("     Connecting {}".format(self.service))
        if self.user and self.user.find('/')>=0:
            self.name = self.user.split('/')[2].split('.')[0]
        else:
            self.name = self.user
        if self.user.find('@')>=0:
            channel, user = self.user.split('@')
            self.user = user
            #self.setChannel(channel)

        client = WebClient(keys[0])
        self.slack_token = keys[0]
        self.user_slack_token = keys[1]
        return client

    def getChannels(self):
        response = self.getClient().conversations_list()
        conversations = response.get("channels", '')
        return conversations

    def setChannel(self, channel=''):
        # setPage in Facebook
        if not channel:
            channel = self.getChannels()[0].get('name','')
        theChannel = self.getChanId(channel)
        self.channel = theChannel

    def getChannel(self):
        return self.channel

    def setSlackClient(self, slackCredentials):
        config = configparser.ConfigParser()
        if not slackCredentials:
            slackCredentials = CONFIGDIR + "/.rssSlack"
        config.read(slackCredentials)

        self.slack_token = config["Slack"].get("oauth-token")
        self.user_slack_token = config["Slack"].get("user-oauth-token")

        try:
            self.sc = WebClient(self.slack_token)
        except:
            logging.info(self.report("Slack", "", "", sys.exc_info()))
            self.sc = slack.WebClient(token=self.slack_token)

        config = configparser.ConfigParser()
        config.read(CONFIGDIR + "/.rssBlogs")
        section = "Blog7"

        url = config.get(section, "url")
        self.setUrl(url)
        self.oldsetSocialNetworks(config, section)
        #    # if ('buffer' in config.options(section)):
        #    #    self.setBufferapp(config.get(section, "buffer"))

        if "cache" in config.options(section):
            self.setProgram(config.get(section, "cache"))
            logging.info("getProgram {}".format(str(self.getProgram())))

    def getSlackClient(self):
        return self.sc

    def setApiPosts(self):
        if not self.channel:
            # FIXME
            # Can we improve this in mosuleSlack and moduleFacebook?
            self.setChannel('links')
        posts = []
        theChannel = self.getChannel()
        self.getClient().token = self.slack_token
        data = {"limit": 1000, "channel": theChannel}
        history = self.getClient().api_call("conversations.history", data=data)
        try:
            posts = history["messages"]
        except:
            posts = []

        logging.debug(f"Posts: {posts}")
        return posts

    def processReply(self, reply):
        # FIXME: Being careful with publishPost, publishPosPost, publishNextPost, publishApiPost
        res = reply
        if isinstance(reply, dict):
           res = reply.get('ok','Fail!')
        return res

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            title, link, comment = args
        if kwargs:
            more = kwargs
        chan = self.getChannel()
        if not chan:
            self.setChannel()
            chan = self.getChannel()
        self.getClient().token = self.user_slack_token
        data = {"channel": chan, "text": f"{title} {link}"}
        result = self.getClient().api_call("chat.postMessage", data=data)  # ,
        self.getClient().token = self.slack_token
        return result

    def deleteApiPosts(self, idPost):
        # theChannel or the name of the channel?
        theChan = self.getChannel()

        result = None

        self.getClient().token = self.user_slack_token
        data = {"channel": theChan, "ts": idPost}
        result = self.getClient().api_call(
            "chat.delete", data=data
        )  # , channel=theChannel, ts=idPost)

        return result

    def getPostId(self, post):
        return (post.get('ts',''))

    def setPostTitle(self, post, newTitle):
        if ("attachments" in post) and ("title" in post["attachments"][0]):
            post["attachments"][0]["title"] = newTitle
        elif "text" in post:
            text = post["text"]
            if text.startswith("<"):
                if "|" in text:
                    title = text.split("|")[1]
                else:
                    title = text
                titleParts = title.split(">")
                title = newTitle
                if (len(titleParts) > 1) and (titleParts[1].find("<") >= 0):
                    # There is a link
                    title = title + ' ' + titleParts[1].split("<")[0]
            else:
                pos = text.find("<")
                if pos>=0:
                    title = newTitle + ' ' + text[pos:]
                else:
                    title = newTitle

            # Last space
            posSpace = text.rfind(' ')
            post["text"] = title + text[posSpace:]
            print(f"Title: {post['text']}")
        else:
            return "No title"

        return post

    def getPostTitle(self, post):
        # print(f"Post: {post}")
        if ("attachments" in post) and ("title" in post["attachments"][0]):
            return post["attachments"][0]["title"]
        elif "text" in post:
            text = post["text"]
            if text.startswith("<"):
                if "|" in text:
                    title = text.split("|")[1]
                else:
                    title = text
                titleParts = title.split(">")
                title = titleParts[0]
                if (len(titleParts) > 1) and (titleParts[1].find("<") >= 0):
                    # There is a link
                    title = title + titleParts[1].split("<")[0]
            else:
                pos = text.find("<")
                if pos>=0:
                    title = text[:pos]
                else:
                    title = text
            return title
        else:
            return "No title"

    def getPostUrl(self, post):
        return (
            f"{self.getUser()}archives/"
            f"{self.getChannel()}/p{self.getPostId(post)}"
        )

    def getPostContent(self, post):
        return self.getPostContentHtml(post)

    def getPostContentHtml(self, post):
        if "attachments" in post:
            text = post.get("attachments", [{}])[0].get('text', '')
        else:
            text = post.get('text', '')
        return text

    def getPostLink(self, post):
        link = ''
        if "attachments" in post:
            link = post["attachments"][0]["original_url"]
        else:
            text = post["text"]
            if text.startswith("<") and text.count("<") == 1:
                # The link is the only text
                link = post["text"][1:-1]
            else:
                # Some people include URLs in the title of the page
                pos = text.rfind("<")
                link = text[pos + 1 : -1]
        return link

    def getPostImage(self, post):
        return post.get('attachments',[{}])[0].get('image_url', '')

    def getChanId(self, name):
        logging.debug("getChanId %s" % self.service)

        self.getClient().token = self.user_slack_token
        chanList = self.getClient().api_call("conversations.list")["channels"]
        self.getClient().token = self.slack_token
        for channel in chanList:
            if channel["name_normalized"] == name:
                return channel["id"]
        return None

    def getBots(self, channel="tavern-of-the-bots"):
        # FIXME: this does not belong here
        if not self.posts:
            oldChan = self.getChannel()
            self.setChannel(channel)
            self.setPosts()
            self.channel = oldChan
        msgs = {}
        for msg in self.getPosts():
            if msg["text"].find("Hello") >= 0:
                posN = msg["text"].find("Name:") + 6
                posFN = msg["text"].find('"', posN)
                posI = msg["text"].find("IP:") + 4
                posFI = msg["text"].find(" ", posI + 1) - 1
                posC = msg["text"].find("[")
                name = msg["text"][posN:posFN]
                ip = msg["text"][posI:posFI]
                command = msg["text"][posC + 1 : posC + 2]
                if name not in msgs:
                    theTime = "%d-%d-%d" % time.localtime(float(msg["ts"]))[:3]
                    msgs[name] = (ip, command, theTime)
        theBots = []
        for name in msgs:
            a, b, c = msgs[name]
            theBots.append("{2} [{1}] {0} {3}".format(a, b, c, name))

        return theBots

    def search(self, channel, text):
        logging.debug("     Searching in Slack...")
        try:
            self.getClient().token = self.slack_token
            data = {"query": text}
            res = self.getClient().api_call(
                "search.messages", data=data
            )  # , query=text)

            if res:
                logging.info(self.report(self.service, "", "", sys.exc_info()))
                return res
        except:
            return self.report("Slack", text, sys.exc_info())


def main():

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format="%(asctime)s %(message)s"
    )

    import moduleRules
    import moduleSlack
    rules = moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    # 
    # src: ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
    #
    # More: {'url': 'http://fernand0-errbot.slack.com/', 'service': 'slack', 'cache': 'linkedin\ntwitter\nfacebook\nmastodon\ntumblr', 'twitter': 'fernand0Test', 'facebook': 'Fernand0Test', 'mastodon': '@fernand0@mastodon.social', 'linkedin': 'Fernando Tricas', 'tumblr': 'fernand0', 'buffermax': '9'}
    # It can be empty: {}
    
    indent = ""
    for src in rules.rules.keys():
        if src[0] == 'slack':
            print(f"Src: {src}")
            more = rules.more[src]
            break
    apiSrc = rules.readConfigSrc(indent, src, more)

    apiSrc.setChannel("links")

    testingInit = False
    if testingInit:
        import moduleRules
        src = ('slack', 'set', 'http://fernand0-errbot.slack.com/', 'posts')
        rules = moduleRules.moduleRules()
        more = {}
        indent = ''
        apiSrc = rules.readConfigSrc(indent, src, more)
        logging.info(f"User: {apiSrc.getUser()}")
        logging.info(f"Name: {apiSrc.getName()}")
        logging.info(f"Nick: {apiSrc.getNick()}")
        return

    testingPublishing = True
    if testingPublishing:
        links  = [
'https://www.muyinteresante.es/ciencia/articulo/cajal-y-la-divulgacion-cientifica-171662364442',
'https://philip.greenspun.com/blog/2022/08/30/building-self-esteem-in-oslo/',
'https://hackaday.com/2022/09/07/the-era-of-distributed-independent-email-servers-is-over/',
'https://cincodias-elpais-com.cdn.ampproject.org/c/s/cincodias.elpais.com/cincodias/2022/09/15/companias/1663236364_939136.amp.html',
'https://www.genbeta.com/a-fondo/cuando-google-fotos-gratuito-se-acabo-comence-a-usar-alternativa-que-ha-acabado-gustandome-video-no-veo-solucion',
'https://www.genbeta.com/actualidad/como-se-hizo-fotos-instagram-accesible-gracias-a-camaras-urbanas-a-ia-este-artista-experto-privacidad',
'https://www.xataka.com/entrevistas/huawei-cree-que-puede-resurgir-mercado-smartphone-esta-su-vision-para-europa',
'https://www.xataka.com/movilidad/inesperada-resurreccion-tren-hotel-como-europa-esta-impulsando-nuevo-frente-al-avion',
'https://www.theregister.com/2022/09/01/surrey_police_waze_traffic/',
'https://www.facebook.com/login/?next=https%3A%2F%2Fwww.facebook.com%2Facysvalencia%2Fposts%2Fpfbid0scaycn9wr3Tc31VSFfmNCr8kdhrE9ThnLzCSNtogmmWuZKi4u85gTbyutjwchvC7l',
'https://unaaldia.hispasec.com/2022/09/rockstar-games-es-hackeado-y-se-filtra-codigo-fuente-y-videos-de-gta-6.html',
'https://blogs.harvard.edu/doc/2022/09/18/attention-is-not-a-commodity/',
'https://www.wired.com/story/ukraine-war-mobile-networks-russia/',
'https://www.pewresearch.org/journalism/fact-sheet/social-media-and-news-fact-sheet/',
'https://www.julianmarquina.es/aplicaciones-para-hacer-un-seguimiento-de-los-libros-leidos-y-pendientes-de-leer/',
'https://pimylifeup.com/raspberry-pi-freshrss/',
'https://www.edn.com/1st-fortran-program-runs-september-20-1954/',
'https://github.com/DonDebonair/slack-machine',
'https://deps.dev/about',
'https://www.bbg.org/gardening/article/hardy_cacti',
'https://www.ctcactussociety.org/john-spain-slide-shows',
'https://carpetaciudadana.gob.es/carpeta/clave.htm',
'https://higheredstrategy.com/the-decline-of-american-higher-education/',
'https://privacy.twitter.com/en/blog/2022/an-issue-impacting-password-resets',
'https://www.idsalliance.org/2022-trends-in-security-digital-identities-breaches-continue-to-plague-organizations/',
'https://fission.codes/blog/ipfs-thing-intro-webnative-file-system/',
'https://cfenollosa.com/blog/after-self-hosting-my-email-for-twenty-three-years-i-have-thrown-in-the-towel-the-oligopoly-has-won.html',
'https://acreelman.blogspot.com/2022/09/on-personal-note-at-crossroads-in-life.html',
'https://blog.google/products/gmail/gmail-experts-rewrite-my-emails/',
'https://bertrandmeyer.com/2022/09/12/oosc-2-available-online-officially/',
'https://martinfowler.com/articles/patterns-of-distributed-systems/request-waiting-list.html',
'https://developers.slashdot.org/story/22/09/18/1624258/will-low-code-and-no-code-development-replace-traditional-coding',
'https://techfordemocracy.dk/join-the-initiative/',
'https://github.blog/2022-09-08-github-copilot-now-available-for-teachers/',
'https://hynek.me/articles/productive-fruit-fly-programmer/',
'https://simonwillison.net/2022/Sep/19/docsets/#atom-everything',
'https://picodotdev.github.io/blog-bitix/2022/09/introduccion-al-protocolo-oauth-2-para-delegar-la-autorizacion/',
'https://spectrum.ieee.org/upcycle-a-vintage-lcd',
'https://artemis.sh/2022/09/18/wayland-from-an-x-apologist.html',
'http://blog.computationalcomplexity.org/2022/09/there-are-two-different-definitions-of.html',
'http://blog.computationalcomplexity.org/2022/09/thirty-years-of-dagstuhl.html',
'https://scottaaronson.blog/?p=6718',
'https://www.trellix.com/en-us/about/newsroom/stories/threat-labs/tarfile-exploiting-the-world.html',
'https://www.xataka.com/medicina-y-salud/cada-vez-hay-cyborgs-humanos-caminando-mundo-su-problema-no-ciencia-ley',
'https://www.xataka.com/cine-y-tv/mad-max-furia-carretera-como-obra-maestra-george-miller-sufrio-anos-traumas-conflictos-llegar-al-cine',
'https://www.genbeta.com/a-fondo/compre-online-acabe-registrada-privicompras-pagando-15-euros-al-mes-saberlo-le-puse-solucion-recupere-dinero',
'https://lsc-canfranc.es/jornada-puertas-abiertas/',
'https://www.unizar.es/actualidad/vernoticia_ng.php?id=68447',
'https://www.camarahuesca.com/events/jornada-industria-4-0-transforma-tu-empresa/',
'https://www.bleepingcomputer.com/news/security/ragnar-locker-ransomware-claims-attack-on-portugals-flag-airline/',
'https://dl.acm.org/doi/fullHtml/10.1145/3501247.3531545',
'https://www.netwrix.com/47_percent_of_educational_institutions_experienced_a_cyberattack_on_their_cloud_infrastructure_in_2022.html',
'https://unaaldia.hispasec.com/2022/09/chema-alonso-entrevista-roman-ramirez.html',
'https://www.spanishrailwaysnews.com/noticias.asp?cs=repo',
'https://www.theatlantic.com/ideas/archive/2022/09/big-tech-founders-gates-neumann-jobs/671519/',
'https://python-bloggers.com/2022/09/automatically-sort-python-module-imports-using-isort/',
'https://zenodo.org/record/7097366#.Yy3dVtJBxhE',
'https://www.xataka.com/investigacion/algunos-cientificos-no-creen-computacion-cuantica-minimo-estas-razones-dos-ellos',
'https://www.xataka.com/movilidad/citroen-cree-que-no-necesitas-coche-mil-pantallas-aplicaciones-sino-coche-barato-tiene-uno',
'https://www.archdaily.com/954611/are-suburbs-the-new-cities-exploring-the-future-of-suburban-development',
'https://www.microsoft.com/security/blog/2022/09/22/malicious-oauth-applications-used-to-compromise-email-servers-and-spread-spam/',
'https://elordenmundial.com/tecnonacionalismo-estrategia-china-potencia-tecnologica-gepolitica/',
'https://blog.segu-info.com.ar/2022/09/albania-expulso-diplomaticos-iranies.html',
'https://signal.org/blog/run-a-proxy/',
'https://hackaday.com/2022/09/23/nazi-weapons-of-the-future/',
'https://hackaday.com/2022/09/21/a-3d-printed-marble-run-features-neat-elevator-linkage/',
'https://lifehacker.com/why-your-wifi-router-needs-a-guest-mode-1849573880',
'https://www.elperiodicodearagon.com/zaragoza/2022/09/24/entorno-paraninfo-jardin-da-lecciones-zaragoza-zaragozeando-75770497.html',
'https://www.theverge.com/2022/9/16/23356974/health-cybersecurity-devices-fbi-ransomware',
'https://www.nytimes.com/2022/09/14/technology/personaltech/texting-ios-android.html',
'https://lifehacker.com/why-passive-income-is-a-myth-1849568396',
'https://www.microsiervos.com/archivo/ordenadores/ojo-copias-seguridad-nube.html',
'https://www.cpsc.gov/Newsroom/News-Releases/2022/CPSC-Warns-Consumers-to-Immediately-Stop-Using-Male-to-Male-Extension-Cords-Sold-on-Amazon-com-Due-to-Electrocution-Fire-and-Carbon-Monoxide-Poisoning-Hazards',
'https://interferencia.cl/articulos/mails-hackeados-informes-del-emco-recomendaron-familias-castrenses-estar-abastecidas-al',
'https://www.xataka.com/energia/visionario-plan-anos-60-que-ha-convertido-a-espana-potencia-regasificadora',
'https://malcolmgladwell.bulletin.com/princeton-university-is-the-worlds-first-perpetual-motion-machine/',
'https://activatelearning.com.au/2022/09/unselfing/',
'https://www.theguardian.com/us-news/2022/sep/24/los-angeles-drought-resistant-plants-lawns-landscaping',
'https://www.vanitatis.elconfidencial.com/estilo/ocio/2022-09-25/matarrana-teruel-turismo-planes_3494925/',
'https://www.theguardian.com/world/2022/sep/25/spain-plans-digital-nomad-visa-scheme-to-attract-remote-workers?CMP=Share_iOSApp_Other',
'https://theobjective.com/espana/2022-09-25/gran-engano-universidades/',
'https://www.whatsapp.com/security/advisories/2022/',
'https://landgeist.com/2022/07/16/trust-in-the-news/',
'https://www.nytimes.com/2022/09/24/business/linkedin-social-experiments.html?referringSource=articleShare',
'https://www.theverge.com/2022/9/16/23356959/uber-hack-social-engineering-threats',
'https://thenewstack.io/nsa-software-supply-chain-guidance/',
'https://www.avclub.com/hans-niemann-anal-beads-chess-grandmaster-cam-site-1849545231',
'https://securityawareness.usalearning.gov/cdse/nitam/index.html',
'https://www.wired.com/story/nigeria-cybersecurity-issues/',
'https://edition.cnn.com/2022/09/08/politics/fbi-north-korea-hackers-30-million-axie-infinity/index.html',
'https://www.wired.com/story/tiktok-nationa-security-threat-why/',
'https://www.fierceelectronics.com/iot-wireless/ovens-eyes-chameleon-fridge-and-other-electronic-eccentricities-ifa',
'https://www.cbc.ca/news/politics/champagne-telecommunications-agreement-1.6574900',
'https://www.bleepingcomputer.com/news/security/google-microsoft-can-get-your-passwords-via-web-browsers-spellcheck/',
'https://joeposnanski.substack.com/p/checkmate',
'https://www.theregister.com/2022/09/17/glasses_reflections_zoom/',
'https://www.theverge.com/2022/9/26/23369070/twitch-revenue-split-70-30-streamers-reaction-amazon',
'https://www.euronews.com/2022/09/24/tap-cyberattack-portuguese-presidents-personal-data-stolen',
'https://app.wallabag.it/share/63329827233b60.41356865',
'https://arstechnica.com/gadgets/2022/09/a-history-of-arm-part-1-building-the-first-chip/',
'https://www.cloudflare.com/ko-kr/press-releases/2022/cloudflare-announces-the-first-zero-trust-sim/',
'https://www.laaab.es/2022/09/un-laboratorio-para-experimentar-con-el-futuro/',
'http://www.figuritas.es/',
                ]
        apiSrc.setChannel('links')
        for link in links:
            apiSrc.publishPost('', link, '')
            import time
            import random
            time.sleep(5+random.random()*5)
        return

    testingEditTitle = False
    if testingEditTitle:
        print("Testing edit posts")
        site.setPostsType("posts")
        site.setPosts()
        print(site.getPostTitle(site.getPosts()[0]))
        print(site.getPostLink(site.getPosts()[0]))
        input("Edit? ")
        site.setPostTitle(site.getPosts()[0], "prueba")
        print(site.getPostTitle(site.getPosts()[0]))
        print(site.getPostLink(site.getPosts()[0]))
        return


    testingPosts = False
    if testingPosts:
        print("Testing posts")
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('links')
        apiSrc.setPosts()

        print("Testing title and link")

        for i, post in enumerate(apiSrc.getPosts()):
            # print(f"Post: {post}")
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            url = apiSrc.getPostUrl(post)
            theId = apiSrc.getPostId(post)
            summary = apiSrc.getPostContentHtml(post)
            image = apiSrc.getPostImage(post)
            print(f"{i}) Title: {title}\n"
                  f"Link: {link}\n"
                  f"Url: {url}\nId: {theId}\n"
                  f"Content: {summary} {image}")

        if input("All? (y/n) ") == 'y':
            print(f"Channels: {apiSrc.getChannels()}")
            for channel in apiSrc.getChannels():
                print(f"Name: {channel['name']}")
                apiSrc.setChannel(channel['name'])
                apiSrc.setPosts()
                for i, post in enumerate(apiSrc.getPosts()):
                    print(f"{i}) Title: {apiSrc.getPostTitle(post)}\n"
                          f"Link: {apiSrc.getPostLink(post)}\n")
                print(f"Name: {channel['name']}")
                input("More? (any key to continue) ")

        return

    testingDeleteLast = False
    if testingDeleteLast:
        site.setPostsType("posts")
        site.setPosts()
        print(f"Testing delete last")
        post = site.getPosts()[0]
        input(f"Delete {site.getPostTitle(post)}? ")
        site.delete(0)
        return
        
    testingDelete = False
    if testingDelete:
        # print("Testing posting and deleting")
        res = site.publishPost(
            "FOSDEM 2022 - FOSDEM 2022 will be online",
            "https://fosdem.org/2022/news/2021-10-22-fosdem-online-2022/", ""
        )
        print("res", res)
        # idPost = res
        # print(idPost)
        # input("Delete? ")
        # site.deletePostId(idPost)
        # sys.exit()

        i = 0
        post = site.getPost(i)
        title = site.getPostTitle(post)
        link = site.getPostLink(post)
        url = site.getPostUrl(post)
        print(post)
        print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
        print(f"Content: {site.getPostContentHtml(post)}\n")
        input("Delete?")
        site.delete(i)
        return

    myChan = None
    channels = []
    testingChannels = False
    if testingChannels:
        for i, chan in enumerate(apiSrc.getChannels()):
            channels.append(chan.get('name',''))
            print(f"{i}) Chan: {chan.get('name','')}")


        select = input("Which one? ")
        if select.isdigit():
            channels = [ channels[int(select)], ]

    testingDelete = False
    if testingDelete:
        for chan in channels:
            apiSrc.setChannel(chan)

            apiSrc.setPosts()

            [ print(f"{i}) {apiSrc.getPostTitle(post)}")
                    for i, post in enumerate(apiSrc.getPosts()) ]
            pos = input("Which post to delete (a for all)? ")
            if pos.isdigit():
                post = apiSrc.getPost(int(pos))
                apiSrc.deletePost(post)
            else:
                for pos, post in enumerate(apiSrc.getPosts()):
                    apiSrc.deletePost(post)

        return

    testingCleaning = False
    if testingCleaning:
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('tavern-of-the-bots')
        apiSrc.setPosts()
        ipList = {}
        for i, post in enumerate(apiSrc.getPosts()):
            title = apiSrc.getPostTitle(post)
            link = apiSrc.getPostLink(post)
            url = apiSrc.getPostUrl(post)
            print("Title: {}\nTuit: {}\nLink: {}\n".format(title, link, url))
            # if 'Rep' in link:
            # if 'foto' in link:
            # if '"args": ""' in link:
            if 'Hello' in title:
                posIni = title.find('IP')+4
                posFin = title.find(' ', posIni) - 1
                if title[posIni:posFin] not in ipList:
                    print(title[posIni:posFin])
                    ipList[title[posIni:posFin]] = 1
                    print(ipList)
                else:
                    print(f"{link[posIni:posFin]}")
                    input("Delete? ")
                    print(f"Deleted {apiSrc.delete(i)}")

            # time.sleep(5)

    sys.exit()

    res = site.search("url:fernand0")

    for tt in res["statuses"]:
        # print(tt)
        print(
            "- @{0} {1} https://twitter.com/{0}/status/{2}".format(
                tt["user"]["name"], tt["text"], tt["id_str"]
            )
        )
    sys.exit()


if __name__ == "__main__":
    main()

    sys.exit()

    print("Set Client")
    site.setClient("fernand0-errbot")
    print("sc", site.getClient())
    site.setUrl(url)
    site.setPosts()

    print("Posts: {}".format(site.getPosts()))
    sys.exit()
    theChannel = site.getChanId(CHANNEL)
    print("the Channel {} has code {}".format(CHANNEL, theChannel))
    site.setPosts(CHANNEL)
    # post = site.getPosts()[0] # Delete de last post
    post = site.publishPost(CHANNEL, "test")
    print(post)
    input("Delete ?")
    print(site.deletePost(post["ts"], CHANNEL))
    res = site.search(
        "links",
        "https://elmundoesimperecto.com/",
    )
    print("res", res)
    print("res", res["messages"]["total"])
    sys.exit()
    post = site.getPosts()[0]
    print(site.getPostTitle(post))
    print(site.getPostLink(post))
    rep = site.publishPost("tavern-of-the-bots", "hello")
    input("Delete %s?" % rep)
    theChan = site.getChanId("tavern-of-the-bots")
    rep = site.deletePost(rep["ts"], theChan)

    sys.exit()

    site.setPosts("links")
    site.setPosts("tavern-of-the-bots")
    print(site.getPosts())
    print(site.getBots())
    print(site.sc.api_call("channels.list"))
    sys.exit()
    rep = site.publishPost("tavern-of-the-bots", "hello")
    site.deletePost(rep["ts"], theChan)
    sys.exit()

    site.setSocialNetworks(config, section)

    if "buffer" in config.options(section):
        site.setBufferapp(config.get(section, "buffer"))

    if "cache" in config.options(section):
        site.setProgram(config.get(section, "cache"))

    theChannel = site.getChanId("links")

    i = 0
    listLinks = ""

    lastUrl = ""
    for i, post in enumerate(site.getPosts()):
        url = site.getLink(i)
        if urllib.parse.urlparse(url).netloc == lastUrl:
            listLinks = listLinks + "%d>> %s\n" % (i, url)
        else:
            listLinks = listLinks + "%d) %s\n" % (i, url)
        lastUrl = urllib.parse.urlparse(url).netloc
        print(site.getTitle(i))
        print(site.getLink(i))
        print(site.getPostTitle(post))
        print(site.getPostLink(post))
        i = i + 1

    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == "x":
        sys.exit()

    elem = int(i)
    print(site.getPosts()[elem])

    action = input("Delete [d], publish [p], exit [x] ")

    if action == "x":
        sys.exit()
    elif action == "p":
        if site.getBufferapp():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getBufferapp():
                    print("   getBuffer %s" % profile)
                    socialNetwork = (
                        profile,
                        site.getSocialNetworks()[profile],
                    )
                    title = site.getTitle(elem)
                    url = site.getLink(elem)
                    listPosts = []
                    listPosts.append((title, url))
                    site.buffer[socialNetwork].addPosts(listPosts)

        if site.getProgram():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getProgram():
                    print("   getProgram %s" % profile)

                    socialNetwork = (
                        profile,
                        site.getSocialNetworks()[profile],
                    )

                    listP = site.cache[socialNetwork].getPosts()
                    listPsts = site.obtainPostData(elem)
                    listP = listP + [listPsts]
                    # for i,l in enumerate(listP):
                    #    print(i, l)
                    # sys.exit()
                    site.cache[socialNetwork].posts = listP
                    site.cache[socialNetwork].updatePostsCache()
        t = moduleTumblr.moduleTumblr()
        t.setClient("fernand0")
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        t.publishPost(title, url, "")

    site.deletePost(site.getId(j), theChannel)
    # print(outputData['Slack']['pending'][elem][8])


if __name__ == "__main__":
    main()
