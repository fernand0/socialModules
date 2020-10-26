#!/usr/bin/env python

import configparser
import pickle
import os
import sys

from pocket import Pocket, PocketException

from configMod import *
from moduleContent import *

class modulePocket(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.client = None
        self.service = 'Pocket'

    def setClient(self, pocket=''):
        logging.info("     Connecting {}".format(self.service))
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssPocket')

            self.user = pocket
            if config.sections():

                consumer_key = config.get("appKeys", "consumer_key")
                access_token = config.get("appKeys", "access_token")

                try:
                    client = Pocket(consumer_key=consumer_key, 
                            access_token=access_token)
                except:
                    logging.warning("Pocket authentication failed!")
                    logging.warning("Unexpected error:", sys.exc_info()[0])
                    client = None
            else: 
                logging.warning("Account not configured") 
                if sys.exc_info()[0]: 
                    logging.warning("Unexpected error: {}".format( 
                        sys.exc_info()[0])) 
                print("Please, configure a {} Account".format(self.service))
                sys.exit(-1)
        except: 
            logging.warning("Account not configured")
            if sys.exc_info()[0]: 
                logging.warning("Unexpected error: {}".format( 
                    sys.exc_info()[0])) 
            print("Please, configure a {} Account".format(self.service))
            sys.exit(-1)

        self.client = client
 
    def getClient(self):
        return self.client    
    
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

    def publishPost(self, post, link, comment):
    
        try:
            logging.info("    Publishing in {}: {}".format(self.service, post))
            client = self.client 
            res = client.add(link)
            logging.info("Res: %s" % res)
            logging.info("Posted!: %s" % post)
            return(res)
        except:        
            return(self.report('Pocket', post, link, sys.exc_info()))
 
def main(): 

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import modulePocket
    
    p = modulePocket.modulePocket()

    p.setClient('fernand0')

    p.setPosts()
    
    p.publishPost('El Mundo Es Imperfecto', 'https://elmundoesimperfecto.com/', '')

if __name__ == '__main__':
    main()

