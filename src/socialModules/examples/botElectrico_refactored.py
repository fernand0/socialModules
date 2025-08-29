#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Refactored version of botElectrico.py using unified publication logic

This version shows how the original code is simplified using the
unified methods from moduleRules
"""

import logging
import os
import time

import socialModules.moduleRules


class BotElectricoRefactored:
    """
    Refactored version of the electrical bot
    """
    
    def __init__(self, cache_dir="/tmp/cache"):
        self.cache_dir = cache_dir
        self.rules = socialModules.moduleRules.moduleRules()
        self.rules.checkRules()
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def publicar_grafico_consumo(self, destinations, title, png_path, alt_text, message):
        """
        Refactored version of consumption chart publication
        
        BEFORE: Duplicated code with manual loop and complex image logic
        AFTER: Use of unified method
        """
        
        # Generate markdown content (original logic maintained)
        now = time.time()
        file_name = lambda t: time.strftime("%Y-%m-%d-%H-%M", time.localtime(t))
        
        # Create markdown content (simplified for example)
        markdown_content = f"# {title}\n\n{message}\n\n"
        
        # Save markdown file
        with open(f"{self.cache_dir}/{file_name(now)}-post.md", "w") as f:
            f.write(markdown_content)
        
        # ORIGINAL CODE (commented):
        # for destination, account in destinations.items():
        #     logging.info(f" Now in: {destination} - {account}")
        #     if account:
        #         key = ("direct", "post", destination, account)
        #         indent = "  "
        #         api = self.rules.readConfigDst(indent, key, None, None)
        #         try:
        #             result = api.publishImage(title, png_path, alt=alt_text)
        #             if (hasattr(api, "lastRes") and api.lastRes and 
        #                 "media_attachments" in api.lastRes and 
        #                 api.lastRes["media_attachments"] and
        #                 "url" in api.lastRes["media_attachments"][0]):
        #                 image_url = api.lastRes["media_attachments"][0]["url"]
        #             else:
        #                 image_url = None
        #         except Exception as e:
        #             logging.error(f"Failed to publish image to {destination}: {e}")
        #             image_url = None
        #         result = api.publishPost(message, "", "")
        #         logging.info(f"Published to {destination}: {result}")
        
        # REFACTORED CODE:
        results = self.rules.publish_to_multiple_destinations(
            destinations=destinations,
            title=message,  # The message as title
            url="",
            content="",
            image_path=png_path,
            alt_text=alt_text
        )
        
        # Process results
        for service, result in results.items():
            if result['success']:
                logging.info(f"Published to {service}: {result['result']}")
                if result.get('image_url'):
                    logging.info(f"Image URL for {service}: {result['image_url']}")
            else:
                logging.error(f"Failed to publish to {service}: {result['error']}")
        
        return results
    
    def publicar_mensaje_horario(self, destinations, message):
        """
        Refactored version of publicar_mensaje_horario
        
        BEFORE: Independent function with duplicated code
        AFTER: Simplified method using unified logic
        """
        
        # ORIGINAL CODE (commented):
        # for destination, account in destinations.items():
        #     logging.info(f" Now in: {destination} - {account}")
        #     if account:
        #         key = ("direct", "post", destination, account)
        #         indent = "  "
        #         api = self.rules.readConfigDst(indent, key, None, None)
        #         result = api.publishPost(message, "", "")
        #         logging.info(f"Published to {destination}: {result}")
        
        # REFACTORED CODE:
        results = self.rules.publish_message_to_destinations(destinations, message)
        
        # Process results
        for service, result in results.items():
            if result['success']:
                logging.info(f"Published message to {service}: {result['result']}")
            else:
                logging.error(f"Failed to publish message to {service}: {result['error']}")
        
        return results
    
    def generar_reporte_consumo(self, datos_consumo):
        """
        Example method to generate consumption report
        """
        # Simulate data and chart generation
        title = f"Consumption Report - {time.strftime('%Y-%m-%d')}"
        message = f"Total consumption: {datos_consumo.get('total', 0)} kWh"
        
        # In a real case, the chart would be generated here
        png_path = f"{self.cache_dir}/consumption_chart.png"
        alt_text = "Daily electrical consumption chart"
        
        # Simulate image file creation
        with open(png_path, "w") as f:
            f.write("# Simulated image file")
        
        return title, message, png_path, alt_text


def ejemplo_uso_refactorizado():
    """
    Ejemplo de uso de la versión refactorizada
    """
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Crear instancia del bot
    bot = BotElectricoRefactored()
    
    # Definir destinos
    destinations = {
        "mastodon": "mi_cuenta_mastodon",
        "twitter": "mi_cuenta_twitter",
        # "telegram": "mi_canal_telegram"
    }
    
    print("=== Ejemplo Bot Eléctrico Refactorizado ===")
    
    # Ejemplo 1: Publicar gráfico de consumo
    print("\n1. Publicando gráfico de consumo...")
    
    datos_consumo = {"total": 1234, "pico": 156, "valle": 89}
    title, message, png_path, alt_text = bot.generar_reporte_consumo(datos_consumo)
    
    results_grafico = bot.publicar_grafico_consumo(
        destinations=destinations,
        title=title,
        png_path=png_path,
        alt_text=alt_text,
        message=message
    )
    
    # Mostrar resultados
    successful = sum(1 for r in results_grafico.values() if r['success'])
    print(f"Gráfico publicado: {successful}/{len(results_grafico)} exitosas")
    
    # Ejemplo 2: Publicar mensaje horario
    print("\n2. Publicando mensaje horario...")
    
    mensaje_horario = "¡Buenos días! Recordatorio: usa la energía de forma responsable 🌱"
    
    results_mensaje = bot.publicar_mensaje_horario(destinations, mensaje_horario)
    
    # Mostrar resultados
    successful = sum(1 for r in results_mensaje.values() if r['success'])
    print(f"Mensaje publicado: {successful}/{len(results_mensaje)} exitosas")
    
    print("\n=== Comparación de código ===")
    print("ANTES:")
    print("- Código duplicado en múltiples funciones")
    print("- Manejo manual de errores en cada bucle")
    print("- Lógica de configuración repetida")
    print("- Logging inconsistente")
    
    print("\nDESPUÉS:")
    print("- Lógica centralizada en moduleRules")
    print("- Manejo consistente de errores")
    print("- Configuración unificada")
    print("- Logging estandarizado")
    print("- Código más limpio y mantenible")


def comparacion_lineas_codigo():
    """
    Muestra la reducción de líneas de código
    """
    print("\n=== Reducción de Líneas de Código ===")
    
    print("Función original publicar_grafico_consumo:")
    print("- ~25 líneas de código duplicado")
    print("- Manejo manual de APIs")
    print("- Try/except individuales")
    
    print("\nFunción refactorizada:")
    print("- ~8 líneas de código principal")
    print("- Uso de método unificado")
    print("- Manejo automático de errores")
    
    print("\nReducción: ~70% menos código")
    print("Beneficios adicionales:")
    print("- Menos bugs potenciales")
    print("- Más fácil de testear")
    print("- Más fácil de mantener")
    print("- Reutilizable en otros proyectos")


def main():
    """Función principal"""
    
    try:
        ejemplo_uso_refactorizado()
        comparacion_lineas_codigo()
        
    except Exception as e:
        print(f"Error ejecutando ejemplos: {e}")
        logging.error(f"Error en ejemplos: {e}")


if __name__ == "__main__":
    main()