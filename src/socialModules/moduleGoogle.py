#!/usr/bin/env python
# encoding: utf-8

# This module has common methods por Google APIs

# From: https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
from __future__ import print_function

import os
import pathlib

from googleapiclient.discovery import build
from httplib2 import Http

import google
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account

from socialModules.configMod import *


class socialGoogle:

    def API(self, Acc):
        # Back compatibility
        self.setClient(Acc)

    def getKeys(key, config):
        return ('keys')

    def authorize(self):
        # based on Code from
        # https://github.com/gsuitedevs/python-samples/blob/aacc00657392a7119808b989167130b664be5c27/gmail/quickstart/quickstart.py

        SCOPES = self.scopes

        msgLog = (f"{self.indent} Authorizing...")
        logMsg(msgLog, 1, 0)
        #logging.info(f"    Connecting {self.service}: {account}")
        pos = self.user.rfind('@')
        self.server = self.user[pos+1:]
        self.nick = self.user[:pos]

        fileCredStore = self.confName((self.server, self.nick))
        fileTokenStore = self.confTokenName((self.server, self.nick))
        creds = None

        try:
            store = file.Storage(fileTokenStore)
            msgLog = (f"{self.indent}  filetokenstore: {fileTokenStore}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"{self.indent}  fileCred: {fileCredStore}")
            logMsg(msgLog, 2, 0)
            # creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            creds = store.get()
            msgLog = (f"{self.indent}  creds: {creds.to_json()}")
            logMsg(msgLog, 2, 0)
        except:
            creds = None

        if not creds:
            msgLog = (f"{self.indent} No creds")
            logMsg(msgLog, 2, 0)
            if creds and creds.expired and creds.refresh_token:
                msgLog = (f"{self.indent} Needs to refresh token GMail")
                logMsg(msgLog, 2, 0)
                creds.refresh(Request())
            else:
                msgLog = (f"{self.indent} Needs to re-authorize token GMail")
                logMsg(msgLog, 2, 0)

                try:
                    if not os.path.exists(fileCredStore):
                        with open(fileCredStore, 'w') as fHash:
                            pass
                    else:
                        import json
                        with open(fileCredStore, 'r') as fHash:
                            client_config = json.load(fHash) #.read()
                            logging.info(f"Config: {client_config}")
                            logging.info(f"Config: {client_config['installed']}")
                            client_config['installed']['token_uri'] = 'https://oauth2.googleapis.com/token'
                            client_config['installed']['redirect_uris'] = ["http://localhost/"]
                            logging.info(f"Config: {client_config['installed']}")
                    # flow = client.flow_from_clientsecrets(fileCredStore, 
                    #                                      SCOPES)
                    logging.info(f"1111")
                    logging.info(f"Scopes: {SCOPES}")
                    # flow = InstalledAppFlow.from_client_config(
                    #         client_config=client_config,
                    #         scopes=SCOPES)
                    logging.info(f"2111")
                    # creds = flow.run_local_server(open_browser=False#,
                    #                               #port=59185#,
                    #                               #timeout_seconds=5
                    #                               )
                    p = pathlib.PosixPath('~/.config/gcloud/application_default_credentials.json')
 
                    creds = service_account.Credentials.from_service_account_file(p.expanduser() , scopes=SCOPES)

                    #creds = tools.run_flow(flow, store, 
                    #       tools.argparser.parse_args(args=['--noauth_local_webserver']))

                    # credentials = run_flow(flow, storage, args)

                    # flow = InstalledAppFlow.from_client_secrets_file(
                    #     fileCredStore, SCOPES)

                    # creds = flow.run_local_server(port=0)
                    # creds = flow.run_console(
                    #         authorization_prompt_message='Please visit this URL: {url}',
                    #         success_message='The auth flow is complete; you may close this window.')
                    # Save the credentials for the next run
                except FileNotFoundError:
                    print("noooo")
                    print(fileCredStore)
                    sys.exit()
                except ValueError:
                    res = self.report('moduleGoogle', 'Wrong data in file', '', sys.exc_info())
                    creds.refresh(Request())
                    #creds = 'Fail!'
        msgLog = (f"{self.indent} Storing creds")
        logMsg(msgLog, 2, 0)

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
 
