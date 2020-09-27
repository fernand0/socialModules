#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

# From: https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


import configparser, os
import datetime
import importlib
import io
import logging
import pickle
import sys

import moduleSocial
import moduleImap

import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


import base64
import email
from email.parser import BytesParser

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleGmail(Content,Queue):

    def __init__(self):
        super().__init__()
        Content().__init__()
        Queue().__init__()
        self.service = None
        self.nick = None
        self.id = None
        self.scopes = ['https://www.googleapis.com/auth/gmail.modify']

    def API(self, Acc):
        # Back compatibility
        self.setClient(Acc)

    def setClient(self, Acc):
        logging.info("     Connecting GMail %s"%str(Acc))
   
        SCOPES = self.scopes
        api = {}
    
        self.service = 'gmail'
        if type(Acc) == str: 
            self.url = Acc
            pos = Acc.rfind('@') 
            self.server = Acc[pos+1:] 
            self.nick   = Acc[:pos] 
            self.name = 'GMail_{}'.format(Acc[0]) 
            import hashlib
            self.name = 'GMail_{}'.format(Acc)
        elif isinstance(Acc, tuple):
            if (len(Acc) > 1) and isinstance(Acc[1], tuple):
                logging.debug("Acc %s" % str(Acc))
                self.url = Acc[0]
                pos = Acc[0].rfind('@') 
                self.server = Acc[0][pos+1:] 
                self.nick   = Acc[0][:pos]
                self.setPostsType(Acc[1][2])
            elif len(Acc)>1:
                logging.info("Acc %s" % str(Acc))
                self.url = Acc[1]
                pos = Acc[1].rfind('@') 
                self.server = Acc[1][pos+1:] 
                self.nick   = Acc[1][:pos]
            self.name = 'GMail_{}'.format(Acc[0]) 

        self.id = '{} {}@{}'.format(self.name[-1], self.nick, self.server)
        logging.debug("Id %s" % self.id)

        try:
            creds = self.authorize()
            service = build('gmail', 'v1', credentials=creds)
            self.client = service
        except:
            logging.warning("Problem with authorization")
            logging.warning("Unexpected error:", sys.exc_info()[0])

    def authorize(self):
        # based on Code from
        # https://github.com/gsuitedevs/python-samples/blob/aacc00657392a7119808b989167130b664be5c27/gmail/quickstart/quickstart.py

        SCOPES = self.scopes

        logging.info("Authorizing GMail")
        fileCredStore = self.confName((self.server, self.nick)) 
        fileTokenStore = self.confTokenName((self.server, self.nick)) 
        creds = None

        if os.path.exists(fileTokenStore): 
            with open(fileTokenStore, 'rb') as token: 
                logging.info("Opening {}".format(fileTokenStore))
                creds = pickle.load(token)

        logging.info("creds {}".format(str(creds)))

        if not creds or not creds.valid: 
            if creds and creds.expired and creds.refresh_token: 
                logging.info("Needs to refresh token GMail")
                creds.refresh(Request()) 
            else: 
                logging.info("Needs to re-authorize token GMail")

                try:
                    flow = InstalledAppFlow.from_client_secrets_file( 
                        fileCredStore, SCOPES, 
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                    creds = flow.run_console(
                            authorization_prompt_message='Please visit this URL: {url}', 
                            success_message='The auth flow is complete; you may close this window.')
                    # Save the credentials for the next run
                except FileNotFoundError:
                    print("no")
                    print(fileCredStore)
                    sys.exit()

        logging.info("Storing creds")
        with open(fileTokenStore, 'wb') as token:
            pickle.dump(creds, token)

        return(creds)


    def getClient(self):
        return(self.client)

    def createLabel(self, labelName):
        api = self.getClient()
        label_object = {'messageListVisibility': 'show', 
                'name': labelName, 'labelListVisibility': 'labelShow'}
        return(api.users().labels().create(userId='me', 
                body=label_object).execute())

    def updateLabel(self, label_id, labelName):
        api = self.getClient()
        label_object = {'messageListVisibility': 'show', 
                'name': labelName, 'labelListVisibility': 'labelShowIfUnread'}
        return(api.users().labels().update(userId='me', id=label_id,
                body=label_object).execute())

    def setLabels(self):
        api = self.getClient()
        response = api.users().labels().list(userId='me').execute()
        if 'labels' in response:
            self.labels = response['labels']

    def getLabels(self, sel=''):
        return(list(filter(lambda x: sel in x['name'] ,self.labels)))

    def getLabelsIds(self, sel=''):
        labels = (list(filter(lambda x: sel in x['name'] ,self.labels)))
        return (list(map(lambda x: x['id'], labels)))

    def getLabelsEqIds(self, sel=''):
        labels = (list(filter(lambda x: sel.upper() == x['name'].upper() ,self.labels)))
        return (list(map(lambda x: x['id'], labels)))

    def getListLabel(self, label):
        api = self.getClient()
        list_labels = [ label, ]
        print(list_labels)
        response = api.users().messages().list(userId='me',
                                               labelIds=list_labels).execute()
        return(response)

    def modifyLabels(self, message, oldLabelId, labelId):
        api = self.getClient()
        list_labels = {'removeLabelIds': [oldLabelId, ], 
                'addLabelIds': [labelId, ]}
        print(list_labels)
        print(message)
        
        message = api.users().messages().modify(userId='me', id=message['id'],
                                                body=list_labels).execute()
        return(message)
        
    def setPosts(self, label=None, mode=''):
        logging.info("  Setting posts")
        api = self.getClient()

        self.posts = []
        self.drafts = []
        try: 
            if hasattr(self, 'getPostsType'): 
                typePosts = self.getPostsType()
                logging.info("  Setting posts type {}".format(typePosts))
            elif label == 'drafts': 
                typePosts = 'drafts' 
            else: 
                typePosts = 'messages' 
            if typePosts == 'drafts':
                posts = api.users().drafts().list(userId='me').execute() 
            else:
                posts = api.users().messages().list(userId='me').execute()
        #except client.HttpAccessTokenRefreshError: 
        #    return "Fail"
        except: 
            logging.warning("GMail failed!") 
            logging.warning("Unexpected error:", sys.exc_info()[0]) 
            return("Fail")

        logging.debug("--setPosts %s" % posts)

        if typePosts in posts:
           self.rawPosts = []
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

               if typePosts == 'drafts': 
                   self.drafts.insert(0, message) 
               else: 
                   self.posts.insert(0, message) 
        logging.info("drafts {}".format(str(self.drafts)))
        return "OK"

    def confName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + acc[0]+ '_' 
                + acc[1]+ '.json')
        return(theName)
    
    def confTokenName(self, acc): 
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + acc[0]+ '_' 
                + acc[1]+ '.pickle')
        return(theName)
    
    def getMessage(self, id): 
        api = self.getClient()
        message = api.users().drafts().get(userId="me", 
                id=id).execute()['message']
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

    def getPostLink(self, post):
        return ''

    def getPostTitle(self, post):
        logging.debug(post)
        if post:
            title = self.getHeader(post)
            return (title)
        return(None)

    def getPostDate(self, post):
        logging.debug(post)
        if post:
            date = int(self.getHeader(post,'internalDate'))/1000
            date = '{}'.format(datetime.datetime.fromtimestamp(date)) # Bad!
            return (date)
        return(None)

    def getHeader(self, message, header = 'Subject'):
        if 'meta' in message:
            message = message['meta']
        for head in message: 
            if head.capitalize() == header.capitalize(): 
                return(message[head])
        for head in message['payload']['headers']: 
            if head['name'].capitalize() == header.capitalize(): 
                return(head['value'])

    def getPostId(self, message):
        if 'list' in message:
            message = message['meta']
        return(message['id'])

    def getHeaderEmail(self, message, header = 'Subject'):
        if header in message:
            return(moduleImap.headerToString(message[header]))

    def getHeaderRaw(self, message, header = 'Subject'):
        if header in message:
            return(message[header])

    def getEmail(self, messageRaw):
        messageEmail = email.message_from_bytes(base64.urlsafe_b64decode(messageRaw['raw']))
        return(messageEmail)

    def getBody(self, message):
        return(message['payload']['parts'])
 
    def getLabelList(self):
        api = self.getClient()
        results = api.users().labels().list(userId='me').execute() 
        return(results['labels'])

    def getLabelId(self, name):
        api = self.getClient()
        results = self.getLabelList() 
        labelId = None
        for label in results: 
            if (label['name'].lower() == name.lower()) or (label['name'].lower() == name.lower().replace('-',' ')): 
                print(label)
                labelId = label['id'] 
                break
    
        return(labelId)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        message = self.getPosts()[i]
        logging.info("Message %s"% message)

        theTitle = self.getHeader(message, 'Subject')
        if theTitle == None:
            theTitle = self.getHeader(message, 'subject')
        snippet = self.getHeader(message, 'snippet')

        theLink = None
        if snippet:
            posIni = snippet.find('http')
            posFin = snippet.find(' ', posIni)
            posSignature = snippet.find('-- ')
            if posIni < posSignature: 
                theLink = snippet[posIni:posFin]
        theLinks = None
        content = None
        theContent = None
        #date = int(self.getHeader(message, 'internalDate'))/1000
        #firstLink = '{}'.format(datetime.datetime.fromtimestamp(date)) # Bad!
        firstlink = None
        theImage = None
        theSummary = snippet

        theSummaryLinks = message
        comment = self.getPostId(message) 

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def editl(self, j, newTitle):
        return('Not implemented!')

    def edit(self, j, newTitle):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        logging.info("servicename %s" %self.service)

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


        logging.info("Update %s" % update)
        update = "Changed "+title+" with "+newTitle
        return(update)

    def publish(self, j):
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service)
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        
        api = self.getClient()
        try:
            res = api.users().drafts().send(userId='me', 
                       body={ 'id': idPost}).execute()
            logging.info("Res: %s" % res)
        except:
            return(self.report('Gmail', idPost, '', sys.exc_info()))

        return("%s"% title)

    def trash(self, j, typePost='drafts'):
        logging.info("Trashing %d"% j)

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
 
    def delete(self, j, typePost='drafts'):
        logging.info("Deleting %d"% j)

        api = self.getClient()
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        try: 
            title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        except:
            title = ''
        if typePost == 'drafts': 
            update = api.users().drafts().delete(userId='me', id=idPost).execute() 
        else:
            update = api.users().messages().delete(userId='me', id=idPost).execute() 
 
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
                print("label %s"%label)
                try: 
                    print("aquí")
                    labelId = self.getLabelId(label)
                    print("aquí",labelId)
                except:
                    print("except")
                    labelId = self.getLabelId('old-'+label)
                    print("except")
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
            logging.info("Subject %s",subj)
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
    
           logging.info("Fail 1! Trying another method.")
           try: 
               if not isinstance(message,dict): 
                   mesGS = BytesParser().parsebytes(message).as_string()
                   media =  googleapiclient.http.MediaIoBaseUpload(io.StringIO(mesGS), mimetype='message/rfc822')
                   logging.info("vamos method")
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
               logging.info("messageR method")
           except: 
               logging.info("Error with message %s" % message) 
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
    
    def copyPost(self, log, pp, profiles, toCopy, toWhere):
        # Undefined
        pass
    
    def movePost(self, log, pp, profiles, toMove, toWhere):
        # Undefined
        pass
    

