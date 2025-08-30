# Publication Cache System

This system adds functionality to store detailed information about publications made on different websites and social networks.

## Features

- **Persistent storage**: Saves title, original link, publication service and response link
- **Advanced search**: Search publications by title, link or site
- **Statistics**: Generate publication statistics by service
- **Export**: Export data to CSV for external analysis
- **Integration**: Easily integrates with existing system

## System Files

### `modulePublicationCache.py`
Main module that manages the publication cache.

**Main functionalities:**
- `add_publication()`: Add new publication
- `update_response_link()`: Update response link
- `get_publications_by_service()`: Get publications by service
- `search_publications()`: Search publications by text
- `get_stats()`: Generate statistics
- `export_to_csv()`: Export to CSV

### `modulePublishingWithCache.py`
Extension of the publishing system that automatically integrates the cache.

**Main functionalities:**
- `publish_and_cache()`: Publish and store automatically
- `get_publication_history()`: History of a specific link
- `get_service_publications()`: Publications from a site
- `search_cached_publications()`: Search in cache

### `example_publication_cache.py`
Complete usage examples of the system.

## Basic Usage

### 1. Create a simple cache

```python
from socialModules.modulePublicationCache import PublicationCache

# Create cache
cache = PublicationCache()

# Add publication
pub_id = cache.add_publication(
    title="My interesting article",
    original_link="https://myblog.com/article",
    service="twitter",
    response_link="https://twitter.com/user/status/123456"
)

# Search publications
twitter_posts = cache.get_publications_by_service("twitter")
python_posts = cache.search_publications("Python")
```

### 2. Integration with automatic publishing

```python
from socialModules.modulePublishingWithCache import PublisherWithCache

# Create publisher with cache
publisher = PublisherWithCache()

# Publish and store automatically
result = publisher.publish_and_cache(
    title="New tutorial",
    original_link="https://myblog.com/tutorial",
    service="facebook",
    api_instance=facebook_api
)

# View article history
history = publisher.get_publication_history("https://myblog.com/tutorial")
```

## Data Structure

Each publication stores:

```json
{
    "id": "twitter_1642234567",
    "title": "Publication title",
    "original_link": "https://example.com/article",
    "service": "twitter",
    "response_link": "https://twitter.com/user/status/123456",
    "publication_date": "2024-01-15T10:30:00"
}
```

## Configuration

### Custom cache file

```python
# Use custom file
cache = PublicationCache("/custom/path/my_cache.json")

# Or use default file in DATADIR
cache = PublicationCache()  # Uses DATADIR/publication_cache.json
```

### Integration with existing APIs

The system automatically detects response links for:

- **Twitter**: Extracts tweet ID and generates link
- **Facebook**: Extracts post ID
- **LinkedIn**: Extracts post URL
- **Mastodon**: Uses direct toot URL

For other sites, you can customize extraction:

```python
def _extract_response_link(self, publish_result, service):
    if site.lower() == 'my_custom_site':
        if 'custom_id' in publish_result:
            return f"https://mysite.com/post/{publish_result['custom_id']}"
    
    return super()._extract_response_link(publish_result, service)
```

## Usage Examples

### Publication statistics

```python
cache = PublicationCache()
stats = cache.get_stats()

print("Statistics by service:")
for service, data in stats.items():
    print(f"{site}: {data['total']} publications")
    print(f"  With response link: {data['with_response_link']}")
    print(f"  Without response link: {data['without_response_link']}")
```

### Advanced search

```python
# Search by title
python_posts = cache.search_publications("Python", field="title")

# Search by service
twitter_posts = cache.search_publications("twitter", field="service")

# Search by link
blog_posts = cache.search_publications("myblog.com", field="original_link")
```

### Data export

```python
# Export all publications
csv_file = cache.export_to_csv("my_publications.csv")

# The CSV file will contain:
# id,title,original_link,service,response_link,publication_date
```

### Duplicate publication management

```python
# View all publications of a specific article
history = cache.get_publications_by_original_link("https://myblog.com/article")

print(f"This article was published on {len(history)} sites:")
for pub in history:
    print(f"- {pub['service']}: {pub['response_link'] or 'No link'}")
```

## Integration with Existing System

To integrate with your current workflow:

1. **Replace direct API calls** with `publish_and_cache()`
2. **Use cache to avoid duplicates** by consulting `get_publications_by_original_link()`
3. **Generate reports** using `get_stats()` and `export_to_csv()`

### Migration example

**Before:**
```python
# Existing code
result = twitter_api.publishPost(title, link, comment)
```

**After:**
```python
# With integrated cache
publisher = PublisherWithCache()
result = publisher.publish_and_cache(
    title=title,
    original_link=link,
    service="twitter",
    api_instance=twitter_api,
    comment=comment
)
```

## Tests

Run the example file to test functionality:

```bash
python examples/example_publication_cache.py
```

This command will run demonstrations of:
- Basic cache usage
- Integration with simulated APIs
- Search and management
- Data export

## Considerations

- **Performance**: Cache uses JSON for storage, suitable for thousands of publications
- **Concurrency**: For intensive concurrent use, consider using a database
- **Backup**: JSON file can be easily backed up
- **Privacy**: Does not store full content, only publication metadata

## Future Extensions

Possible improvements:
- Database support (SQLite, PostgreSQL)
- Web interface for visual management
- Social media analytics integration
- Engagement notifications
- Republication scheduling