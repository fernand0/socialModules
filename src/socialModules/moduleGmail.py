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

import googleapiclient
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

import socialModules.moduleImap
from socialModules.configMod import *
from socialModules.moduleContent import *
from socialModules.moduleGoogle import *

class moduleGmail(Content,socialGoogle): #Queue,socialGoogle):

    def initApi(self, keys):
        msgLog = f"{self.indent} initApi moduleGmail"
        logMsg(msgLog, 2, 0)
        self.service = "Gmail"
        self.nick = None
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly',
                       'https://www.googleapis.com/auth/gmail.labels',
                       'https://www.googleapis.com/auth/gmail.modify',
                       #'https://mail.google.com/']
                       ]

        SCOPES = self.scopes
        creds = self.authorize()
        # fileTokenStore = '/home/ftricas/.mySocial/config/tokenGmail.json'
        # msgLog = (f"{self.indent}  before creds: {creds}")
        # logMsg(msgLog, 2, 0)
        # creds = Credentials.from_authorized_user_file(fileTokenStore, SCOPES)
        # msgLog = (f"{self.indent}  creds: {creds}")
        # logMsg(msgLog, 2, 0)
        # msgLog = (f"{self.indent}  creds after: {creds}")
        # logMsg(msgLog, 2, 0)
        if isinstance(creds, str) and ("Fail!" in creds):
            service = None
        else:
            try:
                msgLog = (f"{self.indent}  building service")
                logMsg(msgLog, 2, 0)
                service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            except:
                service = self.report(self.service, "", "", sys.exc_info())
            msgLog = (f"{self.indent}  service: {service}")
            logMsg(msgLog, 2, 0)

        return service

    # def authorize(self):
    #     # based on Code from
    #     # https://github.com/gsuitedevs/python-samples/blob/aacc00657392a7119808b989167130b664be5c27/gmail/quickstart/quickstart.py

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
    #     # creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    #     creds = store.get()

    #     if not creds:
    #         if creds and creds.expired and creds.refresh_token:
    #             logging.info("Needs to refresh token GMail")
    #             creds.refresh(Request())
    #         else:
    #             logging.info("Needs to re-authorize token GMail")

    #             try:
    #                 print(f"fileCred: {fileCredStore}")
    #                 flow = client.flow_from_clientsecrets(fileCredStore,
    #                                                      SCOPES)
    #                 creds = tools.run_flow(flow, store,
    #                        tools.argparser.parse_args(args=['--noauth_local_webserver']))

    #                 # credentials = run_flow(flow, storage, args)

    #                 # flow = InstalledAppFlow.from_client_secrets_file(
    #                 #     fileCredStore, SCOPES)

    #                 # creds = flow.run_local_server(port=0)
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

    def createLabel(self, labelName):
        api = self.getClient()
        label_object = {'messageListVisibility': 'show',
                'name': labelName, 'labelListVisibility': 'labelShow'}
        return(api.users().labels().create(userId='me',
                body=label_object).execute())

    def deleteLabel(self, labelName):
        api = self.getClient()
        label_id = self.getLabelId(labelName)
        msgLog = (f"{self.indent} Label id: {label_id}")
        logMsg(msgLog, 2, 0)
        return(api.users().labels().delete(userId='me', id=label_id).execute())

    def updateLabel(self, label_id, labelName):
        api = self.getClient()
        label_object = {'messageListVisibility': 'show',
                'name': labelName, 'labelListVisibility': 'labelShowIfUnread'}
        return(api.users().labels().update(userId='me', id=label_id,
                body=label_object).execute())

    def listFolders(self):
        self.setLabels()
        return self.getLabels()

    def getChannelName(self, channel):
        return channel.get('name', '')

    def setLabels(self):
        api = self.getClient()
        response = api.users().labels().list(userId='me').execute()
        if 'labels' in response:
            self.labels = response['labels']

    def getLabels(self, sel=''):
        if not hasattr(self, 'labels') or not self.labels:
            self.setLabels()
        return(list(filter(lambda x: sel in x['name'], self.labels)))


    def getLabelsNames(self, sel=''):
        labels = (list(filter(lambda x: sel in x['id'] ,self.labels)))
        return (list(map(lambda x: x['name'], labels)))

    def getLabelsIds(self, sel=''):
        labels = (list(filter(lambda x: sel in x['name'] ,self.labels)))
        return (list(map(lambda x: x['id'], labels)))

    def getLabelsEqIds(self, sel=''):
        labels = (list(filter(lambda x: sel.upper() == x['name'].upper() ,self.labels)))
        return (list(map(lambda x: x['id'], labels)))

    def getListLabel(self, label):
        api = self.getClient()
        list_labels = [ label, ]
        logging.info(list_labels)
        response = api.users().messages().list(userId='me',
                                               #q='before:2021/6/1 is:unread',
                                               labelIds=list_labels).execute()
        return(response)

    def modifyLabels(self, message, oldLabelId, labelId):
        api = self.getClient()
        list_labels = {'removeLabelIds': [oldLabelId, ],
                'addLabelIds': [labelId, ]}
        logging.info(list_labels)
        # print(message)

        message = api.users().messages().modify(userId='me', id=message['id'],
                                                body=list_labels).execute()
        return(message)

    def getDrafts(self):
        return self.getPosts()

    def processPosts(self, posts, label, mode):
        pPosts = []
        typePosts = self.getPostsType()
        if typePosts in ['search', 'posts']:
            typePosts = 'messages'
        #if typePosts in posts:
        #for post in posts['messages']: #[typePosts]:
        if posts['resultSizeEstimate'] > 0:
            for post in posts[typePosts]:
                if mode != 'raw':
                   meta = self.getMessageMeta(post['id'],typePosts)
                   message = {}
                   message['list'] = post
                   message['meta'] = meta
                else:
                   raw = self.getMessageRaw(post['id'],typePosts)
                   message = {}
                   message['list'] = post
                   message['meta'] = ''
                   message['raw'] = raw

                pPosts.insert(0, message)
        return pPosts

    def setApiSearch(self, label=None, mode=''):
        client = self.getClient()
        posts = []
        if client:
            posts = self.getClient().users().messages().list(userId='me',
                q=self.getSearch()).execute()
            posts = self.processPosts(posts, label, mode)
        logging.info(f"Num posts {len(posts)}")
        return posts

    def setApiSearchh(self, label=None, mode=''):
        # Not sure about how the searching works
        searchTerm  = self.getSearch()
        searchQ = f"in:inbox is:unread Subject:({searchTerm})"
        posts = self.getClient().users().messages().list(
                userId='me',q=searchQ,includeSpamTrash=False).execute()
        posts = self.processPosts(posts, label, mode)
        return posts

    def setApiDrafts(self, label=None, mode=''):
        posts = self.getClient().users().drafts().list(userId='me').execute()
        posts = self.processPosts(posts, label, mode)
        return posts

    def setChannel(self, channel=''):
        self.channel = channel

    def getChannel(self):
        return self.channel

    def setApiPosts(self, label=None, mode=''):
        label = ''
        if (not label) and hasattr(self, 'channel'):
            label = self.getChannel()
        return self.setApiMessages(label, mode)

    def setApiMessages(self, label=None, mode=''):
        msgLog = (f"{self.indent} Label: {label}")
        logMsg(msgLog, 2, 0)
        if isinstance(label, str):
            self.setLabels()
            label = self.getLabels(label)
            label = label[0]
            msgLog = (f"{self.indent} Label: {label}")
            logMsg(msgLog, 2, 0)
        if label:
            posts = self.getListLabel(label['id'])
        else:
            posts = self.getClient().users().messages().list(userId='me', maxResults=150).execute()
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
        if 'body' in message:
            mes  = mes + str(base64.urlsafe_b64decode(message['body']))
        elif 'parts' in message['payload']:
            for part in message['payload']['parts']:
                # logging.debug(f"Part: {part}")
                if 'data' in part['body']:
                    mes  = mes + str(base64.urlsafe_b64decode(part['body']['data']))
                elif 'parts' in part:
                        for pp in part['parts']:
                            if 'data' in pp['body']:
                                mes  = mes + str(base64.urlsafe_b64decode(pp['body']['data']))
                elif 'data' in part['body']:
                    print(f"Part body: {part['body']}")
                    mes = mes + str(base64.urlsafe_b64decode(part['body']['data']))
        else:
            mes  = str(base64.urlsafe_b64decode(message['payload']['body']['data']))
        mes = mes.encode().decode('unicode_escape')
        # The messages come with escape characters and some encoding
        # FIXME Is this the correct place?

        return(mes)

    def getMessage(self, idPost):
        api = self.getClient()
        message = api.users().drafts().get(userId="me", id=idPost).execute()
        # print(message)
        # print(message['message'])
        return message

    def getMessageFull(self, msgId, typePost='drafts'):
        api = self.getClient()
        if typePost == 'drafts':
            message = api.users().drafts().get(userId="me",
                id=msgId, format='full').execute()['message']
        else:
            message = api.users().messages().get(userId="me",
                id=msgId, format='full').execute()

        return message


    def getMessageRaw(self, msgId, typePost='drafts'):
        api = self.getClient()
        if typePost == 'drafts':
            message = api.users().drafts().get(userId="me",
                id=msgId, format='raw').execute()['message']
        else:
            message = api.users().messages().get(userId="me",
                id=msgId, format='raw').execute()

        return message

    def getMessageMeta(self, msgId, typePost='drafts'):
        api = self.getClient()
        if typePost == 'drafts':
            message = api.users().drafts().get(userId="me",
                id=msgId, format='metadata').execute()['message']
        else:
            message = api.users().messages().get(userId="me",
                id=msgId, format='metadata').execute()
        return message

    def setHeader(self, message, header, value):
        for head in message['payload']['headers']:
            if head['name'].capitalize() == header.capitalize():
                head['value'] = value

    def setHeaderEmail(self, message, header, value):
        # Email methods are related to the email.message objetcs
        if header in message:
            del message[header]
            message[header]= value

    def getPosNextPost(self):
        # gmail always shows the first item ?
        # Some standard contition?

        posLast = 1

        return posLast

    def getPostLinksWithText(self, post):
        message = self.getMessageId(self.getPostId(post))
        messageClean = message.replace('\\r\\n',' ')
        soup = BeautifulSoup(messageClean, 'lxml')
        logging.debug(f"Soup: {soup}")
        res = soup.find_all('a', href=True)
        data = {}
        for element in res:
            link = element['href']
            if not link and 'title' in element:
                if 'http' in element['title']:
                    link = element['title']
            text = element.text
            logging.debug(f"Linkk: {link} text: {text}")
            if (link and not (link in data)):
                data[link] = (text, link, element)
            else:
                data[link] = (f"{data[link][0]} {text}", data[link][1],
                        data[link][2])
        links = []
        for key in data:
            links.append(data[key])
        return(links)

    def getPostContentHtml(self, post):
        # message = self.getMessageId(self.getPostId(post))
        snippet = self.getHeader(post, 'snippet')
        return snippet

    def getPostLinks(self, post):
        message = self.getMessageId(self.getPostId(post))
        soup = BeautifulSoup(message, 'lxml')
        # logging.debug(soup)
        res = soup.find_all('a', href=True)
        # logging.debug(res)
        links = []
        for element in res:
            link = element['href']
            if not (link in links):
                links.append(link)
        return(links)

    def getPostLink(self, post):
        # fromP = self.getHeader(post, 'From')
        # snippet = self.getHeader(post, 'snippet')
        theLink = ''
        if post:
            msgLog = (f"{self.indent} Post: {post}")
            logMsg(msgLog, 2, 0)
            links = self.getPostLinks(post)
            msgLog = (f"{self.indent} Links: {links}")
            logMsg(msgLog, 2, 0)
            if links:
                theLink = links[0]

        # result = f"From: {fromP}\nText: {snipP}"
        result = theLink
        return result

    def getPostTitle(self, post):
        msgLog = (f"{self.indent} getPostTitle")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} {post}")
        logMsg(msgLog, 2, 0)
        title = ""
        if post:
            title = self.getHeader(post)
        return (title)

    def getPostDate(self, post):
        msgLog = (f"{self.indent} getPostDate")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} {post}")
        logMsg(msgLog, 2, 0)
        if post:
            date = self.getHeader(post,'internalDate')
            # date = int(self.getHeader(post,'internalDate'))/1000
            # print(f"Dateeeee: {date}")
            # date = '{}'.format(datetime.datetime.fromtimestamp(date)) # Bad!
            return (date)
        return(None)

    def getHeader(self, message, header = 'Subject'):
        msgLog = (f"{self.indent} getHeader")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Message: {message}")
        logMsg(msgLog, 2, 0)
        if 'meta' in message:
            message = message['meta']
        for head in message:
            if head.capitalize() == header.capitalize():
                return(message[head])
        for head in message['payload']['headers']:
            if head['name'].capitalize() == header.capitalize():
                return(head['value'])

    def getPostId(self, message):
        # print(f"Message: {message}")
        # print(f"Message: {'list' in message}")
        if isinstance(message, str):
            idPost = message
        elif 'meta' in message:
            message = message['meta']
            idPost = message['id']
        elif isinstance(message, tuple):
            # logging.debug(message)
            idPost = message

        return(idPost)

    def getHeaderEmail(self, message, header = 'Subject'):
        if header in message:
            return(moduleImap.headerToString(message[header]))

    def getHeaderRaw(self, message, header = 'Subject'):
        if header in message:
            return(message[header])

    def getEmail(self, messageRaw):
        messageEmail = email.message_from_bytes(base64.urlsafe_b64decode(messageRaw['raw']))
        return(messageEmail)

    def getPostBody(self, message):
        res = self.getHeader(message, 'payload')
        if not res:
            print("No ressss")
            res = message
        print(f"Res: {res}")
        if "parts" in res:
            if "parts" in res["parts"]:
                print("parts 1 parts")
                text = res["parts"]["parts"][0]["parts"]
            else:
                text = res["parts"][0]
                if "parts" in text:
                    print("parts 2 parts")
                    text = text["parts"][0]
        else:
            print("No partssss")
            text = res
        print(f"Headers: {text['headers']}")

        dataB = ""
        if 'body' in text and 'data' in text['body']:
            dataB = text['body']['data']
        else:
            if 'parts' in text['body']:
                dataB = text['body']['parts'][0]

        if dataB:
            text = base64.urlsafe_b64decode(dataB)
        else:
            text = self.getHeader(message, 'snippet')

        return text

    def getLabelList(self):
        api = self.getClient()
        results = api.users().labels().list(userId='me').execute()
        return(results['labels'])

    def nameFolder(self, label):
        return self.getLabelName(label)

    def getLabelName(self, label):
        api = self.getClient()
        return label['name']

    def getLabelId(self, name):
        api = self.getClient()
        results = self.getLabelList()
        msgLog = (f"{self.indent} Labels: {results}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Name: {name}")
        logMsg(msgLog, 2, 0)
        labelId = None
        for label in results:
            if (label['name'].lower() == name.lower()) or (label['name'].lower() == name.lower().replace('-',' ')):
                msgLog = (f"{self.indent} {label}")
                logMsg(msgLog, 2, 0)
                labelId = label['id']
                break

        return(labelId)

    def editl(self, j, newTitle):
        return('Not implemented!')

    def edit(self, j, newTitle):
        msgLog = (f"{self.indent} edit")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} New title: {newTitle}")
        logMsg(msgLog, 2, 0)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        #logging.info("servicename %s" %self.service)

        import base64
        import email
        from email.parser import BytesParser
        api = self.getClient()

        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        message = self.getMessageRaw(idPost)
        theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
        self.setHeaderEmail(theMsg, 'subject', newTitle)
        message['raw'] = theMsg.as_bytes()
        message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

        update = api.users().drafts().update(userId='me',
            body={'message':message},id=idPost).execute()


        msgLog = (f"{self.indent} Update {update}")
        logMsg(msgLog, 2, 0)
        update = "Changed "+title+" with "+newTitle
        return(update)

    def publishApiPost(self, *args, **kwargs):
        if args and len(args) == 3:
            # logging.info(f"Tittt: args: {args}")
            title, link, comment = args
        if kwargs:
            # logging.info(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # FIXME: We need to do something here
            post = more.get('post', '')
            api = more.get('api', '')
            # logging.info(f"Post: {post}")
            idPost = api.getPostId(post)
            # logging.info(f"Postt: {post['meta']}")
            # idPost = post['meta']['payload']['headers'][2]['value'] #[1:-1]
            idPost = post['list']['id'] #[1:-1]
            # logging.info(f"Post id: {idPost}")
        res = 'Fail!'
        try:
            # credentials = self.authorize()
            res = api.getClient().users().drafts().send(userId='me',
                       body={'id': str(idPost)}).execute()
            # logging.info("Res: %s" % res)
        except:
            res = self.report('Gmail', idPost, '', sys.exc_info())

        return(f"Res: {res}")

    def trash(self, j, typePost='drafts'):
        msgLog = (f"{self.indent} trash")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Trashing {j}")
        logMsg(msgLog, 2, 0)

        api = self.getClient()
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        try:
            title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        except:
            title = ''
        if typePost == 'drafts':
            update = api.users().drafts().trash(userId='me', id=idPost).execute()
        else:
            update = api.users().messages().trash(userId='me', id=idPost).execute()

        return("Trashed %s"% title)

    def deleteApiSearch(self, idPost):
        result = self.deleteApiPost(idPost)
        return result

    def deleteApiMessages(self, idPost):
        return self.deleteApiPost(idPost)

    def deleteApiPosts(self, idPost):
        return self.deleteApiPost(idPost)

    def deleteApiPost(self, idPost):
        api = self.getClient()
        result = api.users().messages().trash(userId='me', id=idPost).execute()
        msgLog = (f"{self.indent} Res: {result}")
        logMsg(msgLog, 2, 0)
        return(result)

    def deleteApiPostDelete(self, idPost):
        api = self.getClient()
        result = api.users().messages().delete(userId='me', id=idPost).execute()
        msgLog = (f"{self.indent} Res: {result}")
        logMsg(msgLog, 2, 0)
        return(result)


    def delete(self, j):
        msgLog = (f"{self.indent} getHeader")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Deleting {j}")
        logMsg(msgLog, 2, 0)

        typePost = self.getPostsType()
        # logging.info(f"Deleting {typePost}")

        if (not typePost or (typePost == 'search')):
            typePost = 'messages'

        api = self.getClient()
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        try:
            title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        except:
            title = ''

        # logging.info(f"id {idPost}")

        if typePost == 'drafts':
            update = api.users().drafts().trash(userId='me', id=idPost).execute()
        else:
            # logging.info(f"id {idPost}")
            update = api.users().messages().trash(userId='me', id=idPost).execute()
            # logging.info(f"id {update}")

        return("Deleted %s"% title)

    def copyMessage(self,  message, labels =''):
        notAllowedLabels=['DRAFTS', 'SENT']
        api = self.getClient()
        labelIdName = 'importedd'
        try:
            labelId = self.getLabelId(labelIdName)
        except:
            labelId = self.getLabelId('old-'+labelIdName)
        if not labelId:
            try:
                labelId = self.createLabel(labelIdName)
            except:
                labelId = self.createLabel('old-'+labelIdName)
        labelIds = [labelId]
        labelIdsNames = [labelIdName]
        if labels:
            for label in labels:
                if label.startswith('"'):
                    label = label[1:]
                if label.endswith('"'):
                    label = label[:-1]
                if label.upper() in notAllowedLabels:
                    label = 'old-'+label
                # logging.debug("label %s"%label)
                try:
                    labelId = self.getLabelId(label)
                except:
                    labelId = self.getLabelId('old-'+label)
                if not labelId :
                    try:
                        labelId = self.createLabel(label)
                    except:
                        labelId = self.createLabel('old-'+label)
                labelIds.append(labelId)
                labelIdsNames.append(label)

        if not isinstance(message,dict):
            mesGE = base64.urlsafe_b64encode(message).decode()
            mesT = email.message_from_bytes(message)
            if mesT['subject']:
                subj = email.header.decode_header(mesT['subject'])[0][0]
            else:
                subj = ""
            msgLog = (f"{self.indent} Subject {subj}")
            logMsg(msgLog, 1, 0)
        else:
            if 'raw' in message:
                mesGE = message['raw']

        try:
            messageR = api.users().messages().import_(userId='me',
                      fields='id',
                      neverMarkSpam=False,
                      processForCalendar=False,
                      internalDateSource='dateHeader',
                      body={'raw': mesGE}).execute(num_retries=5)
           #           media_body=media).execute(num_retries=1)
        except:
           # When the message is too big
           # https://github.com/google/import-mailbox-to-gmail/blob/master/import-mailbox-to-gmail.py

           msgLog = (f"{self.indent} Fail 1! Trying another method.")
           logMsg(msgLog, 3, 0)

           try:
               if not isinstance(message,dict):
                   mesGS = BytesParser().parsebytes(message).as_string()
                   media =  googleapiclient.http.MediaIoBaseUpload(io.StringIO(mesGS), mimetype='message/rfc822')
                   # logging.info("vamos method")
               else:
                    media = message
               #print(media)

               messageR = api.users().messages().import_(userId='me',
                           fields='id',
                           neverMarkSpam=False,
                           processForCalendar=False,
                           internalDateSource='dateHeader',
                           body={},
                           media_body=media).execute(num_retries=3)
               # logging.info("messageR method")
           except:
               msgLog = ("Error with message %s" % message)
               logMsg(msgLog, 3, 0)
               return("Fail 2!")

        msg_labels = {'removeLabelIds': [], 'addLabelIds': ['UNREAD', labelId]}
        msg_labels = {'removeLabelIds': [], 'addLabelIds': labelIds }# ['UNREAD', labelId]}

        messageR = api.users().messages().modify(userId='me',
                id=messageR['id'], body=msg_labels).execute()
        return(messageR)


    #######################################################
    # These need work
    #######################################################


    def listSentPosts(self, pp, service=""):
        # Undefined
        pass

    # def copyPost(self, log, pp, profiles, toCopy, toWhere):
    #     # Undefined
    #     pass

    def movePost(self, log, pp, profiles, toMove, toWhere):
        # Undefined
        pass


