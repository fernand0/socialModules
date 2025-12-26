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
        logMsg(msgLog, 2, False)
        self.scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar",
        ]

        service = self.authorize("calendar", "v3")
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

    def getApiPostTitle(self, post):
        text = post.get("summary")
        return text

    def getPostId(self, post):
        text = post.get("id")
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
        event = None
        idCal = None

        if args and len(args) == 3:
            title, link, comment = args
            # Basic event structure from args, might need more details depending on usage
            event = {
                "summary": title,
                "description": comment or "",
                "start": {
                    "dateTime": (datetime.datetime.now()).isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": (
                        datetime.datetime.now() + datetime.timedelta(hours=1)
                    ).isoformat(),
                    "timeZone": "UTC",
                },
            }
            idCal = self.getActive()  # Assume we're publishing to the active calendar
        elif kwargs:
            more = kwargs.get("post", {})
            event = more.get("event")
            idCal = more.get("idCal")

        if not event or not idCal:
            self.res_dict["error_message"] = "Event data or calendar ID is missing."
            return self.res_dict

        try:
            api = self.getClient()
            res = api.events().insert(calendarId=idCal, body=event).execute()
            self.res_dict["raw_response"] = res
            if res and "htmlLink" in res:
                self.res_dict["success"] = True
                self.res_dict["post_url"] = res["htmlLink"]
            else:
                self.res_dict["error_message"] = (
                    "Event creation did not return the expected response."
                )
        except Exception as e:
            self.res_dict["error_message"] = self.report(
                "Gcalendar", idCal, "", sys.exc_info()
            )
            self.res_dict["raw_response"] = e

        return self.res_dict

    def get_user_info(self, client):
        # For Gcalendar, we can return the active calendar's summary
        if hasattr(self, "active"):
            return f"Active Calendar: {self.active}"
        return "Gcalendar User"

    def get_post_id_from_result(self, result):
        # Assuming result is the event object itself
        return self.getPostId(result)


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    gcalendar_module = moduleGcalendar()
    tester = ModuleTester(gcalendar_module)
    tester.run()


if __name__ == "__main__":
    main()
