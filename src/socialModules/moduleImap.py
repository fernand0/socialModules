#!/usr/bin/env python

# We will have here the set of functions related to imap mail management

import binascii
import chardet
import click
import configparser
import dateutil
import distance
import email
import email.message
import email.policy
import getpass
import hashlib
import imaplib
import io
import keyring
import os
import pickle
import re
import ssl
import sys
import time
from email import encoders
from email.header import Header, decode_header
from email.parser import BytesParser
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

from apiclient.http import MediaIoBaseUpload
from bs4 import BeautifulSoup
from dateutil.parser import parse
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

import smtplib
#FIXME should we have another module?

import socialModules.moduleGmail
import socialModules.moduleSieve
from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

msgHeaders = ['List-Id', 'From', 'Sender', 'Subject', 'To',
              'X-Original-To', 'X-Envelope-From',
              'X-Spam-Flag', 'X-Forward']
headers = ["address", "header"]
keyWords = {"address": ["From", "To"],
            "header":  ["subject", "Sender", "X-Original-To", "List-Id"]
            }

class moduleImap(Content): #, Queue):

    def getKeys(self, config):
        msgLog = (f"{self.indent} Getting keys")
        logMsg(msgLog, 2, 0)
        self.server = config.get(self.user, "server")
        try:
            password = config.get(self.user, "token")
        except:
            msgLog = (f"No key for {key}")
            logMsg(msgLog, 3, 0)
        self.user = config.get(self.user, "user")
        #FIXME: We are using the same value for configuration and the
        # identifier of the account return password
        return password

    def setPassword(self, server, user):
        msgLog = (f"[{server},{user}] New account. Setting password")
        logMsg(msgLog, 3, 0)
        print("Server: %s,  User: %s" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
        return(password)

    def getPassword(self, server, user):
        # Deleting keyring.delete_password(server, user)
        #print("keyrings",keyring.backend.get_all_keyring())
        #print("the keyring",keyring.get_keyring())
        password = keyring.get_password(server, user)
        if not password:
            password = self.setPassword(server, user)
        return password

    def getPosNextPost(self):
        # mail always shows the first item
        # Some standard contition?

        posLast = 1
        return posLast

    def initApi(self, keys):
        msgLog = (f"{self.indent} User: {self.user}")
        logMsg(msgLog, 2, 0)
        msgLog = (f"{self.indent} Server: {self.server}")
        logMsg(msgLog, 2, 0)
        client = None
        try:
            client = self.makeConnection(self.server, self.user, keys)
            msgLog = (f"{self.indent} Connection: {client}")
            logMsg(msgLog, 2, 0)
        except:
            self.report(self.service, '', '', sys.exc_info())
            msgLog = (f"{self.indent} makeConnection failed")
            logMsg(msgLog, 3, 0)

        ok, folders = client.list()
        if ok == 'OK':
            separator= str(folders[0]).split('"')[1]
            logging.info(f"Separator: {separator}")

        self.separator = separator

        specialFolders = ['Trash', 'Junk', 'Sent', 'Drafts']
        self.special = {}
        for folder in folders:
            parts = str(folder).split(self.separator)
            for special in specialFolders:
                if special in parts[0]:
                    self.special[special] = self.getChannelName(folder)

        return client

    def setApiNew(self):
        try:
            # Trying to avoid re-authentication. Are ther better ways?
            self.getClient().noop()
        except:
            self.setClient(f"{self.user}")
        # print(f"getChannel: {self.getChannel()}")
        posts = self.listMessages(self.getClient(), self.getChannel())
        return posts

    def setApiDrafts(self):
        # IMAP accounts get disconnected when time passes.
        # Maybe we should check if this is needed

        #print(f"getChannel: {self.user}@{self.server}")
        try:
            # Trying to avoid re-authentication. Are ther better ways?
            self.getClient().noop()
        except:
            self.setClient(f"{self.user}")

        self.setChannel('Drafts')
        channel = self.getChannel()
        posts = self.listMessages(self.getClient(), channel)
        return posts

    def setApiPosts(self):
        # IMAP accounts get disconnected when time passes.
        # Maybe we should check if this is needed

        logging.info(f"getChannel: {self.user}@{self.server}")
        self.checkConnected()
        channel = self.getChannel()
        logging.info(f"getChannel: {channel}")
        if not channel:
            self.setChannel()
            channel = self.getChannel()
        posts = self.listMessages(self.getClient(), channel)
        return posts

    def getChannels(self):
        msgLog = (f"{self.indent} getChannels")
        logMsg(msgLog, 1, 0)
        labels = self.getLabels()
        return labels

    def getChannelName(self, channel):
        # Examples:
        # b'(\\HasNoChildren \\UnMarked) "/" INBOX/unizar/vrtic'
        # b'(\\HasNoChildren \\UnMarked) "." INBOX.unizar.vrtic'
        name = str(channel).split(f'"{self.separator}"')[-1][1:-1]
        return name

    def setPage(self, channel=''):
        self.setChannel(channel)

    def setChannel(self, channel=''):
        # setPage in Facebook
        if not channel:
            channel = self.getChannelName(self.getChannels()[0])
            # str(self.getChannels()[0]).split(' ')[-1][:-1]
            # b'(\\HasChildren) "." INBOX'
        self.channel = channel

    def getChannel(self):
        rep = ''
        if hasattr(self, 'channel'):
            rep = self.channel
        return rep

    def createChannel(self, channel):
        api = self.getClient()
        res, data = api.create(channel)
        if res != 'NO':
            return res
        else:
            print(f"Res: {res} {data}")
        return data

    def stripRe(self, header):
        # Drop some standard strings added by email clients
        Res = ['Fwd', 'Fw', 'Re', 'RV', '(fwd)']
        for h in Res:
            header = header.replace(h+': ', '')
        if header.startswith('[') and header.endswith(']'):
            header = header[1:-1]
        return(header)

    def headerToString(self, header):
        if not (header is None):
            headRes = ""
            for (headDec, enc) in decode_header(header):
                # It is a list of coded and not coded strings
                if (enc is None) or (enc == 'unknown-8bit'):
                    enc = 'iso-8859-1'
                if (not isinstance(headDec, str)):
                    headDec = headDec.decode(enc)
                headRes = headRes + headDec
        else:
            headRes = ""

        return headRes

    def mailFolder(self, account, accountData, logging, res):
        # Apply rules to mailboxes

        SERVER = account[0]
        USER = account[1]
        PASSWORD = getPassword(SERVER, USER)

        srvMsg = SERVER.split('.')[0]
        usrMsg = USER.split('@')[0]
        try:
            M = makeConnection(SERVER, USER, PASSWORD)
        except:
            msgLog = (f"{self.indent} Error with {USER}-{SERVER}")
            logMsg(msgLog, 3, 0)
            sys.exit()


        for actions in accountData['RULES']:
            RULES = actions[0]
            INBOX = actions[1]
            FOLDER = actions[2]

            if INBOX:
               M.select(INBOX)
            else:
               M.select()

            i = 0
            total = 0
            msgs = ''
            for rule in RULES:
                action = rule.split(',')
                msgLog = (f"{self.indent} {action}")
                logMsg(msgLog, 2, 0)
                header = action[0][1:-1]
                content = action[1][1:-1]
                msgTxt = "[%s,%s] Rule: %s %s" % (srvMsg, usrMsg, header, content)
                msgLog = (f"{self.indent} {msgTxt}")
                logMsg(msgLog, 2, 0)
                if (header == 'hash'):
                    msgs = selectHash(M, FOLDER, content)
                    #M.select(folder)
                    FOLDER = ""
                    data = None
                elif (header == 'status'):
                    (typ, data) = M.search(None, '(ALL)')
                else:
                    data = ''
                    try:
                        cadSearch = "("+header+' "'+content+'")'
                        typ, data = M.search(None, cadSearch)
                    except:
                        cadSearch = "(HEADER "+header+' "'+content+'")'
                        typ, data = M.search(None, cadSearch)
                if data and data[0]:
                    if msgs:
                        msgs = msgs + ' ' + data[0].decode('utf-8')
                    else:
                        msgs = data[0].decode('utf-8')
                else:
                    msgLog = (f"{msgTxt} - No messages matching.")
                    logMsg(msgLog, 2, 0)
                    msgTxt = f"{msgTxt} - No messages matching."

                if len(msgs)==0:
                    msgLog = (f"{msgTxt} Nothing to do")
                    logMsg(msgLog, 2, 0)
                    msgTxt = "%s Nothing to do" % msgTxt
                else:
                    msgLog = (f"{msgTxt} - Let's go!")
                    logMsg(msgLog, 2, 0)
                    msgTxt = f"{msgTxt} - Let's go!"
                    logMsg(msgTxt, 2, 0)
                    msgs = msgs.replace(" ", ",")
                    status = 'OK'
                    if FOLDER:
    		    # M.copy needs a set of comma-separated mesages, we have a
    		    # list with a string
                        #print(FOLDER)
                        if FOLDER.find('@')>=0:
                            #print("msgs", msgs)
                            #print("remote")
                            status = copyMailsRemote(M, msgs, FOLDER)
                        else:
                            msgLog = (f"msgs {msgs}")
                            logMsg(msgLog, 2, 0)
                            result = M.copy(msgs, FOLDER)
                            status = result[0]
                    i = msgs.count(',') + 1
                    msgLog = (f"[{SERVER},{USER}] *{msgs}* Status: {status}")
                    logMsg(msgLog, 2, 0)

                    if status == 'OK':
                        # If the list of messages is too long it won't work
                        flag = '\\Deleted'
                        result = M.store(msgs, '+FLAGS', flag)
                        if result[0] == 'OK':
                            msgLog = ("%s: %d messages have been deleted."
                                          % (msgTxt, i))
                            logMsg(msgLog, 2, 0)
                            msgTxt = "%s: %d messages have been deleted." \
                                          % (msgTxt, i)
                            total = total + i
                        else:
                            msgLog = ("%s -  Couldn't delete messages!" % msgTxt)
                            logMsg(msgLog, 2, 0)

                            msgTxt = "%s -  Couldn't delete messages!" % msgTxt
                    else:
                        msgLog = ("%s - Couldn't move messages!" % msgTxt)
                        logMsg(msgLog, 2, 0)
                        msgTxt = "%s - Couldn't move messages!" % msgTxt
                logMsg(msgTxt, 2, 0)
        M.close()
        M.logout()
        res.put(("ok", SERVER, USER, total))

    def doFolderExist(self, folder, M):
        if not folder.startswith(('"', "'")):
            folderName = '"%s"'%folder
        else:
            folderName = folder

        return (M.select(folderName))

    def selectHeader(self):
        i = 1
        for j in headers:
            print(i, ") ", j, "(", keyWords[headers[i-1]], ")")
            i = i + 1
        return headers[int(input("Select header: ")) - 1]

    def showMessagesList(self, M, folder, messages, startMsg):
        rows, columns = os.popen('stty size', 'r').read().split()
        numMsgs = 24
        if rows:
           numMsgs = int(rows) - 3
        if columns:
           col = int(columns)

        msg_data = []
        msg_numbers = []
        j = 0
        print("%d messsages in folder: %s" % (len(messages), folder))
        if startMsg == 0:
            startMsg = len(messages) - numMsgs + 1
        else:
            # It will be a negative number, we'll use it a starting point
            # changing the sing
            startMsg = -startMsg - 1

        if startMsg < 0:
            startMsg = 0
        for i in messages[startMsg:min(startMsg + numMsgs - 1, len(messages))]:
            if i:
                typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[])')
                # print msg_data_fetch
                for response_part in msg_data_fetch:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1],
                              policy = email.policy.SMTP)
                        msg_data.append(msg)
                        msg_numbers.append(i)
                        # Variable length fmt
                        fmt = "%2s) %-20s %-40s"
                        headFrom = msg['From']
                        headSubject = msg['Subject']
                        headFromDec = headerToString(headFrom)
                        headSubjDec = headerToString(headSubject)
                        print(fmt % (j,
                                     headFromDec[:20],#[0][0][:20],
                                     headSubjDec[:col - 20 - 5]))#[0][0][:40]))
                        j = j + 1
        return(msg_data, msg_numbers)

    def selectMessageAndFolder(self, M):
        msg_number =""
        startMsg = 0
        folder = "INBOX"
        while (not msg_number.isdigit() or (startMsg < 0)):
            rows, columns = os.popen('stty size', 'r').read().split()
            numMsgs = 24
            if rows:
               numMsgs = int(rows) - 3
            #print("folder",folder)
            try:
               M.select(folder)
            except:
               return("","", -1)
            data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
            if (data[0] == 'OK'):
                messages = data[1][0].decode("utf-8").split(' ')
                (msg_data, msg_numbers) = showMessagesList(M, folder, messages, startMsg)
                msg_number = input("Which message? ([-] switches mode: [number] starting point [string] folder name 'x' exit) [+] to read the message [.] to select just *this* message [>] use this message to create a sieve filter\n")
                if msg_number.isdigit():
                    startMsg = int(msg_number)
                    if int(msg_number) > numMsgs:
                        msg_number=""
                        continue
                elif (len(msg_number) > 0) and (msg_number[0] == '-'):
                    if msg_number[1:].isdigit():
                        startMsg = int(msg_number)
                    elif msg_number[1] == 'x':
                        return ("x","","")
                    else:
                        folder = selectFolder(M, msg_number[1:])
                        startMsg = 0
                        #print("folder",folder)
                        #folder = nameFolder(folder)
                elif (len(msg_number) > 0) and (msg_number[0] == '+'):
                    if msg_number[1:].isdigit():
                        printMessage(M, msg_data[int(msg_number[1:])],int(rows),int(columns))
                        startMsg = 0
                elif (len(msg_number) > 0) and (msg_number[0] == '.'):
                    # Just *this* message
                    if msg_number[1:].isdigit():
                        printMessage(M, msg_data[int(msg_number[1:])],
                                0,int(columns), ['Subject'])
                        return(".",msg_data[int(msg_number[1:])], msg_numbers[int(msg_number[1:])])
                elif (len(msg_number) > 0) and (msg_number[0] == '>'):
                    if msg_number[1:].isdigit():
                        moduleSieve.addToSieve(msg_data[int(msg_number[1:])])
                elif (len(msg_number) > 0) and (not msg_number.isdigit()):
                    print("Selecting messages with %s" % msg_number)
                    return(folder, "", msg_number)
                else:
                    startMsg = 0
            else:
                return ("","")

        return (folder, msg_data[int(msg_number)], msg_numbers[int(msg_number)])  # messages[-10+int(msg_number)-1]

    def selectMessage(self, M):
        msg_number =""
        startMsg = 0
        folder = "INBOX"
        while (not msg_number.isdigit()):
            rows, columns = os.popen('stty size', 'r').read().split()
            numMsgs = 24
            if rows:
               numMsgs = int(rows) - 3
            #print("folder",folder)
            try:
               M.select(folder)
            except:
               return("")
            data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
            if (data[0] == 'OK'):
                j = 0
                msg_data = []
                msg_numbers = []
                messages = data[1][0].decode("utf-8").split(' ')
                (msg_data, msg_numbers) = showMessagesList(M, folder, messages, startMsg)
                msg_number = input("Which message? ")
            else:
                return 0

        return msg_data[int(msg_number)]  # messages[-10+int(msg_number)-1]


    def selectHeaderAuto(self, M, msg):
        i = 1
        print(f"Msg: {msg}")
        if 'List-Id' in msg:
            return ('List-Id', msg['List-Id'][msg['List-Id'].find('<')+1:-1])
        else:

            # print(f"{msg} - {type(msg)}")
            # print(f"{msg[1].keys()}")

            # headers = [f"{header}: {msg[1].get(header)}" for header in msg[1].keys()]

            # print(f"Headers: {headers}")

            # sel, sel_txt = select_from_list(headers, negation_selector="Received:")

            # print(f"Sel: {sel} - {sel_txt}")
            
            textHeaders = []
            nameHeaders = []
            for header in msgHeaders:
                textHeader = M.getHeader(msg, header)
                textHeader = email.header.decode_header(str(textHeader))
                textHeader = str(email.header.make_header(textHeader))
                if textHeader!='None':
                    #print(f"{i}) {header}: {textHeader}")
                    textHeaders.append(f"{textHeader}")
                    nameHeaders.append(f"{header}")
                #i = i + 1
            import locale
            #header_num = input("Select header: ")

            headers = [f"{cad1}: {cad2}" for cad1, cad2 in zip(nameHeaders, textHeaders)]
            header_num, sel_txt = select_from_list(headers)

            header = nameHeaders[header_num]
            textHeader = textHeaders[header_num]
            # textHeader = M.getHeader(msg, header)
            # textHeader = email.header.decode_header(str(textHeader))
            # textHeader = str(email.header.make_header(textHeader))
            pos = textHeader.find('<')
            if (pos >= 0):
                textHeader = textHeader[pos+1:textHeader.find('>', pos + 1)]
            else:
                pos = textHeader.find('[')
                if (pos >= 0):
                    textHeader = textHeader[pos+1:textHeader.find(']', pos + 1)]
                else:
                    textHeader = textHeader

            print("Filter: (header) ", header, ", (text) ", textHeader)
            filterCond = input("Text for selection (empty for all): ")
            # Trying to solve the problem with accents and so
            filterCond = filterCond#.decode('utf-8')

            if not filterCond:
                filterCond = textHeader

        return (header, filterCond)

    def selectHash(self, M, folder, hashSelect):
        M.select(folder)
        typ, data = M.search(None, 'ALL')
        i = 0
        msgs = ''
        dupHash = []
        for num in data[0].split():
            m = hashlib.md5()
            typ, msg = M.fetch(num, '(BODY.PEEK[TEXT])')
            # PEEK does not change access flags
            msgLog = ("%s" % msg[0][1])
            logMsg(msgLog, 2, 0)
            m.update(msg[0][1])
            msgDigest = binascii.hexlify(m.digest())
            if (msgDigest == hashSelect):
                if msgs:
                    msgs = msgs + ' ' + num.decode('utf-8')
                    # num is a string or a number?
                else:
                    msgs = num.decode('utf-8')
                i = i + 1
            else:
                msgLog = ("Message %s\n%s" % (num, msgDigest))
                logMsg(msgLog, 2, 0)
            # We are deleting duplicate messages
            if msgDigest in dupHash:
                if msgs:
                    msgs = msgs + ' ' + num.decode('utf-8')
                    # num is a string or a number?
                else:
                    msgs = num.decode('utf-8')
                i = i + 1
            else:
                dupHash.append(msgDigest)
            if (i % 10 == 0):
                msgLog = ("Counter %d" % i)
                logMsg(msgLog, 2, 0)

        msgLog = ("END\n\n%d messages have been selected\n" % i)
        logMsg(msgLog, 2, 0)

        return msgs

    def selectAllMessages(self, folder, M):
        msgs = ""
        #print("folder",folder)
        M.select(folder)
        try:
            data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        except:
            data = M.search(None,'ALL')
        if data and (data[0] == 'OK'):
            messages = data[1][0].decode("utf-8").split(' ')
            return ",".join(messages)
        else:
            return None

    def selectMessageSubject(self, folder, M, sbj, sens=0, partial=False):
        msg_number =""
        rows, columns = os.popen('stty size', 'r').read().split()
        numMsgs = 24
        msgs = ""
        distMsgs = ""
        if rows:
           numMsgs = int(rows) - 3
        try:
            M.select(folder)
            folderM = folder.split('/')[-1]
        except:
            return("","")

        data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        sbjDec = stripRe(headerToString(sbj))
        if (data[0] == 'OK'):
            j = 0
            msg_data = []
            messages = data[1][0].decode("utf-8").split(' ')
            lenId = len(str(messages[-1]))
            print("")
            for i in messages: #[-40:]: #[-numMsgs:]:
                typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
                # print msg_data_fetch
                for response_part in msg_data_fetch:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        msg_data.append(msg)
                        # Variable length fmt
                        fmt = "%2s) %-20s %-40s"
                        headFrom = msg['From']
                        headSubject = msg['Subject']
                        headSubjDec =  stripRe(headerToString(headSubject))
                        minLen = min(len(headSubjDec), len(sbjDec))
                        maxLen = max(len(headSubjDec), len(sbjDec))
    		            # What happens when the subjects are very similar in the
    		            # final part only?
                        # ayudita
                        # b'Visualizaci\xc3\xb3n ayudica'
    		            #dist = distance.levenshtein(headSubject[-minLen:], sbj[-minLen:])
                        if partial:
                            if (headSubjDec.find(sbjDec)>=0) or (sbjDec=='*'):
                                dist = -1
                            else:
                                dist = 100
                        elif minLen > maxLen/2:
                            if minLen > 0:
                                #print("len",minLen)
                                #print("he",headSubjDec[-minLen:])
                                #print("sb",sbjDec[-minLen:])
                                if minLen < 20:
                                    # print("he",headSubjDec[-minLen:])
                                    # print("sb",sbjDec[-minLen:])
                                    dist = distance.levenshtein(headSubjDec[-minLen:], sbjDec[-minLen:])
                                    #:dist = distance.hamming(headSubjDec[-minLen:], sbjDec[-minLen:])
                                else:
                                    dist = distance.levenshtein(headSubjDec[-minLen:], sbjDec[-minLen:])
                            else:
                                dist = minLen
                        else:
                            dist = maxLen
                        #print("dist", dist)

                        if (dist < minLen/(4+sens)):
                            print("+", end = "", flush = True)
                            if msgs:
                               msgs = msgs + ',' + str(i)
                               distMsgs = distMsgs + ',' + str(dist)
                            else:
                               msgs = str(i)
                               distMsgs = str(dist)
                        else:
                            print(".", end ="", flush = True)
            print("")

        return (msgs,distMsgs)

    def selectMessagesNew(self, M):
        M.select()
        end = ""
        while (not end):
           # Could we move this parsing part out of the while?
           # We are going to filter based on one message
           moveSent(M)
           msgs = ""
           listMsgs = ""
           moreMessages = ""
           badSel = ""
           while not moreMessages:
                (folder, msg, msgNumber) = selectMessageAndFolder(M)
                if msgNumber == -1:
                    return(-1)
                elif (folder != 'x'):
                    if (folder != "."):
                        if msg:
                            sbj = msg['Subject']
                            partial = False
                        else:
                            sbj = msgNumber
                            partial = True
                        ok = ""
                        badSel = ""
                        sens = 0
                        while not ok:
                            (msgs, distMsgs) = selectMessageSubject(folder, M, sbj, sens, partial)
                            isOk = input("Less messages [-] More messages [+] Wrong message selected [x] ")
                            if isOk == '-':
                               sens = sens + 1
                            elif isOk == '+':
                               moreMessages = ""
                               ok = "ok"
                            elif isOk == 'x':
                               ok = "ok"
                               badSel = "yes"
                            else:
                               ok = "ok"
                    else:
                        msgs = msgNumber
                        isOk = ""
                        moreMessages = input("String in the folder ("+moreMessages+') ')
                        folderM = folder
                    if listMsgs:
                        listMsgs = listMsgs + ',' + msgs
                    else:
                        listMsgs = msgs

                    if (isOk != '+') and (folder != '.'):
                       moreMessages = isOk
                    #elif (isOk == '+'):
                    #   moreMessages = input("More messages? ")
                else:
                    end = 'x'
                    moreMessages = end

           if listMsgs and not badSel:
                printMessageHeaders(M, listMsgs)
                if isOk:
                    moreMessages = isOk
                folder = selectFolder(M, moreMessages)
                #print("Selected folder (before): ", folder)
                #folder = nameFolder(folder)
                print("Selected folder (final): ", folder)
                moveMails(M,listMsgs, folder)
           elif badSel == "yes":
               listMsgs = ""

        return(0)

    def cleanHtml(self, html):
        soup = BeautifulSoup(html,'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return(re.sub(r"\n\s*\n*", "\n", soup.get_text()))

    def getMessageBody(self, msg):
        # http://blog.magiksys.net/parsing-email-using-python-content
        body = msg.get_body()
        try:
           bodyTxt = body.get_content()
           typeB = body.get_content_type()
           print(typeB)
           if (typeB == 'text/html'):
               bodyTxt = cleanHtml(bodyTxt)
           return(bodyTxt)
        except KeyError:
           for part in body.get_payload():
               type=part.get_content_type()
               print(type)
               if type[:4] == 'text':
                  bodyTxt = part.get_content()
                  if (type == 'text/html'):
                      bodyTxt = cleanHtml(bodyTxt)
                  return(bodyTxt)
               elif type == 'multipart/alternative':
                  print("alternative")
                  return(getMessageBody(part))
               else:
                  print("Not managed type: ", type)

        return("")

    def printMessage(self, M, msg, rows = 24, columns = 80, headers = ['From', 'To', 'Subject', 'Date']):


        for head in headers:
            print("%s: %s"% (head,headerToString(msg[head][:columns - len(head) - 2])))

        body = getMessageBody(msg)

        count = 0
        for line in body.split('\n'):
            print(line[:columns])
            count += 1
            if count > rows - len(headers) - 3:
                break
        wait = input("Any key to follow")


    def createFolder(self, M="", name="", folder="", search=True):
        exclude = ['Trash']
        if not M:
            M = self.getClient()
        if search:
            print("We can select a folder where our new folder will be created")
            folder = self.selectFolder(newFolderName=folder)
            print(folder)
        #folder  = nameFolder(folder)
        if folder:
            if (folder[-1] == '"'):
                folder = folder[:-1]+'/'+name+'"'
            else:
                if (' ' in name):
                    folder = '"' + folder+'/'+name + '"'
                else:
                    folder = folder+'/'+name
        else:
            folder = name
        if folder not in exclude:
            (typ, create_response) = M.create(folder)
            if typ == "OK":
                print("Created "+folder+ " ")
            else:
                print("Error creating "+folder+ " ")
                print(typ, create_response)

        return(folder)

    def selectFolderOld(self, M, moreMessages = "", folderM=''):
        resp, data = M.list('""', '*')
        listFolders = ""
        numberFolder = -1
        if moreMessages: inNameFolder = moreMessages
        while listFolders == "":
            inNameFolder = input("String in the folder ("+moreMessages+') ')
            i = 0
            if not inNameFolder: inNameFolder = moreMessages
            for name in data:
                if inNameFolder.encode('ascii').lower() in name.lower():
                    listFolders = listFolders + "%d) %s\n" % (i, nameFolder(name))
                    numberFolder = i
                i = i + 1
            iFolder = ""
            while listFolders and not iFolder.isdigit():
                listFoldersS = ""
                if (listFolders.count('\n') > 1):
                    print(listFolders, end = "")
                    iFolder = input("Folder number ("+str(numberFolder)+") [-cf] Create Folder // A string to select a smaller set of folders ({folderM})")
                    if not iFolder: iFolder = str(numberFolder)
                    if ((len(iFolder) > 0)
                        and not(iFolder.isdigit())
                        and (iFolder[0] != '-')):
                        listFoldersS = ""
                        for line in listFolders.split('\n'):
                             if line.find(iFolder)>0:
                                 if listFoldersS:
                                     listFoldersS = listFoldersS + '\n' + line
                                 else:
                                     listFoldersS = line
                    elif (len(iFolder) > 0) and (iFolder[0] == '-') and (iFolder == '-cf'):
                        break
                    else:
                        iFolder = (iFolder)

                    if listFoldersS:
                        listFolders = listFoldersS
                else:
                    iFolder = listFolders[:listFolders.find(')')]#str(numberFolder)
                    print("iFolder",iFolder, iFolder.find('\n'))
            if not iFolder:
                iFolder = nameFolder(data[numberFolder])
            elif (len(iFolder) > 0) and (iFolder[0] == '-'):
                if (len(iFolder) == 3) and (iFolder == '-cf'):
                    nfn = input("New folder name? (%s)"% folderM)
                    if not nfn:
                        nfn = folderM
                    iFolder = createFolder(M, nfn, moreMessages)
                    listFolders = iFolder
                else:
                    listFolders = ""
                    moreMessages = iFolder[1:]
            else:
                iFolder = nameFolder(data[int(iFolder)])
        print("ifolder", iFolder, iFolder.find('\n'))
        return(iFolder)

    def listFolderNames(self, data, inNameFolder = ""):
        listFolders = ""
        i = 0

        for name in data:
            try:
                if (type(name) == str): name = name.encode('ascii')
            except:
                logging.info(f"Non ascii: {name}")
            #print(inNameFolder.isdigit(), (inNameFolder+") "), name.lower().find((inNameFolder+") ").encode('ascii').lower()))
            if inNameFolder.isdigit() and name.lower().find((inNameFolder+") ").encode('ascii').lower()) == 0:
                # There can be a problem if the number is part of the name or
                # the number of the folder.
                listFolders = "%d) %s" % (i, self.nameFolder(name))
                return(listFolders)
            if isinstance(name.lower(), bytes):
                search = inNameFolder.encode('ascii')
            else:
                search = inNameFolder
            if search.lower() in name.lower():
                if listFolders:
                   listFolders = listFolders + '\n' + "%d) %s" % (i, self.nameFolder(name))
                else:
                   listFolders = "%d) %s" % (i, self.nameFolder(name))
            i = i + 1

        return(listFolders)

    def setLabels(self):
        api = self.getClient()
        resp, data = self.getClient().list('""', '*')
        if 'OK' in resp and data:
            self.labels = data

    def getLabels(self, sel=""):
        if not hasattr(self, "labels") or not self.labels:
            self.setLabels()
        return list(filter(lambda x: sel in str(x), self.labels))

    def listFolders(self):
        # resp, data = self.getClient().list('""', '*')
        self.setLabels
        return self.getLabels()

    def checkConnected(self):
        try:
            # Trying to avoid re-authentication. Are ther better ways?
            self.getClient().noop()
        except:
            self.setClient(f"{self.user}")

    def selectFolderN(self, moreMessages ="",
                      newFolderName = '', folderM=''):
        self.checkConnected()
        data = self.listFolders()
        folders = [self.nameFolder(fol) for fol in data]
        sel, folder = select_from_list(folders, more_options=['-cf'])
        if isinstance(sel, str) and '-cf' in sel:
            nfn = input("New folder name? (%s)"% folderM)
            if not nfn:
                nfn = folderM
            iFolder = self.createFolder(name=nfn, folder=moreMessages)
            listFolders = iFolder
            folder = iFolder

        return folder


    def selectFolder(self, M="", moreMessages = "",
                     newFolderName='', folderM=''):

        self.checkConnected()
        if not M:
            M = self.getClient()

        data = self.listFolders()
        #print(data)
        listAllFolders = self.listFolderNames(data, moreMessages)
        if not listAllFolders: listAllFolders = self.listFolderNames(data, "")
        listFolders = listAllFolders
        while listFolders:
            if (listFolders.count('\n') == 0):
                nF = self.nameFolder(listFolders)
                nF = nF.strip('\n')
                print("nameFolder", nF)
                return(nF)
            rows, columns = os.popen('stty size', 'r').read().split()
            if listFolders.count('\n') > int(rows) - 2:
                click.echo_via_pager(listFolders)
            else:
                print(listFolders)
            inNameFolder = input(f"Folder number [-cf] Create Folder // A string to select a smaller set of folders ({folderM}) ")
            if not inNameFolder and folderM:
                inNameFolder = folderM

            if (len(inNameFolder) > 0) and (inNameFolder == '-cf'):
                if newFolderName:
                    nfn = newFolderName
                else:
                    nfn = input("New folder name? (%s)" % folderM)
                    if not nfn:
                        print(folderM)
                        nfn = folderM
                iFolder = createFolder(M, nfn, moreMessages)
                return(iFolder)
                #listFolders = iFolder
            listFolders = self.listFolderNames(listFolders.split('\n'),
                                               inNameFolder)
            if (not inNameFolder):
                print("Entra")
                listAllFolders = self.listFolderNames(data, "")
                listFolders = ""
            if (not listFolders):
                listFolders = listAllFolders

    def selectMessages(self, M):
        M.select()
        end = ""
        while (not end):
            # Could we move this parsing part out of the while?
            # We are going to filter based on one message
            msgs = ""
            listMsgs = ""
            moreMessages = ""
            while not moreMessages:
                 (folder, msg) = selectMessage(M)
                 sbj = msg['Subject']
                 (msgs, distMsgs, folderM) = selectMessageSubject(folder, M, sbj)

                 printMessageHeaders(M, msgs)

                 if listMsgs:
                     listMsgs = listMsgs + ',' + msgs
                 else:
                     listMsgs = msgs

                 moreMessages = input("More messages? ")
            print(listMsgs)
            syx.exit()

            if listMsgs:
                 printMessageHeaders(M, listMsgs)
                 folder = selectFolder(M, moreMessages)
                 #folder = nameFolder(folder)
                 print("Selected folder (final): ", folder)
                 moveMails(M,listMsgs, folder)
            end = input("More rules? (empty to continue) ")

    def loadImapConfig(self):
        config = configparser.ConfigParser()
        config.read([os.path.expanduser('~/.IMAP.cfg')])

        return(config, len(config.sections()))

    def readImapConfig(self, config, confPos = 0):
        # sections=['IMAP6']
        sections=config.sections()

        SERVER = config.get(sections[confPos], "server")
        USER = config.get(sections[confPos], "user")
        PASSWORD = getPassword(SERVER, USER)
        if config.has_option(sections[confPos], 'rules'):
            RULES = config.get(sections[confPos], 'rules').split('\n')
        else:
            RULES = ""
        if config.has_option(sections[confPos], 'inbox'):
            INBOX = config.get(sections[confPos], 'inbox')
        else:
            INBOX = ""
        if config.has_option(sections[confPos], 'move'):
            FOLDER = config.get(sections[confPos], "move")
        else:
            FOLDER = ""
        return (SERVER, USER, PASSWORD, RULES, INBOX, FOLDER)

    def makeConnection(self, SERVER, USER, PASSWORD):
        msgLog = (f"{self.indent} Making connection {self.service}: "
                  f"{USER} at {SERVER}")
        logMsg(msgLog, 2, 0)
        # IMAP client connection
        import ssl
        context = ssl.create_default_context() #ssl.PROTOCOL_TLSv1)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # context.protocol = ssl.PROTOCOL_TLS_SERVER
        try:
            M = imaplib.IMAP4_SSL(SERVER, 993, ssl_context=context)
            # M = imaplib.IMAP4(SERVER)
            # M.starttls(ssl_context=context)
        except:
            logging.debug("{self.indent} except user, server", USER, SERVER)
            logging.debug("{self.indent} except", sys.exc_info()[0])
            logging.debug("{self.indent} except", sys.exc_info()[1])
            logging.debug("{self.indent} except", sys.exc_info()[2])
            sys.exit()
        ok = ''
        while not ok:
            try:
                M.login(USER, PASSWORD)
                PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                # We do not want passwords in memory when not needed
                ok = 'ok'
            except Exception as ins:
                # We will ask for the new password
                print(f"{self.indent} server", M.state)
                print(f"{self.indent} except", SERVER, USER)
                print(f"{self.indent} except {sys.exc_info()}")
                print(f"{self.indent} except", ins.args)
                sys.exit()
                srvMsg = SERVER.split('.')[0]
                usrMsg = USER.split('@')[0]
                msgLog = ("[%s,%s] wrong password!"
                                 % (srvMsg, usrMsg))
                logMsg(msgLog, 3, 0)
                PASSWORD= setPassword(SERVER, USER)
                #res.put(("no", SERVER, USER))
                #return 0

        return M

    def nameFolder(self, folder):
        # This function has two modes of working:
        # The first one is when it receives a list of IMAP folders like:
        # b'(\\HasNoChildren) "/" Departamento/estudiantes' b'Departamento/estudiantes'
        #   01234567890123456789012
        # b'(\\HasChildren) "/" "unizar/aa vrtic/sicuz/servicios/web"'
        # The other one can be a number followed by a ) and the folder
        # 1) folderName
        # 2) "Folder name"

        if type(folder) == bytes: folder = folder.decode()
        if folder and folder[0].isdigit():
            pos = folder.find(') ')
            if pos >= 0:
                folder = folder[pos+2:]
        elif "/" in folder:
            pos = folder.find('"/" ')
            if pos >=0:
                folder = folder[pos+4:]
        elif "." in folder:
            pos = folder.find('"." ')
            if pos >=0:
                folder = folder[pos+4:]

        return(folder)

    def moveSent(self, M):
        msgs = selectAllMessages('Sent', M)
        if msgs:
            moveMails(M,  msgs, 'INBOX')

    def copyMailsRemote(self, M, msgs, account, folder=None, delete=False):

        # We start at the end because we can have accounts where the user
        # includes an @ (there can be two): user@host@mailhost
        pos = account.rfind('@')

        SERVERD = account[pos+1:]
        USERD   = account[:pos]
        msgLog = ("Datos.... %s %s" %(SERVERD, USERD))
        logMsg(msgLog, 2, 0)

        method = None

        try:
            # First we try to see if there is a Gmail configuration
            config = configparser.ConfigParser()
            config.read(os.path.expanduser(CONFIGDIR+'/.oauthG.cfg'))
            for sect in config.sections():
                if SERVERD == config[sect].get('server'):
                    if USERD == config[sect].get('user'):
                        method = 'oauth'
                        acc = sect
                        break
        except:
            msgLog = ("No oauth config!")
            logMsg(msgLog, 3, 0)

        if not method:
            msgLog = ("No method")
            logMsg(msgLog, 2, 0)
            PASSWORDD = getPassword(SERVERD, USERD)
            method = 'imap'

        msgLog = ("Method %s" % method)
        logMsg(msgLog, 2, 0)
        if method == 'imap':
            MD = makeConnection(SERVERD, USERD, PASSWORDD)
            if not folder:
                folder = 'INBOX'
                MD.select('INBOX')
            else:
                iFolder = createFolder(MD,folder,'', False)
                MD.select(folder)

            i = 0
            for msgId in msgs.split(','): #[40000:]: #[:25]:
                print(msgId)
                #print('.', end='')
                msgLog = ("Message %s" % msgId)
                logMsg(msgLog, 1, 0)

                typ, data = M.fetch(msgId, '(FLAGS RFC822)')
                flagsM = data[0][0]
                print("flags",flagsM)
                if not (b'Deleted' in flagsM):
                    M.store(msgId, "-FLAGS", "\\Seen")

                    if (typ == 'OK'):
                        message = data[0][1]
                        msgLog = ("Message %s", message)
                        logMsg(msgLog, 2, 0)

                        flags = ''

                        msg = email.message_from_bytes(message);
                        res = MD.append(folder,flags, None, message)

                        if res[0] == 'OK':
                            M.store(msgId, "+FLAGS", "\\Seen")
                i = i + 1
            MD.close()
            MD.logout()
        else:
            service = moduleGmail.moduleGmail()
            service.API(acc)

            i = 0
            lenM = len(msgs.split(','))
            for msgId in msgs.split(','): #[:25]:
                #print('.', end='')
                msgLog = ("Message %d %s" % (i, msgId))
                logMsg(msgLog, 2, 0)
                print("Message %d %s (%d)" % (i, msgId, lenM))
                typ, data = M.fetch(msgId, '(FLAGS RFC822)')
                flagsM = data[0][0]
                M.store(msgId, "-FLAGS", "\\Seen")

                if (typ == 'OK'):
                    print("flagsM %s" % flagsM)
                    if not (b'Deleted' in flagsM):

                        message = data[0][1]
                        msgLog = ("Message %s", message)
                        logMsg(msgLog, 2, 0)

                        rep = service.copyMessage(message, folder)
                        msgLog = ("Reply %s" %rep)
                        logMsg(msgLog, 2, 0)
                        if rep != "Fail!":
                            M.store(msgId, "+FLAGS", "\\Seen")
                            flag = '\\Deleted'
                            M.store(msgId, '+FLAGS', flag)
                        time.sleep(0.1)
                i = i + 1
                if i%1000 == 0:
                    time.sleep(5)


        # We are returning a different code from 'OK' because we do not want to
        # delete these messages.
        if (i == len(msgs.split(','))):
           return('OKOK')
        else:
           return('OKNO')

    def deleteLabel(self, folderName):
        M = self.getClient()
        return M.delete(folderName)

    def deletePostId(self, idPost):
        return self.deleteApiPosts(idPost)

    def deleteApiPosts(self, idPost):
        try:
            res = self.moveMails(self.getClient(), str(idPost).encode(), self.special['Trash'])
        except:
            logging.warning("Some error moving mails to Trash")

    def moveMails(self, M, msgs, folder):
        if hasattr(self, 'channel'): # in self:
            M.select(self.channel)
        else:
            channel = self.getPostsType()
            M.select(channel.capitalize())
        msgLog = ("Copying %s in %s" % (msgs, folder))
        logMsg(msgLog, 2, 0)
        (status, resultMsg) = M.copy(msgs, folder)
        res = status
        logging.debug(f"Res status: {res}")
        if status == 'OK':
            # If the list of messages is too long it won't work
            flag = '\\Deleted'
            result = M.store(msgs, '+FLAGS', flag)
            if result[0] != 'OK':
                print("Fail deleting!")
                res = "Fail!"
            else:
                print(f"deleting! {result}")
        else:
            logging.debug(f"Fail copying")
            res = "Fail!"
        #print(f"Expunge: {M.expunge()}")
        # msgs contains the index of the message, we can retrieve/move them
        return res

    def printMessageHeaders(self, M, msgs):
        if msgs:
            # logging.info(msgs)
            for i in msgs.split(','):
                typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
                for response_part in msg_data_fetch:
                    if isinstance(response_part, tuple):
                        msgI = email.message_from_bytes(response_part[1])
                        print(headerToString(msgI['Subject']))

    def getPostContentHtml(self, msg):
        if isinstance(msg, tuple):
            post = msg[1]
        else:
            post = msg
        if post.is_multipart():
            mail_content = ''
            for part in post.get_payload():
                # print(f"type: {part.get_content_type()}")
                if part.get_content_type() == 'text/html':
                    mail_content += part.get_payload()
                elif part.get_content_type() == 'multipart/alternative':
                    for subpart in part.get_payload():
                        # print(f"sub: *{subpart}*")
                        if subpart and (subpart.get_content_charset() is None):
                            # print(f"sub: *{subpart}*")
                            charset = chardet.detect(subpart.as_bytes())['encoding']
                        else:
                            charset = subpart.get_content_charset()
                        if subpart.get_content_type() == 'text/plain':
                            mail_content += str(subpart.get_payload(decode=True))
                        if subpart.get_content_type() == 'text/html':
                            mail_content += str(subpart.get_payload(decode=True))
        else:
            mail_content = post.get_payload()

        # print(f"Mail: {mail_content}")

        return mail_content

    def getPostContent(self, msg):
        post = msg[1]
        if post.is_multipart():
            mail_content = ''
            for part in post.get_payload():
                if part.get_content_type() == 'text/plain':
                    mail_content += part.get_payload()
                elif part.get_content_type() == 'text/html':
                    text = part.get_payload(decode=True)
                    soup = BeautifulSoup(text, "html.parser")
                    mail_content += soup.get_text('\n')
                elif part.get_content_type() == 'multipart/alternative':
                    for partt in part.get_payload():
                        mail_content += partt.get_payload()
        else:
            mail_content = post.get_payload()

        return mail_content

    def getPostLinks(self, msg):
        if isinstance(msg, tuple):
            post = msg[1]
        else:
            post = msg
        html = self.getPostContentHtml(post)
        # logging.debug(f"Html: {html}")
        try:
            import quopri
            html = quopri.decodestring(html)
        except:
            msgLog = ("Not quoted")
            logMsg(msgLog, 3, 0)
        soup = BeautifulSoup(html, 'lxml')
        res = soup.find_all('a', href=True)
        # print(f"Res: {res}")
        links = []
        for element in res:
            link = element['href']
            if not link in links:
                links.append(link)
        return links

    def getPostLink(self, msg):
        post = msg[1]
        theLink = ''
        if post:
            # msgLog = (f"Post: {post}")
            # logMsg(msgLog, 2, 0)
            links = self.getPostLinks(post)
            if links:
                theLink = links[0]

        # result = f"From: {fromP}\nText: {snipP}"
        result = theLink
        return result

    def getHeader(self, msg, header):
        post = msg[1]
        return safe_get(post, [header])

    def getPostDate(self, msg):
        post = msg[1]
        return post.get('Date')

    def getPostFrom(self, msg):
        post = msg[1]
        return post.get('From')

    def getPostTo(self, msg):
        post = msg[1]
        return post.get('To')

    def getPostListId(self, msg):
        post = msg[1]
        return post.get('List-Id')

    def getPostTitle(self, msg):
        post = msg[1]
        return self.getPostSubject(post)

    def getPostSubject(self, msg):
        if isinstance(msg, tuple):
            post = msg[1]
        else:
            post = msg
        subject = post.get('Subject')
        theHeader = email.header.decode_header(str(subject))
        subject = str(email.header.make_header(theHeader))
        return subject

    def getPostId(self, msg):
        return msg[0]

    def getPostAttachmentPdf(self, msg):
        if msg.is_multipart():
            for part in msg.get_payload():
                if part.get_content_type() == 'application/pdf':
                    fileName = part.get_filename()
                    myFile = part.get_payload(decode=True)
                    return (fileName, myFile)

        return None, None

    def listMessages(self, M, folder):
        # List the headers of all e-mails in a folder
        posts = []
        msgLog = (f"Folder: {folder}")
        logMsg(msgLog, 2, 0)
        nameF = self.nameFolder(folder)
        logging.debug(f"Folder: {nameF}")
        self.channel = nameF
        logging.debug(f"Select: {M.select(nameF)}")
        # data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        if self.getPostsType() == 'new':
            try:
                data = M.search(None, '(UNSEEN)')
            except:
                data = ('NO', [])
        else:
            try:
                data = M.sort('ARRIVAL', 'UTF-8', 'NOT DELETED')
            except:
                data = M.sort('ARRIVAL', 'UTF-8', 'NOT DELETED')
        msgLog = (f"Msgs data: {data}")
        logMsg(msgLog, 2, 0)
        # print(f"Datos: {data}")
        if (data[0] == 'OK'):
            messages = data[1][0].decode("utf-8")
            if messages:
                for i in messages.split(' ')[:75]: #[-40:]: #[-numMsgs:]:
                    # typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE 1.2)])')
                    typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[])')
                    for response_part in msg_data_fetch:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            posts.append((i,msg))
                            continue
                            print(f"Mess c: {mail_content}")
                            return
                            print(self.headerToString(headFrom),
                                  self.headerToString(headSubject),
                                  self.headerToString(headDate))

        return posts

    def sendMessage(self, msg):
        smtpsrv  = 'localhost'
        logging.debug(f"Msg (sendMessage): {type(msg)}")
        fromaddr = msg.get('from')
        logging.debug(f"Msg (sendMessage): {fromaddr}")
        toaddrs = msg['to']
        logging.debug(f"Msg (sendMessage): {fromaddr}")
        res = None
        try:
            #FIXME: we should use moduleSmtp
            server = smtplib.SMTP(smtpsrv)
            server.connect(smtpsrv, 587)
            server.starttls()

            res = server.send_message(msg)
            server.quit()
        except:
            res = self.report(self.service, '', '', sys.exc_info())

        if not res:
            res = 'OK'
        return res

    def publishApiDrafts(self, *args, **kwargs):
        return self.publishApiDraft(*args, **kwargs)

    def publishApiDraft(self, *args, **kwargs):
        logging.debug(f"Args: {args} Kwargs: {kwargs}")
        if kwargs:
            post = kwargs.get('post', '')
            api = kwargs.get('api', '')
        logging.debug(f"Post: {post} Api: {api}")
        idMsg, msg = post
        res = self.sendMessage(msg)
        logging.info(f"Res: {res}")
        resMove = self.moveMails(self.getClient(), idMsg, 'Trash')
        logging.info(f"Res move: {resMove}")
        return res

    def publishApiPost(self, *args, **kwargs):
        link = None
        logging.debug(f"Tittt: args: {args} kwargs: {kwargs}")
        if args and len(args) == 3 and args[0]:
            logging.info(f"Tittt: args: {args}")
            post, link, comment = args
        if kwargs:
            logging.debug(f"Tittt: kwargs: {kwargs}")
            more = kwargs
            # logging.debug(f"More: {more}")
            # FIXME: We need to do something here
            post = more.get('post', '')
            api = more.get('api', '')
            # logging.debug(f"Post: {post}")
            # idPost = api.getPostId(post)
            # logging.info(f"Postt: {post['meta']}")
            # idPost = post['meta']['payload']['headers'][2]['value'] #[1:-1]
            # idPost = post['list']['id'] #[1:-1]
            # logging.info(f"Post id: {idPost}")
        res = 'Fail!'
        try:
            if (isinstance(post, tuple)
                and isinstance(post[1], email.message.Message)):
                msg = post[1]
            else:
                destaddr = self.user
                toaddrs = self.user
                fromaddr = self.user
                smtpsrv  = 'localhost'
                theUrl = link
                subject = post.split('\n')[0]

                msg = MIMEMultipart()
                msg['From']    = fromaddr
                msg['To']      = destaddr
                msg['Date']    = time.asctime(time.localtime(time.time()))
                msg['X-URL']   = theUrl
                msg['X-print'] = theUrl
                msg['Subject'] = subject
                htmlDoc = (f"Title: {subject} \n\n"
                           f"Url: {link} \n\n"
                           f"{post}")
                adj = MIMEApplication(htmlDoc)
                encoders.encode_base64(adj)
                name = 'notumblr'
                ext = '.html'
                adj.add_header('Content-Disposition',
                                   'attachment; filename="%s"' % name+ext)

                msg.attach(adj)
                msg.attach(MIMEText(f"[{subject}]({theUrl})\n\n"
                                    f"URL: {theUrl}\n"))

            self.sendMessage(msg)
            res = 'OK. Published!'
        except:
            res = self.report(self.service, '', '', sys.exc_info())

        return(f"Res: {res}")

