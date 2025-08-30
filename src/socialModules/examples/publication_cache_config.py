#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration options for the publication cache system.
This file shows how to customize the caching behavior.
"""

import os
from socialModules.configMod import DATADIR


class PublicationCacheConfig:
    """Configuration class for publication cache system"""

    # Cache file location
    CACHE_FILE = os.path.join(DATADIR, "publication_cache.json")

    # Enable/disable automatic caching
    AUTO_CACHE_ENABLED = True

    # Services to exclude from automatic caching
    EXCLUDED_SERVICES = []  # e.g., ['test', 'debug']

    # Maximum number of publications to keep in cache (0 = unlimited)
    MAX_CACHE_SIZE = 0

    # Enable/disable response link extraction
    EXTRACT_RESPONSE_LINKS = True

    # Custom response link extractors for specific services
    CUSTOM_EXTRACTORS = {
        # Example custom extractor
        # 'myservice': lambda reply: reply.get('custom_url') if isinstance(reply, dict) else None
    }

    # Metadata fields to include in cache (deprecated)
    METADATA_FIELDS = []

    # Enable/disable logging for cache operations
    CACHE_LOGGING = True

    # Log level for cache operations (1=info, 2=debug, 3=warning)
    CACHE_LOG_LEVEL = 2


def get_cache_config():
    """Get current cache configuration"""
    return {
        'cache_file': PublicationCacheConfig.CACHE_FILE,
        'auto_cache_enabled': PublicationCacheConfig.AUTO_CACHE_ENABLED,
        'excluded_services': PublicationCacheConfig.EXCLUDED_SERVICES,
        'max_cache_size': PublicationCacheConfig.MAX_CACHE_SIZE,
        'extract_response_links': PublicationCacheConfig.EXTRACT_RESPONSE_LINKS,
        'custom_extractors': PublicationCacheConfig.CUSTOM_EXTRACTORS,
        'cache_logging': PublicationCacheConfig.CACHE_LOGGING,
        'cache_log_level': PublicationCacheConfig.CACHE_LOG_LEVEL,
    }


def should_cache_publication(service, title, link):
    """
    Determine if a publication should be cached based on configuration

    Args:
        service: Publication service name
        title: Publication title
        link: Publication link

    Returns:
        bool: True if should be cached
    """
    import logging
    logging.info(f"Cacheeeessss")
    if not PublicationCacheConfig.AUTO_CACHE_ENABLED:
        return False
    logging.info(f"Cacheeeessss+")

    if service.lower() in [s.lower() for s in PublicationCacheConfig.EXCLUDED_SERVICES]:
        return False
    logging.info(f"Cacheeeessss++")
    logging.info(f"Cacheeeessss++ {title} - {link}")

    if not title or not link:
        return False
    return True


def get_custom_extractor(service):
    """
    Get custom response link extractor for a service

    Args:
        service: Service name

    Returns:
        function or None: Custom extractor function
    """
    return PublicationCacheConfig.CUSTOM_EXTRACTORS.get(service.lower())


def filter_metadata(metadata_dict):
    """
    Filter metadata to include only configured fields (deprecated)

    Args:
        metadata_dict: Original metadata dictionary

    Returns:
        dict: Empty dictionary
    """
    return {}


# Example usage and customization
def example_custom_configuration():
    """Example of how to customize the cache configuration"""

    print("=== Publication Cache Configuration Example ===\n")

    # Show current configuration
    config = get_cache_config()
    print("Current configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    # Example: Disable caching for test services
    PublicationCacheConfig.EXCLUDED_SERVICES = ['test', 'debug', 'staging']
    print("Excluded services updated:", PublicationCacheConfig.EXCLUDED_SERVICES)

    # Example: Add custom extractor for a proprietary platform
    def custom_myservice_extractor(reply):
        """Custom extractor for 'myservice' platform"""
        if isinstance(reply, dict) and 'post_url' in reply:
            return reply['post_url']
        return None

    PublicationCacheConfig.CUSTOM_EXTRACTORS['myservice'] = custom_myservice_extractor
    print("Custom extractor added for 'myservice'")

    # Example: Limit cache size
    PublicationCacheConfig.MAX_CACHE_SIZE = 1000
    print(f"Cache size limited to: {PublicationCacheConfig.MAX_CACHE_SIZE}")

    # Example: Custom cache file location
    PublicationCacheConfig.CACHE_FILE = "/custom/path/my_publications.json"
    print(f"Custom cache file: {PublicationCacheConfig.CACHE_FILE}")

    print("\nConfiguration updated successfully!")


def example_conditional_caching():
    """Example of conditional caching logic"""

    print("=== Conditional Caching Example ===\n")

    test_cases = [
        ('twitter', 'My Article', 'https://blog.com/article'),
        ('test', 'Test Post', 'https://test.com/post'),
        ('facebook', '', 'https://blog.com/no-title'),
        ('linkedin', 'Professional Post', ''),
    ]

    for service, title, link in test_cases:
        should_cache = should_cache_publication(service, title, link)
        status = "✓ CACHE" if should_cache else "✗ SKIP"
        print(f"{status} - {service}: '{title}' -> {link}")

    print()


if __name__ == "__main__":
    example_custom_configuration()
    example_conditional_caching()
