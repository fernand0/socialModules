### Additional Services
- **SMTP** - Email sending capabilities
- **IMAP** - Email reading and processing
- **HTML** - Web content processing
- **XML-RPC** - Remote procedure calls
- **Forum** - Forum content management
- **Gitter** - Chat platform integration
- **Cursor** - IDE integration and development automation
- **Gemini** - Google Gemini AI integration for intelligent responses 

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

### Gemini AI Integration
```python
from socialModules.configMod import getApi

# Initialize Gemini AI module
gemini_api = getApi('Gemini', 'your_gemini_user')

# Ask questions to Gemini AI
response = gemini_api.publishPost("¿Qué es Python?")
print(response)

response = gemini_api.publishPost("¿Qué es Docker?")
print(response)

response = gemini_api.publishPost("¿Qué es la inteligencia artificial?")
print(response)
```

### Cursor IDE Integration with AI
```python
from socialModules.configMod import getApi

# Initialize Cursor module (uses Gemini AI internally)
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

**Tipos de consultas disponibles en Cursor:**
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
- `query` / `pregunta` - Consultas genéricas de información con IA real (Gemini)

### Consultas Genéricas de Información con IA Real

El módulo Cursor soporta consultas genéricas de información usando `query` o `pregunta` con respuestas de IA real de Google Gemini:

```python
# Consultas genéricas con IA real
response = cursor_api.publishPost("query", "¿Qué sabes de Zaragoza?")
print(response)

response = cursor_api.publishPost("pregunta", "¿Qué es Python?")
print(response)

response = cursor_api.publishPost("query", "¿Qué hay en el workspace?")
print(response)

response = cursor_api.publishPost("query", "¿Cuántos archivos hay?")
print(response)

# Consultas técnicas con IA
response = cursor_api.publishPost("query", "¿Cómo optimizar este código Python?")
print(response)

response = cursor_api.publishPost("pregunta", "¿Qué patrones de diseño usar para este proyecto?")
print(response)
```

### Arquitectura Modular

El proyecto utiliza una arquitectura modular donde cada servicio tiene su propio módulo:

```python
# Módulos independientes
gemini_api = getApi('Gemini', 'user')  # Solo IA
cursor_api = getApi('Cursor', 'user')   # IDE + IA (usa Gemini internamente)
twitter_api = getApi('Twitter', 'user') # Red social
```

**Ventajas de la arquitectura modular:**
- **Separación de responsabilidades**: Cada módulo tiene una función específica
- **Reutilización**: El módulo Gemini puede ser usado por otros módulos
- **Mantenibilidad**: Cambios en un módulo no afectan a otros
- **Escalabilidad**: Fácil agregar nuevos módulos
- **Configuración independiente**: Cada módulo tiene su propia configuración 

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

### Ejemplo de configuración: `.rssBlogs`

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

### Configuración de Gemini AI

Para habilitar respuestas de IA real con Google Gemini, crea el archivo `~/.mySocial/config/.rssGemini`:

```ini
[your_gemini_user]
api_key = your_gemini_api_key
```

**Para obtener una API key de Gemini:**
1. Ve a https://makersuite.google.com/app/apikey
2. Crea una nueva API key
3. Configúrala en el archivo `.rssGemini`

### Configuración de Cursor IDE

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

**Nota:** El módulo Cursor leerá automáticamente la API key de Gemini desde `.rssGemini` y la usará para generar respuestas de IA real. Si Gemini no está disponible o hay errores de cuota, el módulo usará respuestas básicas predefinidas como fallback. 