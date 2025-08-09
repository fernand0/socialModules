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

## Ejemplo de archivo de configuración (`.rssBlogs`)

```ini
[blog1]
url = http://example.com/rss
service = reddit
reddit = user
posts = posts
direct = telegram

[blog2]
url = http://another.com/rss
service = mastodon
mastodon = user2
posts = posts
direct = slack
```

Coloca este archivo en el directorio de configuración (`CONFIGDIR`) o pásalo como path absoluto al script.

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