def main():
    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    print(f"Selecting rule")
    apiSrc = rules.selectRuleInteractive()

    if not apiSrc.getClient().__getstate__():
        return

    testingBody = True
    if testingBody:
        apiSrc.setPostsType("posts")
        apiSrc.setChannel('INBOX')
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            # print(f"Post: {post}")
            title = apiSrc.getPostTitle(post)
            print(f"{i}) Subject: {title}")
            content = apiSrc.getPostContent(post)
            print(f"Text: {content}")
            idPost = apiSrc.getPostId(post)
            print(f"Id: {idPost}")
            res = (
                apiSrc.getClient().users().messages().get(userId="me", id=idPost).execute()
            )
            body = apiSrc.getPostBody(res)
            print(f"Body: {body}")
        return

    testingPostsLabel = False
    if testingPostsLabel:
        print(f"{apiSrc.listFolders()}")
        print(f"{apiSrc.getLabels('zAgenda')}")
        labelId = apiSrc.getLabels('zAgenda')[0]
        apiSrc.assignPosts(apiSrc.setApiMessages(label=labelId))
        for i, post in enumerate(apiSrc.getPosts()):
            title = apiSrc.getPostTitle(post)
            print(f"{i}) {title}")
            print(f"{post}")
            print(f"{apiSrc.getMessageId(apiSrc.getPostId(post))}")
        return


    testingDrafts = False
    if testingDrafts:
        for key in rules.rules.keys():
            print(f"Key: {key}")
            if ((key[0] == 'gmail')
                    and ('ftricas' in key[2])
                    and (key[3] == 'posts')):
                print(f"SKey: {key}\n"
                      f"SRule: {rules.rules[key]}\n"
                      f"SMore: {rules.more[key]}")
                apiSrc = rules.readConfigSrc("", key, rules.more[key])
                apiSrc.setPosts()
                post = apiSrc.getNextPost()
                print(f"titleeeee: {apiSrc.getPostTitle(post)}")
                print(f"linkkkkk: {apiSrc.getPostLink(post)}")
                for i, post in enumerate(apiSrc.getPosts()):
                    print(f"{i}) Subject: {apiSrc.getPostTitle(post)}")
                    print(f"{i}) Link: {apiSrc.getPostLink(post)}")
                    # print(f"{i}) {apiSrc.getPostLinks(post)}")

        return

    return
    import moduleGmail

    # instantiate the api object

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    accounts = ['Blog35'] #'Blog13','Blog14','Blog15','Blog24']
    # [Blog15]
    # url:test@gmail.com
    # Gmail:test@gmail.com
    # posts:drafts

    for acc in accounts:
        print("Account: {}".format(acc))
        url = config.get(acc, 'url')
        api = moduleGmail.moduleGmail()
        api.setClient(url)
        print(api.name)
        #if 'posts' in config.options(Acc):
        #    self.setPostType(config.get(Acc, 'posts'))
        print("Test setPosts")
        api.setPostsType('messages')
        res = api.setPosts()
        print("Test getPosts")
        #print(api.getPosts())
        #api.setPostsType('messages')
        #print("Test setPosts (posts)")
        #res = api.setPosts()
        #print("Test getPosts")
        for post in api.getPosts():
            print(post)
            print(api.getPostTitle(post))
            print(api.getPostLink(post))

    sys.exit()
    print(api.getPosts())
    print(api.getPosts()[0])
    print(len(api.getPosts()[0]))
    api = moduleGmail.moduleGmail()
    api.setClient(('gmail','ftricas@elmundoesimperfecto.com'))
    api.setPosts()
    print(api.getPosts())
    print(api.getPosts()[0])
    print(len(api.getPosts()[0]))
    sys.exit()
    # It has 8 elements
    # print(api.obtainPostData(0))
    # print('G21', api.selectAndExecute('show', 'G21'))
    # print('G23', api.selectAndExecute('show', 'G23'))
    # print('G05', api.selectAndExecute('show', 'G05'))
    # sys.exit()
    # print('G29', api.selectAndExecute('publish', 'G29'))
    # print('G29', api.selectAndExecute('delete', 'G29'))
    # print('G25', api.selectAndExecute('edit', 'G27'+' '+'Cebollinos (hechos)'))
    # print('M18', api.editPost('M18', 'Vaya'))
    # print('M10', api.publishPost('M10'))
    # sys.exit()
    # api.editPost(pp, api.getPosts(), "M17", 'Prueba.')

    logging.basicConfig(#filename='example.log',
            level=logging.DEBUG,format='%(asctime)s %(message)s')

    print("profiles")
    print(api.profile)
    #postsP, profiles = api.listPosts(pp)
    print("-> Posts",postsP)
    print(apil.getPostsFormatted())
    sys.exit()
    api.editPost(pp, api.getPosts(), "M11", 'No avanza.')
    sys.exit()
    msg = 353
    copyMessage(api[1], msg)

    #publishPost(api, pp, postsP, ('G',1))
    #deletePost(api, pp, postsP, ('M0',0))
    #sys.exit()

    # publishPost(api, pp, profiles, ('F',1))

    # posts.update(postsP)
    # print("-> Posts",posts)
    # #print("Posts",profiles)
    # print("Keys",posts.keys())
    # print(pp.pformat(profiles))
    # print("Pending",type(profiles))
    # print(pp.pformat(profiles))
    # profiles = listSentPosts(api, pp, "")
    # print("Sent",type(profiles))
    # print(pp.pformat(profiles))
    # print(type(profiles[1]),pp.pformat(profiles[1]))


    # if profiles:
    #    toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
    #    #publishPost(api, pp, profiles, toPublish)


if __name__ == '__main__':
    main()
