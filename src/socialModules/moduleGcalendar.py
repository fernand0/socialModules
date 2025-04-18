#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

import configparser
import datetime
import logging
import os
import sys

# from dateutil.parser import parse
import dateparser

from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleGoogle import *


class moduleGcalendar(Content, socialGoogle):

    def initApi(self, keys):
        self.service = "Gcalendar"
        msgLog = f"{self.indent} initApi {self.service}"
        logMsg(msgLog, 2, 0)
        self.scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar",
        ]

        service = self.authorize('calendar', 'v3')
        self.active = "primary"

        return service

    def setActive(self, idCal):
        self.active = idCal

    def getActive(self):
        return self.active

    def setCalendarList(self):
        logging.info(f"{self.indent} Setting calendar list")
        api = self.getClient()
        page_token = None
        self.calendars = (
            api.calendarList().list(pageToken=page_token).execute().get("items", [])
        )

    def getCalendarList(self):
        return self.calendars

    def setPosts(self, date=""):
        logging.info(f"{self.indent} Setting posts")
        logging.info(f"{self.indent} Setting posts date {date}")
        api = self.getClient()
        if not date:
            theDate = datetime.datetime.now()
            theDate = theDate.isoformat(timespec="seconds") + "Z"
        else:
            theDate = dateparser.parse(date)
            if theDate:
                theDate = theDate.isoformat() + "Z"

        # 'Z' indicates UTC time
        page_token = None
        logging.info(f"{self.indent} Setting posts date {theDate}")

        self.posts = []
        if hasattr(self, "active"):
            events_result = (
                api.events()
                .list(
                    calendarId=self.active,
                    timeMin=theDate,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            self.posts = []
            for item in events_result.get("items", []):
                if item["eventType"] == "workingLocation":
                    continue
                else:
                    self.posts.append(item)
        else:
            self.posts = None
        # logging.info(f"{self.indent} Results: {events_result}")
        # logging.info(f"{self.indent} Results: {self.posts}")

        return "orig. " + date + " Translated." + theDate

    def getPostTitle(self, post):
        text = post.get('summary')
        return text

    def getPostId(self, post):
        print(f"Post: {post}")
        text = post.get('id')
        return text

    def getPostAbstract(self, post):
        if "start" in post:
            if "dateTime" in post["start"]:
                dd = post["start"]["dateTime"]
            else:
                if "date" in post["start"]:
                    dd = post["start"]["date"]

        description = post.get("description", "")
        if description:
            description = description[:60]
        text = f"{dd[11:16]} " f"{post.get('summary')}"
        if description:
            text = f"{text} {description}"
        text = text.replace("\n", " ")
        return text

    def extractDataMessage(self, i):
        logging.info("Service %s" % self.service)

        (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        ) = (None, None, None, None, None, None, None, None, None, None)

        event = self.getPosts()[i]
        import pprint

        pprint.pprint(event)

        if "summary" in event:
            theTitle = event["summary"]
        else:
            theTitle = "Busy"
        if "htmlLink" in event:
            theLink = event["htmlLink"]
        else:
            theLink = ""
        if "description" in event:
            theContent = event["description"]
        else:
            theContent = ""
        if "start" in event:
            theSummary = event["start"]["dateTime"] + " " + event["end"]["dateTime"]
        else:
            theSummary = ""
        if "creator" in event:
            content = event["creator"]["email"]
        else:
            content = ""

        print(theTitle, theLink)
        print(theContent)
        print(theSummary)

        return (
            theTitle,
            theLink,
            firstLink,
            theImage,
            theSummary,
            content,
            theSummaryLinks,
            theContent,
            theLinks,
            comment,
        )

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            event = more.get("post", "").get("event","")
            api = more.get("api", "")
            idCal = more.get("post", "").get("idCal")
        res = "Fail!"
        try:
            # credentials = self.authorize()
            res = (
                api.getClient()
                .events()
                .insert(calendarId=idCal, body=event)
                .execute()
            )
            # logging.info("Res: %s" % res)
        except:
            res = self.report("Gmail", idCal, "", sys.exc_info())

        return f"Res: {res}"

def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    import moduleRules

    rules = moduleRules.moduleRules()
    rules.checkRules()

    print(f"Selecting rule")
    apiSrc = rules.selectRuleInteractive()

    if not apiSrc.getClient().__getstate__():
        return

    print(f"Testing list")
    testingList = True
    if testingList:
        apiSrc.setCalendarList()
        print(f"List: {apiSrc.getCalendarList()}")
        for i, cal in enumerate(apiSrc.getCalendarList()):
            print(f"{i}) {cal.get('summary')}")
        option = input("Select one: ")

        apiSrc.setActive(apiSrc.getCalendarList()[int(option)].get("id"))
        import datetime
        from dateutil import parser
        import pytz

        today = datetime.datetime.combine(
            datetime.date.today(), datetime.datetime.min.time()
        )
        today = pytz.utc.localize(today)
        # today = pytz.utc.localize(parser.parse("2022-07-11"))

        date = input("Date? (today) ")
        print(f"Date: *{date}*")
        apiSrc.setPosts(date)
        print(f"\nHoy: {str(today)[:10]}")
        print(f"Citas [{apiSrc.getCalendarList()[int(option)].get('summary')}]:")

        prevDifTime = ""
        for i, event in enumerate(apiSrc.getPosts()):
            # if event['eventType'] == 'workingLocation':
            #     continue
            if "start" in event:
                if "dateTime" in event["start"]:
                    dd = event["start"]["dateTime"]
                    d1 = parser.parse(dd)
                else:
                    if "date" in event["start"]:
                        dd = event["start"]["date"]
                        d1 = parser.parse(dd)
                        d1 = pytz.utc.localize(d1)
            else:
                d1 = today

            difTime = str(d1 - today).split(",")[0]
            if difTime != prevDifTime:
                # difTimeP = parser.parse(difTime)
                print(f"In {difTime} ({str(d1)[:10]})")
                prevDifTime = difTime
            if abs((d1 - today).days) < 7:
                text = apiSrc.getPostAbstract(event)
                print(f" Abstract: {text}")
                # text = apiSrc.getPostTitle(event)
                # print(f"Title: {text}*")
    return


if __name__ == "__main__":
    main()
