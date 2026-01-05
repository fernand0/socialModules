#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of using unified publication functionality in moduleRules

This example shows how to refactor duplicated publication code
that appears in WebContentProcessor.py and botElectrico.py
"""

import logging
import os
import sys

# Agregar el path de socialModules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socialModules.moduleRules


def ejemplo_web_content_processor():
    """
    Example equivalent to WebContentProcessor.py code lines 230+
    """
    print("=== Refactored WebContentProcessor Example ===")

    # Example data
    title = "Interesting article about Python"
    url = "https://example.com/python-article"
    content = "This is a great article about Python worth reading..."

    # Social media targets (equivalent to social_media_targets)
    social_media_targets = {
        # "slack": "http://fernand0-errbot.slack.com/",
        # "pocket": "fernand0kobo",
        "smtp": "ftricas@unizar.es",
    }

    # Additional configuration
    from_email = "ftricas@elmundoesimperfecto.com"
    to_email = "ftricas@unizar.es"

    # Create rules instance
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # BEFORE (duplicated code):
    # for target in social_media_targets:
    #     try:
    #         logging.info(f"Posting to {target}")
    #         key = ("direct", "post", target, social_media_targets[target])
    #         apiSrc = rules.readConfigDst("", key, None, None)
    #         if hasattr(apiSrc, "setChannel"):
    #             apiSrc.setChannel("links")
    #         if "smtp" in target:
    #             apiSrc.fromaddr = from_email
    #             apiSrc.to = to_email
    #         msgLog = apiSrc.publishPost(title, url, content)
    #         logging.info(msgLog)
    #     except Exception as e:
    #         logging.error(f"Error posting to {target}: {e}")

    # AFTER (unified code):
    results = rules.publish_to_multiple_destinations(
        destinations=social_media_targets,
        title=title,
        url=url,
        content=content,
        channel="links",  # For services that support it
        from_email=from_email,
        to_email=to_email,
    )

    # Show results
    print("Publication results:")
    for service, result in results.items():
        if result["success"]:
            print(f"✓ {service}: {result['result']}")
        else:
            print(f"✗ {service}: {result['error']}")


def ejemplo_bot_electrico():
    """
    Example equivalent to botElectrico.py code lines 379+
    """
    print("\n=== Refactored BotElectrico Example ===")

    # Example data
    # title = "Updated electrical consumption"
    message = "Today's electrical consumption has been 1.234 kWh"
    image_path = "/tmp/consumption_chart.png"
    alt_text = "Daily electrical consumption chart"

    # Destinations (equivalent to destinations)
    destinations = {
        "mastodon": "mi_cuenta_mastodon",
        "twitter": "mi_cuenta_twitter",
        # "telegram": "mi_canal_telegram"
    }

    # Crear instancia de rules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # BEFORE (duplicated code):
    # for destination, account in destinations.items():
    #     logging.info(f" Now in: {destination} - {account}")
    #     if account:
    #         key = ("direct", "post", destination, account)
    #         indent = "  "
    #         api = rules.readConfigDst(indent, key, None, None)
    #         try:
    #             result = api.publishImage(title, image_path, alt=alt_text)
    #             # ... lógica para extraer image_url ...
    #         except Exception as e:
    #             logging.error(f"Failed to publish image to {destination}: {e}")
    #         result = api.publishPost(message, "", "")
    #         logging.info(f"Published to {destination}: {result}")

    # AFTER (unified code):
    results = rules.publish_to_multiple_destinations(
        destinations=destinations,
        title=message,
        url="",
        content="",
        image_path=image_path,
        alt_text=alt_text,
    )

    # Show results
    print("Publication results:")
    for service, result in results.items():
        if result["success"]:
            print(f"✓ {service}: {result['result']}")
            if result.get("image_url"):
                print(f"  Image: {result['image_url']}")
        else:
            print(f"✗ {service}: {result['error']}")


def ejemplo_publicacion_mensaje_simple():
    """
    Ejemplo de la función publicar_mensaje_horario refactorizada
    """
    print("\n=== Ejemplo Mensaje Simple Refactorizado ===")

    message = "¡Buenos días! Recordatorio de consumo responsable de energía"

    destinations = {"mastodon": "mi_cuenta_mastodon", "twitter": "mi_cuenta_twitter"}

    # Crear instancia de rules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # ANTES (función publicar_mensaje_horario):
    # for destination, account in destinations.items():
    #     logging.info(f" Now in: {destination} - {account}")
    #     if account:
    #         key = ("direct", "post", destination, account)
    #         indent = "  "
    #         api = rules.readConfigDst(indent, key, None, None)
    #         result = api.publishPost(message, "", "")
    #         logging.info(f"Published to {destination}: {result}")

    # DESPUÉS (método simplificado):
    results = rules.publish_message_to_destinations(destinations, message)

    # Mostrar resultados
    print("Resultados de publicación:")
    for service, result in results.items():
        if result["success"]:
            print(f"✓ {service}: {result['result']}")
        else:
            print(f"✗ {service}: {result['error']}")


def ejemplo_con_manejo_errores():
    """
    Ejemplo mostrando el manejo de errores mejorado
    """
    print("\n=== Ejemplo con Manejo de Errores ===")

    # Incluir un servicio que probablemente falle para mostrar el manejo de errores
    destinations = {
        "mastodon": "cuenta_valida",
        "servicio_inexistente": "cuenta_cualquiera",
        "smtp": "email@example.com",
    }

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    results = rules.publish_to_multiple_destinations(
        destinations=destinations,
        title="Prueba de manejo de errores",
        url="https://example.com",
        content="Contenido de prueba",
    )

    # Análisis de resultados
    successful = [k for k, v in results.items() if v["success"]]
    failed = [k for k, v in results.items() if not v["success"]]

    print(f"Exitosas: {len(successful)}/{len(results)}")
    print(f"Servicios exitosos: {successful}")
    print(f"Servicios fallidos: {failed}")

    # Mostrar errores específicos
    for service, result in results.items():
        if not result["success"]:
            print(f"Error en {service}: {result['error']}")


def main():
    """Main function that executes all examples"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Unified Publication Examples")
    print("=" * 50)

    try:
        ejemplo_web_content_processor()
        ejemplo_bot_electrico()
        ejemplo_publicacion_mensaje_simple()
        ejemplo_con_manejo_errores()

        print("\n" + "=" * 50)
        print("Unification advantages:")
        print("- Eliminates duplicated code")
        print("- Consistent error handling")
        print("- Unified logging")
        print("- Easy to add new services")
        print("- Centralized configuration")

    except Exception as e:
        print(f"Error executing examples: {e}")
        logging.error(f"Error in examples: {e}")


if __name__ == "__main__":
    main()
