#!/usr/bin/env python

import configparser
import logging
import os
import smtplib
import sys
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from socialModules.configMod import *
from socialModules.moduleContent import *

#import getpass
#import keyring
#import keyrings

class moduleSmtp(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.client = None

    def setClient(self, user):
        logging.info("     Connecting SMTP")
        try: 
            self.user = user 
            self.client = smtplib.SMTP()
            try: 
                self.client.connect('localhost')
                logging.info("     Logging OK")
            except:
                logging.warning("SMTP authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
            logging.warning("Account not configured")
            api = None

    def publishPost(self, post, subject, toaddr, fromaddr='fernand0@elmundoesimperfecto.com'):
        logging.info("     Publishing in SMTP")
        if True: 
            msg = MIMEText(post,'html')
            msg['Subject'] = subject
            msg['From'] = fromaddr
            res = self.client.sendmail(fromaddr, toaddr, msg.as_string())
        else:
            logging.info("     Not published in SMTP. Exception ...")
            return('Fail')

def main():
    logging.basicConfig(stream=sys.stdout, 
            level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    import moduleSmtp

    ig = moduleSmtp.moduleSmtp()

    ig.setClient('fernand0')

    url = 'https://avecesunafoto.wordpress.com/2017/07/19/maria-fernandez-guajardo-consejos-practicos-de-una-feminista-zaragozana-en-el-silicon-valley/'
    import requests
    req = requests.get(url)
    import time
    ig.publishPost(req.text, 'Test {}'.format(time.asctime()), 'fernand0@elmundoesimperfecto.com')
    ig.publishPost(req.text, 'Test {}'.format(time.asctime()), 
                        'fernand0elmundoesimperfecto.com',
                        'fernand0movilizado@gmail.com')
    


if __name__ == '__main__':
    main()

