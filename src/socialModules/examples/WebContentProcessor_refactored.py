#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Refactored version of WebContentProcessor.py using unified publication logic

This version shows how the original code is simplified using the
publish_to_multiple_destinations method from moduleRules
"""

import logging
import os
import re
import time
import urllib.parse

import socialModules.moduleRules


class WebContentProcessorRefactored:
    """
    Refactored version of the web content processor
    """
    
    def __init__(self, from_email=None, to_email=None):
        self.from_email = from_email
        self.to_email = to_email
        self.rules = socialModules.moduleRules.moduleRules()
        self.rules.checkRules()
    
    def prepare_text(self, title, url, text, file_name):
        """
        Prepares text for publication (original method maintained)
        """
        # Original text preparation logic
        return text
    
    def publish_content(self, title, url, text, file_name):
        """
        Refactored version of the publication method
        
        BEFORE: Duplicated code with manual loop and individual error handling
        AFTER: Use of unified method
        """
        
        # Prepare content
        read_data = self.prepare_text(title, url, text, file_name)
        
        # Define social media destinations
        social_media_targets = {
            # "slack": "http://fernand0-errbot.slack.com/",
            # "pocket": "fernand0kobo", 
            "smtp": "ftricas@unizar.es",
        }
        
        # ORIGINAL CODE (commented):
        # for target in social_media_targets:
        #     try:
        #         logging.info(f"Posting to {target}")
        #         key = ("direct", "post", target, social_media_targets[target])
        #         apiSrc = self.rules.readConfigDst("", key, None, None)
        #         logging.info(f"Api: {apiSrc}")
        #         if hasattr(apiSrc, "setChannel"):
        #             apiSrc.setChannel("links")
        #         if "smtp" in target:
        #             apiSrc.fromaddr = self.from_email if self.from_email else "ftricas@elmundoesimperfecto.com"
        #             apiSrc.to = self.to_email if self.to_email else social_media_targets[target]
        #         msgLog = apiSrc.publishPost(title, url, read_data)
        #         logging.info(msgLog)
        #     except Exception as e:
        #         logging.error(f"Error posting to {target}: {e}")
        
        # REFACTORED CODE:
        results = self.rules.publish_to_multiple_destinations(
            destinations=social_media_targets,
            title=title,
            url=url,
            content=read_data,
            channel="links",  # For services that support it
            from_email=self.from_email or "ftricas@elmundoesimperfecto.com",
            to_email=self.to_email
        )
        
        # Process results if needed
        for service, result in results.items():
            if result['success']:
                logging.info(f"Successfully posted to {service}: {result['result']}")
            else:
                logging.error(f"Failed to post to {service}: {result['error']}")
        
        return results
    
    @staticmethod
    def is_url_skipped(url):
        """Método original mantenido sin cambios"""
        skip_domains = [
            "youtube.com",
            "vimeo.com", 
            "rtve.es",
            "slideshare.net",
            "npr.org",
            "tumblr.com",
            "bloomberg.com",
        ]
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.hostname
        
        if hostname:
            for skipped_domain in skip_domains:
                if skipped_domain in hostname:
                    return True
        return False
    
    @staticmethod
    def save_text_to_file(text_content, title, temp_dir="/tmp/"):
        """Método original mantenido sin cambios"""
        file_name = re.sub(r"[^a-zA-Z0-9]+", "-", title)
        file_name = time.strftime("%Y-%m-%d-", time.gmtime()) + file_name
        file_name_os = os.path.join(temp_dir, file_name[:80])
        
        with open(f"{file_name_os}.html", "w") as f:
            f.write(text_content)
        
        return file_name_os


def main():
    """Ejemplo de uso de la versión refactorizada"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create processor instance
    processor = WebContentProcessorRefactored(
        from_email="test@example.com",
        to_email="recipient@example.com"
    )
    
    # Example data
    title = "Interesting article about refactoring"
    url = "https://example.com/refactoring-article"
    text = "This article explains how to refactor duplicated code..."
    file_name = "refactoring-article"
    
    # Publish content
    print("Publishing content with refactored version...")
    results = processor.publish_content(title, url, text, file_name)
    
    # Show summary
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    print(f"\nSummary: {successful}/{total} successful publications")
    
    print("\nRefactoring advantages:")
    print("- Elimination of duplicated code")
    print("- Consistent error handling")
    print("- Centralized logging")
    print("- Easy maintenance")
    print("- Reusability in other projects")


if __name__ == "__main__":
    main()