#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script generates a Markdown list of links published on Twitter for a given date,
using the data from the publication cache.
"""

import sys
from datetime import datetime

from socialModules.modulePublicationCache import PublicationCache


def get_twitter_links_by_date(date_str):
    """
    Retrieves Twitter links for a specific date from the publication cache.

    Args:
        date_str (str): The date in 'YYYY-MM-DD' format.

    Returns:
        list: A list of dictionaries, each containing the 'title' and 'original_link'
              of a Twitter publication for the given date.
    """
    try:
        # Validate the date format
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print("Error: Invalid date format. Please use 'YYYY-MM-DD'.")
        return []

    # Initialize the publication cache
    cache = PublicationCache()
    
    # Get all publications from Twitter
    twitter_publications = cache.get_publications_by_service('twitter')

    # Filter publications by the selected date
    links_for_date = []
    for pub in twitter_publications:
        pub_date_str = pub.get('publication_date', '').split('T')[0]
        try:
            pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
            if pub_date == selected_date:
                links_for_date.append({
                    'title': pub.get('title', 'No Title'),
                    'original_link': pub.get('original_link', '#')
                })
        except (ValueError, TypeError):
            # Ignore publications with invalid date formats
            continue
            
    return links_for_date

def generate_markdown_list(links):
    """
    Generates a Markdown list from a list of links and titles.

    Args:
        links (list): A list of dictionaries with 'title' and 'original_link'.

    Returns:
        str: A Markdown-formatted string representing the list of links.
    """
    if not links:
        return "No Twitter links found for the specified date."

    markdown_list = ""
    for link in links:
        markdown_list += f"- [{link['title']}]({link['original_link']})\n"
    
    return markdown_list

def main():
    """
    Main function to execute the script.
    It expects a date as a command-line argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python list_twitter_links_by_date.py YYYY-MM-DD")
        sys.exit(1)

    date_str = sys.argv[1]
    
    # Get the links for the specified date
    twitter_links = get_twitter_links_by_date(date_str)
    
    # Generate and print the Markdown list
    markdown_output = generate_markdown_list(twitter_links)
    print(markdown_output)

if __name__ == "__main__":
    main()
