# Social Modules

A comprehensive Python package for managing interactions with multiple social networks and content sites through a unified, enhanced, and efficient interface.

## Overview

Social Modules provides a modular architecture for reading from and writing to various social media platforms and content sites. It offers a consistent API across different services, making it easy to manage content, and now includes powerful new features for unified publishing and automatic publication caching.

## Key Enhancements

### 1. Unified Publishing Logic

The publishing workflow has been centralized and significantly improved. The new `publish_to_multiple_destinations` method in `moduleRules` provides a single, robust entry point for all publications.

- **Simplified API**: Publish to multiple platforms with a single function call.
- **Improved Error Handling**: Robust error handling and detailed, structured results for each publication attempt.
- **Flexible Destinations**: Supports both dictionary and list formats for specifying destinations.
- **Automatic Configuration**: Smartly configures service-specific settings (e.g., channels for Slack/Telegram, email fields for SMTP).
- **Image & Content Support**: Natively handles image attachments, alt text, and different content types.

### 2. Automatic Publication Caching

A powerful, opt-in caching system is now integrated directly into the core content module. This allows you to automatically track every publication made through the system.

- **Opt-In Activation**: Disabled by default for backward compatibility. Enable it with a single line: `api.setAutoCache(True)`.
- **Rich Data Storage**: Caches publication title, original link, target service, the platform's response link (e.g., tweet URL), and metadata.
- **Zero-Effort History**: Automatically builds a complete history of all your publications across all platforms.
- **Powerful Analytics**: The cache module provides functions to search, filter, get statistics, and export your publication history to CSV.

## Features

- **Unified Interface**: Common API for all supported platforms.
- **Unified Publishing**: Centralized, robust method for multi-platform publishing.
- **Publication Caching**: Optional, automatic caching of all publications.
- **Content Management**: Read and write content across multiple social networks.
- **Modular Design**: Easy to extend with new platforms.
- **Configuration Management**: Centralized configuration for all services.

## Supported Platforms

### Social Networks
- **Twitter** - Post tweets, retweets, and manage content
- **Facebook** - Share posts and manage pages
- **LinkedIn** - Professional networking content
- **Mastodon** - Federated social networking
- **Telegram** - Messaging and channel management
- **Slack** - Team communication
- **Reddit** - Community discussions and content
- **Tumblr** - Microblogging and social media
- **Medium** - Content publishing platform

### Content Sites
- **RSS Feeds** - Read and process RSS content
- **WordPress** - Blog management and publishing
- **Flickr** - Photo sharing and management
- **Imgur** - Image hosting and sharing
- **Pocket** - Read-it-later service
- **Gmail** - Email content processing
- **Google Calendar** - Event management
- **IMDB** - Movie and TV show data
- **Matrix** - Decentralized communication

### Additional Services
- **SMTP** - Email sending capabilities
- **IMAP** - Email reading and processing
- **HTML** - Web content processing
- **XML-RPC** - Remote procedure calls
- **Forum** - Forum content management
- **Gitter** - Chat platform integration

## Installation

### From GitHub
```bash
pip install social-modules@git+https://git@github.com/fernand0/socialModules
```

### From Source
```bash
git clone https://github.com/fernand0/socialModules.git
cd socialModules
pip install -e .
```

---

## Command-Line Arguments

The main script `moduleRules.py` accepts the following arguments:

*   `--timeSlots` / `-t` (default: 50): Defines the number of time slots (in minutes) for publishing.
*   `[Blog]` (positional): Allows selecting a specific blog to process. Example: `python3 src/socialModules/moduleRules.py MyBlog`
*   `--simmulate` / `-s`: If used, simulates publications without actually executing them.
*   `--noWait` / `-n`: Ignores time restrictions between publications.
*   `--interactive` / `-i`: Enables interactive publishing mode, allowing manual selection of rules and actions.
*   `--rules` / `-r`: Displays the list of configured rules and actions.

---

## Quick Start: Unified Publishing & Caching

This example demonstrates publishing a single piece of content to multiple platforms and automatically caching the results.

