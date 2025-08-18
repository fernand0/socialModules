#!/usr/bin/env python

import smtplib
import sys
import time

from email import encoders
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import socialModules
from socialModules.configMod import *
from socialModules.moduleContent import *
# from socialModules.moduleQueue import *

#import getpass
#import keyring
#import keyrings

class moduleSmtp(Content): #, Queue):

    def getKeys(self, config):
        SERVER = config.get(self.user, "server")
        USER = config.get(self.user, "user")
        PASSWORD = config.get(self.user, "token")
        PORT = config.get(self.user, "port")

        return (SERVER, PORT, USER, PASSWORD,)

    def initApi(self, keys):
        self.fromaddr = self.user
        self.server = keys[0]
        self.port = keys[1]
        self.user = keys[2]
        self.password = keys[3]
        self.to = ''

        client = None
        try:
            import ssl
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            client = smtplib.SMTP_SSL(self.server, self.port)
            #client.starttls() #context=context)
            logging.info("     User: self.user")
            client.login(self.user, self.password)
            logging.info("     Logging OK")
        except:
            logging.warning("SMTP authentication failed!")
            logging.warning(f"Unexpected error: {sys.exc_info()[0]}")

        return client

    def publishApiPost(self, *args, **kwargs):
        comment = ""
        if args and len(args) == 3:
            post, link, comment = args
        if kwargs:
            more = kwargs
            # FIXME: We need to do something here
            thePost = more.get('post', '')
            api = more.get('api', '')
            post = api.getPostTitle(thePost)
            link = api.getPostLink(thePost)
        res = 'Fail!'
        if True:
            if self.to:
                destaddr = self.to
                toaddrs = self.to
            else:
                destaddr = self.user
                toaddrs = self.user
            if hasattr(self, 'fromaddr') and self.fromaddr:
                logging.info(f"{self.indent} 1")
                fromaddr = self.fromaddr
            else:
                logging.info(f"{self.indent} 2")
                fromaddr = self.user
            theUrl = link
            if post:
                subject = post.split('\n')[0]
            else:
                if link:
                    subject = link
                else:
                    subject = "No subject"

            msg = MIMEMultipart()
            msg['From']    = fromaddr
            msg['To']      = destaddr
            msg['Date']    = time.asctime(time.localtime(time.time()))
            msg['X-URL']   = theUrl
            msg['X-print'] = theUrl
            msg['Subject'] = subject

            htmlDoc = (f"<html><body>"
                       f"Title: {subject}<br />\n"
                       f"Url: {link}<br />\n"
                       f"{post}<br />\n"
                       f"</body></html>\n")

            if comment:
                htmlDoc = comment

                msgLog = (f"{self.indent} Doc: {htmlDoc}")
                logMsg(msgLog, 2, 0)


            subtype = 'html'
            # if htmlDoc.startswith('<'):
            #     subtype = 'html'
            # else:
            #     subtype = 'plain'

            adj = MIMEText(htmlDoc, _subtype=subtype)
            msg.attach(adj)

            #     adj = MIMEApplication(htmlDoc)
            #     encoders.encode_base64(adj)
            #     name = 'content'
            #     ext = '.html'

            #     adj.add_header('Content-Disposition',
            #                    f'attachment; filename="{name}{ext}"')
            #     adj.add_header('Content-Type','application/octet-stream')

            #     msg.attach(adj)

            #     if htmlDoc.startswith('<'):
            #         subtype = 'html'
            #     else:
            #         subtype = 'plain'

            #     adj = MIMEText(htmlDoc, _subtype=subtype)
            #     msg.attach(adj)
            # else:
            #     if htmlDoc.startswith('<'):
            #         subtype = 'html'
            #     else:
            #         subtype = 'plain'

            #     adj = MIMEText(htmlDoc, _subtype=subtype)
            #     msg.attach(adj)


            if not self.client:
                smtpsrv  = 'localhost'
                server = smtplib.SMTP(smtpsrv)
                server.connect(smtpsrv, 587)
                server.starttls()
            else:
                server = self.client
                respN = server.noop()
                logging.info(f"Noop: {respN}")
                if isinstance(respN, tuple):
                    respN = respN[0]
                if not (respN == 250):
                    logging.info(f"Noop: not")
                    import ssl
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    server = smtplib.SMTP_SSL(self.server, self.port)
                    #server.starttls(context=context)
                    server.login(self.user, self.password)

            msgLog = (f"From: {fromaddr} To:{toaddrs}")
            logMsg(msgLog, 2, 0)
            msgLog = (f"Msg: {msg.as_string()[:250]}")
            logMsg(msgLog, 2, 0)

            try:
                res = server.sendmail(fromaddr, toaddrs, msg.as_string())
            except:
                res = self.report(self.service,
                                    f"{post} {link}", post, sys.exc_info())

            if not res:
                res = "OK"
            # server.quit()

        else:
            res = self.report(self.service, '', '', sys.exc_info())

        return(f"{res}")

    def getPostTitle(self, post):
        """
        Extract title from email post data
        For SMTP, this would typically be the subject line
        """
        if isinstance(post, dict):
            return post.get('subject', post.get('title', ''))
        elif isinstance(post, str):
            # If it's a string, use first line as title
            lines = post.split('\n')
            return lines[0] if lines else post[:50]
        return str(post)[:50]  # Fallback

    def getPostLink(self, post):
        """
        Extract link from email post data
        """
        if isinstance(post, dict):
            return post.get('url', post.get('link', ''))
        return ''

    def getPostContent(self, post):
        """
        Extract content from email post data
        """
        if isinstance(post, dict):
            return post.get('content', post.get('body', ''))
        elif isinstance(post, str):
            return post
        return str(post)

    def getPostId(self, post):
        """
        Get post ID for email (could be message ID)
        """
        if isinstance(post, dict):
            return post.get('id', post.get('message_id', ''))
        return ''

    def getSiteTitle(self):
        """
        Get site title for SMTP service
        """
        if hasattr(self, 'user') and self.user:
            return f"SMTP ({self.user})"
        return "SMTP Service"

    def testConnection(self):
        """
        Test SMTP connection
        """
        try:
            if self.client:
                resp = self.client.noop()
                return True, f"Connection OK: {resp}"
            else:
                return False, "No client available"
        except Exception as e:
            return False, f"Connection failed: {e}"

