#!/usr/bin/env python

import smtplib
import sys
import time

from email import encoders
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import socialModules
from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

#import getpass
#import keyring
#import keyrings

class moduleSmtp(Content): #, Queue):

    def getKeys(self, config):
        SERVER = config.get(self.user, "server")
        USER = config.get(self.user, "user")
        PASSWORD = config.get(self.user, "token")
        PORT = config.get(self.user, "port")

        return (SERVER, PORT, USER, PASSWORD,)

    def initApi(self, keys):
        self.fromaddr = self.user
        self.server = keys[0]
        self.port = keys[1]
        self.user = keys[2]
        self.password = keys[3]

        try:
            import ssl
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            client = smtplib.SMTP(self.server, self.port)
            client.starttls(context=context)
            client.login(self.user, self.password)
            logging.info("     Logging OK")
        except:
            logging.warning("SMTP authentication failed!")
            logging.warning(f"Unexpected error: {sys.exc_info()[0]}")

        return client

    def publishApiPost(self, *args, **kwargs):
        comment = ""
        if args and len(args) == 3:
            post, link, comment = args
        if kwargs:
            more = kwargs
            # FIXME: We need to do something here
            thePost = more.get('post', '')
            api = more.get('api', '')
            post = api.getPostTitle(thePost)
            link = api.getPostLink(thePost)
        res = 'Fail!'
        try:
            destaddr = self.user
            toaddrs = self.user
            if hasattr(self, 'fromaddr') and self.fromaddr:
                logging.info(f"{self.indent} 1")
                fromaddr = self.fromaddr
            else:
                logging.info(f"{self.indent} 2")
                fromaddr = self.user
            theUrl = link
            if post:
                subject = post.split('\n')[0]
            else:
                if link:
                    subject = link
                else:
                    subject = "No subject"

            msg = MIMEMultipart()
            msg['From']    = fromaddr
            msg['To']      = destaddr
            msg['Date']    = time.asctime(time.localtime(time.time()))
            msg['X-URL']   = theUrl
            msg['X-print'] = theUrl
            msg['Subject'] = subject

            htmlDoc = (f"<html><body>"
                       f"Title: {subject}\n"
                       f"Url: {link}\n"
                       f"{post}"
                       f"</body></html>\n")

            if comment:
                htmlDoc = comment

                msgLog = (f"{self.indent} Doc: {htmlDoc}")
                logMsg(msgLog, 2, 0)


            if htmlDoc.startswith('<'):
                subtype = 'html'
            else:
                subtype = 'plain'

            adj = MIMEText(htmlDoc, _subtype=subtype)
            msg.attach(adj)

            #     adj = MIMEApplication(htmlDoc)
            #     encoders.encode_base64(adj)
            #     name = 'content'
            #     ext = '.html'

            #     adj.add_header('Content-Disposition',
            #                    f'attachment; filename="{name}{ext}"')
            #     adj.add_header('Content-Type','application/octet-stream')

            #     msg.attach(adj)

            #     if htmlDoc.startswith('<'):
            #         subtype = 'html'
            #     else:
            #         subtype = 'plain'

            #     adj = MIMEText(htmlDoc, _subtype=subtype)
            #     msg.attach(adj)
            # else:
            #     if htmlDoc.startswith('<'):
            #         subtype = 'html'
            #     else:
            #         subtype = 'plain'

            #     adj = MIMEText(htmlDoc, _subtype=subtype)
            #     msg.attach(adj)


            if not self.client:
                smtpsrv  = 'localhost'
                server = smtplib.SMTP(smtpsrv)
                server.connect(smtpsrv, 587)
                server.starttls()
            else:
                server = self.client
                respN = server.noop()
                if not (respN == "250"):
                    import ssl
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    server = smtplib.SMTP(self.server, self.port)
                    server.starttls(context=context)
                    server.login(self.user, self.password)

            msgLog = (f"From: {fromaddr} To:{toaddrs}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"Msg: {msg.as_string()}")
            logMsg(msgLog, 2, 0)

            try:
                res = server.sendmail(fromaddr, toaddrs, msg.as_string())
            except:
                res = self.report(self.service, 
                                    f"{post} {link}", post, sys.exc_info())

            if not res:
                res = "OK"
            server.quit()

        except:
            res = self.report(self.service, '', '', sys.exc_info())

        return(f"{res}")

def main():
    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()
    rules.printDict(rules.rules, "Rules")

    indent = ""
    print(f"Rules: {rules}")
    srcs = rules.selectRule('cache', '')
    for i, src in enumerate(srcs): 
        print(f"{i}) Src: {src}")

    sel = input("Which one? ")
    src = srcs[int(sel)]
    print(f"Rule: {src}")
    more = None
    apiSrc = rules.readConfigSrc(indent, src, more)
    action =  rules.rules[src][0]
    print(f"Action: {action}")
    apiDst = rules.readConfigDst(indent, action, more, apiSrc)
    print(f"Client: {apiDst.client}")
    apiDst.user = 'fernand0Enlaces@elmundoesimperfecto.com'

    testingPublishing = False
    if testingPublishing:
        apiDst.publishPost('Mensaje', 'https://www.unizar.es/', '')

        return

    testingHtml = False
    if testingHtml:
        msgHtml = '<body><html><p>Cuadro de mandos<hr></hr></p><p><img alt="Cuadro de mandos" height="240" src="https://live.staticflickr.com/65535/53057264758_272560e5d9_m.jpg" width="160"/></p><p>https://www.flickr.com/photos/fernand0/53057264758/</p></body></html>'
        apiDst.publishPost('Mensaje', 'https://www.unizar.es/', msgHtml)

        return


    testingWeb = True
    if testingWeb:
        url = 'https://avecesunafoto.wordpress.com/2017/07/19/maria-fernandez-guajardo-consejos-practicos-de-una-feminista-zaragozana-en-el-silicon-valley/'
        import requests
        req = requests.get(url)
        import time
        myTime = time.asctime()
        print(f"Res1: {apiDst.publishPost(req.text, myTime ,'')}")
        print(f"Res2: {apiDst.publishPost(req.text, myTime, req.text)}")


if __name__ == '__main__':
    main()

