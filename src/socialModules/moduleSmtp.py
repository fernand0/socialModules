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

# import getpass
# import keyring
# import keyrings


class moduleSmtp(Content):  # , Queue):
    def getKeys(self, config):
        SERVER = config.get(self.user, "server")
        USER = config.get(self.user, "user")
        PASSWORD = config.get(self.user, "token")
        PORT = config.get(self.user, "port")

        return (
            SERVER,
            PORT,
            USER,
            PASSWORD,
        )

    def initApi(self, keys):
        self.fromaddr = self.user
        self.server = keys[0]
        self.port = keys[1]
        self.user = keys[2]
        self.password = keys[3]
        self.to = ""

        client = None
        try:
            import ssl

            context = ssl._create_unverified_context()
            client = smtplib.SMTP_SSL(self.server, self.port, context=context)
            # client.starttls() #context=context)
            logging.info("     User: self.user")
            client.login(self.user, self.password)
            logging.info("     Logging OK")
        except:
            logging.warning("SMTP authentication failed!")
            logging.warning(f"Unexpected error: {sys.exc_info()[0]}")

        return client

    def _create_html_email(self, subject, link, body_content):
        """Creates an HTML email with a standard template."""
        body_content_br = body_content.replace("\n", "\n<br>")
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }}
                .header {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
                .link {{ margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">Title: {subject}</div>
                <div class="link">Url: <a href="{link}">{link}</a></div>
                <div class="content">
                    {body_content_br}
                </div>
            </div>
        </body>
        </html>
        """

    def publishApiPost(self, *args, **kwargs):
        comment = ""
        if args and len(args) == 3:
            post, link, comment = args
        if kwargs:
            more = kwargs
            # FIXME: We need to do something here
            thePost = more.get("post", "")
            api = more.get("api", "")
            post = api.getPostTitle(thePost)
            link = api.getPostLink(thePost)
        res = "Fail!"
        if True:
            if self.to:
                destaddr = self.to
                toaddrs = self.to
            else:
                destaddr = self.user
                toaddrs = self.user
            if hasattr(self, "fromaddr") and self.fromaddr:
                logging.info(f"{self.indent} 1")
                fromaddr = self.fromaddr
            else:
                logging.info(f"{self.indent} 2")
                fromaddr = self.user
            theUrl = link
            if post:
                subject = post.split("\n")[0]
            else:
                if link:
                    subject = link
                else:
                    subject = "No subject"

            msg = MIMEMultipart()
            msg["From"] = fromaddr
            msg["To"] = destaddr
            msg["Date"] = time.asctime(time.localtime(time.time()))
            msg["X-URL"] = theUrl
            msg["X-print"] = theUrl
            msg["Subject"] = subject

            # Construct the email body
            body_content = ""
            if comment:
                body_content = comment
            else:
                body_content = post

            htmlDoc = self._create_html_email(subject, link, body_content)

            if comment:
                msgLog = f"{self.indent} Doc: {htmlDoc}"
                logMsg(msgLog, 2, False)

            subtype = "html"
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
                smtpsrv = "localhost"
                server = smtplib.SMTP(smtpsrv)
                server.connect(smtpsrv, 587)
                server.starttls()
            else:
                server = self.client
                respN = server.noop()
                # logging.info(f"Noop: {respN}")
                if isinstance(respN, tuple):
                    respN = respN[0]
                if not (respN == 250):
                    logging.info(f"Noop: not")
                    import ssl

                    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    server = smtplib.SMTP_SSL(self.server, self.port)
                    # server.starttls(context=context)
                    server.login(self.user, self.password)

            # msgLog = f"From: {fromaddr} To:{toaddrs}"
            # logMsg(msgLog, 2, 0)
            # msgLog = f"Msg: {msg.as_string()[:250]}"
            # logMsg(msgLog, 2, 0)

            try:
                res = server.sendmail(fromaddr, toaddrs, msg.as_string())
            except:
                res = self.report(self.service, f"{post} {link}", post, sys.exc_info())

            if not res:
                res = "OK"
            # server.quit()

        else:
            res = self.report(self.service, "", "", sys.exc_info())

        return f"{res}"

    def getApiPostTitle(self, post):
        """
        Extract title from email post data
        For SMTP, this would typically be the subject line
        """
        if isinstance(post, dict):
            return post.get("subject", post.get("title", ""))
        elif isinstance(post, str):
            # If it's a string, use first line as title
            lines = post.split("\n")
            return lines[0] if lines else post[:50]
        return str(post)[:50]  # Fallback

    def getApiPostLink(self, post):
        """
        Extract link from email post data
        """
        if isinstance(post, dict):
            return post.get("url", post.get("link", ""))
        return ""

    def getPostContent(self, post):
        """
        Extract content from email post data
        """
        if isinstance(post, dict):
            return post.get("content", post.get("body", ""))
        elif isinstance(post, str):
            return post
        return str(post)

    def getPostId(self, post):
        """
        Get post ID for email (could be message ID)
        """
        if isinstance(post, dict):
            return post.get("id", post.get("message_id", ""))
        return ""

    def getSiteTitle(self):
        """
        Get site title for SMTP service
        """
        if hasattr(self, "user") and self.user:
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

    def register_specific_tests(self, tester):
        """Registers SMTP-specific tests with the ModuleTester."""
        tester.add_test("Basic Email", self._test_basic_email)
        tester.add_test("HTML Email", self._test_html_email)

    def get_user_info(self, client):
        if hasattr(self, "user"):
            return f"User: {self.user}"
        return "User: Unknown"

    def get_post_id_from_result(self, result):
        return None

    def _test_basic_email(self, api_src):
        """Tests sending a basic email."""
        print("\n=== Testing Basic Email ===")
        title = "Test Email from moduleSmtp"
        link = "https://example.com/test"
        comment = "This is a test email sent from the SMTP module."

        print(f"Sending email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  Comment: {comment}")

        result = api_src.publishPost(title, link, comment)
        print(f"Result: {result}")

    def _test_html_email(self, api_src):
        """Tests sending an HTML email."""
        print("\n=== Testing HTML Email ===")
        title = "HTML Test Email"
        link = "https://example.com/html-test"
        htmlContent = """
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
        """

        print(f"Sending HTML email:")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print(f"  HTML content length: {len(htmlContent)} chars")

        result = api_src.publishPost(title, link, htmlContent)
        print(f"Result: {result}")


def main():
    """
    Main function for testing moduleSmtp functionality using ModuleTester.
    """
    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    smtp_module = moduleSmtp()
    tester = ModuleTester(smtp_module)
    tester.run()


if __name__ == "__main__":
    main()
