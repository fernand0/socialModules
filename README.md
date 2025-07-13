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
- **Cursor** - IDE integration and development automation

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

## Ejemplo de configuración: `.rssBlogs`

El fichero `.rssBlogs` permite definir múltiples blogs y sus parámetros asociados para automatizar la publicación y gestión de contenido en diferentes servicios. Cada sección representa un blog distinto:

```ini
[Blog1]
url = https://tublog.com/
rss = https://tublog.com/feed.xml
xmlrpc = https://tublog.com/xmlrpc.php
twitterAC = tu_usuario_twitter
pageFB = tu_pagina_facebook
telegramAC = tu_usuario_telegram
mediumAC = tu_usuario_medium
linksToAvoid = https://tublog.com/evitar1,https://tublog.com/evitar2
```

**Campos típicos:**
- `url`: URL principal del blog
- `rss`: URL del feed RSS
- `xmlrpc`: Endpoint XML-RPC para publicación remota (WordPress, etc.)
- `twitterAC`: Cuenta de Twitter asociada
- `pageFB`: Página de Facebook asociada
- `telegramAC`: Usuario/canal de Telegram asociado
- `mediumAC`: Cuenta de Medium asociada
- `linksToAvoid`: Lista de enlaces a evitar (separados por comas)

Puedes añadir tantas secciones `[BlogX]` como necesites, cada una con sus propios parámetros.

### Ejemplo de configuración: `.rssCursor`

El fichero `.rssCursor` permite configurar la integración con Cursor IDE:

```ini
[your_cursor_user]
cursor_path = /usr/bin/cursor
api_key = your_cursor_api_key
workspace_path = /home/user/projects
```

**Campos típicos:**
- `cursor_path`: Ruta de instalación de Cursor (opcional, se auto-detecta)
- `api_key`: Clave API de Cursor (para futuras integraciones)
- `workspace_path`: Directorio de trabajo por defecto

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

### Cursor IDE Integration
```python
from socialModules.configMod import getApi

# Initialize Cursor module
cursor_api = getApi('Cursor', 'your_cursor_user')

# Query Cursor using publishPost
response = cursor_api.publishPost("help", "")
print(response)

# List files in workspace
files = cursor_api.publishPost("files", "")
print(files)

# Check Cursor status
status = cursor_api.publishPost("status", "")
print(status)

# Read a file
content = cursor_api.publishPost("read", "moduleCursor.py")
print(f"File content: {content[:100]}...")

# Search for files
python_files = cursor_api.publishPost("search", "*.py")
print(f"Python files: {python_files}")

# Analyze code
analysis = cursor_api.publishPost("analyze_code", "moduleCursor.py")
print(f"Code analysis: {analysis}")

# Create a project
result = cursor_api.publishPost("create_project", "my_project:python")
print(result)

# Write to a file
result = cursor_api.publishPost("write", "test.txt:Hello from Cursor!")
print(result)

# Get file information
info = cursor_api.publishPost("info", "moduleCursor.py")
print(f"File info: {info}")

# List projects
projects = cursor_api.publishPost("list_projects", "")
print(f"Projects: {projects}")

# Custom query
custom = cursor_api.publishPost("custom", "analyze")
print(custom)
```

**Tipos de consultas disponibles:**
- `help` - Obtener ayuda
- `files` - Listar archivos del workspace
- `status` - Verificar estado de Cursor
- `projects` - Listar proyectos
- `analyze` - Analizar workspace
- `read` - Leer archivo específico
- `write` - Escribir en archivo (formato: "archivo:contenido")
- `search` - Buscar archivos
- `info` - Obtener información de archivo
- `analyze_code` - Analizar archivo de código
- `create_project` - Crear proyecto (formato: "nombre:tipo")
- `list_projects` - Listar todos los proyectos
- `custom` - Consulta personalizada
- `query` / `pregunta` - Consultas genéricas de información

### Consultas Genéricas de Información

El módulo Cursor también soporta consultas genéricas de información usando `query` o `pregunta`:

```python
# Consultas genéricas
response = cursor_api.publishPost("query", "¿Qué sabes de Zaragoza?")
print(response)

response = cursor_api.publishPost("pregunta", "¿Qué es Python?")
print(response)

response = cursor_api.publishPost("query", "¿Qué hay en el workspace?")
print(response)

response = cursor_api.publishPost("query", "¿Cuántos archivos hay?")
print(response)
```

**Temas soportados en consultas genéricas:**
- Información sobre ciudades (Zaragoza, etc.)
- Lenguajes de programación (Python, etc.)
- Información sobre Cursor IDE
- Estado del workspace y archivos
- Análisis de código y proyectos

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
