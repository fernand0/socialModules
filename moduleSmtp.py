#!/usr/bin/env python

import configparser
import os
import logging
import sys

from configMod import *
from moduleContent import *

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import smtplib

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

    import moduleSmtp

    ig = moduleSmtp.moduleSmtp()

    ig.setClient('fernand0')

    url = 'https://avecesunafoto.wordpress.com/2017/07/19/maria-fernandez-guajardo-consejos-practicos-de-una-feminista-zaragozana-en-el-silicon-valley/'
    import requests
    req = requests.get(url)
    import time
    ig.publishPost(req.text, 'Test {}'.format(time.asctime()), 'fernand0@elmundoesimperfecto.com')
    


if __name__ == '__main__':
    main()

