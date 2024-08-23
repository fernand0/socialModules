#!/usr/bin/env python

import configparser
import json
import logging
import sys

import telepot

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleTelegram(Content):

    def getKeys(self, config):
        print(config)
        print(config.get('Telegram', 'TOKEN'))
        TOKEN = config['Telegram']['TOKEN']
        print(TOKEN)
        return((TOKEN, ))

    def initApi(self, keys):
        self.service = 'Telegram'
        # logging.info("     Connecting {self.service}")
        TOKEN = keys[0]
        # logging.info("     token: {TOKEN}")
        try:
            bot = telepot.Bot(TOKEN)
            logging.info("     token: {TOKEN}")

            meMySelf = bot.getMe()
        except:
            logging.warning("Telegram authentication failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])

        # self.user = meMySelf
        # self.channel = channel
        return bot

    def setClient(self, channel):
        msgLog = (f"{self.indent} Start setClient account: {channel}")
        logMsg(msgLog, 1, 0)
        self.indent = f"{self.indent} "
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTelegram')

            if channel in config:
                TOKEN = config.get(channel, "TOKEN")
            else:
                TOKEN = config.get("Telegram", "TOKEN")
            try:
                bot = telepot.Bot(TOKEN)
            except:
                logging.warning("Telegram authentication failed!")
                # logging.warning("Unexpected error:", sys.exc_info())
        except:
            logging.warning("Account not configured")
            bot = None

        self.client = bot
        self.user = channel
        self.channel = channel
        self.indent = self.indent[:-1]
        msgLog = (f"{self.indent} End setClientt")
        logMsg(msgLog, 1, 0)

    def setChannel(self, channel):
        self.channel = channel

    def publishApiImage(self, *args, **kwargs):
        msgLog = (f"{self.indent} Service {self.service} publishing args "
                  f"{args}: kwargs {kwargs}")
        logMsg(msgLog, 2, 0)
        post, image = args
        more = kwargs

        bot = self.getClient()
        channel = self.user
        if True:
            bot.sendPhoto('@'+channel, photo=open(image, 'rb'), caption=post)
        else:
            return(self.report('Telegram', post, sys.exc_info()))

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
                reply = "No posts available"
        except:
            reply = self.report(self.service, apiSrc, sys.exc_info())

        return reply

    def publishApiPost(self, *args, **kwargs):
        rep = 'Fail!'
        content = ''
        if args and len(args) == 3:
            title, link, comment = args
            if comment:
                content=comment
        if kwargs:
            more = kwargs
            post = more.get('post', '')
            api = more.get('api', '')
            title = api.getPostTitle(post)
            link = api.getPostLink(post)
            if post:
                contentHtml = api.getPostContentHtml(post)
                soup = BeautifulSoup(contentHtml,'lxml')
                (theContent, theSummaryLinks) = api.extractLinks(soup, "")
                content = f"{theContent}\n{theSummaryLinks}"

        bot = self.getClient()

        links = ""
        channel = self.user

        logging.info(f"{self.service}: Title: {title} Link: {link}")
        text = ('<a href="'+link+'">' + title+ "</a>\n")
        logging.debug(f"{self.service}: Text: {text}")
        #FIXME: This code needs improvement
        textToPublish = text
        textToPublish2 = ""
        from html import unescape
        title = unescape(title)
        if content:
            content = content.replace('<', '&lt;')
            text = (text + content + '\n\n' + links)

        textToPublish = text
        while textToPublish:
            try:
                res = bot.sendMessage('@'+channel, textToPublish[:4080],
                                      parse_mode='HTML')
                textToPublish = textToPublish[4080:]
            except:
                return(self.report('Telegram', textToPublish,
                    link, sys.exc_info()))

            if links:
                bot.sendMessage('@'+channel, links, parse_mode='HTML')
            rep = res

        return rep

    def processReply(self, reply):
        res = ''
        if not isinstance(reply, list):
            origReply = [reply, ]
        else:
            origReply = reply
        for rep in origReply:
            if isinstance(rep, str):
                rep = rep.replace("'",'"')
                rep = json.loads(rep)
            else:
                rep = reply
            if 'message_id' in rep:
                idPost = rep['message_id']
                res = f"{res} https://t.me/{self.user}/{idPost}"
        return (res)

    def getPostTitle(self, post):
        if 'channel_post' in post:
            if 'text' in post['channel_post']:
                return(post['channel_post']['text'])
            else:
                return ''
        else:
            return ''


def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    import moduleTelegram

    tel = moduleTelegram.moduleTelegram()

    tel.setClient('testFernand0')
    # tel.setChannel('testFernand-1')

    msgAlt = "hola"

    testingImage = False
    if testingImage:
        res = tel.publishImage("Prueba imagen", "/tmp/prueba.png", alt=msgAlt)
        return

    testingRssPost = True
    if testingRssPost:
        selRules = rules.selectRule('rss', '')
        print(f"Rules:")
        for i, rul in enumerate(selRules):
            print(f"{i}) {rul}")

        iRul = input("Which rule? ")
        src = selRules[int(iRul)]
        apiSrc = rules.readConfigSrc("", src, rules.more[src])
        apiSrc.setPosts()
        posts = apiSrc.getPosts()
        if posts:
            tel.publishPost(api=apiSrc, post=posts[0])

        return

    testingPost = False
    if testingPost:
        res = tel.publishPost("Prueba texto", "https://t.me/testFernand0", '')
                #api = 'lala' , post = 'lele')
        print(f"Res: {res}")
        return

    testingLongPost = True
    longText = """
Huesca

Article
Talk
Read
Edit
View history

Tools
Coordinates: 42°8′N 0°25′W
From Wikipedia, the free encyclopedia
Huesca
Uesca (Aragonese)
Municipality

Panoramic view from the cathedral

Cathedral

Miguel Servet park
Flag of Huesca
Flag
Coat of arms of Huesca
Coat of arms
Motto: Gate of the Pyrenees
MapWikimedia | © OpenStreetMap
Location of Huesca
Huesca is located in AragonHuescaHuesca
Location of Huesca within Aragon
Show map of Aragon
Show map of Spain
Show all
Coordinates: 42°8′N 0°25′W
Country	Spain
Autonomous community	Aragon
Province	Huesca
Comarca	Hoya de Huesca
Judicial district	Huesca
Founded by	Iberians
Government
 • Type	Mayor-council
 • Body	Ayuntamiento de Huesca
 • Mayor	Lorena Orduna (2023) (PP)
Area
 • Total	161.0 km2 (62.2 sq mi)
Elevation	488 m (1,601 ft)
Population (2020)[1]
 • Total	53,956
 • Density	340/km2 (870/sq mi)
Demonym	Oscense
Time zone	UTC+1 (CET)
 • Summer (DST)	UTC+2 (CEST)
Postal code
22001 - 22006
Dialing code	974
Patron Saints	Saint Lawrence
Saint Vincent
Website	Official website
Huesca (Spanish: [ˈweska]; Aragonese: Uesca) is a city in north-eastern Spain, within the autonomous community of Aragon. It was the capital of the Kingdom of Aragon between 1096 and 1118. It is also the capital of the Spanish province of the same name and of the comarca of Hoya de Huesca. In 2009, it had a population of 52,059, almost a quarter of the total population of the province. The city is one of the smallest provincial capitals in Spain.

Huesca celebrates its main festival, the Fiestas de San Lorenzo,[2] in honor of Saint Lawrence, from the 9th to the 15th of August.

History
Huesca dates from pre-Roman times, and was once known as Bolskan (Iberian: ) in the ancient Iberian language. It was once the capital of the Vescetani, in the north of Hispania Tarraconensis, on the road from Tarraco (modern Tarragona) and Ilerda (modern Lleida) to Caesaraugusta (modern Zaragoza).[3] During Roman times, the city was known as Osca, and was a Roman colony under the rule of Quintus Sertorius, who made Osca his base. The city minted its own coinage and was the site of a prestigious school founded by Sertorius to educate young Iberians in Latin and Roman customs. After Sertorius, it is thought that it was renamed Ileoscan (Ἰλεόσκαν) by Strabo.[4] It appears to have been situated on silver mines.[5]

Eighteenth-century Spanish historian Enrique Flórez[6] has pointed out the impossibility of one city supplying such vast quantities of minted silver as has been recorded by ancient writers under the terms argentum Oscense, signatum Oscense; and is of the opinion that "Oscense" meant "Spanish", being a corruption of "Eus-cara".[7] The Romanised city was made a municipium by decree of Augustus in 30 BC.


The Bell of Huesca, by José Casado del Alisal
The Arabs conquered the city in the late 8th century, and the city came to be called Washqah (وشقة in Arabic), falling within the Upper March of the Emirate of Córdoba. It was ruled by a local governor appointed from Córdoba, but was repeatedly subject to political turmoil, rebellion and assassination as the Banu Qasi, Banu Amrus and Banu al-Tawil clans, as well as the Arista dynasty of Pamplona, struggled for control, autonomy and independence from the Emirate. In the mid-10th century, Wasqah was transferred to the Banu Tujib, who governed the Upper March from Zaragoza, and it became part of the Taifa of Zaragoza in 1018 when they successfully freed themselves from the disintegrating Caliphate. In 1094 Sancho Ramirez built the nearby Castle of Montearagón with the intention of laying siege to Wasqah but was killed by a stray arrow as he reached the city's walls. It was conquered in 1096 by Peter I of Aragon and moved his royal capital to Huesca from the ancient capital of Jaca. In 1118 the Aragonese capital was moved to Zaragoza.[8]

In 1354, King Peter IV of Aragon founded the University of Huesca [es], which initially had a faculty of theology. The school expanded, but by the end of the 16th century was eclipsed by the University of Zaragoza.[9] The university was abolished in 1845.[10]

During the First Carlist War, Huesca was the site of a battle between Spanish Constitutionalists and Carlists.[11]

During the Spanish Civil War (1936–39) the "Huesca Front" was the scene of some of the worst fighting between the Republicans and Franco's army. Held by the Nationalists, the city was besieged by the Republicans, with George Orwell among them,[12][13] but did not fall.[14][15]

Modern Huesca

Allué square
Huesca celebrates its most important annual festival in August: the festival (or fiesta) of San Lorenzo (Saint Lawrence), a native of Huesca martyred in 268 AD. The anniversary of his martyrdom falls on August 10. The fiesta starts on 9 August and finishes on the 15. Many of the inhabitants dress in green and white for the duration.

San Lorenzo, born in Huesca, was a deacon in Rome and a martyr who, according to legend, was burned on a grille by the Romans. The grille is the symbol of San Lorenzo and can be seen in a number of decorative works in the city.

Huesca is also the birthplace of film director Carlos Saura and his brother Antonio Saura, a contemporary artist. There is an international film festival held annually.

The writer Oscar Sipan, winner of several literary prizes, was born in Huesca in 1974. The celebrated illustrator Isidro Ferrer, though born in Madrid, lives in the city.

Various streets in the centre of Huesca have recently been pedestrianised.[16][citation needed]

Geography
Huesca lies on a plateau in the northern region of Aragón, with an elevation of 488 m (1,601 ft) above sea level. Close to the city lie the Sierra de Guara mountains, which reach 2,077 m. The geographical coordinates of the city are: 42° 08´ N, 0° 24´ W.

Its municipal area is 161.02 km ² and borders the municipalities of Almudévar, Vicién, Monflorite-Lascasas Tierz, Quicena, Loporzano, Nueno, Igriés, Banastás, Chimillas, Alerre, Barbués and Albero Bajo.

The city lies 71 kilometres (44 miles) from Zaragoza, 160 kilometres (99 miles) from Pamplona, 118 kilometres (73 miles) from Lleida, 380 kilometres (240 miles) from Madrid and 273 kilometres (170 miles) from Barcelona.

Coat of arms
Both the modern Coat of Arms of Huesca (es) (which date from the 16th century) and its mediaeval predecessor (from the 13th) include at their top the device of a block having a V-shaped notch. It is commonly said that it symbolises Salto de Roldán ('Roland's Leap'), a natural rock formation about 25 km (16 mi) north of the city.[17][18][19][a] Some writers have suggested that the official Spanish name of Huesca (Catalan: Osca) derives from a Latin, Basque and Catalan word osca, meaning notch or indentation, referring to the Salto de Roldán.[17]

Climate
Huesca has a humid subtropical climate (Köppen Cfa). with semi-arid influences. Winters are cool (with normal maximums from 8 to 16 °C and minimums from -2 to 6 °C) and summers are hot, with daily maximums reaching up to 35 °C (95 °F), while the rainiest seasons are autumn and spring. The average precipitation is 480 mm per year. Frost is common and there is sporadic snowfall, with an average of 3 snowy days per year.[20]

Climate data for Huesca Airport, 541 m a.s.l. (1981-2010)
Month	Jan	Feb	Mar	Apr	May	Jun	Jul	Aug	Sep	Oct	Nov	Dec	Year
Record high °C (°F)	20.3
(68.5)	21.0
(69.8)	26.2
(79.2)	31.0
(87.8)	34.2
(93.6)	41.2
(106.2)	42.6
(108.7)	41.4
(106.5)	39.2
(102.6)	30.6
(87.1)	24.8
(76.6)	19.6
(67.3)	42.6
(108.7)
Mean daily maximum °C (°F)	9.0
(48.2)	11.6
(52.9)	15.7
(60.3)	18.0
(64.4)	22.3
(72.1)	28.1
(82.6)	31.6
(88.9)	30.9
(87.6)	25.9
(78.6)	19.8
(67.6)	13.4
(56.1)	9.2
(48.6)	19.6
(67.3)
Daily mean °C (°F)	5.2
(41.4)	6.9
(44.4)	10.1
(50.2)	12.1
(53.8)	16.1
(61.0)	21.0
(69.8)	24.1
(75.4)	23.7
(74.7)	19.8
(67.6)	15.0
(59.0)	9.3
(48.7)	5.5
(41.9)	14.0
(57.2)
Mean daily minimum °C (°F)	1.4
(34.5)	2.2
(36.0)	4.5
(40.1)	6.2
(43.2)	9.8
(49.6)	13.8
(56.8)	16.5
(61.7)	16.6
(61.9)	13.6
(56.5)	10.1
(50.2)	5.2
(41.4)	1.9
(35.4)	8.4
(47.1)
Record low °C (°F)	−12.6
(9.3)	−13.2
(8.2)	−8.6
(16.5)	−3.0
(26.6)	−1.5
(29.3)	3.6
(38.5)	4.5
(40.1)	7.0
(44.6)	4.2
(39.6)	−0.4
(31.3)	−8.2
(17.2)	−10.8
(12.6)	−13.2
(8.2)
Average precipitation mm (inches)	31
(1.2)	28
(1.1)	30
(1.2)	53
(2.1)	52
(2.0)	33
(1.3)	22
(0.9)	29
(1.1)	48
(1.9)	60
(2.4)	47
(1.9)	44
(1.7)	480
(18.9)
Average precipitation days (≥ 1 mm)	5	5	4	6	7	4	3	3	4	7	6	6	61
Average snowy days	1	1	0	0	0	0	0	0	0	0	0	1	3
Average relative humidity (%)	78	70	61	60	57	50	47	50	57	67	76	81	63
Mean monthly sunshine hours	138	173	230	243	275	302	346	314	247	197	146	123	2,732
Source: AEMET[21]
Main sights

Cathedral of Huesca.

Fuente de las Musas.
A double line of ancient walls can still be seen in present-day Huesca.

Nearby, in the territory of Quicena, lie the ruins of the Castle of Montearagón Monastery.

Churches of Huesca
Huesca Cathedral (Catedral de la Transfiguración del Señor), a Gothic-style cathedral built by king James I of Aragon around 1273 on the ruined foundations of a mosque. Work continued until the fifteenth century, and the cathedral is now one of the architectural gems of northern Spain. The doorway, built between 1300 and 1313, has carvings depicting the Apostles. The interior contains a triple nave and chapels. It includes a magnificent high altar made from alabaster, carved to represent the crucifixion, built between 1520 and 1533 by Damián Forment. The cloister and the bell-tower were built in the fifteenth century.
Abbey of San Pedro el Viejo, erected between 1100 and 1241, is one of the oldest Romanesque structures in the Iberian Peninsula. It was partially rebuilt in the seventeenth century, and retains its cloister built in 1140.
Church of St. Lawrence (Iglesia de San Lorenzo), built in the seventeenth and eighteenth centuries.

Huesca City Hall
Iglesia de Santo Domingo, a Baroque style church.
Iglesia de la Compañía San Vicente, from the 17th century
Ermita de Ntr. Sra. de Salas, a Romanesque and Baroque hermitage.
Ermita de Loreto, San Lorenzo's oldest hermitage, according to tradition.
Ermita de San Jorge, built in memory of the Battle of Alcoraz
Ermita de las Mártires
Ermita de Santa Lucía
Ermita de Jara, in ruins
San Miguel, a Romanesque tower
Santa María de Foris, built in a transitional Romanesque style
Santa Cruz, Seminary, on Romanesque foundations.
There are several old monasteries in the local area. One in the Castle of Montearagón contains the tomb of king Alfonso I of Aragon in its crypt.
The Museum of Huesca occupies the building formerly belonging to the old university. The famous "Bell of Huesca" lies in one of its vaults, and is said to have been constructed from the heads of rebels who were executed by King Ramiro II of Aragon.
Notable people
Amrus ibn Yusuf (Huesca, 760- 808/9 or 813/4 Talavera de la Reina or Zaragoza), general of the Emirate of Córdoba and governor of Zaragoza
Petrus Alphonsi (Born at an unknown date in the 11th century in Huesca, died 1140?), was a Jewish Spanish physician, writer, astronomer, and polemicist, who converted to Christianity.
Petronilla of Aragon (Huesca, 1136 – 15 October 1173), Queen of Aragon from the abdication of her father in 1137 until her own abdication in 1164.
Alfonso II of Aragon (Huesca, March 1157 – 25 April 1196), was the King of Aragon and Count of Barcelona from 1164 until his death.
Peter II of Aragon (Huesca, July 1178 – 12 September 1213), was the King of Aragon (as Pedro II) and Count of Barcelona (as Pere I) from 1196 to 1213.
Vincencio Juan de Lastanosa (Huesca, 1607 - 1681), collector, scholar, Spanish cultural promoter and patron.
Valentín Carderera (Huesca, 1796 - Madrid, 1880), promoter of the arts, writer and academic art painter.
Lucas Mallada y Pueyo (Huesca, 1841 - Madrid 1921), mining engineer, paleontologist and writer, belonging to Regenerationism movement.
Fidel Pagés (Huesca, January 26, 1886 - September 21, 1923 Madrid), Spanish military surgeon, known for developing the technique of epidural anesthesia.
Ramón Acín Aquilué (1888, Huesca, Aragon, Spain – 1936), anarcho-syndicalist, teacher, writer and avant-garde artist murdered by fascists in the first year of the Spanish Civil War.
Pepín Bello (13 May 1904, Huesca – 11 January 2008), intellectual and writer. He was regarded as the last survivor of the "Generation of '27".
Julio Alejandro (Huesca, 1906 – 1995 Javea), was a Spanish screenwriter. He wrote for 80 films between 1951 and 1984.
Antonio Saura (September 22, 1930, Huesca – July 22, 1998, Cuenca) was a Spanish artist and writer, one of the major post-war painters to emerge in Spain in the fifties.
Carlos Saura (4 January 1932, Huesca – 10 February 2023, Collado Mediano) is a Spanish film director and photographer.
Josep Acebillo (born in Huesca, Spain, in 1946), architect.
Esteban Navarro (Moratalla, 1965), writer. Huesca resident since 2001.
Nunilo and Alodia (Huesca, A.D. 851), martyrs of Christianity. Died after refusing to deny Christ.
Sara Giménez Giménez (born in Huesca, 1977), Roma lawyer
Popular references

The Casino (Oscense Circle).
Huesca is notable for the saying "Tomorrow we'll have coffee in Huesca", a running joke among militiamen of the Spanish Civil War. In February 1937, George Orwell was stationed near the falangist-held Huesca as a member of the POUM militia.[13] In Homage to Catalonia, Orwell writes about this running joke, originally a naïvely optimistic comment made by one of the Spanish Republican generals:

Months earlier, when Siétamo was taken, the general commanding the Government troops had said gaily: "Tomorrow we'll have coffee in Huesca." It turned out that he was mistaken. There had been bloody attacks, but the town did not fall, and [the phrase] had become a standing joke throughout the army. If I ever go back to Spain I shall make a point of having a cup of coffee in Huesca.[22]

Huesca is also famous for the legend of the Bell of Huesca.

Twin towns - sister cities
See also: List of twin towns and sister cities in Spain
The following are Sister cities of Huesca:[23]

France Tarbes, France (since 1964)
Transportation
The Autovía A-23 runs through Huesca, connecting the city with Zaragoza. While under construction as of 2018, the Autovía A-22 also connects Huesca to Lleida. The two highways will eventually connect.

Huesca has been served by Huesca–Pirineos Airport since 1930,[24] but the airport does not currently have any scheduled commercial passenger services.

Huesca railway station is served by regional and AVE trains to destinations including Zaragoza, Canfranc, Madrid and Jaca.

Sports
In 2018, SD Huesca, became the town's first football team to be promoted to La Liga. They became the 63rd team to play in the league, and their stadium's maximum capacity was the smallest in the 2018–19 La Liga.

See also

Holy week, Huesca.

Tapa El Lince from Huesca.
Diocese of Huesca"""

    if testingLongPost:
        res = tel.publishPost(longText[:24], "https://t.me/testFernand0",
                              longText)
        print(f"Res: {res}")
        return


    # print("Testing posts")
    # tel.setPosts()

    # for post in tel.getPosts():
    #     print(post)

    # print("Testing title and link")

    # for post in tel.getPosts():
    #     print(post)
    #     title = tel.getPostTitle(post)
    #     link = tel.getPostLink(post)
    #     print("Title: {}\nLink: {}\n".format(title, link))

    sys.exit()


if __name__ == '__main__':
    main()
