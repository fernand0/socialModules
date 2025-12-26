#!/usr/bin/env python
"""
This is a skeleton file for creating new social media modules.
It provides a template with all the required methods that a module should implement.
To create a new module, copy this file, rename it to 'module<YourServiceName>.py',
and implement the methods according to the service's API.
"""

import logging
import sys

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleSkeleton(Content):
    """
    A skeleton class for new social media modules.
    It inherits from the Content class and provides a template for all the
    methods that a module should implement.
    """

    def getKeys(self, config):
        """
        Retrieves the API keys from the configuration file.
        The keys are specific to each service and user.
        """
        pass

    def initApi(self, keys):
        """
        Initializes the API client with the retrieved keys.
        This method should create and return an API client object.
        """
        pass

    def setApiPosts(self):
        """
        Fetches the user's posts from the social media service.
        If the service has channels/folders, this should fetch posts from the current channel.
        It should return a list of post objects.
        """
        pass

    def setApiFavs(self):
        """
        Fetches the user's favorite/liked posts.
        It should return a list of post objects.
        """
        pass

    def getChannels(self):
        """
        (Optional) Fetches the list of available channels/folders for the service.
        This is only necessary for services that have a concept of channels,
        folders, or similar content containers.
        """
        pass

    def setChannel(self, channel):
        """
        (Optional) Sets the current channel/folder for the service.
        """
        pass

    def getChannel(self):
        """
        (Optional) Gets the current channel/folder for the service.
        """
        pass

    def createChannel(self, channel_name):
        """
        (Optional) Creates a new channel/folder for the service.
        """
        pass

    def deleteChannel(self, channel_name):
        """
        (Optional) Deletes a channel/folder for the service.
        """
        pass

    def processReply(self, reply):
        """
        Processes the reply from the API after a publication.
        It should extract and return the URL of the new post.
        """
        pass

    def publishApiImage(self, *args, **kwargs):
        """
        Publishes a post with an image.
        It takes the post content and image data as arguments.
        """
        pass

    def publishApiPost(self, *args, **kwargs) -> dict:
        """
        Publishes content to the service.

        This method should return a dictionary with the following structure:
        ```python
        {
            "success": bool,          # True if the publication was successful, False otherwise.
            "post_url": str,          # The URL of the newly created post, if available. Empty string if not.
            "error_message": str,     # A descriptive error message if the publication failed. Empty string if successful.
            "raw_response": Any       # The raw response object from the API, for debugging.
        }
        ```
        """
        pass

    def deleteApiPosts(self, idPost):
        """
        Deletes a post by its ID.
        """
        pass

    def deleteApiFavs(self, idPost):
        """
        Unfavorites/unlikes a post by its ID.
        """
        pass

    def getPostTime(self, post):
        """
        Extracts the timestamp from a post object.
        """
        pass

    def getPostId(self, post):
        """
        Extracts the unique ID from a post object.
        """
        pass

    def getUrlId(self, post):
        """
        Extracts the ID from a URL.
        """
        pass

    def getSiteTitle(self):
        """
        Returns a title for the site/service (e.g., "My Twitter Feed").
        """
        pass

    def getApiPostTitle(self, post):
        """
        Extracts the title from an API post object.
        """
        pass

    def getApiPostUrl(self, post):
        """
        Extracts the URL from an API post object.
        """
        pass

    def getApiPostLink(self, post):
        """
        Extracts a shareable link from an API post object.
        """
        pass

    def extractPostLinks(self, post, linksToAvoid=""):
        """
        Extracts links from a post's content.
        """
        pass

    def getPostContent(self, post):
        """
        Extracts the main content from a post object.
        """
        pass

    def getPostContentLink(self, post):
        """
        Extracts a link from the main content of a post.
        """
        pass

    def search(self, text):
        """
        Searches for content on the social media service.
        """
        pass

    def register_specific_tests(self, tester):
        """
        Registers specific tests for this module with the ModuleTester.
        """
        pass

    def get_user_info(self, client):
        """
        Retrieves user information from the API client.
        """
        pass

    def get_post_id_from_result(self, result):
        """
        Extracts the post ID from the result of a publication operation.
        """
        pass


def main():
    """
    Main function for standalone execution and testing of the module.
    """
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
    )

    from socialModules.moduleTester import ModuleTester

    skeleton_module = moduleSkeleton()
    tester = ModuleTester(skeleton_module)
    tester.run()


if __name__ == "__main__":
    main()
