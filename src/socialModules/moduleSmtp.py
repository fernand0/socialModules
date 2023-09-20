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

    def setClient(self, user):
        self.user = None
        self.client = None

        logging.info("     Connecting SMTP")
        try: 
            self.user = user 
            try: 
                self.client = smtplib.SMTP('localhost', 587)
                # self.client.connect('localhost', 587)
                logging.info("     Logging OK")
            except:
                logging.warning("SMTP authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
            logging.warning("Account not configured")
            api = None

    def publishApiPost(self, *args, **kwargs):
        comment = ""
        if args and len(args) == 3:
            logging.info(f"Tittt: args: {args}")
            post, link, comment = args
        if kwargs:
            logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            thePost = more.get('post', '')
            api = more.get('api', '')
            # logging.info(f"Post: {thePost}")
            post = api.getPostTitle(thePost)
            # logging.info(f"Post: {post}")
            link = api.getPostLink(thePost)
            # idPost = api.getPostId(post)
            # logging.info(f"Postt: {post['meta']}")
            # idPost = post['meta']['payload']['headers'][2]['value'] #[1:-1]
            # idPost = post['list']['id'] #[1:-1]
            # logging.info(f"Post id: {idPost}")
        res = 'Fail!'
        try: 
            destaddr = self.user 
            toaddrs = self.user 
            fromaddr = self.user 
            smtpsrv  = 'localhost' 
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
            # if not link:
            #     htmlDoc = (f"Title: {subject} \n\n" 
            #            f"Url: {link} \n\n"
            #            f"{post}") 
            # else:
            if comment: 
                htmlDoc = comment
            else: 
                htmlDoc = (f"Title: {subject} <br />\n" 
                        f"Url: {link} <br />\n"
                        f"{post}") 
            logging.info(f"{self.indent} Doc: {htmlDoc}")
            adj = MIMEApplication(htmlDoc) 
            encoders.encode_base64(adj) 
            name = 'forum'
            ext = '.html'
            adj.add_header('Content-Disposition', 
                               f'attachment; filename="{name}{ext}"')

            adj.add_header('Content-Type','application/octet-stream')

            msg.attach(adj) 

            if htmlDoc.startswith('<'):
                subtype = 'html'
            else:
                subtype = 'plain'

            adj = MIMEText(htmlDoc, _subtype=subtype) 
            # adj.add_header('Content-Type','text/html')
            msg.attach(adj)
            # if link  and link.find('http')>=0:
            #     if post.startswith('<'):
            #         msg.attach(MIMEText(f"{post}", _subtype='html'))
            #     else:
            #         if comment:
            #             msg.attach(MIMEText(f"{comment}"))
            #         else:
            #             msg.attach(MIMEText(f"{post}"))
            # # else:
            # #     msg.attach(MIMEText(f"[{subject}]({theUrl})\n\nURL: {theUrl}\n{post}"))
            server = smtplib.SMTP(smtpsrv)
            server.connect(smtpsrv, 587)
            server.starttls()

            logging.info(f"From: {fromaddr} To:{toaddrs}")
            logging.info(f"Msg: {msg.as_string()}")
            res = server.sendmail(fromaddr, toaddrs, msg.as_string())
            if not res:
                res = "OK"
            server.quit()

        except:
            res = self.report(self.service, '', '', sys.exc_info())

        return(f"Res: {res}")


    def publishPostt(self, post, subject, toaddr, fromaddr='fernand0@elmundoesimperfecto.com'):
        logging.info("     Publishing in SMTP")
        if True: 
            msg = MIMEText(post,'html')
            msg['Subject'] = subject
            msg['From'] = fromaddr
            self.client.starttls()
            res = self.client.sendmail(fromaddr, toaddr, msg.as_string())
        else:
            logging.info("     Not published in SMTP. Exception ...")
            return('Fail')

def main():
    logging.basicConfig(stream=sys.stdout, 
            level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()
    rules.printDict(rules.rules, "Rules")

    indent = ""
    src, more = rules.selectRule('cache', 'smtp')
    apiSrc = rules.readConfigSrc(indent, src, more)
    action =  rules.rules[src][0]
    print(f"Action: {action}")
    apiDst = rules.readConfigDst(indent, action, more, apiSrc)
    # print(f"Folders: {apiSrc.getChannels()}")
    # apiSrc.setChannel(more['search'])

    testingPublishing = False
    if testingPublishing:
        apiDst.publishPost('Mensaje', 'https://www.unizar.es/', '')

        return

    testingHtml = True
    if testingHtml:
        msgHtml = '<body><html><p>Cuadro de mandos<hr></hr></p><p><img alt="Cuadro de mandos" height="240" src="https://live.staticflickr.com/65535/53057264758_272560e5d9_m.jpg" width="160"/></p><p>https://www.flickr.com/photos/fernand0/53057264758/</p></body></html>'
        apiDst.publishPost('Mensaje', 'https://www.unizar.es/', msgHtml)

        return

    import socialModules.moduleSmtp

    apiSrc = socialModules.moduleSmtp.moduleSmtp()

    apiSrc.setClient('fernand0')

    url = 'https://avecesunafoto.wordpress.com/2017/07/19/maria-fernandez-guajardo-consejos-practicos-de-una-feminista-zaragozana-en-el-silicon-valley/'
    import requests
    req = requests.get(url)
    import time
    apiSrc.publishPost(req.text, 'Test {}'.format(time.asctime()), 'fernand0@elmundoesimperfecto.com')
    apiSrc.publishPost(req.text, 'Test {}'.format(time.asctime()), 
                        'fernand0elmundoesimperfecto.com',
                        'fernand0movilizado@gmail.com')
    


if __name__ == '__main__':
    main()