```python
from socialModules.moduleRules import Rules
from socialModules.configMod import getApi

# 1. Define your destinations
destinations = {
    "twitter": "your_twitter_username",
    "mastodon": "your_mastodon_username",
    "linkedin": "your_linkedin_username"
}

# 2. Enable automatic caching for each destination API
for service, account in destinations.items():
    api = getApi(service, account)
    api.setAutoCache(True) # Enable automatic caching

# 3. Use the unified publishing method from moduleRules
rules = Rules()
results = rules.publish_to_multiple_destinations(
    destinations=destinations,
    title="Check out my new blog post!",
    url="https://example.com/my-awesome-post",
    content="Here's a brief summary of my new post about..."
)

# 4. Review the structured results
print(results)

# 5. Analyze your cached publications
from socialModules.modulePublicationCache import PublicationCache
cache = PublicationCache()
stats = cache.get_stats()
print("\nPublication Statistics:")
print(stats)
```

## Usage Examples

### Reading Content
```python
from socialModules.configMod import getApi

# Read from an RSS feed
rss_api = getApi('Rss', 'https://example.com/feed.xml')
posts = rss_api.setApiPosts()
print(f"Found {len(posts)} posts in RSS feed.")

# Read from a Twitter timeline
twitter_api = getApi('Twitter', 'your_twitter_username')
tweets = twitter_api.setApiPosts()
print(f"Found {len(tweets)} tweets on timeline.")
```

### Analyzing the Publication Cache
```python
from socialModules.modulePublicationCache import PublicationCache

cache = PublicationCache()

# Search for all publications related to a specific link
history = cache.get_publications_by_original_link("https://example.com/my-awesome-post")
print(f"Found {len(history)} publications for the link.")

# Search for publications containing 'Python'
python_posts = cache.search_publications("Python")
print(f"Found {len(python_posts)} posts about Python.")

# Export all data to a CSV file
cache.export_to_csv("my_publications.csv")
print("Publication history exported to my_publications.csv")
```

## Configuration

The core configuration remains in the `~/.mySocial/` directory.

### Directory Structure
```
~/.mySocial/
├── config/          # Service configuration files (e.g., .rssTwitter)
├── data/            # Cached data, including publication_cache.json
└── logs/            # Application logs
```

### Service Configuration
Each service requires its own configuration file in `~/.mySocial/config/`. For example, `~/.mySocial/config/.rssTwitter`:

```ini
[your_twitter_username]
CONSUMER_KEY = your_consumer_key
CONSUMER_SECRET = your_consumer_secret
TOKEN_KEY = your_access_token
TOKEN_SECRET = your_access_token_secret
BEARER_TOKEN = your_bearer_token
```

## Architecture

### Core Components

1.  **Rules Module** (`moduleRules.py`)
    -   Provides the centralized `publish_to_multiple_destinations` method for unified publishing.
    -   Orchestrates interactions with various service modules.

2.  **Content Module** (`moduleContent.py`)
    -   Base class for all platform-specific modules.
    -   Contains the integrated, opt-in logic for automatic publication caching.

3.  **Publication Cache Module** (`modulePublicationCache.py`)
    -   Manages the storage, retrieval, and analysis of publication data.
    -   Persists data to a local JSON file.

4.  **Platform-Specific Modules** (`moduleTwitter.py`, `moduleFacebook.py`, etc.)
    -   Implement the platform-specific API calls for reading and writing content.
    -   Inherit from `moduleContent`.

## Dependencies

The package requires Python 3.7+. See `pyproject.toml` for the complete dependency list.

## Contributing

1.  Fork the repository
2.  Create a feature branch
3.  Implement your changes
4.  Add tests if applicable
5.  Submit a pull request

### Code Style Guidelines

When contributing to this project, please follow these coding conventions:

- **Single Return Statement**: Functions should have a single return statement at the end when possible
- **Avoid break/continue**: Use boolean flags or conditional logic instead of break/continue statements
- Follow PEP 8 style guide
- Write clear, descriptive names for variables and functions
- Document complex logic with comments

For detailed information, see the [Coding Conventions](docs/coding_conventions.md) document.

## License

This project is licensed under the GNU General Public License. See `LICENSE.md` for details.