def main():
    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    import moduleGmail

    # instantiate the api object 

    config = configparser.ConfigParser() 
    config.read(CONFIGDIR + '/.rssBlogs')

    accounts = ['Blog13','Blog14','Blog15']
    for acc in accounts:
        print("Account: {}".format(acc))
        url = config.get(acc, 'url')
        api = moduleGmail.moduleGmail()
        api.setClient(url)
        print(api.name)
        #if 'posts' in config.options(Acc):
        #    self.setPostType(config.get(Acc, 'posts'))
        print("Test setPosts")
        res = api.setPosts()
        print("Test getPosts")
        print(api.getPosts())
        api.setPostsType('messages')
        print("Test setPosts (posts)")
        res = api.setPosts()
        print("Test getPosts")
        print(api.getPosts())

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
    print(api.obtainPostData(0))
    print('G21', api.selectAndExecute('show', 'G21'))
    print('G23', api.selectAndExecute('show', 'G23'))
    print('G05', api.selectAndExecute('show', 'G05'))
    sys.exit()
    print('G29', api.selectAndExecute('publish', 'G29'))
    print('G29', api.selectAndExecute('delete', 'G29'))
    print('G25', api.selectAndExecute('edit', 'G27'+' '+'Cebollinos (hechos)'))
    print('M18', api.editPost('M18', 'Vaya'))
    print('M10', api.publishPost('M10'))
    sys.exit()
    api.editPost(pp, api.getPosts(), "M17", 'Prueba.')

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

    publishPost(api, pp, profiles, ('F',1))

    posts.update(postsP)
    print("-> Posts",posts)
    #print("Posts",profiles)
    print("Keys",posts.keys())
    print(pp.pformat(profiles))
    print("Pending",type(profiles))
    print(pp.pformat(profiles))
    profiles = listSentPosts(api, pp, "")
    print("Sent",type(profiles))
    print(pp.pformat(profiles))
    print(type(profiles[1]),pp.pformat(profiles[1]))


    if profiles:
       toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
       #publishPost(api, pp, profiles, toPublish)


if __name__ == '__main__':
    main()
