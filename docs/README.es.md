# socialModules: Sistema Modular de Reglas para Automatización Social

## Descripción
Este proyecto permite definir y gestionar reglas para la publicación y procesamiento de contenidos en múltiples servicios sociales (Reddit, Mastodon, Telegram, etc.) a partir de archivos de configuración tipo INI. El sistema es modular, extensible y robusto, con validación exhaustiva y tests automáticos.

---

## Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/fernand0/socialModules.git
   cd socialModules/src/socialModules
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   # O instala pytest para los tests
   pip install pytest
   ```

---

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

---

## Ejecución del script principal

Puedes usar el script de ejemplo `test_modular_architecture.py` para ver las reglas generadas:

```bash
python3 test_modular_architecture.py
```

Salida esperada:
```
Reglas generadas:
Fuente: ('reddit', 'set', 'user', 'posts')
  Acción: ('direct', 'post', 'telegram', 'user')
...
Fuentes disponibles:
...
Lista de disponibles:
...
```

---

## Ejecución de los tests automáticos

1. Ve al directorio raíz del proyecto.
2. Ejecuta:
   ```bash
   PYTHONPATH=. pytest tests/
   ```
3. Todos los tests deben pasar. Los tests cubren:
   - Validación de claves obligatorias
   - Múltiples secciones
   - Manejo de errores y duplicados
   - Robustez ante configuraciones incorrectas

---

## Buenas prácticas y contribución
- Añade nuevos módulos siguiendo la estructura de los existentes.
- Escribe tests para nuevas funcionalidades.
- Usa excepciones personalizadas para errores de configuración.
- Mantén la documentación y los ejemplos actualizados.

---

## Contacto y enlaces útiles
- Autor: Fernando Tricas
- Repositorio: https://github.com/fernand0/socialModules
- Issues y soporte: Usa el sistema de issues de GitHub

---

¡Contribuciones y sugerencias son bienvenidas! 