#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example usage of the publication cache system.
Shows how to integrate the new functionality with the existing system.
"""

import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialModules.modulePublishingWithCache import PublisherWithCache
from socialModules.modulePublicationCache import PublicationCache


def demo_basic_usage():
    """Basic demonstration of cache usage"""
    
    print("=== Basic publication cache demonstration ===\n")
    
    # Create cache
    cache = PublicationCache()
    
    # Add some example publications
    print("1. Adding example publications...")
    
    pub1 = cache.add_publication(
        title="Introduction to Python for beginners",
        original_link="https://myblog.com/python-beginners",
        service="twitter",
        response_link="https://twitter.com/user/status/123456789"
    )
    
    pub2 = cache.add_publication(
        title="Complete Git and GitHub guide",
        original_link="https://myblog.com/git-github-guide",
        service="facebook",
        response_link="https://facebook.com/post/987654321"
    )
    
    pub3 = cache.add_publication(
        title="Introduction to Python for beginners",  # Same article
        original_link="https://myblog.com/python-beginners",
        service="linkedin"  # But on different site
    )
    
    print(f"Publications added: {pub1}, {pub2}, {pub3}\n")
    
    # Show statistics
    print("2. Publication statistics:")
    stats = cache.get_stats()
    for service, data in stats.items():
        print(f"   {site}: {data['total']} publications "
              f"({data['with_response_link']} with response link)")
    print()
    
    # Search publications
    print("3. Publication search:")
    python_posts = cache.search_publications("Python")
    print(f"   Python publications: {len(python_posts)}")
    for post in python_posts:
        print(f"   - {post['title']} on {post['service']}")
    print()
    
    # Search by original link
    print("4. Specific article history:")
    history = cache.get_publications_by_original_link("https://myblog.com/python-beginners")
    print(f"   The Python article was published on {len(history)} sites:")
    for post in history:
        response = post['response_link'] or "No response link"
        print(f"   - {post['service']}: {response}")
    print()


def demo_integration_with_existing_system():
    """Demonstration of integration with existing system"""
    
    print("=== Integration with existing system ===\n")
    
    # Create publisher with cache
    publisher = PublisherWithCache()
    
    # Simulate APIs from different services
    class MockTwitterAPI:
        def publishPost(self, title, link, comment):
            return {
                'id': '1234567890123456789',
                'text': f"{title} {link}",
                'created_at': '2024-01-15T10:30:00Z'
            }
    
    class MockFacebookAPI:
        def publishPost(self, title, link, comment):
            return {
                'post_id': 'user_987654321',
                'message': f"{title}\n{link}"
            }
    
    class MockLinkedInAPI:
        def publishPost(self, title, link, comment):
            return {
                'id': 'urn:li:share:6789012345',
                'url': 'https://linkedin.com/feed/update/urn:li:share:6789012345'
            }
    
    # Publish same content on multiple services
    article_title = "Best practices in software development"
    article_link = "https://myblog.com/best-practices-development"
    
    print("1. Publishing on multiple services...")
    
    # Twitter
    twitter_result = publisher.publish_and_cache(
        title=article_title,
        original_link=article_link,
        service="twitter",
        api_instance=MockTwitterAPI(),
        metadata={'hashtags': ['#development', '#software']}
    )
    print(f"   Twitter: {twitter_result['message']}")
    
    # Facebook
    facebook_result = publisher.publish_and_cache(
        title=article_title,
        original_link=article_link,
        service="facebook", 
        api_instance=MockFacebookAPI(),
        metadata={'audience': 'public'}
    )
    print(f"   Facebook: {facebook_result['message']}")
    
    # LinkedIn
    linkedin_result = publisher.publish_and_cache(
        title=article_title,
        original_link=article_link,
        service="linkedin",
        api_instance=MockLinkedInAPI(),
        metadata={'professional': True}
    )
    print(f"   LinkedIn: {linkedin_result['message']}")
    print()
    
    # Show article history
    print("2. Article publication history:")
    history = publisher.get_publication_history(article_link)
    for pub in history:
        print(f"   - {pub['service']}: {pub['response_link'] or 'No link'}")
    print()
    
    # Updated statistics
    print("3. Updated statistics:")
    stats = publisher.get_cache_stats()
    for service, data in stats.items():
        print(f"   {site}: {data['total']} publications")
    print()


def demo_search_and_management():
    """Demonstration of publication search and management"""
    
    print("=== Publication search and management ===\n")
    
    cache = PublicationCache()
    
    # Add more example content
    articles = [
        ("Docker tutorial for developers", "https://blog.com/docker-tutorial", "twitter"),
        ("Introduction to Kubernetes", "https://blog.com/kubernetes-intro", "facebook"),
        ("Docker vs Kubernetes: Which to choose?", "https://blog.com/docker-vs-kubernetes", "linkedin"),
        ("Container guide with Docker", "https://blog.com/containers-docker", "twitter"),
    ]
    
    for title, link, site in articles:
        cache.add_publication(title, link, service)
    
    print("1. Search by term:")
    docker_posts = cache.search_publications("Docker")
    print(f"   Docker publications: {len(docker_posts)}")
    for post in docker_posts:
        print(f"   - {post['title']} ({post['service']})")
    print()
    
    print("2. Publications by service:")
    twitter_posts = cache.get_publications_by_service("twitter")
    print(f"   Twitter publications: {len(twitter_posts)}")
    for post in twitter_posts:
        print(f"   - {post['title']}")
    print()
    
    print("3. All publications (sorted by date):")
    all_posts = cache.get_all_publications()
    for i, post in enumerate(all_posts[-5:], 1):  # Last 5
        print(f"   {i}. {post['title']} ({post['service']})")
    print()


def demo_export_functionality():
    """Demonstration of export functionality"""
    
    print("=== Data export ===\n")
    
    cache = PublicationCache()
    
    # Export to CSV
    csv_file = cache.export_to_csv("publications_export.csv")
    if csv_file:
        print(f"Publications exported to: {csv_file}")
    else:
        print("Error exporting publications")
    print()


def main():
    """Main function that runs all demonstrations"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("PUBLICATION CACHE SYSTEM")
    print("=" * 50)
    print()
    
    try:
        # Run demonstrations
        demo_basic_usage()
        demo_integration_with_existing_system()
        demo_search_and_management()
        demo_export_functionality()
        
        print("Demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        logging.error(f"Error in demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())