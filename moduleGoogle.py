#!/usr/bin/env python
# encoding: utf-8

# This module has common methods por Google APIs

# From: https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
from __future__ import print_function

import logging
import os

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

from configMod import *


class socialGoogle:

    def API(self, Acc):
        # Back compatibility
        self.setClient(Acc)

    def getKeys(key, config):
        return (())

    def authorize(self):
        # based on Code from
        # https://github.com/gsuitedevs/python-samples/blob/aacc00657392a7119808b989167130b664be5c27/gmail/quickstart/quickstart.py

        SCOPES = self.scopes

        logging.info(f"Authorizing...")
        #logging.info(f"    Connecting {self.service}: {account}")
        pos = self.user.rfind('@')
        self.server = self.user[pos+1:]
        self.nick = self.user[:pos]

        fileCredStore = self.confName((self.server, self.nick))
        fileTokenStore = self.confTokenName((self.server, self.nick))
        creds = None

        store = file.Storage(fileTokenStore)
        logging.debug(f"filetokenstore: {fileTokenStore}")
        # creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        creds = store.get()

        if not creds:
            if creds and creds.expired and creds.refresh_token:
                logging.info("Needs to refresh token GMail")
                creds.refresh(Request())
            else:
                logging.info("Needs to re-authorize token GMail")

                try:
                    print(f"fileCred: {fileCredStore}")
                    flow = client.flow_from_clientsecrets(fileCredStore, 
                                                         SCOPES)
                    creds = tools.run_flow(flow, store, 
                           tools.argparser.parse_args(args=['--noauth_local_webserver']))

                    # credentials = run_flow(flow, storage, args)

                    # flow = InstalledAppFlow.from_client_secrets_file(
                    #     fileCredStore, SCOPES)

                    # creds = flow.run_local_server(port=0)
                    # creds = flow.run_console(
                    #         authorization_prompt_message='Please visit this URL: {url}',
                    #         success_message='The auth flow is complete; you may close this window.')
                    # Save the credentials for the next run
                except FileNotFoundError:
                    print("no")
                    print(fileCredStore)
                    sys.exit()
                except ValueError:
                    print("Error de valor")
                    creds = 'Fail!'
        logging.debug("Storing creds")
        # with open(fileTokenStore, 'wb') as token:
        #     pickle.dump(creds, token)

        return(creds)

    def confName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + self.service + '_'
                + acc[0]+ '_' 
                + acc[1]+ '.json')
        return(theName)

    def confTokenName(self, acc): 
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + acc[0]+ '_' 
                + acc[1]+ '.token.json')
        return(theName)
 
