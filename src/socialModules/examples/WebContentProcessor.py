#!/usr/bin/env python

# pip install readability-lxml
import argparse
import logging
import os
import re
import time
import urllib.parse

import html2text

# pip install pytidylib
import requests

import socialModules
import socialModules.moduleHtml
import socialModules.moduleRules
import socialModules.moduleSlack
from socialModules.configMod import *

API_URL_PREFIX = "https://www.instapaper.com/api/1"
ADD_BOOKMARK = "/bookmarks/add"
ARCHIVE_BOOKMARK = "/bookmarks/archive"
GET_TEXT_BOOKMARK = "/bookmarks/get_text"


class Alarm(Exception):
    pass


def alarm_handler(signum, frame):
    raise Alarm


def _parse_arguments():
    parser = argparse.ArgumentParser(description="Process a URL and send it to Kindle.")
    parser.add_argument("url", help="The URL to process.")
    parser.add_argument("-txt", action="store_true", help="Process as plain text.")
    parser.add_argument(
        "-rea", action="store_true", help="Process as readable text and mail."
    )
    parser.add_argument(
        "-reau",
        action="store_true",
        help="Process as readable text and mail (unconditional).",
    )
    parser.add_argument(
        "--referrer", dest="referer", help="Optional referrer URL."
    )  # Renamed to referrer
    parser.add_argument("--from-email", help="Email address for sender.")
    parser.add_argument("--to-email", help="Email address for recipient.")

    args = parser.parse_args()

    # Determine the processing mode
    processing_mode = None
    if args.txt:
        processing_mode = "txt"
    elif args.rea:
        processing_mode = "rea"
    elif args.reau:
        processing_mode = "reau"

    return (
        args.url,
        processing_mode,
        args.referer,
        args.from_email,
        args.to_email,
    )  # args.referer remains as the parsed argument name


class UrlLogger:
    def __init__(self, log_file_path="~/usr/var/data/urls.txt"):
        self.log_file_path = os.path.expanduser(log_file_path)

    def check_and_log_url(self, url, processing_mode, title=None):
        # Duplication check
        if (
            processing_mode is not None and processing_mode != "reau"
        ):  # Only check for duplication if not in unconditional mode
            logging.info("Checking if duplicated")
            try:
                with open(self.log_file_path, "rb") as f:
                    lines = f.readlines()
                    for i in range(200):  # Check last 200 lines
                        if lines and str(lines[-1 - i]).find(url) > 0:
                            logging.info("Dupe!")
                            return False  # Indicate duplicate found
            except FileNotFoundError:
                logging.info(
                    f"URL log file not found: {self.log_file_path}. Creating it."
                )
            except Exception as e:
                logging.error(f"Error checking for duplicate URLs: {e}")

        # Log URL
        if (
            title is not None
        ):  # Only log if a title is provided (i.e., after content processing)
            try:
                with open(self.log_file_path, "a") as f:
                    date = time.asctime(time.localtime(time.time()))
                    line = f"{url}\t{title}\t{date}\n"
                    f.write(line)
            except Exception as e:
                logging.error(f"Error logging URL to file: {e}")
        return True  # No duplicate found or logging successful


class ContentFetcher:
    def __init__(self):
        pass

    def download_and_clean_content(self, url, html_processor):
        text_content = ""
        title = ""
        file_name = ""
        file_name_os = ""
        res = None  # Initialize res to None

        if WebContentProcessor.is_url_skipped(url):
            logging.info("Not downloading " + url)
            title = "Not downloaded " + url
            return text_content, title, file_name, file_name_os, "Skipped"

        if url.find("ojs") >= 0:
            url = url.replace("view", "download")

        try:
            response, moreContent = html_processor.downloadUrl(url)
            logging.info(f"Response: {response}")

            if response and response.status_code != 200:
                logging.error(
                    f"Error: HTTP Status Code {response.status_code} for {url}"
                )
                return (
                    text_content,
                    title,
                    file_name,
                    file_name_os,
                    f"HTTP Error {response.status_code}",
                )

            # Dealing with redirections and so on
            if response:
                url = html_processor.cleanUrl(response.url)

            text = ""
            if moreContent:
                pos = response.text.find("</html>")
                text = response.text[:pos] + moreContent + "</html>"
            else:
                if response:
                    text = response.text

            if not text:
                res = "Fail!"
                logging.error(f"Error: No content downloaded for {url}")
                return text_content, title, file_name, file_name_os, "No content"
            elif "JavaScript is not available" in text:
                text_content = ""
                title = "No title because of Javascript rendering"
                logging.warning(
                    f"Warning: JavaScript not available for {url}. Content might be incomplete."
                )
                res = "JS not available"
            else:
                text_content, title = html_processor.cleanDocument(text, url, response)

                if title == "[no-title]":
                    title = ""
                res = "Success"

            if text_content:
                file_name, file_name_os = WebContentProcessor.save_text_to_file(
                    text_content, title
                )

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while downloading {url}: {e}")
            return text_content, title, file_name, file_name_os, f"Network Error: {e}"
        except Exception:
            logging.exception("An unexpected error occurred during content processing")

        return text_content, title, file_name, file_name_os, res


