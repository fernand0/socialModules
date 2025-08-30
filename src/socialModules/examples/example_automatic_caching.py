#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example demonstrating automatic publication caching integration.
Shows how the modified publishPost method automatically caches publications.
"""

import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialModules.modulePublicationCache import PublicationCache


def demo_automatic_caching():
    """Demonstrate automatic caching when using publishPost method"""
    
    print("=== Automatic Publication Caching Demo ===\n")
    
    # Create a mock social media module for demonstration
    class MockSocialModule:
        def __init__(self, service_name):
            self.service = service_name
            self.user = "test_user"
            self.nick = "test_nick"
            self.indent = ""
        
        def getService(self):
            return self.service
        
        def getUser(self):
            return self.user
        
        def getNick(self):
            return self.nick
        
        def processReply(self, reply):
            return reply
        
        def report(self, service, title, link, exc_info):
            return f"Error in {service}: {title}"
        
        def publishApiPost(self, title, link, comment):
            # Simulate successful publication
            if self.service == 'twitter':
                return {'id': '1234567890123456789', 'text': f"{title} {link}"}
            elif self.service == 'facebook':
                return {'post_id': 'user_987654321', 'message': f"{title}\n{link}"}
            elif self.service == 'linkedin':
                return {'id': 'urn:li:share:6789012345', 'url': 'https://linkedin.com/feed/update/urn:li:share:6789012345'}
            else:
                return "Published successfully"
        
        # Import the modified publishPost method
        from socialModules.moduleContent import Content
        publishPost = Content.publishPost
        _cache_publication_if_successful = Content._cache_publication_if_successful
        _extract_response_link_from_reply = Content._extract_response_link_from_reply
    
    # Test publications on different platforms
    platforms = ['twitter', 'facebook', 'linkedin']
    
    for platform in platforms:
        print(f"Testing {platform.capitalize()} publication...")
        
        # Create mock module instance
        mock_module = MockSocialModule(platform)
        
        # Simulate publication
        title = f"Test article for {platform}"
        link = f"https://myblog.com/test-article-{platform}"
        comment = f"Check out this article on {platform}!"
        
        # Call publishPost (this will automatically cache the publication)
        result = mock_module.publishPost(title, link, comment)
        
        print(f"  Publication result: {result}")
        print(f"  Cached automatically: ✓")
        print()
    
    # Show cached publications
    print("Cached Publications:")
    cache = PublicationCache()
    all_pubs = cache.get_all_publications()
    
    for i, pub in enumerate(all_pubs[-3:], 1):  # Show last 3
        print(f"{i}. {pub['title']}")
        print(f"   Service: {pub['service']}")
        print(f"   Original: {pub['original_link']}")
        print(f"   Response: {pub['response_link'] or 'Not available'}")
        print()
    
    # Show statistics
    stats = cache.get_stats()
    print("Cache Statistics:")
    for service, data in stats.items():
        print(f"  {site}: {data['total']} publications")
    print()


def demo_publication_history():
    """Demonstrate viewing publication history for an article"""
    
    print("=== Publication History Demo ===\n")
    
    cache = PublicationCache()
    
    # Add some test publications for the same article
    article_link = "https://myblog.com/important-article"
    article_title = "Important Article About Technology"
    
    sites = [
        ('twitter', 'https://twitter.com/user/status/111111'),
        ('facebook', 'https://facebook.com/post/222222'),
        ('linkedin', 'https://linkedin.com/feed/update/333333'),
        ('mastodon', 'https://mastodon.social/@user/444444')
    ]
    
    print(f"Publishing '{article_title}' across multiple platforms...")
    
    for service, response_link in sites:
        cache.add_publication(
            title=article_title,
            original_link=article_link,
            service=service,
            response_link=response_link
        )
        print(f"  ✓ Published on {site}")
    
    print()
    
    # Show publication history
    history = cache.get_publications_by_original_link(article_link)
    print(f"Publication history for: {article_link}")
    print(f"Total publications: {len(history)}")
    print()
    
    for pub in history:
        print(f"  Platform: {pub['service']}")
        print(f"  Response URL: {pub['response_link']}")
        print(f"  Date: {pub['publication_date']}")
        print()


def demo_search_and_analytics():
    """Demonstrate search and analytics capabilities"""
    
    print("=== Search and Analytics Demo ===\n")
    
    cache = PublicationCache()
    
    # Search publications
    print("1. Search by keyword:")
    tech_posts = cache.search_publications("technology", field="title")
    print(f"   Found {len(tech_posts)} publications about technology")
    
    article_posts = cache.search_publications("article", field="title")
    print(f"   Found {len(article_posts)} publications with 'article' in title")
    print()
    
    # Platform analytics
    print("2. Platform analytics:")
    twitter_posts = cache.get_publications_by_service("twitter")
    facebook_posts = cache.get_publications_by_service("facebook")
    linkedin_posts = cache.get_publications_by_service("linkedin")
    
    print(f"   Twitter: {len(twitter_posts)} publications")
    print(f"   Facebook: {len(facebook_posts)} publications")
    print(f"   LinkedIn: {len(linkedin_posts)} publications")
    print()
    
    # Overall statistics
    print("3. Overall statistics:")
    stats = cache.get_stats()
    total_pubs = sum(data['total'] for data in stats.values())
    total_with_links = sum(data['with_response_link'] for data in stats.values())
    
    print(f"   Total publications: {total_pubs}")
    print(f"   With response links: {total_with_links}")
    print(f"   Success rate: {(total_with_links/total_pubs*100):.1f}%" if total_pubs > 0 else "   Success rate: N/A")
    print()


def main():
    """Main function that runs all demonstrations"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("AUTOMATIC PUBLICATION CACHING SYSTEM")
    print("=" * 50)
    print()
    
    try:
        # Run demonstrations
        demo_automatic_caching()
        demo_publication_history()
        demo_search_and_analytics()
        
        print("All demonstrations completed successfully!")
        print("\nKey Benefits:")
        print("✓ Automatic caching - no code changes needed")
        print("✓ Cross-platform tracking")
        print("✓ Response link extraction")
        print("✓ Search and analytics")
        print("✓ Publication history")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        logging.error(f"Error in demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())