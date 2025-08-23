# Publication Cache System

A new caching system for tracking publications across different social media platforms and websites.

## Overview

This system provides functionality to store and manage information about content publications, including:

- Publication title
- Original content link  
- Publication service (Twitter, Facebook, LinkedIn, etc.)
- Response link from the site (if available)
- Publication date and metadata

## Quick Start

### Enable Auto-Caching

```python
# Enable auto-caching for any social media module
api = moduleTwitter.moduleTwitter()
api.setAutoCache(True)  # Enable automatic caching

# Now all publishPost calls will be cached automatically
result = api.publishPost("My Title", "https://blog.com/post", "Comment")
```

### Manual Cache Usage

```python
from socialModules.modulePublicationCache import PublicationCache

# Create cache
cache = PublicationCache()

# Add publication manually
pub_id = cache.add_publication(
    title="My Article Title",
    original_link="https://myblog.com/article",
    service="twitter",
    response_link="https://twitter.com/user/status/123456"
)

# Search publications
twitter_posts = cache.get_publications_by_service("twitter")
```

### Integrated Publishing (Alternative)

```python
from socialModules.modulePublishingWithCache import PublisherWithCache

# Create publisher with automatic caching
publisher = PublisherWithCache()

# Publish and cache automatically
result = publisher.publish_and_cache(
    title="New Tutorial",
    original_link="https://myblog.com/tutorial", 
    service="facebook",
    api_instance=facebook_api
)
```

## Files

- `modulePublicationCache.py` - Core cache functionality
- `modulePublishingWithCache.py` - Integration with publishing system
- `examples/` - Complete examples and documentation

## Examples and Documentation

See the `examples/` directory for:

- **`example_publication_cache.py`** - Complete working examples
- **`README_publication_cache.md`** - Detailed documentation

Run the example:

```bash
python examples/example_publication_cache.py
```

## Features

- ✅ Persistent JSON storage
- ✅ Search and filtering capabilities  
- ✅ Statistics generation
- ✅ CSV export functionality
- ✅ Optional automatic integration (backward compatible)
- ✅ Automatic response link detection
- ✅ Integration with existing APIs
- ✅ Duplicate publication tracking

## Cache Storage

### Default Location
The cache is stored as a JSON file at:
```
~/.mySocial/data/publication_cache.json
```

### Custom Location
```python
# Use custom cache file
cache = PublicationCache("/custom/path/my_cache.json")
```

### Cache Management
```bash
# Interactive management tool
python examples/cache_management.py

# Command line options
python examples/cache_management.py info      # Show cache info
python examples/cache_management.py stats     # Show statistics  
python examples/cache_management.py backup    # Create backup
python examples/cache_management.py export    # Export to CSV/JSON
```

### Cache File Format
The cache uses JSON format for easy inspection and portability:
```json
{
  "twitter_1642234567": {
    "id": "twitter_1642234567",
    "title": "My Article Title",
    "original_link": "https://blog.com/article",
    "service": "twitter", 
    "response_link": "https://twitter.com/user/status/123456",
    "publication_date": "2024-01-15T10:30:00",
    "metadata": {
      "service": "twitter",
      "user": "my_user"
    }
  }
}
```

## Integration

### Optional Automatic Integration

The system **optionally integrates** with the existing `publishPost` method in `moduleContent.py`. When enabled, every publication is automatically cached. **By default, auto-caching is disabled** to maintain backward compatibility.

**What gets cached automatically:**
- Publication title and original link
- Target site (twitter, facebook, linkedin, etc.)
- Response link from the platform (when available)
- User information and metadata
- Publication timestamp

### Manual Integration

You can also use the system manually for more control:

```python
from socialModules.modulePublishingWithCache import PublisherWithCache

publisher = PublisherWithCache()
result = publisher.publish_and_cache(title, link, service, api_instance)
```

### Supported Platforms

The system automatically detects response links from:

- Twitter
- Facebook  
- LinkedIn
- Mastodon
- Custom sites (extensible)

For detailed usage instructions and examples, see `examples/README_publication_cache.md`.