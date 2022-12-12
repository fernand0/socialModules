#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

import configparser
import datetime
import logging
import os
import sys

#from dateutil.parser import parse
import dateparser
import googleapiclient
from googleapiclient import http
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools
from oauth2client.service_account import ServiceAccountCredentials

from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleGoogle import *


class moduleGcalendar(Content,socialGoogle):    
    
    # def API(self, Acc):
    #     # Back compatibility
    #     self.setClient(Acc)

    # def getKeys(key, config):
    #     return (())

    def initApi(self, keys):
        self.service = "Gcalendar"
        self.nick = None
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly',
                       'https://www.googleapis.com/auth/calendar']

        SCOPES = self.scopes
        creds = self.authorize()
        # logging.debug(f"Service: {creds}")
        # if isinstance(creds, str) and ("Fail!" in creds):
        #     service = None
        # else:
        if True:
            service = build('calendar', 'v3', 
                         credentials=creds) #, cache_discovery=False)
        return service

    # def confTokenName(self, acc): 
    #     theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
    #             + acc[0]+ '_' 
    #             + acc[1]+ '.token.json')
    #     return(theName)
 
    # def confName(self, acc):
    #     theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
    #             + self.service + '_'
    #             + acc[0]+ '_' 
    #             + acc[1]+ '.json')
    #     return(theName)
 
    # def setClient(self, Acc):
    #     # based on get_credentials from 
    #     # Code from
    #     # https://developers.google.com/gmail/api/v1/reference/users/messages/list
    #     # and
    #     # http://stackoverflow.com/questions/30742943/create-a-desktop-application-using-gmail-api
    # 
    #     SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    #     self.url = SCOPES
    #     api = {}
    # 
    #     config = configparser.ConfigParser() 
    #     config.read(CONFIGDIR + '/.calendar.cfg')
    #     
    #     self.service = 'gcalendar'
    #     self.nick = config.get(Acc,'user')+'@'+config.get(Acc,'server')
    #     fileStore = self.confName((config.get(Acc,'server'), 
    #         config.get(Acc,'user'))) 
    # 
    #     logging.debug("Filestore %s"% fileStore)
    #     store = file.Storage(fileStore)
    #     credentials = store.get()
    #     
    #     service = build('calendar', 'v3', http=credentials.authorize(Http()))
    # 
    #     self.client = service
    #     self.name = 'GCalendar' + Acc[3:]
    #     self.active = 'primary'

    # def authorize(self):
    #     # based on Code from
    #     # https://github.com/gsuitedevs/python-samples/blob/aacc00657392a7119808b989167130b664be5c27/gmail/quickstart/quickstart.py
    #     # https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py?hl=es

    #     SCOPES = self.scopes

    #     #logging.info(f"    Connecting {self.service}: {account}")
    #     pos = self.user.rfind('@') 
    #     self.server = self.user[pos+1:]
    #     self.nick = self.user[:pos]

    #     fileCredStore = self.confName((self.server, self.nick)) 
    #     fileTokenStore = self.confTokenName((self.server, self.nick)) 
    #     creds = None

    #     store = file.Storage(fileTokenStore)
    #     logging.debug(f"filetokenstore: {fileTokenStore}")
    #     creds = store.get()

    #     if not creds: 
    #         if creds and creds.expired and creds.refresh_token: 
    #             logging.info("Needs to refresh token GMail")
    #             creds.refresh(Request()) 
    #         else: 
    #             logging.info("Needs to re-authorize token GMail")

    #             try:
    #                 flow = client.flow_from_clientsecrets(fileCredStore, 
    #                                                      SCOPES)
    #                 creds = tools.run_flow(flow, store, 
    #                        tools.argparser.parse_args(args=['--noauth_local_webserver']))
    #                 # creds = ServiceAccountCredentials.from_json_keyfile_name(
    #                 #                     key_file_location, scopes=SCOPES)
    #                 # flow = InstalledAppFlow.from_client_secrets_file( 
    #                 #     fileCredStore, SCOPES, 
    #                 #     redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    #                 # creds = flow.run_console(
    #                 #         authorization_prompt_message='Please visit this URL: {url}', 
    #                 #         success_message='The auth flow is complete; you may close this window.')
    #                 # Save the credentials for the next run
    #             except FileNotFoundError:
    #                 print("no")
    #                 print(fileCredStore)
    #                 sys.exit()
    #             except ValueError:
    #                 print("Error de valor")
    #                 creds = 'Fail!'
    #     logging.debug("Storing creds")
    #     # with open(fileTokenStore, 'wb') as token:
    #     #     pickle.dump(creds, token)

    #     return(creds)

    def setActive(self, idCal):
        self.active = idCal

    def setCalendarList(self): 
        logging.info(f"{self.indent} Setting calendar list")
        api = self.getClient()
        page_token = None
        self.calendars = api.calendarList().list(pageToken=page_token).execute().get('items',[])

    def getCalendarList(self): 
        return(self.calendars)

    def setPosts(self, date=''):
        logging.info(f"{self.indent} Setting posts")
        logging.info(f"{self.indent} Setting posts date %s"%date)
        api = self.getClient()
        theDate = ''
        if date:
            theDate = dateparser.parse(date)
            if theDate: 
                theDate = theDate.isoformat()+'Z'
        if not theDate: 
            theDate= datetime.datetime.utcnow().isoformat() + 'Z' 

        # 'Z' indicates UTC time
        page_token = None

        self.posts = []
        if hasattr(self, 'active'):
            events_result = api.events().list(calendarId=self.active,
                timeMin=theDate, maxResults=10, singleEvents=True,
                orderBy='startTime').execute() 
            self.posts = events_result.get('items',[])
        else:
            self.posts = None

        return("orig. "+date+" Translated." + theDate)


    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)

        (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment) = (None, None, None, None, None, None, None, None, None, None) 

        event = self.getPosts()[i]
        import pprint
        pprint.pprint(event)

        if 'summary' in event:
            theTitle = event['summary']
        else:
            theTitle = 'Busy'
        if 'htmlLink' in event:
            theLink = event['htmlLink']
        else:
            theLink = ''
        if 'description' in event:
            theContent = event['description']
        else:
            theContent = ""
        if 'start' in event:
            theSummary = event['start']['dateTime'] + ' ' + event['end']['dateTime']
        else:
            theSummary = ''
        if 'creator' in event:
            content = event['creator']['email']
        else:
            content = ''

        print(theTitle, theLink)
        print(theContent)
        print(theSummary)


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


