#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example showing how to integrate auto-cache with the rules system.
Demonstrates configuration via moduleRules and setMoreValues.
"""

import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def demo_rules_integration():
    """Demonstrate integration with the rules system"""

    print("=== Rules System Integration Demo ===\n")

    # Example configuration that could be added to rules
    example_rules_config = {
        "twitter_personal": {
            "src": ("rss", "https://myblog.com/feed.xml"),
            "dst": ("twitter", "my_personal_account"),
            "more": {
                "auto_cache": True,  # Enable auto-caching
                "max": 5,
                "time": 3600,
                "tags": ["personal", "blog"],
            },
        },
        "facebook_business": {
            "src": ("rss", "https://business.com/feed.xml"),
            "dst": ("facebook", "business_page"),
            "more": {
                "auto_cache": True,  # Enable auto-caching
                "max": 3,
                "time": 7200,
                "audience": "public",
            },
        },
        "linkedin_professional": {
            "src": ("rss", "https://professional.com/feed.xml"),
            "dst": ("linkedin", "professional_profile"),
            "more": {
                "auto_cache": False,  # Explicitly disable (optional)
                "max": 2,
                "time": 14400,
            },
        },
    }

    print("Example rules configuration with auto_cache:")
    print("```python")
    for rule_name, config in example_rules_config.items():
        print(f"'{rule_name}': {{")
        print(f"    'src': {config['src']},")
        print(f"    'dst': {config['dst']},")
        print(f"    'more': {{")
        for key, value in config["more"].items():
            if key == "auto_cache":
                print(
                    f"        '{key}': {value},  # {'Enable' if value else 'Disable'} auto-caching"
                )
            else:
                print(f"        '{key}': {value},")
        print(f"    }}")
        print(f"}},")
    print("```")
    print()


def demo_selective_caching():
    """Show how to enable caching selectively"""

    print("=== Selective Caching Demo ===\n")

    scenarios = [
        {
            "name": "Production Blog Posts",
            "description": "Enable caching for important content",
            "config": {"auto_cache": True, "tags": ["production", "blog"]},
            "reason": "Track publication success and analytics",
        },
        {
            "name": "Test Publications",
            "description": "Disable caching for test content",
            "config": {"auto_cache": False, "tags": ["test", "debug"]},
            "reason": "Avoid cluttering cache with test data",
        },
        {
            "name": "High-Volume Feeds",
            "description": "Enable caching with limits",
            "config": {"auto_cache": True, "max_cache_size": 1000},
            "reason": "Monitor performance while limiting storage",
        },
        {
            "name": "Legacy Systems",
            "description": "Keep existing behavior",
            "config": {},  # No auto_cache setting = disabled by default
            "reason": "Maintain backward compatibility",
        },
    ]

    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"  Description: {scenario['description']}")
        print(f"  Configuration: {scenario['config']}")
        print(f"  Reason: {scenario['reason']}")
        print()


def demo_configuration_methods():
    """Show different ways to configure auto-cache in rules"""

    print("=== Configuration Methods Demo ===\n")

    print("Method 1: Direct in rules configuration")
    print("```python")
    print("rules = {")
    print("    'my_rule': {")
    print("        'src': ('rss', 'https://blog.com/feed'),")
    print("        'dst': ('twitter', 'account'),")
    print("        'more': {")
    print("            'auto_cache': True,  # Enable here")
    print("            'max': 5")
    print("        }")
    print("    }")
    print("}")
    print("```")
    print()

    print("Method 2: Environment-based configuration")
    print("```python")
    print("import os")
    print("")
    print("# In rules or configuration")
    print("enable_cache = os.getenv('ENABLE_CACHE', 'false').lower() == 'true'")
    print("")
    print("rules = {")
    print("    'my_rule': {")
    print("        'more': {")
    print("            'auto_cache': enable_cache,")
    print("            'max': 5")
    print("        }")
    print("    }")
    print("}")
    print("```")
    print()

    print("Method 3: Conditional based on service")
    print("```python")
    print("# Enable caching only for specific services")
    print("cache_enabled_services = ['twitter', 'facebook', 'linkedin']")
    print("")
    print("for rule_name, rule_config in rules.items():")
    print("    service = rule_config['dst'][0]")
    print("    if service in cache_enabled_services:")
    print("        rule_config['more']['auto_cache'] = True")
    print("```")
    print()


def demo_migration_strategy():
    """Show a practical migration strategy"""

    print("=== Migration Strategy Demo ===\n")

    phases = [
        {
            "phase": "Phase 1: Preparation",
            "duration": "1 week",
            "actions": [
                "Deploy code with auto_cache=False (default)",
                "Test that existing functionality is unchanged",
                "Verify no performance impact",
            ],
        },
        {
            "phase": "Phase 2: Pilot Testing",
            "duration": "2 weeks",
            "actions": [
                "Enable auto_cache for 1-2 non-critical rules",
                "Monitor cache performance and storage",
                "Test search and analytics functionality",
            ],
        },
        {
            "phase": "Phase 3: Gradual Rollout",
            "duration": "4 weeks",
            "actions": [
                "Enable for 25% of rules in week 1",
                "Enable for 50% of rules in week 2",
                "Enable for 75% of rules in week 3",
                "Enable for all rules in week 4",
            ],
        },
        {
            "phase": "Phase 4: Optimization",
            "duration": "Ongoing",
            "actions": [
                "Analyze publication patterns",
                "Optimize cache configuration",
                "Build analytics dashboards",
                "Add custom extractors as needed",
            ],
        },
    ]

    for phase in phases:
        print(f"{phase['phase']} ({phase['duration']})")
        for action in phase["actions"]:
            print(f"  • {action}")
        print()


def demo_troubleshooting():
    """Show common troubleshooting scenarios"""

    print("=== Troubleshooting Demo ===\n")

    issues = [
        {
            "issue": "Publications not being cached",
            "causes": [
                "auto_cache is disabled (default)",
                "Publication failed (only successful pubs are cached)",
                "Missing title or link in publication",
            ],
            "solutions": [
                "Check api.getAutoCache() returns True",
                "Verify publishPost returns success",
                "Ensure title and link are provided",
            ],
        },
        {
            "issue": "Cache file growing too large",
            "causes": ["High publication volume", "No cache size limits configured"],
            "solutions": [
                "Set MAX_CACHE_SIZE in configuration",
                "Implement cache rotation policy",
                "Export and archive old data",
            ],
        },
        {
            "issue": "Response links not extracted",
            "causes": [
                "Unsupported platform response format",
                "API response structure changed",
            ],
            "solutions": [
                "Add custom extractor for platform",
                "Check API response format",
                "Update extraction logic",
            ],
        },
    ]

    for issue in issues:
        print(f"Issue: {issue['issue']}")
        print("  Possible causes:")
        for cause in issue["causes"]:
            print(f"    • {cause}")
        print("  Solutions:")
        for solution in issue["solutions"]:
            print(f"    • {solution}")
        print()


def main():
    """Main function that runs all demonstrations"""

    print("RULES SYSTEM INTEGRATION FOR PUBLICATION CACHE")
    print("=" * 60)
    print()

    try:
        demo_rules_integration()
        demo_selective_caching()
        demo_configuration_methods()
        demo_migration_strategy()
        demo_troubleshooting()

        print("Integration guide completed!")
        print("\nNext Steps:")
        print("1. Add 'auto_cache': True to rules where caching is desired")
        print("2. Test with a small subset of rules first")
        print("3. Monitor cache performance and storage usage")
        print("4. Gradually enable for all rules")
        print("5. Build analytics and reporting on cached data")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        logging.error(f"Error in demonstration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
