#!/usr/bin/env python

import configparser
import getpass
import io
import os
# GitPython
import ssl
import sys
#import sievelib
import time

import keyring
from git import Repo
from sievelib.factory import FiltersSet
from sievelib.managesieve import Client
from sievelib.parser import Parser

from socialModules.moduleImap import *

msgHeaders = ['List-Id', 'From', 'Sender', 'Subject', 'To', 
              'X-Original-To', 'X-Envelope-From', 
              'X-Spam-Flag', 'X-Forward']
headers = ["address", "header"]
keyWords = {"address": ["From", "To"],
            "header":  ["subject", "Sender", "X-Original-To", "List-Id"]
            }
FILE_SIEVE = "/tmp/sieveTmp"

repoDir='/home/ftricas/Documents/config/'
repoFile='sogo.sieve'

def printRule(rule):
    print("Rule ")
    for cond in rule[1]:
        cond.tosieve()
        print()

def printRules(listRules):
    # For debugging
    for rule in list(listRules.keys()):
        printRule(listRules[rule])

def addRule(rules, more, keyword, filterCond, actions):
        #printRules(rules)
        #print(rules['"Docencia/master/masterbdi"'])
        #print(type(rules['"Docencia/master/masterbdi"']))
        theActions = actions[0][1].strip('"')
        if theActions not in rules:
                rules[theActions] = ['fileinto', []]
            
        #printRule(rule)

        # Is there a better way to do this?
        cmd = sievelib.factory.get_command_instance("header",
                                                    rules[theActions])
        cmd.check_next_arg("tag", ":contains")
        # __quote_if_necessary
        if not filterCond.startswith(('"', "'")):
            filterCond = '"%s"' % filterCond
        if not keyword.startswith(('"', "'")):
            #print(keyword)
            keyword = '"%s"' % keyword
        cmd.check_next_arg("string", keyword)
        cmd.check_next_arg("string", filterCond)
#print("cmd Cmd",cmd)
        #print("theActions",theActions[1])
        rules[theActions][1].append(cmd)
        #print("theActions++",theActions[1])

        # print "--------------------"
        #printRule(rules[theActions])
        # print "--------------------"
        #print(rules[theActions])
        #if theActions in more:
        #    print(more[theActions])
        #sys.exit()
        newActions = constructActions(rules, more)

        # print "actions, ", actions
        return newActions

def extractActions(p):
    i = 1
    rules = {}
    more = {}
    for r in p.result:
        # print("children", r.children)
        if r.children:
            tests = r.arguments['test'].arguments['tests']
            # print type(r.children[0])
            key = r.children[0]
            if len(r.children) > 2:
                print(r.children)
                key = ()
                for i in range(len(r.children)): 
                    print(r.children[i]) 
                    if 'address' in r.children[i]: 
                        key = key + (r.children[i]['address'], )
                    elif 'mailbox' in r.children[i]:
                        key = key + (r.children[i]['mailbox'], ) 

                print("keys", key)
                ## If there are more actions (just one more
                ## action, in fact), we will store it in more
                #theKey = key['address'].strip('"') 
                #more[theKey] = []
                #print("---->", r)
                #print("---->", r.children)
                #print("---->", r.children[1])
                #if 'address' in r.children[1]: 
                #    more[theKey].append(r.children[1]['address'])
                #elif 'mailbox' in r.children[1]:
                #    more[theKey].append(r.children[1]['mailbox'])
            if (type(key) == sievelib.commands.FileintoCommand):
                # print(i, ") Folder   ", key['mailbox'])
                tests = r.arguments['test'].arguments['tests']
                if key['mailbox'] in rules:
                    #print("tests-mailbox.", )
                    #tests[0].tosieve()
                    #print()
                    theKey = key['mailbox'].strip('"') 
                    rules[theKey][1] = rules[theKey][1] + tests
                else:
                    #print("rules..",rules)
                    #print("tests..",dir(tests[0]))
                    #print("\ntests..", vars(tests[0]))
                    #print("\ntosieve...") 
                    #tests[0].tosieve()
                    #print()
                    #print("key..",key['mailbox'])
                    theKey = key['mailbox'].strip('"') 
                    rules[theKey] = []
                    rules[theKey].append("fileinto")
                    rules[theKey].append(tests)
                    #print("rules..++",rules)
            elif (type(key) == sievelib.commands.RedirectCommand):
                # print i, ") Redirect ", key['address']
                tests = r.arguments['test'].arguments['tests']
                theKey = key['address'].strip('"') 
                if theKey in rules:
                    rules[theKey][1] = rules[theKey][1] + tests
                else:
                    rules[theKey] = []
                    rules[theKey].append("redirect")
                    rules[theKey].append(tests)
            elif type(key) == tuple:
                # We are not managing rules with several actions, just pass 
                # them 
                rules[key] = r
                #print("key----", key, rules[key])
            else:
                print(i, ") Not implented ", type(key))

        else:
            print(i, ") Not implented ", type(r))

        i = i + 1

    return (rules, more)


