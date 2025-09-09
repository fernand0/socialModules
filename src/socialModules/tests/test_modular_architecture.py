from socialModules.moduleRules import moduleRules


def main():
    rules = moduleRules()
    rules.checkRules()  # Processes the configuration file

    # Show generated rules
    print("Generated rules:")
    for src, actions in rules.rules.items():
        print(f"Source: {src}")
        for action in actions:
            print(f"  Action: {action}")

    print("\nAvailable sources:")
    for key, value in rules.available.items():
        print(f"{key}: {value}")

    print("\nAvailable list:")
    print(rules.availableList)


if __name__ == "__main__":
    main()