def main():
    logging.basicConfig(stream=sys.stdout, 
            level=logging.DEBUG, 
            format='%(asctime)s %(message)s')

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    testingList = True
    if testingList:
        for key in rules.rules.keys():
            if (key[0] == 'gcalendar'):
                print(f"SKey: {key}\n"
                      f"SRule: {rules.rules[key]}\n"
                      f"SMore: {rules.more[key]}")
                apiSrc = rules.readConfigSrc("", key, rules.more[key])
                apiSrc.setCalendarList()
                print(f"List: {apiSrc.getCalendarList()}")
                for i, cal in enumerate(apiSrc.getCalendarList()): 
                    print(f"{i}) {cal.get('summary')}")
                option = input("Select one: ")

                apiSrc.setActive(apiSrc.getCalendarList()[int(option)].get('id'))
                apiSrc.setPosts('2022-07-11')
                print("Citas:")
                for i, event in enumerate(apiSrc.getPosts()):
                    import datetime

                    import pytz
                    from dateutil import parser

                    d1 = parser.parse(event['updated'])
                    today = datetime.datetime.combine(datetime.date.today(), 
                            datetime.datetime.min.time())
                    today = pytz.utc.localize(today)
                    today = pytz.utc.localize(parser.parse("2022-07-11"))

                    # print(f"Hoy: {today}")

                    # print (f"{event['created']} {event['updated']}")
                    # print(f"{d1 - today}")
                    if abs((d1 - today).days) < 7:
                        import pprint

                        # print (f"{i}) {event}")
                        description = event.get('description') 
                        if description:
                            description = description[:60]
                        print (f"{event['start']['dateTime']} "
                               f"{event.get('summary')} "
                               f"{description} "
                               f"{event.get('hangoutLink')}")

 
    return 
    calendar = moduleGcalendar()
    calendar.setClient('ACC0')
    calendar.setCalendarList()
    print(calendar.getCalendarList())
    for i, cal in enumerate(calendar.getCalendarList()):
        print (f"{i}) {cal}")
    return
    print(calendar.getCalendarList()[10])
    sys.exit()
    calendar.setActive('dpi6ce608h8j09ocolamshl8kk@group.calendar.google.com')
    sys.exit()
    calendar.setPosts()

    print(calendar.getPosts())
    print(calendar.extractDataMessage(1))
    print(calendar.nick)
    print(len(calendar.getPosts()))
    calendar.setCalendarList()
    print(calendar.getCalendarList())
    for i, cal in enumerate(calendar.getCalendarList()):
        print(i, cal['summary'],cal['id'])
    calendar.setActive(calendar.getCalendarList()[10]['id'])
    calendar.setPosts()
    print(calendar.getPosts())


if __name__ == "__main__":
    main()

