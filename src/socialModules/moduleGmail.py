#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

# From: https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
from __future__ import print_function

import base64
import configparser
import datetime
import email
import io
import logging
import os
import pickle
import sys
from email.parser import BytesParser

from bs4 import BeautifulSoup

import socialModules.moduleImap
from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleGoogle import *

class moduleGmail(Content, socialGoogle):  # Queue,socialGoogle):
    def initApi(self, keys):
        self.service = "Gmail"
        msgLog = f"{self.indent} initApi {self.service}"
        logMsg(msgLog, 2, False)
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.labels",
            "https://www.googleapis.com/auth/gmail.modify",
            #'https://mail.google.com/']
        ]

        service = self.authorize("gmail", "v1")

        return service

    def createLabel(self, labelName):
        api = self.getClient()
        label_object = {
            "messageListVisibility": "show",
            "name": labelName,
            "labelListVisibility": "labelShow",
        }
        return api.users().labels().create(userId="me", body=label_object).execute()

    def deleteLabel(self, labelName):
        api = self.getClient()
        label_id = self.getLabelId(labelName)
        msgLog = f"{self.indent} Label id: {label_id}"
        logMsg(msgLog, 2, False)
        return api.users().labels().delete(userId="me", id=label_id).execute()

    def updateLabel(self, label_id, labelName):
        api = self.getClient()
        label_object = {
            "messageListVisibility": "show",
            "name": labelName,
            "labelListVisibility": "labelShowIfUnread",
        }
        return (
            api.users()
            .labels()
            .update(userId="me", id=label_id, body=label_object)
            .execute()
        )

    def listFolders(self):
        self.setLabels()
        return self.getLabels()

    def getChannelName(self, channel):
        return channel.get("name", "")

    def setLabels(self):
        api = self.getClient()
        response = api.users().labels().list(userId="me").execute()
        if "labels" in response:
            self.labels = response["labels"]

    def getLabels(self, sel=""):
        if not hasattr(self, "labels") or not self.labels:
            self.setLabels()
        if isinstance(sel, dict):
            sel = sel["name"]
        logging.info(f"Labels: {self.labels}")
        logging.info(f"Labels: {sel}")
        return list(filter(lambda x: sel in x["name"], self.labels))

    def getLabelsNames(self, sel=""):
        labels = list(filter(lambda x: sel in x["id"], self.labels))
        return list(map(lambda x: x["name"], labels))

    def getLabelsIds(self, sel=""):
        labels = list(filter(lambda x: sel in x["name"], self.labels))
        return list(map(lambda x: x["id"], labels))

    def getLabelsEqIds(self, sel=""):
        labels = list(filter(lambda x: sel.upper() == x["name"].upper(), self.labels))
        return list(map(lambda x: x["id"], labels))

    def getListLabel(self, label):
        api = self.getClient()
        list_labels = [
            label,
        ]
        response = (
            api.users()
            .messages()
            .list(
                userId="me",
                # q='before:2021/6/1 is:unread',
                labelIds=list_labels,
            )
            .execute()
        )
        return response

    def modifyLabels(self, messageId, oldLabelId, labelId):
        api = self.getClient()
        if isinstance(oldLabelId, dict):
            oldLabelId = oldLabelId.get("id")
        list_labels = {
            "removeLabelIds": [
                oldLabelId,
            ],
            "addLabelIds": [
                labelId,
            ],
        }
        logging.info(list_labels)
        # print(message)

        try:
            message = (
                api.users()
                .messages()
                .modify(userId="me", id=messageId, body=list_labels)
                .execute()
            )
        except googleapiclient.errors.HttpError as e:
            logging.error(f"Error deleting email: {e}")
            message = ""

        return message

    def getDrafts(self):
        return self.getPosts()

    def processPosts(self, posts, label, mode):
        pPosts = []
        typePosts = self.getPostsType()
        if typePosts in ["search", "posts"]:
            typePosts = "messages"
        # if typePosts in posts:
        # for post in posts['messages']: #[typePosts]:
        if posts["resultSizeEstimate"] > 0:
            for post in posts[typePosts]:
                if mode != "raw":
                    meta = self.getMessageMeta(post["id"], typePosts)
                    message = {}
                    message["list"] = post
                    message["meta"] = meta
                    post_id = self.getPostId(post)
                    email_result = self.getMessage(post_id)
                    message["body"] = email_result
                else:
                    raw = self.getMessageRaw(post["id"], typePosts)
                    message = {}
                    message["list"] = post
                    message["meta"] = ""
                    message["raw"] = raw

                pPosts.insert(0, message)
        return pPosts

    def setApiSearch(self, label=None, mode=""):
        client = self.getClient()
        posts = []
        if client:
            posts = (
                self.getClient()
                .users()
                .messages()
                .list(userId="me", q=self.getSearch())
                .execute()
            )
            posts = self.processPosts(posts, label, mode)
        logging.info(f"Num posts {len(posts)}")
        return posts

    def setApiSearchh(self, label=None, mode=""):
        # Not sure about how the searching works
        searchTerm = self.getSearch()
        searchQ = f"in:inbox is:unread Subject:({searchTerm})"
        posts = (
            self.getClient()
            .users()
            .messages()
            .list(userId="me", q=searchQ, includeSpamTrash=False)
            .execute()
        )
        posts = self.processPosts(posts, label, mode)
        return posts

    def setApiDrafts(self, label=None, mode=""):
        posts = self.getClient().users().drafts().list(userId="me").execute()
        posts = self.processPosts(posts, label, mode)
        return posts

    def setChannel(self, channel=""):
        logging.info(f"Channel: {channel}")
        if not channel:
            folder = self.selectFolder()
            print(f"Folder: {folder}")
            self.channel = folder
        else:
            self.channel = channel

    def checkConnected(self):
        try:
            self.getClient().users().getProfile(userId='me').execute()
        except Exception as e:
            logMsg(f"Gmail connection issue detected: {e}", 3, False)
            self.setClient(f"{self.user}")
            try:
                self.getClient().users().getProfile(userId='me').execute()
                logMsg("Gmail reconnection successful.", 1, False)
            except Exception as e:
                log_msg = f"Gmail reconnection failed for user {self.user}."
                logMsg(f"{log_msg} Error: {e}", 3, False)
                self.report(self.service, "", "", sys.exc_info())
                raise ConnectionError(log_msg) from e

    def getChannel(self):
        return self.channel

    def setApiPosts(self, label=None, mode=""):
        label = ""
        if (not label) and hasattr(self, "channel"):
            label = self.getChannel()
        return self.setApiMessages(label, mode)

    def setApiMessages(self, label=None, mode=""):
        msgLog = f"{self.indent} Label: {label}"
        logMsg(msgLog, 2, False)
        if isinstance(label, str):
            if not label:
                label = "INBOX"
            self.setLabels()
            label = self.getLabels(label)
            if len(label) > 0:
                label = label[0]
                msgLog = f"{self.indent} Label: {label}"
                logMsg(msgLog, 2, False)
            else:
                msgLog = f"{self.indent} The label does not exist"
                logMsg(msgLog, 2, False)
        if label:
            posts = self.getListLabel(label["id"])
        else:
            posts = (
                self.getClient()
                .users()
                .messages()
                .list(userId="me", maxResults=150)
                .execute()
            )
        posts = self.processPosts(posts, label, mode)
        return posts

    # def confName(self, acc):
    #     theName = os.path.expanduser(CONFIGDIR + '/' + '.'
    #             + acc[0]+ '_'
    #             + acc[1]+ '.json')
    #     return(theName)

    # def confTokenName(self, acc):
    #     theName = os.path.expanduser(CONFIGDIR + '/' + '.'
    #             + acc[0]+ '_'
    #             + acc[1]+ '.token.json')
    #     return(theName)

    def getMessageId(self, idPost):
        api = self.getClient()
        message = api.users().messages().get(userId="me", id=idPost).execute()
        # import pprint
        # pprint.pprint(f"mes: {message}")
        mes = ""
        if "body" in message:
            mes = mes + str(base64.urlsafe_b64decode(message["body"]))
        elif "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                # logging.debug(f"Part: {part}")
                if "data" in part["body"]:
                    mes = mes + str(base64.urlsafe_b64decode(part["body"]["data"]))
                elif "parts" in part:
                    for pp in part["parts"]:
                        if "data" in pp["body"]:
                            mes = mes + str(
                                base64.urlsafe_b64decode(pp["body"]["data"])
                            )
                elif "data" in part["body"]:
                    print(f"Part body: {part['body']}")
                    mes = mes + str(base64.urlsafe_b64decode(part["body"]["data"]))
        else:
            mes = str(base64.urlsafe_b64decode(message["payload"]["body"]["data"]))
        mes = mes.encode().decode("unicode_escape")
        # The messages come with escape characters and some encoding
        # FIXME Is this the correct place?

        return mes

    def getMessage(self, idPost):
        api = self.getClient()
        if "draft" in self.getPostsType():
            message = api.users().drafts().get(userId="me", id=idPost).execute()
        else:
            message = api.users().messages().get(userId="me", id=idPost).execute()
        # print(message)
        # print(message['message'])
        return message

    def getMessageFull(self, msgId, typePost="drafts"):
        api = self.getClient()
        if typePost == "drafts":
            message = (
                api.users()
                .drafts()
                .get(userId="me", id=msgId, format="full")
                .execute()["message"]
            )
        else:
            message = (
                api.users()
                .messages()
                .get(userId="me", id=msgId, format="full")
                .execute()
            )

        return message

    def getMessageRaw(self, msgId, typePost="drafts"):
        api = self.getClient()
        if typePost == "drafts":
            message = (
                api.users()
                .drafts()
                .get(userId="me", id=msgId, format="raw")
                .execute()["message"]
            )
        else:
            message = (
                api.users()
                .messages()
                .get(userId="me", id=msgId, format="raw")
                .execute()
            )

        return message

    def getMessageMeta(self, msgId, typePost="drafts"):
        api = self.getClient()
        if typePost == "drafts":
            message = (
                api.users()
                .drafts()
                .get(userId="me", id=msgId, format="metadata")
                .execute()["message"]
            )
        else:
            message = (
                api.users()
                .messages()
                .get(userId="me", id=msgId, format="metadata")
                .execute()
            )
        return message

    def setHeader(self, message, header, value):
        for head in message["payload"]["headers"]:
            if head["name"].capitalize() == header.capitalize():
                head["value"] = value

    def setHeaderEmail(self, message, header, value):
        # Email methods are related to the email.message objetcs
        if header in message:
            del message[header]
            message[header] = value

    def getPosNextPost(self):
        # gmail always shows the first item ?
        # Some standard contition?

        posLast = 1

        return posLast

    def getPostLinksWithText(self, post):
        message = self.getMessageId(self.getPostId(post))
        messageClean = message.replace("\\r\\n", " ")
        soup = BeautifulSoup(messageClean, "lxml")
        logging.debug(f"Soup: {soup}")
        res = soup.find_all("a", href=True)
        data = {}
        for element in res:
            link = element["href"]
            if not link and "title" in element:
                if "http" in element["title"]:
                    link = element["title"]
            text = element.text
            logging.debug(f"Linkk: {link} text: {text}")
            if link and not (link in data):
                data[link] = (text, link, element)
            else:
                data[link] = (f"{data[link][0]} {text}", data[link][1], data[link][2])
        links = []
        for key in data:
            links.append(data[key])
        return links

    def getPostContentHtml(self, post):
        msgLog = f"{self.indent} getPostDate"
        logMsg(msgLog, 2, False)
        # message = self.getMessageId(self.getPostId(post))
        if post:
            snippet = self.getHeader(post, "snippet")
            return snippet
        return None

    def getPostLinks(self, post):
        message = self.getMessageId(self.getPostId(post))
        soup = BeautifulSoup(message, "lxml")
        # logging.debug(soup)
        res = soup.find_all("a", href=True)
        # logging.debug(res)
        links = []
        for element in res:
            link = element["href"]
            if not (link in links):
                links.append(link)
        return links

    def getApiPostLink(self, post):
        # fromP = self.getHeader(post, 'From')
        # snippet = self.getHeader(post, 'snippet')
        theLink = ""
        if post:
            msgLog = f"{self.indent} Post: {post}"
            logMsg(msgLog, 2, False)
            links = self.getPostLinks(post)
            msgLog = f"{self.indent} Links: {links}"
            logMsg(msgLog, 2, False)
            if links:
                theLink = links[0]

        # result = f"From: {fromP}\nText: {snipP}"
        result = theLink
        return result

    def getApiPostTitle(self, post):
        msgLog = f"{self.indent} getPostTitle"
        logMsg(msgLog, 2, False)
        # msgLog = f"{self.indent} {post}"
        # logMsg(msgLog, 2, False)
        title = ""
        if post:
            title = self.getHeader(post)
        return title

    def getPostDate(self, post):
        msgLog = f"{self.indent} getPostDate"
        logMsg(msgLog, 2, False)
        # msgLog = f"{self.indent} Post: {post}"
        # logMsg(msgLog, 2, False)
        if post:
            date = self.getHeader(post, "internalDate")
            # date = int(self.getHeader(post,'internalDate'))/1000
            # print(f"Dateeeee: {date}")
            # date = '{}'.format(datetime.datetime.fromtimestamp(date)) # Bad!
            return date
        return None

    def getHeader(self, message, header="Subject"):
        msgLog = f"{self.indent} getHeader {header}"
        logMsg(msgLog, 2, False)
        msgLog = f"{self.indent} Message: {message}"
        logMsg(msgLog, 2, False)
        # if "message" in message:
        #     message = message["message"]
        if "meta" in message:
            message = message["meta"]
        for head in message:
            if head.capitalize() == header.capitalize():
                return message[head]
        for head in message["payload"]["headers"]:
            if head["name"].capitalize() == header.capitalize():
                return head["value"]

    def getPostId(self, message):
        logging.debug(f"Message: {message}")
        # print(f"Message: {'list' in message}")
        if isinstance(message, str):
            idPost = message
        elif "meta" in message:
            message = message["meta"]
            idPost = message["id"]
        elif isinstance(message, tuple):
            # logging.debug(message)
            idPost = message
        elif "id" in message:
            idPost = message.get("id")

        return idPost

    def getHeaderEmail(self, message, header="Subject"):
        if header in message:
            return moduleImap.headerToString(message[header])

    def getHeaderRaw(self, message, header="Subject"):
        if header in message:
            return message[header]

    def getEmail(self, messageRaw):
        messageEmail = email.message_from_bytes(
            base64.urlsafe_b64decode(messageRaw["raw"])
        )
        return messageEmail

    def getPostBody(self, message):
        logging.debug(f"Message: {message}")
        if "body" in message:
            mess = message["body"]
        res = self.getHeader(mess, "payload")
        if not res:
            print("No ressss")
            res = message
        if "parts" in res:
            if "parts" in res["parts"]:
                logging.debug("parts 1 parts")
                text = res["parts"]["parts"][0]["parts"]
            else:
                text = res["parts"][0]
                if "parts" in text:
                    logging.debug("parts 2 parts")
                    text = text["parts"][0]
        else:
            logging.debug("No partssss")
            text = res
        # print(f"Headers: {text['headers']}")

        dataB = ""
        if "body" in text and "data" in text["body"]:
            dataB = text["body"]["data"]
        else:
            if "parts" in text["body"]:
                dataB = text["body"]["parts"][0]

        if dataB:
            text = base64.urlsafe_b64decode(dataB)
        else:
            text = self.getHeader(message, "snippet")

        if isinstance(text, bytes):
            extracted_text = text.decode("utf-8")
        else:
            extracted_text = text

        return extracted_text

    def getLabelList(self):
        api = self.getClient()
        results = api.users().labels().list(userId="me").execute()
        return results["labels"]

    def nameFolder(self, label):
        folder = label
        if isinstance(label, str):
            if label and label[0].isdigit():
                pos = label.find(") ")
                if pos >= 0:
                    folder = label[pos + 2 :]
            elif isinstance(label, dict):
                folder = self.getLabelName(label)
        return folder

    def getLabelName(self, label):
        api = self.getClient()
        return label["name"]

    def getLabelId(self, name):
        api = self.getClient()
        results = self.getLabelList()
        msgLog = f"{self.indent} Labels: {results}"
        logMsg(msgLog, 2, False)
        msgLog = f"{self.indent} Name: {name}"
        logMsg(msgLog, 2, False)
        labelId = None
        for label in results:
            if (label["name"].lower() == name.lower()) or (
                label["name"].lower() == name.lower().replace("-", " ")
            ):
                msgLog = f"{self.indent} {label}"
                logMsg(msgLog, 2, False)
                labelId = label["id"]
                break

        return labelId

    def listFolderNames(self, data, inNameFolder=""):
        listFolders = ""
        i = 0

        for name in data:
            if isinstance(name, dict):
                folder_name = self.getChannelName(name)
            else:
                folder_name = name
            if inNameFolder.lower() in folder_name.lower():
                if listFolders:
                    listFolders += f"\n{i}) {self.nameFolder(folder_name)}"
                else:
                    listFolders = f"{i}) {self.nameFolder(folder_name)}"
            i += 1
        return listFolders

    def selectFolder(self, moreMessages="", newFolderName="", folderM=""):

        data = self.listFolders()
        listAllFolders = self.listFolderNames(data, moreMessages)
        if not listAllFolders:
            listAllFolders = self.listFolderNames(data, "")
        listFolders = listAllFolders
        while listFolders:
            if "\n" not in listFolders:
                logging.info(f"Nottt: {listFolders}")
                nF = listFolders
                if isinstance(listFolders, dict):
                    nF = self.getChannelName(listFolders)
                nF = nF.strip("\n")
                nF = nF.split(') ')[1]
                logging.info("nameFolder", nF)
                return nF

            rows, columns = os.popen("stty size", "r").read().split()
            if listFolders.count("\n") > int(rows) - 2:
                click.echo_via_pager(listFolders)
            else:
                print(listFolders)

            inNameFolder = input(
                f"Folder number [-cf] Create Folder // A string to select a smaller set of folders ({folderM}) "
            )
            if not inNameFolder and folderM:
                inNameFolder = folderM

            if inNameFolder == "-cf":
                if newFolderName:
                    nfn = newFolderName
                else:
                    nfn = input(f"New folder name? ({folderM})")
                    if not nfn:
                        nfn = folderM
                iFolder = self.createLabel(nfn)
                return iFolder

            listFolders = self.listFolderNames(listFolders.split("\n"), inNameFolder)
            if not inNameFolder:
                listAllFolders = self.listFolderNames(data, "")
                listFolders = ""
            if not listFolders:
                listFolders = listAllFolders


    def editl(self, j, newTitle):
        return "Not implemented!"

    def edit(self, j, newTitle):
        msgLog = f"{self.indent} edit"
        logMsg(msgLog, 2, False)
        msgLog = f"{self.indent} New title: {newTitle}"
        logMsg(msgLog, 2, False)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        # logging.info("servicename %s" %self.service)

        import base64
        import email
        from email.parser import BytesParser

        api = self.getClient()

        idPost = self.getPosts()[j]["list"]["id"]  # thePost[-1]
        title = self.getHeader(self.getPosts()[j]["meta"], "Subject")
        message = self.getMessageRaw(idPost)
        theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message["raw"]))
        self.setHeaderEmail(theMsg, "subject", newTitle)
        message["raw"] = theMsg.as_bytes()
        message["raw"] = base64.urlsafe_b64encode(message["raw"]).decode()

        update = (
            api.users()
            .drafts()
            .update(userId="me", body={"message": message}, id=idPost)
            .execute()
        )

        msgLog = f"{self.indent} Update {update}"
        logMsg(msgLog, 2, False)
        update = "Changed " + title + " with " + newTitle
        return update

    def publishApiPost(self, *args, **kwargs):
        idPost = None
        if kwargs:
            more = kwargs
            post = more.get("post", "")
            api = more.get("api", "")
            if post:
                idPost = post.get("list", {}).get("id")

        if not idPost:
            self.res_dict["error_message"] = "Could not get post ID to send draft."
            return self.res_dict

        try:
            res = (
                api.getClient()
                .users()
                .drafts()
                .send(userId="me", body={"id": str(idPost)})
                .execute()
            )
            self.res_dict["raw_response"] = res
            if res and 'id' in res:
                self.res_dict["success"] = True
                # The API response for sending a draft doesn't contain a direct web link.
                # We can consider the message ID as a reference.
                self.res_dict["post_url"] = f"gmail_message_id:{res['id']}"
            else:
                self.res_dict["error_message"] = "Failed to send draft."

        except Exception as e:
            self.res_dict["error_message"] = self.report("Gmail", idPost, "", sys.exc_info())
            self.res_dict["raw_response"] = e

        return self.res_dict

    def trash(self, j, typePost="drafts"):
        msgLog = f"{self.indent} trash"
        logMsg(msgLog, 2, False)
        msgLog = f"{self.indent} Trashing {j}"
        logMsg(msgLog, 2, False)

        api = self.getClient()
        idPost = self.getPosts()[j]["list"]["id"]  # thePost[-1]
        try:
            title = self.getHeader(self.getPosts()[j]["meta"], "Subject")
        except:
            title = ""
        if typePost == "drafts":
            update = api.users().drafts().trash(userId="me", id=idPost).execute()
        else:
            update = api.users().messages().trash(userId="me", id=idPost).execute()

        return "Trashed %s" % title

    def deleteApiSearch(self, idPost):
        result = self.deleteApiPost(idPost)
        return result

    def deleteApiMessages(self, idPost):
        return self.deleteApiPost(idPost)

    def deleteApiPosts(self, idPost):
        return self.deleteApiPost(idPost)

    def deleteApiPost(self, idPost):
        api = self.getClient()
        result = api.users().messages().trash(userId="me", id=idPost).execute()
        msgLog = f"{self.indent} Res: {result}"
        logMsg(msgLog, 2, False)
        return result

    def deleteApiPostDelete(self, idPost):
        api = self.getClient()
        result = api.users().messages().delete(userId="me", id=idPost).execute()
        msgLog = f"{self.indent} Res: {result}"
        logMsg(msgLog, 2, False)
        return result

    def delete(self, j):
        msgLog = f"{self.indent} getHeader"
        logMsg(msgLog, 2, False)
        msgLog = f"{self.indent} Deleting {j}"
        logMsg(msgLog, 2, False)

        typePost = self.getPostsType()
        # logging.info(f"Deleting {typePost}")

        if not typePost or (typePost == "search"):
            typePost = "messages"

        api = self.getClient()
        idPost = self.getPosts()[j]["list"]["id"]  # thePost[-1]
        try:
            title = self.getHeader(self.getPosts()[j]["meta"], "Subject")
        except:
            title = ""

        # logging.info(f"id {idPost}")

        if typePost == "drafts":
            update = api.users().drafts().trash(userId="me", id=idPost).execute()
        else:
            # logging.info(f"id {idPost}")
            update = api.users().messages().trash(userId="me", id=idPost).execute()
            # logging.info(f"id {update}")

        return "Deleted %s" % title

    def get_user_info(self, client):
        # For Gmail, we can return the user's email address
        try:
            profile = client.users().getProfile(userId='me').execute()
            return profile.get('emailAddress', 'Gmail User')
        except Exception as e:
            return f"Gmail User (Error: {e})"

    def get_post_id_from_result(self, result):
        # Assuming result is the message object itself after publishing
        if isinstance(result, dict) and "id" in result:
            return result["id"]
        return None

    def copyMessage(self, message, labels=""):
        notAllowedLabels = ["DRAFTS", "SENT"]
        api = self.getClient()
        labelIdName = "importedd"
        try:
            labelId = self.getLabelId(labelIdName)
        except:
            labelId = self.getLabelId("old-" + labelIdName)
        if not labelId:
            try:
                labelId = self.createLabel(labelIdName)
            except:
                labelId = self.createLabel("old-" + labelIdName)
        labelIds = [labelId]
        labelIdsNames = [labelIdName]
        if labels:
            for label in labels:
                if label.startswith('"'):
                    label = label[1:]
                if label.endswith('"'):
                    label = label[:-1]
                if label.upper() in notAllowedLabels:
                    label = "old-" + label
                # logging.debug("label %s"%label)
                try:
                    labelId = self.getLabelId(label)
                except:
                    labelId = self.getLabelId("old-" + label)
                if not labelId:
                    try:
                        labelId = self.createLabel(label)
                    except:
                        labelId = self.createLabel("old-" + label)
                labelIds.append(labelId)
                labelIdsNames.append(label)

        if not isinstance(message, dict):
            mesGE = base64.urlsafe_b64encode(message).decode()
            mesT = email.message_from_bytes(message)
            if mesT["subject"]:
                subj = email.header.decode_header(mesT["subject"])[0][0]
            else:
                subj = ""
            msgLog = f"{self.indent} Subject {subj}"
            logMsg(msgLog, 1, False)
        else:
            if "raw" in message:
                mesGE = message["raw"]

        try:
            messageR = (
                api.users()
                .messages()
                .import_(
                    userId="me",
                    fields="id",
                    neverMarkSpam=False,
                    processForCalendar=False,
                    internalDateSource="dateHeader",
                    body={"raw": mesGE},
                )
                .execute(num_retries=5)
            )
        #           media_body=media).execute(num_retries=1)
        except:
            # When the message is too big
            # https://github.com/google/import-mailbox-to-gmail/blob/master/import-mailbox-to-gmail.py

            msgLog = f"{self.indent} Fail 1! Trying another method."
            logMsg(msgLog, 3, False)

            try:
                if not isinstance(message, dict):
                    mesGS = BytesParser().parsebytes(message).as_string()
                    media = googleapiclient.http.MediaIoBaseUpload(
                        io.StringIO(mesGS), mimetype="message/rfc822"
                    )
                    # logging.info("vamos method")
                else:
                    media = message
                # print(media)

                messageR = (
                    api.users()
                    .messages()
                    .import_(
                        userId="me",
                        fields="id",
                        neverMarkSpam=False,
                        processForCalendar=False,
                        internalDateSource="dateHeader",
                        body={},
                        media_body=media,
                    )
                    .execute(num_retries=3)
                )
                # logging.info("messageR method")
            except:
                msgLog = "Error with message %s" % message
                logMsg(msgLog, 3, False)
                return "Fail 2!"

        msg_labels = {"removeLabelIds": [], "addLabelIds": ["UNREAD", labelId]}
        msg_labels = {
            "removeLabelIds": [],
            "addLabelIds": labelIds,
        }  # ['UNREAD', labelId]}

        messageR = (
            api.users()
            .messages()
            .modify(userId="me", id=messageR["id"], body=msg_labels)
            .execute()
        )
        return messageR

    #######################################################
    # These need work
    #######################################################

    def register_specific_tests(self, tester):
        tester.add_test("Change Mailbox Folder", self.test_change_folder)

    def test_change_folder(self, apiSrc):
        print("\n--- Changing Mailbox Folder ---")
        apiSrc.setChannel()
        print(f"Folder set to '{apiSrc.getChannel()}'")

    def listSentPosts(self, pp, service=""):
        # Undefined
        pass

    # def copyPost(self, log, pp, profiles, toCopy, toWhere):
    #     # Undefined
    #     pass

    def movePost(self, log, pp, profiles, toMove, toWhere):
        # Undefined
        pass

    def publishApiPost(self, *args, **kwargs):
        self.res_dict["error_message"] = "This method appears to be a duplicate and is not fully implemented for Gmail. Use the other publishApiPost for sending drafts."
        
        logging.warning("Attempted to use a duplicate or misplaced publishApiPost method in moduleGmail.")
        
        # The logic here seems to be for Google Calendar, not Gmail.
        # This is likely a copy-paste error. I will return a failure
        # and log a warning.

        return self.res_dict


def main():
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    gmail_module = moduleGmail()
    tester = ModuleTester(gmail_module)
    tester.run()

if __name__ == "__main__":
    main()
