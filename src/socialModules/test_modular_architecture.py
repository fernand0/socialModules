from moduleRules import moduleRules


def main():
    rules = moduleRules()
    rules.checkRules()  # Procesa el archivo de configuración

    # Muestra las reglas generadas
    print("Reglas generadas:")
    for src, actions in rules.rules.items():
        print(f"Fuente: {src}")
        for action in actions:
            print(f"  Acción: {action}")

    print("\nFuentes disponibles:")
    for key, value in rules.available.items():
        print(f"{key}: {value}")

    print("\nLista de disponibles:")
    print(rules.availableList)


if __name__ == "__main__":
    main()
