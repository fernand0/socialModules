#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

import configparser, os
import datetime
#from dateutil.parser import parse
import dateparser
import logging
import sys

import googleapiclient
from googleapiclient.discovery import build
from googleapiclient import http
from httplib2 import Http
from oauth2client import file, client, tools

from configMod import *
from moduleContent import *

class moduleGcalendar(Content):    
    
    def __init__(self):
        Content().__init__()
        self.service = None
        self.nick = None

    def confName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + self.service + '_'
                + acc[0]+ '_' 
                + acc[1]+ '.json')
        return(theName)
 
    def setClient(self, Acc):
        # based on get_credentials from 
        # Code from
        # https://developers.google.com/gmail/api/v1/reference/users/messages/list
        # and
        # http://stackoverflow.com/questions/30742943/create-a-desktop-application-using-gmail-api
    
        SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
        self.url = SCOPES
        api = {}
    
        config = configparser.ConfigParser() 
        config.read(CONFIGDIR + '/.calendar.cfg')
        
        self.service = 'gcalendar'
        self.nick = config.get(Acc,'user')+'@'+config.get(Acc,'server')
        fileStore = self.confName((config.get(Acc,'server'), 
            config.get(Acc,'user'))) 
    
        logging.debug("Filestore %s"% fileStore)
        store = file.Storage(fileStore)
        credentials = store.get()
        
        service = build('calendar', 'v3', http=credentials.authorize(Http()))
    
        self.client = service
        self.name = 'GCalendar' + Acc[3:]
        self.active = 'primary'

    def setActive(self, idCal):
        self.active = idCal

    def setCalendarList(self): 
        logging.info("  Setting calendar list")
        api = self.getClient()
        page_token = None
        self.calendars = api.calendarList().list(pageToken=page_token).execute().get('items',[])

    def getCalendarList(self): 
        return(self.calendars)

    def setPosts(self, date=''):
        logging.info("  Setting posts")
        logging.info("  Setting posts date %s"%date)
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
        events_result = api.events().list(calendarId=self.active,
            timeMin=theDate, maxResults=10, singleEvents=True,
            orderBy='startTime').execute() 
        logging.debug(f"Events: {events_result}")
        self.posts = events_result.get('items',[])

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
            level=logging.INFO, 
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
                print(f"Api: {apiSrc.nick}")
                apiSrc.setCalendarList()
                print(f"List: {apiSrc.getCalendarList()}")
                apiSrc.setActive('dpi6ce608h8j09ocolamshl8kk@group.calendar.google.com')
                apiSrc.setActive('unizar.es_qg30e83ju3fp3l2clpom56kphg@group.calendar.google.com')
                apiSrc.setActive('ftricas@unizar.eS')
                apiSrc.setPosts()
                print("Citas:")
                for i, event in enumerate(apiSrc.getPosts()):
                    import datetime
                    from dateutil import parser
                    import pytz

                    d1 = parser.parse(event['updated'])
                    today = datetime.datetime.combine(datetime.date.today(), 
                            datetime.datetime.min.time())
                    today = pytz.utc.localize(today)

                    # print(f"Hoy: {today}")

                    # print (f"{event['created']} {event['updated']}")
                    # print(f"{d1 - today}")
                    if abs((d1 - today).days) < 7:
                        logging.debug(f"{i}) {event}")
                        start = event.get('start').get('dateTime', event.get('start').get('date'))
                        print (f"Start: {start}")
                        end = event.get('end').get('dateTime', event.get('end').get('date'))
                        print (f"End: {end}")
                        summary = event.get('summary','')
                        if summary:
                            print (f"Summary: {summary}")
                        description = event.get('description','')
                        if description:
                            print (f"Description: {description}")
                        meet = event.get('hangoutLink','')
                        if meet:
                            print (f"Meet link: {meet}")

 
    return 
    calendar = moduleGcalendar()
    calendar.setClient('ACC0')
    calendar.setCalendarList()
    print(calendar.getCalendarList())
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