def constructActions(rules, more):
    actions = []
    for rule in list(rules.keys()):
        action = []
        #print("\n----------------------------")
        #print("rule", rule)
        #print("rules[rule]",rules[rule])
        #print("-----")
        #print(rules[rule][0])
        #print("-----")
        #printRule(rules[rule])
        #print("more",more)
        #print("rule",rule)
        #print("rule[rule]",rules[rule])
        act = []
        #if rule in more:
        #    action.append((rules[rule][0],
        #                  (rule, more[rule][0]), rules[rule][1]))
        if type(rule) == tuple:
            #print("rule---", rule)
            #print("rule---", rules[rule])
            action = rules[rule]
            #for r in rules[rule]:
            #    print("r...", r)
            #    if 'address' in r: 
            #        action.append(r) #('redirect', (r['address'],) , rules[rule][1]))
            #        #print(rules[rule][0])
            #        #print(rules[rule][2])
            #    elif 'mailbox' in r:
            #        action.append(r)#('fileinto', (r['mailbox'],) , rules[rule][1]))
            #        #print("0", rules[rule][0])
            #        #print("1", rules[rule][1])
            #        #print("2", rules[rule][2])
            #print("action---",action)
        else:
            #print("actions",rules[rule][0], rule, rules[rule][1])
            #if not rules[rule][0].startswith(('"', "'")):
            #    rules[rule][0] = '"%s"' % rules[rule][0]
            #if not rule.startswith(('"', "'")):
            #    theRule = '"%s"' % rule
            #else:
            theRule = rule
            #print("actions 2",rules[rule][0], theRule, rules[rule][1])
            action.append((rules[rule][0], (theRule,), rules[rule][1]))
            print("action///", action)
        # action.append(act)

        actions.append(action)
    # print "actions, ", actions
    return actions


def constructFilterSet(actions):
    moreSieve = ""
    print(actions)
    fs = FiltersSet("test")
    sieveContent = io.StringIO()
    for action in actions:
        print("cfS-> act ", action)
        print("type---", type(action))
        if type(action) == sievelib.commands.IfCommand: 
            #print("cfS-> act0 type tosieve", action.tosieve())
            #fs.addfilter(action.name, action['test'], action.children) 
            action.tosieve(target=sieveContent)
            #print(sieveContent.read())
            moreSieve = moreSieve + "# Filter:\n" + sieveContent.getvalue()
            #print("moreSieve", moreSieve)
        else:
            conditions = action[0][2]
            #print("cfSS-> cond", conditions)
            cond = []
            #print("cond....", cond)
            #print(conditions)
            for condition in conditions:
                #print("cfS condition -> ", condition)
                # print(type(condition))
                #print(condition.arguments)
                head = ()
                (key1, key2, key3) = list(condition.arguments.keys())
                #print("keys",key1, key2, key3)
                #print("keys",condition.arguments[key1], condition.arguments[key2], condition.arguments[key3])
                head = head + (condition.arguments['header-names'].strip('"'),
                        condition.arguments['match-type'].strip('"'),
                        condition.arguments['key-list'].strip('"'))#.decode('utf-8'))
                # We will need to take care of these .decode's
                #print("head", head)
                cond.append(head)
                #print("cond", cond)

            # print "cond ->", cond
            act = []
            for i in range(len(action[0][1])):
                act.append((action[0][0], action[0][1][i]))
            act.append(("stop",))
            #print("cfS cond ->", cond)
            #print("cfS act ->", act)
            aList = [()]
            #for a in cond[0]:
            #    print("cfS ",a)
            #    aList[0] = aList[0] + (a.strip('"'),)
            #print("cfS aList", aList)
            #print("cfS cond", cond)
            #print("cfS act", act)
            fs.addfilter("", cond, act)
            #fs.addfilter("", aList, act)
            # print "added!"

    return (fs, moreSieve)