class SocialMediaPoster:
    def __init__(self, from_email=None, to_email=None):
        self.from_email = from_email
        self.to_email = to_email

    def prepare_text(self, title, url, text_content, file_name):
        text_maker = html2text.HTML2Text()
        text_maker.inline_links = False
        text_maker.links_each_paragraph = False
        read_data = text_maker.handle(text_content)
        # ext = '.txt'
        # mail_sent_successfully = self.email_sender.send_mail(title, url, read_data, file_name, '.txt')
        # if not mail_sent_successfully:
        #     res = "Error al enviar el correo."
        #     logging.error(f"Mail sending failed: {res}")
        # else:
        #     res = "Enviado!"
        #     logging.info(f"Mail sending successful: {res}")
        return read_data

    def post_to_social_media(self, title, url, processing_mode, myText, file_name):
        if processing_mode is None:
            return

        read_data = self.prepare_text(title, url, myText, file_name)

        social_media_targets = {
            # "slack": "http://fernand0-errbot.slack.com/",
            # "pocket": "fernand0kobo",
            "smtp": "ftricas@unizar.es",
        }

        rules = socialModules.moduleRules.moduleRules()
        rules.checkRules()
        for target in social_media_targets:
            try:
                logging.info(f"Posting to {target}")
                # key = next(x for x in rules.rules.keys())
                # logging.info(f"Key {key}")
                # apiSrc = rules.readConfigSrc("", key, rules.more[key])
                key = ("direct", "post", target, social_media_targets[target])
                apiSrc = rules.readConfigDst("", key, None, None)
                logging.info(f"Api: {apiSrc}")
                if hasattr(apiSrc, "setChannel"):
                    apiSrc.setChannel("links")  # FIXME

                if "smtp" in target:
                    apiSrc.fromaddr = (
                        self.from_email
                        if self.from_email
                        else "ftricas@elmundoesimperfecto.com"
                    )
                    apiSrc.to = (
                        self.to_email if self.to_email else social_media_targets[target]
                    )
                msgLog = apiSrc.publishPost(title, url, read_data)
                logging.info(msgLog)
            except Exception as e:
                logging.error(f"Error posting to {target}: {e}")


class WebContentProcessor:
    @staticmethod
    def is_url_skipped(url):
        skip_domains = [
            "youtube.com",
            "vimeo.com",
            "rtve.es",
            "slideshare.net",
            "npr.org",
            "tumblr.com",
            "bloomberg.com",
        ]
        parsed_url = urllib.parse.urlparse(url)  # Use urllib.parse directly
        hostname = parsed_url.hostname

        if hostname:
            for skipped_domain in skip_domains:
                if skipped_domain in hostname:
                    return True
        return False

    @staticmethod
    def save_text_to_file(text_content, title, temp_dir="/tmp/"):
        file_name = re.sub(r"[^a-zA-Z0-9]+", "-", title)
        file_name = time.strftime("%Y-%m-%d-", time.gmtime()) + file_name
        file_name_os = os.path.join(temp_dir, file_name[:80])

        # Write the html response to local file
        with open(f"{file_name_os}.html", "w") as f:
            f.write(text_content)

        return file_name, file_name_os

    def __init__(self, log_file="/tmp/traer.log", from_email=None, to_email=None):
        self._setup_logging(log_file)
        self.html_processor = socialModules.moduleHtml.moduleHtml()  # Initialize once
        self.from_email = from_email
        self.to_email = to_email

    def _setup_logging(self, log_file):
        logging.basicConfig(
            filename=log_file, level=logging.DEBUG, format="%(asctime)s %(message)s"
        )

    def process_url(self, url, processing_mode, referrer):
        logging.info(
            f"Processing URL: {url}, Mode: {processing_mode}, Referrer: {referrer}"
        )

        cleaned_url = self.html_processor.cleanUrl(url)
        logging.info(cleaned_url)

        if not UrlLogger().check_and_log_url(cleaned_url, processing_mode):
            logging.info("URL is a duplicate or logging failed. Exiting.")
            return 0

        myText, title, file_name, file_name_os, download_status = (
            ContentFetcher().download_and_clean_content(
                cleaned_url, self.html_processor
            )
        )

        if download_status not in ["Success", "JS not available", "Skipped"]:
            logging.error(
                f"Critical error during download or cleaning: {download_status}. Exiting."
            )
            social_media_poster = SocialMediaPoster(self.from_email, self.to_email)
            error_title = cleaned_url  # Changed to cleaned_url
            error_body = f"Downloading not possible for URL: {cleaned_url}\nError: {download_status}"
            social_media_poster.post_to_social_media(
                error_title, cleaned_url, "smtp", error_body, ""
            )
            return 1

        social_media_poster = SocialMediaPoster(self.from_email, self.to_email)
        mail_result = None
        # if processing_mode == 'rea' or processing_mode == 'reau':
        #     mail_result = social_media_poster.send_email_notification(title, cleaned_url, myText, file_name)
        myText = f"{title}\n{myText}"
        social_media_poster.post_to_social_media(
            title, cleaned_url, processing_mode, myText, file_name
        )
        UrlLogger().check_and_log_url(
            cleaned_url, processing_mode, title
        )  # Log with title

        final_message = mail_result if mail_result is not None else "Procesado!"
        final_message = f"{final_message} {cleaned_url}"
        logging.info(final_message)
        return 0


def main():
    url, processing_mode, referrer, from_email, to_email = _parse_arguments()
    processor = WebContentProcessor(from_email=from_email, to_email=to_email)
    processor.process_url(url, processing_mode, referrer)


if __name__ == "__main__":
    main()