def main():
    """
    Main function for testing moduleSmtp functionality.
    Provides various test scenarios similar to moduleMastodon.
    """
    
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    name = nameModule()
    rulesList = rules.selectRule(name)
    
    print("Available SMTP rules:")
    for i, rule in enumerate(rulesList):
        print(f"{i}) {rule}")

    if not rulesList:
        print("No SMTP rules found. Please configure SMTP in your rules.")
        return

    sel = int(input(f"Which rule to use? "))
    src = rulesList[sel]
    print(f"Selected: {src}")
    
    # Show available actions for this rule
    if src in rules.rules:
        for i, action in enumerate(rules.rules[src]):
            print(f"{i}) {action}")
        sel_action = int(input(f"Which action? "))
        action = rules.rules[src][sel_action]
    else:
        action = ('smtp', 'default_config')
    
    more = rules.more.get(src, {})
    indent = ""
    
    # Initialize SMTP module
    try:
        apiSrc = rules.readConfigSrc(indent, src, more)
        apiDst = rules.readConfigDst(indent, action, more, apiSrc)
        print(f"SMTP Client initialized: {apiDst.client is not None}")
        print(f"Server: {apiDst.server}:{apiDst.port}")
        print(f"User: {apiDst.user}")
    except Exception as e:
        print(f"Error initializing SMTP: {e}")
        return

    # Test scenarios - similar to moduleMastodon structure
    
    testingConnection = False
    if testingConnection:
        print("\n=== Testing SMTP Connection ===")
        try:
            if apiDst.client:
                resp = apiDst.client.noop()
                print(f"SMTP NOOP response: {resp}")
                print("✓ SMTP connection is working")
            else:
                print("✗ No SMTP client available")
        except Exception as e:
            print(f"✗ SMTP connection failed: {e}")
        return

    testingBasicEmail = False
    if testingBasicEmail:
        print("\n=== Testing Basic Email ===")
        title = "Test Email from moduleSmtp"
        link = "https://example.com/test"
        comment = "This is a test email sent from the SMTP module."
        
        print(f"Sending email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  Comment: {comment}")
        
        result = apiDst.publishPost(title, link, comment)
        print(f"Result: {result}")
        return

    testingHtmlEmail = False
    if testingHtmlEmail:
        print("\n=== Testing HTML Email ===")
        title = "HTML Test Email"
        link = "https://example.com/html-test"
        htmlContent = '''
        <html>
        <body>
            <h2>Test HTML Email</h2>
            <p>This is a <strong>test email</strong> with HTML content.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
            <p>Link: <a href="https://example.com/html-test">Click here</a></p>
            <hr>
            <p><em>Sent from moduleSmtp test</em></p>
        </body>
        </html>
        '''
        
        print(f"Sending HTML email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  HTML content length: {len(htmlContent)} chars")
        
        result = apiDst.publishPost(title, link, htmlContent)
        print(f"Result: {result}")
        return

    testingWebContent = False
    if testingWebContent:
        print("\n=== Testing Web Content Email ===")
        url = input("Enter URL to fetch and email (or press Enter for default): ").strip()
        if not url:
            url = 'https://httpbin.org/json'
        
        try:
            import requests
            print(f"Fetching content from: {url}")
            req = requests.get(url, timeout=10)
            req.raise_for_status()
            
            import time
            timestamp = time.asctime()
            title = f"Web content from {url}"
            
            print(f"Content length: {len(req.text)} chars")
            print(f"Content type: {req.headers.get('content-type', 'unknown')}")
            
            # Send content as email
            result = apiDst.publishPost(title, url, req.text[:1000])  # Limit content
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error fetching web content: {e}")
        return

    testingCacheIntegration = False
    if testingCacheIntegration:
        print("\n=== Testing Cache Integration ===")
        
        # Enable auto-cache
        apiDst.setAutoCache(True)
        print(f"Auto-cache enabled: {apiDst.getAutoCache()}")
        
        # Send test email with caching
        title = "Cache Integration Test"
        link = "https://example.com/cache-test"
        comment = "This email tests the publication cache integration."
        
        print("Sending email with auto-cache enabled...")
        result = apiDst.publishPost(title, link, comment)
        print(f"Result: {result}")
        
        # Check cache
        try:
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            smtp_pubs = cache.get_publications_by_service("smtp")
            print(f"SMTP publications in cache: {len(smtp_pubs)}")
            
            if smtp_pubs:
                latest = smtp_pubs[-1]
                print(f"Latest cached publication:")
                print(f"  Title: {latest['title']}")
                print(f"  Link: {latest['original_link']}")
                print(f"  Service: {latest['service']}")
                print(f"  Date: {latest['publication_date']}")
        except Exception as e:
            print(f"Error checking cache: {e}")
        return

    testingMultipleEmails = False
    if testingMultipleEmails:
        print("\n=== Testing Multiple Emails ===")
        
        emails = [
            ("Test Email 1", "https://example.com/1", "First test email"),
            ("Test Email 2", "https://example.com/2", "Second test email"),
            ("Test Email 3", "https://example.com/3", "Third test email"),
        ]
        
        for i, (title, link, comment) in enumerate(emails, 1):
            print(f"Sending email {i}/3: {title}")
            result = apiDst.publishPost(title, link, comment)
            print(f"  Result: {result}")
            
            # Small delay between emails
            import time
            time.sleep(1)
        
        print("All emails sent!")
        return

    testingErrorHandling = False
    if testingErrorHandling:
        print("\n=== Testing Error Handling ===")
        
        # Test with invalid recipient
        original_user = apiDst.user
        apiDst.user = "invalid@nonexistent-domain-12345.com"
        
        print("Testing with invalid recipient...")
        result = apiDst.publishPost("Error Test", "https://example.com", "This should fail")
        print(f"Result with invalid recipient: {result}")
        
        # Restore original user
        apiDst.user = original_user
        return

    # Interactive testing mode (default)
    testingInteractive = True
    if testingInteractive:
        print("\n=== Interactive SMTP Testing ===")
        print("Available test modes:")
        print("1. Basic email test")
        print("2. HTML email test") 
        print("3. Web content email")
        print("4. Cache integration test")
        print("5. Multiple emails test")
        print("6. Connection test")
        print("7. Error handling test")
        print("8. Custom email")
        
        try:
            choice = int(input("Select test mode (1-8): "))
            
            if choice == 1:
                testingBasicEmail = True
            elif choice == 2:
                testingHtmlEmail = True
            elif choice == 3:
                testingWebContent = True
            elif choice == 4:
                testingCacheIntegration = True
            elif choice == 5:
                testingMultipleEmails = True
            elif choice == 6:
                testingConnection = True
            elif choice == 7:
                testingErrorHandling = True
            elif choice == 8:
                print("\n=== Custom Email ===")
                title = input("Email title: ").strip() or "Custom Test Email"
                link = input("Link (optional): ").strip() or "https://example.com"
                comment = input("Message/Comment: ").strip() or "Custom test message"
                
                # Ask about cache
                cache_choice = input("Enable auto-cache? (y/N): ").lower()
                if cache_choice == 'y':
                    apiDst.setAutoCache(True)
                    print("Auto-cache enabled")
                
                print(f"\nSending custom email:")
                print(f"  Title: {title}")
                print(f"  Link: {link}")
                print(f"  Message: {comment}")
                
                result = apiDst.publishPost(title, link, comment)
                print(f"Result: {result}")
            else:
                print("Invalid choice")
                return
                
        except ValueError:
            print("Invalid input")
            return
        except KeyboardInterrupt:
            print("\nTest cancelled by user")
            return
    
    # Re-run the selected test
    if testingConnection:
        print("\n=== Testing SMTP Connection ===")
        try:
            if apiDst.client:
                resp = apiDst.client.noop()
                print(f"SMTP NOOP response: {resp}")
                print("✓ SMTP connection is working")
            else:
                print("✗ No SMTP client available")
        except Exception as e:
            print(f"✗ SMTP connection failed: {e}")
    
    elif testingBasicEmail:
        print("\n=== Testing Basic Email ===")
        title = "Test Email from moduleSmtp"
        link = "https://example.com/test"
        comment = "This is a test email sent from the SMTP module."
        
        print(f"Sending email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  Comment: {comment}")
        
        result = apiDst.publishPost(title, link, comment)
        print(f"Result: {result}")
    
    elif testingHtmlEmail:
        print("\n=== Testing HTML Email ===")
        title = "HTML Test Email"
        link = "https://example.com/html-test"
        htmlContent = '''
        <html>
        <body>
            <h2>Test HTML Email</h2>
            <p>This is a <strong>test email</strong> with HTML content.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
            <p>Link: <a href="https://example.com/html-test">Click here</a></p>
            <hr>
            <p><em>Sent from moduleSmtp test</em></p>
        </body>
        </html>
        '''
        
        print(f"Sending HTML email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  HTML content length: {len(htmlContent)} chars")
        
        result = apiDst.publishPost(title, link, htmlContent)
        print(f"Result: {result}")
    
    elif testingWebContent:
        print("\n=== Testing Web Content Email ===")
        url = 'https://httpbin.org/json'  # Default URL for testing
        
        try:
            import requests
            print(f"Fetching content from: {url}")
            req = requests.get(url, timeout=10)
            req.raise_for_status()
            
            import time
            timestamp = time.asctime()
            title = f"Web content from {url}"
            
            print(f"Content length: {len(req.text)} chars")
            print(f"Content type: {req.headers.get('content-type', 'unknown')}")
            
            # Send content as email
            result = apiDst.publishPost(title, url, req.text[:1000])  # Limit content
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error fetching web content: {e}")
    
    elif testingCacheIntegration:
        print("\n=== Testing Cache Integration ===")
        
        # Enable auto-cache
        apiDst.setAutoCache(True)
        print(f"Auto-cache enabled: {apiDst.getAutoCache()}")
        
        # Send test email with caching
        title = "Cache Integration Test"
        link = "https://example.com/cache-test"
        comment = "This email tests the publication cache integration."
        
        print("Sending email with auto-cache enabled...")
        result = apiDst.publishPost(title, link, comment)
        print(f"Result: {result}")
        
        # Check cache
        try:
            from socialModules.modulePublicationCache import PublicationCache
            cache = PublicationCache()
            smtp_pubs = cache.get_publications_by_service("smtp")
            print(f"SMTP publications in cache: {len(smtp_pubs)}")
            
            if smtp_pubs:
                latest = smtp_pubs[-1]
                print(f"Latest cached publication:")
                print(f"  Title: {latest['title']}")
                print(f"  Link: {latest['original_link']}")
                print(f"  Service: {latest['service']}")
                print(f"  Date: {latest['publication_date']}")
        except Exception as e:
            print(f"Error checking cache: {e}")
    
    elif testingMultipleEmails:
        print("\n=== Testing Multiple Emails ===")
        
        emails = [
            ("Test Email 1", "https://example.com/1", "First test email"),
            ("Test Email 2", "https://example.com/2", "Second test email"),
            ("Test Email 3", "https://example.com/3", "Third test email"),
        ]
        
        for i, (title, link, comment) in enumerate(emails, 1):
            print(f"Sending email {i}/3: {title}")
            result = apiDst.publishPost(title, link, comment)
            print(f"  Result: {result}")
            
            # Small delay between emails
            import time
            time.sleep(1)
        
        print("All emails sent!")
    
    elif testingErrorHandling:
        print("\n=== Testing Error Handling ===")
        
        # Test with invalid recipient
        original_user = apiDst.user
        apiDst.user = "invalid@nonexistent-domain-12345.com"
        
        print("Testing with invalid recipient...")
        result = apiDst.publishPost("Error Test", "https://example.com", "This should fail")
        print(f"Result with invalid recipient: {result}")
        
        # Restore original user
        apiDst.user = original_user


if __name__ == '__main__':
    main()