def selectAction(p, M):  # header="", textHeader=""):
    i = 1
    txtResults = ""
    for r in p.result:
        if r.children:
            txtResults = txtResults + "%02d " % len(r.arguments['test'].arguments['tests'])
            if (type(r.children[0]) == sievelib.commands.FileintoCommand):
                txtResults = txtResults + "%02d) Folder  %s\n" % (i, r.children[0]['mailbox'])
            elif (type(r.children[0]) == sievelib.commands.RedirectCommand):
                txtResults = txtResults + "%02d) Address %s\n" % (i, r.children[0]['address'])
            else:
                txtResults = txtResults + "%02d) Not implemented %s\n" % (i, type(r.children[0]))
        else:
            txtResults = txtResults + "%02d) Not implemented %s\n" % (i, type(r))

        i = i + 1
    txtResults = txtResults + "99 %02d) New folder \n" % i
    txtResults = txtResults + "99 %02d) New redirection\n" % (i+1)


    for cad in sorted(txtResults.split('\n')):
        print(cad[3:], cad[:3])

    option = input("Select one: ")

    print(option, len(p.result))

    actions = []

    if (int(option) <= len(p.result)):
        action = p.result[int(option)-1].children

        for i in action:
            if 'mailbox' in i.arguments:
                actions.append(("fileinto", i.arguments['mailbox']))
            elif 'address'in i.arguments:
                actions.append(("redirect", i.arguments['address']))
            else:
                actions.append(("stop",))

        # print actions

        match = p.result[int(option)-1]['test']
        # print "match ", match
    elif (int(option) == len(p.result)+1):
        folder = selectFolder(M) #input("Name of the folder: ")
        print("Name ", folder)
        if (doFolderExist(folder, M)[0] != 'OK'):
            print("Folder ", folder, " does not exist")
            sys.exit()
        else:
            print("Let's go")
            actions.append(("fileinto", folder))
            actions.append(("stop",))
    elif (int(option) == len(p.result)+2):
        redir = input("Redirection to: ")
        print("Name ", redir)
        itsOK = input("It's ok? (y/n)")
        if (itsOK != 'y'):
            print(redir, " is wrong")
            sys.exit()
        else:
            print("Let's go")
            actions.append(("redirect", redir))
            actions.append(("stop",))

    return actions


def addToSieve(msg=""):
    config = loadImapConfig()[0]

    (SERVER, USER, PASSWORD, RULES, INBOX, FOLDER) = readImapConfig(config)

    # Make connections to server
    # Sieve client connection
    c = Client(SERVER)
    if not c.connect(USER, PASSWORD, starttls=True, authmech="PLAIN"):
        print("Connection failed")
        return 0
    M = makeConnection(SERVER, USER, PASSWORD)
    PASSWORD = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    M.select()

    #end = ""
    #while (not end):
    # Could we move this parsing part out of the while?
    script = c.getscript('sieve-script')
    p = Parser()
    p.parse(script)
    #print("p.result",p.result)

    (rules, more) = extractActions(p)

    # We are going to filter based on one message
    if not msg:
        msg = selectMessage(M)
    (keyword, filterCond) = selectHeaderAuto(M, msg)

    actions = selectAction(p, M)
    # actions[0][1] contains the rule selector
    # print("actions ", actions[0][1])
    # print(rules[actions[0][1].strip('"')])

    # For a manual selection option?
    # header= selectHeader()
    # keyword = selectKeyword(header)

    # Eliminate
    # conditions = []
    # conditions.append((keyword, ":contains", filterCond))

    #print("filtercond", filterCond)
    newActions = addRule(rules, more, keyword, filterCond, actions)

    #print("nA",newActions)
    #print("nA 0",newActions[0][0][2][0].tosieve())
    #print("nA 0")

    (fs, moreSieve) = constructFilterSet(newActions)

    sieveContent = io.StringIO()
    # We need to add the require in order to use the body section
    sieveContent.write('require ["body"];\n')
    # fs.tosieve(open(FILE_SIEVE, 'w'))
    #fs.tosieve()
    #print(moreSieve)
    #sys.exit()
    print(USER)
    fs.tosieve(sieveContent)
    sieveContent.write(moreSieve)
    with open(os.path.expanduser('~'+USER)+'/sieve/body.sieve') as f:
        sieveContent.write(f.read())
    print(sieveContent.getvalue())
