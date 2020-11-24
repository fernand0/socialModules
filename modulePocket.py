#!/usr/bin/env python

import configparser
import pickle
import os
from pocket import Pocket, PocketException

from configMod import *
from moduleContent import *

class modulePocket(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.client = None

    def setClient(self, pocket=''):
        logging.info("    Connecting Pocket")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssPocket')

            self.user = pocket

            consumer_key = config.get("appKeys", "consumer_key")
            access_token = config.get("appKeys", "access_token")

            try:
                client = Pocket(consumer_key=consumer_key, access_token=access_token)
            except:
                logging.warning("Pocket authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
                client = None
        except:
            logging.warning("Account not configured")
            client = None

        self.client = client
 
    def getClient(self):
        return self.client    
    
    def setPosts(self):
        logging.info("  Setting posts")
        print(self.client)
        print(self.client.get())
        self.posts = []

    def publishPost(self, post, link, comment):
    
        try:
            logging.info("    Publishing in Pocket: %s" % post)
            client = self.client 
            res = client.add(link)
            logging.info("Res: %s" % res)
            logging.info("Posted!: %s" % post)
            return(res)
        except:        
            return(self.report('Pocket', post, link, sys.exc_info()))
 
def main(): 

    import modulePocket
    
    p = modulePocket.modulePocket()

    p.setClient('fernand0')

    p.setPosts()

    print(p.getPosts())
    
    sys.exit()
    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')

if __name__ == '__main__':
    main()

