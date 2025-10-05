#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extension of the publishing module that integrates the publication cache.
Allows automatic storage of information about publications made.
"""

import logging
from socialModules.modulePublishing import Publisher
from socialModules.modulePublicationCache import PublicationCache


class PublisherWithCache(Publisher):
    def __init__(self, cache_file=None):
        """
        Initialize the publisher with integrated cache

        Args:
            cache_file: Custom cache file (optional)
        """
        super().__init__()
        self.publication_cache = PublicationCache(cache_file)

    def publish_and_cache(
        self, title, original_link, service, api_instance, comment=""
    ):
        """
        Publish content and store information in cache

        Args:
            title: Publication title
            original_link: Original content link
            service: Service to publish to (twitter, facebook, etc.)
            api_instance: Service API instance
            comment: Additional comment (optional)

        Returns:
            dict: Publication result with cache information
        """
        try:
            # Try to publish using the service API
            publish_result = api_instance.publishPost(title, original_link, comment)

            # Extract response link from result if available
            response_link = self._extract_response_link(publish_result, service)

            # Store in cache
            pub_id = self.publication_cache.add_publication(
                title=title,
                original_link=original_link,
                service=service,
                response_link=response_link,
            )

            result = {
                "success": True,
                "publication_id": pub_id,
                "response_link": response_link,
                "original_result": publish_result,
                "message": f"Published to {service} and stored in cache",
            }

            logging.info(f"Successful publication: {title} to {service}")
            return result

        except Exception as e:
            logging.error(f"Error publishing {title} to {service}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error publishing to {service}",
            }

    def _extract_response_link(self, publish_result, service):
        """
        Extract response link from publication result according to service

        Args:
            publish_result: Publication result
            service: Service where it was published

        Returns:
            str: Response link or None if it cannot be extracted
        """
        if not publish_result:
            return None

        try:
            # For Twitter
            if service.lower() == "twitter":
                if isinstance(publish_result, dict):
                    if "id" in publish_result:
                        return f"https://twitter.com/user/status/{publish_result['id']}"
                    elif "data" in publish_result and "id" in publish_result["data"]:
                        return f"https://twitter.com/user/status/{publish_result['data']['id']}"

            # For Facebook
            elif service.lower() == "facebook":
                if isinstance(publish_result, dict):
                    if "id" in publish_result:
                        return f"https://facebook.com/post/{publish_result['id']}"
                    elif "post_id" in publish_result:
                        return f"https://facebook.com/post/{publish_result['post_id']}"

            # For LinkedIn
            elif service.lower() == "linkedin":
                if isinstance(publish_result, dict) and "id" in publish_result:
                    return f"https://linkedin.com/feed/update/{publish_result['id']}"

            # For Mastodon
            elif service.lower() == "mastodon":
                if isinstance(publish_result, dict) and "url" in publish_result:
                    return publish_result["url"]

            # Try to extract generic URL
            if isinstance(publish_result, dict):
                for key in ["url", "link", "permalink", "web_url"]:
                    if key in publish_result:
                        return publish_result[key]

            # If it's a tuple (old format)
            if isinstance(publish_result, tuple) and len(publish_result) > 1:
                if isinstance(publish_result[1], dict) and "id" in publish_result[1]:
                    return f"https://{service}.com/post/{publish_result[1]['id']}"

        except Exception as e:
            logging.warning(f"Error extracting response link for {service}: {e}")

        return None

    def update_response_link_by_original(self, original_link, service, response_link):
        """
        Update response link of a publication by searching for original link

        Args:
            original_link: Original publication link
            service: Service where it was published
            response_link: New response link

        Returns:
            bool: True if any publication was updated
        """
        publications = self.publication_cache.get_publications_by_original_link(
            original_link
        )
        service_publications = [p for p in publications if p["service"] == service]

        updated = False
        for pub in service_publications:
            if self.publication_cache.update_response_link(pub["id"], response_link):
                updated = True

        return updated

    def get_publication_history(self, original_link):
        """
        Get publication history of a specific link

        Args:
            original_link: Original link to search for

        Returns:
            list: List of publications of that link on different services
        """
        return self.publication_cache.get_publications_by_original_link(original_link)

    def get_service_publications(self, service, limit=None):
        """
        Get publications from a specific service

        Args:
            service: Service name
            limit: Result limit (optional)

        Returns:
            list: List of service publications
        """
        publications = self.publication_cache.get_publications_by_service(service)

        if limit:
            publications = publications[:limit]

        return publications

    def search_cached_publications(self, query, field="title"):
        """
        Search in cached publications

        Args:
            query: Text to search for
            field: Field to search in

        Returns:
            list: Publications matching the search
        """
        return self.publication_cache.search_publications(query, field)

    def get_cache_stats(self):
        """
        Get publication cache statistics

        Returns:
            dict: Statistics by service
        """
        return self.publication_cache.get_stats()

    def export_publications(self, filename=None):
        """
        Export publications to CSV

        Args:
            filename: Filename (optional)

        Returns:
            str: Path of the created file
        """
        return self.publication_cache.export_to_csv(filename)


def main():
    """Module test function"""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("=== PublisherWithCache test ===")

    # Create publisher instance with cache
    publisher = PublisherWithCache()

    # Simulate publication (without real API)
    class MockAPI:
        def publishPost(self, title, link, comment):
            return {"id": "123456789", "success": True}

    mock_api = MockAPI()

    # Test publication with cache
    result = publisher.publish_and_cache(
        title="Test article",
        original_link="https://example.com/article",
        service="twitter",
        api_instance=mock_api,
    )

    print(f"Result: {result}")

    # Show statistics
    stats = publisher.get_cache_stats()
    print(f"Statistics: {stats}")

    # Search publications
    publications = publisher.search_cached_publications("test")
    print(f"Publications found: {len(publications)}")


if __name__ == "__main__":
    main()
