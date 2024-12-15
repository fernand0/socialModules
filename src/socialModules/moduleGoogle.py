#!/usr/bin/env python
# encoding: utf-8

# This module has common methods por Google APIs

# From: https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
from __future__ import print_function

import json
import os
import pathlib
import pickle

from httplib2 import Http

import google
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build

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
        # Latest version based on code from:
        # https://github.com/insanum/gcalcli/tree/main/gcalcli
        # https://github.com/insanum/gcalcli/blob/main/gcalcli/auth.py
        # It needs to be run on a machine where you have access to a browser (?)
        #
        # Following:
        # https://github.com/googleworkspace/python-samples/blob/main/gmail/quickstart/quickstart.py
        # It uses:
        # creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # It needs:
        # credentials.json (downloaded from the web page)
        # It creates:
        # token.json
        #
        # https://github.com/googleworkspace/python-samples/blob/main/gmail/snippet/send%20mail/send_message.py
        # It uses:
        #   creds, _ = google.auth.default()
        # In: https://cloud.google.com/docs/authentication/application-default-credentials
        #
        # GOOGLE_APPLICATION_CREDENTIALS environment variable

        SCOPES = self.scopes

        msgLog = (f"{self.indent} Authorizing...")
        logMsg(msgLog, 1, 0)
        msgLog = (f"{self.indent}  Connecting {self.service}") #: {account}")
        logMsg(msgLog, 1, 0)
        pos = self.user.rfind('@')
        self.server = self.user[pos+1:]
        self.nick = self.user[:pos]

        msgLog = (f"{self.indent}  server: {self.server} nick: {self.nick}")
        logMsg(msgLog, 2, 0)
        creds = None

        try:
            fileTokenStore = self.confTokenName((self.server, self.nick))
            # It's a pickled file
            msgLog = (f"{self.indent}  filetokenstore: {fileTokenStore}")
            logMsg(msgLog, 2, 0)
            # store = file.Storage(fileTokenStore)
            # if False: #'gmail' in self.service.lower():
            #     fileCredStore = os.path.expanduser(CONFIGDIR + '/'
            #     + 'tokenGmail'
            #     + '.json')
            #     msgLog = (f"{self.indent}  fileCredStore: {fileCredStore}")
            #     logMsg(msgLog, 2, 0)
            #     creds = Credentials.from_authorized_user_file(fileCredStore, SCOPES)
            #     # creds = store.get()
            #     # creds = Credentials.from_authorized_user_file(fileTokenStore, SCOPES)
            #     msgLog = (f"{self.indent}  creds: {creds}")
            #     logMsg(msgLog, 2, 0)
            # else:
            try:
                with open(fileTokenStore, 'rb') as fToken:
                    msgLog = (f"{self.indent}   Unpickle: {fileTokenStore}")
                    logMsg(msgLog, 2, 0)
                    creds = pickle.load(fToken)
            except:
                msgLog = (f"{self.indent}  No credentials to pickle")
                logMsg(msgLog, 2, 0)

        except:
            msgLog = (f"{self.indent}  creds except {sys.exc_info()}")
            logMsg(msgLog, 2, 0)
            creds = None

        # msgLog = (f"{self.indent} Read creds {creds}")
        # logMsg(msgLog, 2, 0)
        # msgLog = (f"{self.indent} Exp creds {creds.expired} - {creds.refresh_token}")
        # logMsg(msgLog, 2, 0)

        if not creds:
            msgLog = (f"{self.indent} No creds")
            logMsg(msgLog, 2, 0)
            if creds and creds.expired and creds.refresh_token:
                    msgLog = (f"{self.indent} Needs to refresh token GMail")
                    logMsg(msgLog, 2, 0)
                    try:
                        creds.refresh(Request())
                    except:
                        msgLog =  sys.exc_info()
                        logMsg(msgLog, 2, 0)
            else:
                # This needs to have a desktop application created in
                # https://console.cloud.google.com/auth/clients
                # and some test user, since we are not passing the
                # verification process in Google.
                # It only works in local, since it launches a brower
                msgLog = (f"{self.indent} Needs to re-authorize token GMail")
                logMsg(msgLog, 2, 0)
                fileCredStore = self.confName((self.server, self.nick))
                msgLog = (f"{self.indent}  fileCred: {fileCredStore}")
                logMsg(msgLog, 2, 0)
                # It's a json file
                try:
                    if not os.path.exists(fileCredStore):
                        msgLog = (f"{self.indent}  fileCred: {fileCredStore} does not exist")
                        logMsg(msgLog, 2, 0)
                    else:
                        print(f"This won't work on remote, you need a local browser to pass the oauth process")
                        flow = InstalledAppFlow.from_client_secrets_file(
                                                                         fileCredStore, SCOPES,
                                                                         redirect_uri='http://localhost'
                                                                         )
                        creds = flow.run_local_server(port=0)

                        # Save the credentials for the next run
                        with open(fileTokenStore, 'wb') as token:
                            msgLog = (f"{self.indent}   Pickle: {fileTokenStore}")
                            logMsg(msgLog, 2, 0)
                            pickle.dump(creds, token)
                        # with open(fileCredStore, 'r') as fHash:
                        #    msgLog = (f"{self.indent}  fileCredStore: {fileCredStore}")
                        #    logMsg(msgLog, 2, 0)
                        #    client_config = json.load(fHash) #.read()
                        #    logging.info(f"Config: {client_config}")
                        #    logging.info(f"Config: {client_config['installed']}")
                        #    client_config['installed']['token_uri'] = 'https://oauth2.googleapis.com/token'
                        #    client_config['installed']['redirect_uris'] = ["http://localhost"]
                        #    logging.info(f"Config: {client_config['installed']}")
                        ## flow = client.flow_from_clientsecrets(fileCredStore,
                        ##                                      SCOPES)
                        # logging.info(f"1111")
                        # logging.info(f"Scopes: {SCOPES}")
                        # flow = InstalledAppFlow.from_client_config(
                        #         client_config=client_config,
                        #         scopes=SCOPES)
                        # logging.info(f"2111")
                        # creds = flow.run_local_server() #open_browser=True,
                        #                               # port=59185#,
                        #                               # #timeout_seconds=5
                        #                               # )
                except FileNotFoundError:
                    print("noooo")
                    print(fileCredStore)
                    sys.exit()
                except ValueError:
                    res = self.report('moduleGoogle', 'Wrong data in file', '', sys.exc_info())
                    creds.refresh(Request())
                    #creds = 'Fail!'
        # msgLog = (f"{self.indent} Storing creds")
        # logMsg(msgLog, 2, 0)

        return(creds)

    def confName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.'
                + self.service + '_'
                + acc[0]+ '_'
                + acc[1]+ '.json')
        return(theName)

    def confTokenName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.'
                + self.service + '_'
                + acc[0]+ '_'
                + acc[1]+ '.pickle')
        return(theName)

