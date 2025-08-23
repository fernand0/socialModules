# Social Modules

A comprehensive Python package for managing interactions with multiple social networks and content sites through a unified interface.

## Overview

Social Modules provides a modular architecture for reading from and writing to various social media platforms and content sites. It offers a consistent API across different services, making it easy to manage content across multiple platforms.

## Features

- **Unified Interface**: Common API for all supported platforms
- **Content Management**: Read and write content across multiple social networks
- **Caching System**: Local storage for managing content queues
- **Modular Design**: Easy to extend with new platforms
- **Configuration Management**: Centralized configuration for all services

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

## Quick Start

### Basic Usage

```python
from socialModules.configMod import getApi

# Initialize a Twitter module
twitter_api = getApi('Twitter', 'your_twitter_username')

# Get posts from your timeline
posts = twitter_api.setApiPosts()

# Publish a post
result = twitter_api.publishPost("Hello, World!")
```

### Configuration

Each service requires configuration in `~/.mySocial/config/` directory:

```ini
# Example: ~/.mySocial/config/.rssTwitter
[your_twitter_username]
CONSUMER_KEY = your_consumer_key
CONSUMER_SECRET = your_consumer_secret
TOKEN_KEY = your_access_token
TOKEN_SECRET = your_access_token_secret
BEARER_TOKEN = your_bearer_token
```

## Configuration Example: `.rssBlogs`

The `.rssBlogs` file allows you to define multiple blogs and their associated parameters to automate content publishing and management across different services. Each section represents a different blog:

```ini
[Blog1]
url = https://yourblog.com/
rss = https://yourblog.com/feed.xml
xmlrpc = https://yourblog.com/xmlrpc.php
twitterAC = your_twitter_user
pageFB = your_facebook_page
telegramAC = your_telegram_user
mediumAC = your_medium_user
linksToAvoid = https://yourblog.com/avoid1,https://yourblog.com/avoid2
```

**Typical fields:**
- `url`: Main URL of the blog
- `rss`: URL of the RSS feed
- `xmlrpc`: XML-RPC endpoint for remote publishing (WordPress, etc.)
- `twitterAC`: Associated Twitter account
- `pageFB`: Associated Facebook page
- `telegramAC`: Associated Telegram user/channel
- `mediumAC`: Associated Medium account
- `linksToAvoid`: List of links to avoid (comma-separated)

You can add as many `[BlogX]` sections as you need, each with its own parameters.

## Architecture

### Core Components

1. **Content Module** (`moduleContent.py`)
   - Base class for all content operations
   - Handles post management, caching, and formatting
   - Provides unified interface for all platforms

2. **Configuration Module** (`configMod.py`)
   - Manages API keys and service configuration
   - Handles file operations and logging
   - Provides utility functions for all modules

3. **Cache Module** (`moduleCache.py`)
   - Local storage for content queues
   - Manages temporal storage of content
   - Handles data persistence

4. **Platform-Specific Modules**
   - Each social platform has its own module
   - Inherits from Content class
   - Implements platform-specific API calls

### Module Structure

Each platform module follows this pattern:
```python
class modulePlatform(Content):
    def getKeys(self, config):
        # Extract API keys from config
        
    def initApi(self, keys):
        # Initialize platform-specific API client
        
    def setApiPosts(self):
        # Retrieve posts from platform
        
    def publishPost(self, *args, **kwargs):
        # Publish content to platform
```

## Configuration

### Directory Structure
```
~/.mySocial/
├── config/          # Configuration files
│   ├── .rssTwitter
│   ├── .rssFacebook
│   └── ...
├── data/           # Cached data and logs
└── logs/           # Application logs
```

### Environment Setup
```bash
# Create configuration directories
mkdir -p ~/.mySocial/config
mkdir -p ~/.mySocial/data
mkdir -p ~/.mySocial/logs
```

## Usage Examples

### Reading Content
```python
from socialModules.configMod import getApi

# Read from RSS feed
rss_api = getApi('Rss', 'https://example.com/feed.xml')
posts = rss_api.setApiPosts()

# Read from Twitter timeline
twitter_api = getApi('Twitter', 'username')
tweets = twitter_api.setApiPosts()
```

### Publishing Content
```python
# Publish to Twitter
twitter_api = getApi('Twitter', 'username')
result = twitter_api.publishPost("New blog post: https://example.com/post")

# Publish to multiple platforms
platforms = ['Twitter', 'Facebook', 'LinkedIn']
for platform in platforms:
    api = getApi(platform, 'username')
    api.publishPost("Cross-platform post")
```

### Content Management
```python
# Get cached posts
posts = api.getPosts()

# Get next post to publish
next_post = api.getNextPost()

# Update last published link
api.updateLastLink(url, link)
```

## Dependencies

The package requires Python 3.7+ and includes dependencies for:
- Social media APIs (tweepy, facebook-sdk, etc.)
- Content processing (beautifulsoup4, feedparser)
- Authentication (oauth2, keyring)
- Utilities (requests, click, dateparser)

See `pyproject.toml` for complete dependency list.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the GNU General Public License. See `LICENSE.md` for details.

## History

This code was originally part of [https://github.com/fernand0/scripts](https://github.com/fernand0/scripts) and was moved here following GitHub's guide on [Splitting a subfolder out into a new repository](https://docs.github.com/en/github/using-git/splitting-a-subfolder-out-into-a-new-repository).

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing issues for solutions
- Review the configuration examples in the codebase

## Roadmap

- [ ] Add more social platforms
- [ ] Improve error handling
- [ ] Add comprehensive tests
- [ ] Enhance documentation
- [ ] Performance optimizations