def main():

    logging.basicConfig(stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import moduleImap
    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    # Example:
    # ('imap', 'set', 'ftricas@elmundoesimperfecto.com', 'posts')
    # More:  More: ('imap', 'set', 'ftricas@elmundoesimperfecto.com', 'posts')

    apiSrc = rules.selectRuleInteractive()

    testingFolders=False
    if testingFolders:
        folders=apiSrc.getChannels()
        for folder in folders:
            # print(f"Folder: {folder} Name: {name}")
            print(f"Folder: {apiSrc.getChannelName(folder)}")
        print(f"Special folders: {apiSrc.special}")
        print(f"{apiSrc.selectFolderN()}")
        # print(f"{apiSrc.selectFolder(apiSrc.getClient())}")

        return

    testingPublishingDraft = True
    if testingPublishingDraft:
        apiSrc.setPostsType('drafts')
        apiSrc.setPosts()
        if apiSrc.getPosts():
            posts = [apiSrc.getPostSubject(post[1]) for post in apiSrc.getPosts()]
            sel, post = select_from_list(posts, identifier='Subject')
            print(sel)
            return
            post = apiSrc.getPosts()[0]
            apiSrc.publishApiDraft(post)

        return

    testingPublishing = False
    if testingPublishing:
        apiSrc.publishPost('Mensaje', 'https://www.unizar.es/', '')

        return

    testingDrafts = False
    if testingDrafts:
        apiSrc.setChannel(apiSrc.special['Drafts'])
        apiSrc.setPosts()
        for post in apiSrc.getPosts():
            # print(f"Post: {post}")
            print(f"Title: {apiSrc.getPostTitle(post)}")
            print(f"Content: {apiSrc.getPostContent(post)}")

        return


    testingPosts = True
    if testingPosts:
        apiSrc.setChannel('INBOX')
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            # print(f"Post: {post}")
            print(f"{i}) Title: {apiSrc.getPostTitle(post)}")
            # print(f"Content: {apiSrc.getPostContent(post)}")

        selPost = input("Select one: ")
        if selPost and selPost.isdigit() and (int(selPost)<=i):
            print(f"{i}) Title: "
                  f"{apiSrc.getPostTitle(apiSrc.getPosts()[int(selPost)])}")
            input("Send?")
            res = apiSrc.publishPost(api = apiSrc, post = post)
            print(f"Res: {res}")

        return

    testingAttachment = False
    if testingAttachment:
        apiSrc.setChannel('INBOX')
        apiSrc.setPosts()
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"{i}) {apiSrc.getPostTitle(post)}")
        select = input("Which one? ")

        msg = apiSrc.getPosts()[int(select)][1]
        print(f"Msg: {msg}")

        fileName, myFile = apiSrc.getPostAttachmentPdf(msg)

        with open(f"/tmp/{fileName}", 'wb') as f:
            f.write(myFile)

        return

    testingClick = False
    if testingClick:
        apiSrc.setPosts()

        import moduleHtml
        html = moduleHtml.moduleHtml()
        html.setClient('fernand0')
        post = apiSrc.getNextPost()
        link = apiSrc.getPostLink(post)
        print(f"Ll: {link}")
        html.click(link)
        apiSrc.moveMails(apiSrc.getClient(), str(i+1).encode(), 'INBOX.Trash')
        return

    testingNew = False
    if testingNew:
        channels = apiSrc.getChannels()
        # print(f"blog: {apiSrc.getUrl()}")
        fileName = fileNamePath(apiSrc.getUrl())
        # print(f"fileName: {fileName}")
        with open(fileName,'rb') as f:
            date1 = pickle.load(f)
        # date1 = parse('Sat, 12 Feb 2022 00:00:00 +0000')
        dateLatest = date1
        for chan in channels:
            # print(f"Channel: {apiSrc.getChannelName(chan)}")
            # chan = b'(\\HasNoChildren \\UnMarked) "." INBOX.backup.avecesunafoto'
            if str(chan).find('Noselect')<0:
                apiSrc.setChannel(apiSrc.getChannelName(chan))
                apiSrc.setPosts()
                # print(f"Len: {len(apiSrc.getPosts())}")
                # print(f"Mes: {apiSrc.getPosts()[0]}")
                # print(f"Mes: {apiSrc.getPosts()[1]}")
                # print(f"Date: {apiSrc.getPostDate(apiSrc.getPosts()[0])}")
                # print(f"Date: {apiSrc.getPostDate(apiSrc.getPosts()[1])}")
                for post in apiSrc.getPosts():
                    dateMsg = parse(apiSrc.getPostDate(post))
                    # print(f"Msg: {apiSrc.getPostTitle(post)}")
                    try:
                        if dateMsg > date1:
                            print(f"Chan: {apiSrc.getChannelName(chan)}")
                            # print(f"     Msg: {apiSrc.getPostTitle(post)}")
                            # print(f"     Date: {dateMsg}")
                            if dateMsg > dateLatest:
                                dateLatest = dateMsg
                            break
                    except:
                        print(f"Date: {apiSrc.getPostDate(post)}")
        print(f"Last Message: {dateLatest}")
        with open(fileName,'wb') as f:
            pickle.dump(dateLatest, f)
        return

        apiSrc.setPosts()

    testingMoveMail = False
    if testingMoveMail:
        indent = ""
        i = 0
        myRules = []
        for src in rules.rules.keys():
            if (src[0] == 'imap') or (src[0] == 'gmail'):
                i = i + 1
                print(f"{i}) Src: {src[2]} ({src[-1]})")
                more = rules.more[src]
                myRules.append((src, more))
                # print(f"More: {src}")
        source = input("Select source: ")
        destin = input("Select destination: ")
        src = myRules[int(source) - 1][0]
        more = myRules[int(source) - 1][1]
        action = myRules[int(destin) - 1][0]
        moreA = myRules[int(destin) - 1][1]
        print(f"Copying from {src} to {action}")
        apiSrc = rules.readConfigSrc(indent, src, more)
        apiDst = rules.readConfigSrc(indent, action, moreA)
        foldersSrc = apiSrc.listFolders()
        foldersDst = apiDst.listFolders()
        # print(f"{foldersSrc}")
        # print(f"{foldersDst}")
        sel = ""
        count = 0
        while (count != 1) and (not sel.isdigit()):
            count = 0
            for i, folder in enumerate(foldersSrc):
                nameF = apiSrc.getChannelName(folder)
                if (not sel) or (sel in nameF):
                    print(f"{i}) {nameF}")
                    selI = i
                    count = count + 1
            print(f"count: {count}")
            if count > 1:
                sel = input("Selección? ")
            elif count == 0:
                sel = ''
            else:
                sel = str(selI)
        folderSrc = foldersSrc[int(sel)]
        print(f"Selected: {folderSrc}")
        input("Continue? ")
        apiSrc.setChannel(folderSrc)
        apiSrc.setPostsType('posts')
        apiSrc.setPosts()
        print(f"Selected: {apiSrc.getChannel()}")
        print(f"Posts: {len(apiSrc.getPosts())}")
        if len(apiSrc.getPosts()) == 0:
            input(f"Delete folder {folderSrc}? ")
            print(f"Delete folder: {apiSrc.deleteLabel(apiSrc.getChannelName(folderSrc))}")
            return
        else:
            print(f"Num of messages: {len(apiSrc.getPosts())}")

        sel = ""
        while not sel.isdigit():
            for i, folder in enumerate(foldersDst):
                nameF = apiDst.getChannelName(folder)
                if (not sel) or (sel in nameF):
                    print(f"{i}) {nameF}")

            sel = input("Selección? ")
        if sel.isdigit():
            folderDst = foldersDst[int(sel)]
        # print(f"Folder dst: {folderSrc}")
        print(f"Selected: {folderDst}")
        apiDst.setChannel(folderDst)
        nameF = apiDst.getChannelName(folderDst)
        print(f"Folder dst: {nameF}")
        # nameF = f"INBOX.{nameF}"
        # print(f"Res: {apiDst.createChannel(nameF)}")
        for i, post in enumerate(apiSrc.getPosts()):
            print(f"Msg ({i}): {apiSrc.getPostTitle(post)}")
            # input("Continue? ")
            # print(f"Msg: {post}")
            raw = apiSrc.getMessageRaw(post['list']['id'], 'posts')
            post['raw'] = raw
            flags = None
            if 'UNREAD' not in post['meta']['labelIds']:
                flags = r'(\Seen)'
                print(f"Read!")
            import base64
            messageEmail = email.message_from_bytes(base64.urlsafe_b64decode(post['raw']['raw']))
            if apiDst.getService().lower() == 'imap':
                date = apiSrc.getPostDate(post)
                date = int(date)/1000#.timetuple()
                print(f"Appending: {apiDst.getClient().append(nameF, flags, date, messageEmail.as_bytes())}")
            else:
                print(f"Appending: {apiDst.copyMessage(messageEmail.as_bytes(), [ nameF, ])}")
            apiSrc.deletePost(post)
            time.sleep(0.5)
            # return
        #print(apiSrc.getPosts())

        return

    return

    mail = moduleImap.moduleImap()
    mail.setClient('ftricas@elmundoesimperfecto.com@mail.your-server.de')
    # print(mail.getClient().list())
    # return
    mail.setPosts()
    import moduleHtml
    html = moduleHtml.moduleHtml()
    html.setClient('fernand0')

    for i, post in enumerate(mail.getPosts()):
        print(f"Post: {post}")
        print(f"S: {mail.getPostSubject(post)}")
        print(f"F: {mail.getPostFrom(post)}")
        print(f"D: {mail.getPostDate(post)}")
        print(f"C: {mail.getPostContent(post)}")
        link = mail.getPostLink(post)
        print(f"Ll: {link}")
        html.click(link)
        mail.moveMails(mail.getClient(), str(i+1).encode(), 'INBOX.Trash')
        return

    return

    import moduleRules
    rules = moduleRules.moduleRules()
    rules.checkRules()

    testingSearch = False
    if testingSearch:
        for key in rules.rules.keys():
            print(f"Key: {key}")
            if ((key[0] == 'imap')
                    and ('ftricas' in key[2])
                    and (key[3] == 'search')):
                print(f"SKey: {key}\n"
                      f"SRule: {rules.rules[key]}\n"
                      f"SMore: {rules.more[key]}")
                apiSrc = rules.readConfigSrc("", key, rules.more[key])
                apiSrc.setPosts()
                print(f"Search posts: {apiSrc.setPosts()}")
                return
            elif False:
                post = apiSrc.getNextPost()
                print(f"titleeeee: {apiSrc.getPostTitle(post)}")
                print(f"linkkkkk: {apiSrc.getPostLink(post)}")
                for i, post in enumerate(apiSrc.getPosts()):
                    print(f"{i}) {apiSrc.getPostTitle(post)}")
                    print(f"{i}) {apiSrc.getPostLink(post)}")
                    # print(f"{i}) {apiSrc.getPostLinks(post)}")

        return
    return


    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])

    SERVER = config.get("IMAP6", "server")
    USER = config.get("IMAP6", "user")
    PASSWORD = getPassword(SERVER, USER)

    # IMAP client connection
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    M = imaplib.IMAP4_SSL(SERVER,ssl_context=context)
    try:
        M.login(USER, PASSWORD)
        PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # We do not want passwords in memory when not needed
    except Exception as ins:
        # We will ask for the new password
        self.report("Wrong password", SERVER, USER, sys.exc_info())
        res.put(("no", SERVER, USER))
        return 0

    PASSWORD = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    M.select()

    copyMailsRemote(M, None, 'fernand0movilizado@gmail.com')

if __name__ == "__main__":
    main()