#"""#Filter:
#if anyof (body :raw :contains "puntoclick.info") {
#    fileinto "Spam";
#    stop;
#}""")

    #import time
    #time.sleep(5)
    # Let's do a backup of the old sieve script
    name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    res  = c.putscript(name+'sogo', script)
    print("res",res)

    # Now we can put the new sieve filters in place
    # fSieve = open(FILE_SIEVE, 'r')
    # if not c.putscript('sogo', fSieve.read()):
    #print(sieveContent.getvalue())

    if not c.putscript('sieve-script', sieveContent.getvalue()):
        print("fail!")

    # Let's start the git backup

    repo = Repo(repoDir)
    index = repo.index

    print("listscripts",c.listscripts())
    listScripts=c.listscripts()
    print("listscripts",listScripts)
    if (listScripts != None):
        listScripts=listScripts[1]
        listScripts.sort() 
        print("listscripts",c.listscripts())
        print(listScripts[0])

        # script = listScripts[-1] # The last one
        sieveFile=c.getscript('sieve-script')
        file=open(repoDir+repoFile,'w')
        file.write(sieveFile)
        file.close()
        index.add(['*'])
        index.commit(name+'sogo')

        if len(listScripts)>6:
            # We will keep the last five ones (plus the active one)
            numScripts = len(listScripts) - 6
            i = 0
            while numScripts > 0:
                script = listScripts[i]
                c.deletescript(script)
                i = i + 1
                numScripts = numScripts - 1

    #end = input("More rules? (empty to continue) ")

def main():

    (config, nSec) = loadImapConfig()

    (SERVER, USER, PASSWORD, RULES, INBOX, FOLDER) = readImapConfig(config)

    # Make connections to server
    # Sieve client connection
    c = Client(SERVER)
    if not c.connect(USER, PASSWORD, starttls=True, authmech="PLAIN"):
        print("Connection failed")
        return 0
    else:
        print(c.listscripts())
    M = makeConnection(SERVER, USER, PASSWORD)
    PASSWORD = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    M.select()

    end = ""
    while (not end):
        # Could we move this parsing part out of the while?
        script = c.getscript('sieve-script')
        p = Parser()
        p.parse(script)

        (rules, more) = extractActions(p)

        # We are going to filter based on one message
        msg = selectMessage(M)
        (keyword, filterCond) = selectHeaderAuto(M, msg)

        actions = selectAction(p, M)
        # actions[0][1] contains the rule selector
        # print("actions ", actions[0][1])
        # print(rules[actions[0][1].strip('"')])

        # For a manual selection option?
        # header= selectHeader()
        # keyword = selectKeyword(header)

        # Eliminate
        # conditions = []
        # conditions.append((keyword, ":contains", filterCond))

        #print("filtercond", filterCond)
        newActions = addRule(rules, more, keyword, filterCond, actions)

        #print("nA",newActions)
        #print("nA 0",newActions[0][0][2][0].tosieve())
        #print("nA 0")

        fs = constructFilterSet(newActions)

        sieveContent = io.StringIO()
        # fs.tosieve(open(FILE_SIEVE, 'w'))
        # fs.tosieve()
        # sys.exit()
        fs.tosieve(sieveContent)

        #import time
        #time.sleep(5)
        # Let's do a backup of the old sieve script
        name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        res  = c.putscript(name+'sogo', script)
        print("res",res)

        # Now we can put the new sieve filters in place
        # fSieve = open(FILE_SIEVE, 'r')
        # if not c.putscript('sogo', fSieve.read()):
        #print(sieveContent.getvalue())

        if not c.putscript('sogo', sieveContent.getvalue()):
            print("fail!")

        # Let's start the git backup

        repo = Repo(repoDir)
        index = repo.index

        print("listscripts",c.listscripts())
        listScripts=c.listscripts()
        print("listscripts",listScripts)
        if (listScripts != None):
            listScripts=listScripts[1]
            listScripts.sort() 
            print("listscripts",c.listscripts())
            print(listScripts[0])

            # script = listScripts[-1] # The last one
            sieveFile=c.getscript('sogo')
            file=open(repoDir+repoFile,'w')
            file.write(sieveFile)
            file.close()
            index.add(['*'])
            index.commit(name+'sogo')

            if len(listScripts)>6:
       	        # We will keep the last five ones (plus the active one)
                numScripts = len(listScripts) - 6
                i = 0
                while numScripts > 0:
                    script = listScripts[i]
                    c.deletescript(script)
                    i = i + 1
                    numScripts = numScripts - 1

        end = input("More rules? (empty to continue) ")

if __name__ == "__main__":
    main()
