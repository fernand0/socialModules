#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module to manage a publication cache that stores:
- Publication title
- Original link
- Service response link (if available)
- Service where it was published
- Publication date
"""

import json
import os
import pickle
import logging
from datetime import datetime
from socialModules.configMod import *


class PublicationCache:

    def __init__(self, cache_file=None):
        """
        Initialize the publication cache

        Args:
            cache_file: File to store the cache. If not specified,
                       uses a default file in DATADIR
        """
        if cache_file:
            self.cache_file = cache_file
        else:
            self.cache_file = os.path.join(DATADIR, "publication_cache.json")

        self.publications = self._load_cache()

    def _load_cache(self):
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error loading cache: {e}. Starting empty cache.")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.publications, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logging.error(f"Error saving cache: {e}")
            return False

    def add_publication(self, title, original_link, service, response_link=None,
                       publication_date=None, user=None):
        """
        Add a new publication to the cache

        Args:
            title: Publication title
            original_link: Original content link
            service: Service where it was published (twitter, facebook, etc.)
            response_link: Service response link (optional)
            publication_date: Publication date (optional, uses current date if not specified)

        Returns:
            str: Unique ID of the added publication
        """
        if publication_date is None:
            publication_date = datetime.now().isoformat()

        logging.info(f"Adding publication with title: {title}, service: {service}, user: {user}")

        # Generate unique ID based on timestamp and service
        pub_id = f"{service}_{int(datetime.now().timestamp())}"

        publication = {
            'id': pub_id,
            'title': title,
            'original_link': original_link,
            'service': service,
            'user': user,
            'response_link': response_link,
            'publication_date': publication_date
        }

        logging.debug(f"Publication data: {publication}")

        self.publications[pub_id] = publication

        if self._save_cache():
            logging.info(f"Publication added: {title} in {service}")
            return pub_id
        else:
            logging.error(f"Error saving publication: {title}")
            return None

    def update_response_link(self, pub_id, response_link):
        """
        Update the response link of an existing publication

        Args:
            pub_id: Publication ID
            response_link: New response link

        Returns:
            bool: True if updated successfully
        """
        if pub_id in self.publications:
            self.publications[pub_id]['response_link'] = response_link
            if self._save_cache():
                logging.info(f"Response link updated for {pub_id}")
                return True

        logging.warning(f"Publication {pub_id} not found")
        return False

    def get_publication(self, pub_id):
        """
        Get a publication by its ID

        Args:
            pub_id: Publication ID

        Returns:
            dict: Publication data or None if it doesn't exist
        """
        return self.publications.get(pub_id)

    def get_publications_by_service(self, service):
        """
        Get all publications from a specific service

        Args:
            service: Service name

        Returns:
            list: List of publications from the service
        """
        return [pub for pub in self.publications.values() if pub['service'] == service]

    def get_publications_by_original_link(self, original_link):
        """
        Search publications by original link

        Args:
            original_link: Original link to search for

        Returns:
            list: List of publications with that original link
        """
        return [pub for pub in self.publications.values()
                if pub['original_link'] == original_link]

    def search_publications(self, query, field='title'):
        """
        Search publications by text in a specific field

        Args:
            query: Text to search for
            field: Field to search in ('title', 'original_link', 'service')

        Returns:
            list: List of matching publications
        """
        results = []
        query_lower = query.lower()

        for pub in self.publications.values():
            if field in pub and query_lower in str(pub[field]).lower():
                results.append(pub)

        return results

    def delete_publication(self, pub_id):
        """
        Delete a publication from the cache

        Args:
            pub_id: ID of the publication to delete

        Returns:
            bool: True if deleted successfully
        """
        if pub_id in self.publications:
            del self.publications[pub_id]
            if self._save_cache():
                logging.info(f"Publication {pub_id} deleted")
                return True

        logging.warning(f"Publication {pub_id} not found for deletion")
        return False

    def get_all_publications(self, sort_by='publication_date', reverse=True):
        """
        Get all publications sorted

        Args:
            sort_by: Field to sort by
            reverse: Whether to sort in descending order

        Returns:
            list: Sorted list of publications
        """
        publications = list(self.publications.values())

        try:
            publications.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
        except (TypeError, KeyError):
            logging.warning(f"Could not sort by {sort_by}")

        return publications

    def get_stats(self):
        """
        Get cache statistics

        Returns:
            dict: Publication statistics by service
        """
        stats = {}

        for pub in self.publications.values():
            service = pub['service']
            if service not in stats:
                stats[service] = {
                    'total': 0,
                    'with_response_link': 0,
                    'without_response_link': 0
                }

            stats[service]['total'] += 1

            if pub.get('response_link'):
                stats[service]['with_response_link'] += 1
            else:
                stats[service]['without_response_link'] += 1

        return stats

    def export_to_csv(self, filename=None):
        """
        Export publications to a CSV file

        Args:
            filename: CSV filename (optional)

        Returns:
            str: Path of the created file or None if there was an error
        """
        import csv

        if filename is None:
            filename = os.path.join(DATADIR, "publications_export.csv")

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'original_link', 'service', 'user',
                             'response_link', 'publication_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for pub in self.publications.values():
                    row = {field: pub.get(field, '') for field in fieldnames}
                    writer.writerow(row)

            logging.info(f"Publications exported to {filename}")
            return filename

        except IOError as e:
            logging.error(f"Error exporting to CSV: {e}")
            return None


def main():
    """Module test function"""

    # Configure logging
    logging.basicConfig(level=logging.DEBUG,
                       format='%(asctime)s - %(levelname)s - %(message)s')

    # Create cache instance
    cache = PublicationCache()

    # Usage example
    print("=== PublicationCache module test ===")

    # Add some test publications
    pub1_id = cache.add_publication(
        title="Interesting article about Python",
        original_link="https://example.com/python-article",
        service="twitter",
        user="testuser",
        response_link="https://twitter.com/user/status/123456"
    )

    pub2_id = cache.add_publication(
        title="Git Tutorial",
        original_link="https://example.com/git-tutorial",
        service="facebook",
        user="testuser2"
    )

    # Update response link
    cache.update_response_link(pub2_id, "https://facebook.com/post/789012")

    # Show statistics
    stats = cache.get_stats()
    print(f"\nStatistics: {stats}")

    # Search publications
    python_posts = cache.search_publications("Python")
    print(f"\nPython publications: {len(python_posts)}")

    # Show all publications
    all_pubs = cache.get_all_publications()
    print(f"\nTotal publications: {len(all_pubs)}")

    for pub in all_pubs:
        print(f"- {pub['title']} ({pub['service']})")


if __name__ == "__main__":
    main()
