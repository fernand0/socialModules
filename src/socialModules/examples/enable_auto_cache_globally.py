#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script to enable auto-cache globally for all modules.
This can be used if you want to enable caching for all publications
without modifying individual rules.
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def patch_content_class_for_auto_cache():
    """
    Patch the Content class to enable auto_cache by default.
    This is a global way to enable caching without changing individual rules.
    """

    from socialModules.moduleContent import Content

    # Store original __init__ method
    original_init = Content.__init__

    def patched_init(self, indent=""):
        # Call original init
        original_init(self, indent)
        # Enable auto_cache by default
        self.auto_cache = True
        print(f"Auto-cache enabled globally for {self.__class__.__name__}")

    # Replace the __init__ method
    Content.__init__ = patched_init

    print("✓ Content class patched - auto_cache now enabled by default")
    return True


def enable_auto_cache_via_environment():
    """
    Enable auto-cache based on environment variable.
    Set ENABLE_AUTO_CACHE=true to enable globally.
    """

    import os

    if os.getenv("ENABLE_AUTO_CACHE", "false").lower() == "true":
        patch_content_class_for_auto_cache()
        return True
    else:
        print(
            "Auto-cache not enabled via environment (set ENABLE_AUTO_CACHE=true to enable)"
        )
        return False


def create_auto_cache_config_file():
    """
    Create a configuration file that enables auto-cache globally.
    """

    config_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global auto-cache configuration.
Import this module to enable auto-cache for all Content-based modules.
"""

# Enable auto-cache globally by patching the Content class
def enable_global_auto_cache():
    """Enable auto-cache for all Content-based modules"""
    
    try:
        from socialModules.moduleContent import Content
        
        # Store original __init__
        if not hasattr(Content, '_original_init'):
            Content._original_init = Content.__init__
            
            def auto_cache_init(self, indent=""):
                # Call original init
                Content._original_init(self, indent)
                # Enable auto_cache by default
                self.auto_cache = True
            
            # Replace __init__
            Content.__init__ = auto_cache_init
            
        print("✓ Global auto-cache enabled")
        return True
        
    except Exception as e:
        print(f"✗ Failed to enable global auto-cache: {e}")
        return False


# Auto-enable when this module is imported
if __name__ != "__main__":
    enable_global_auto_cache()


if __name__ == "__main__":
    print("Global Auto-Cache Configuration")
    print("=" * 40)
    print()
    print("This script enables auto-cache globally for all modules.")
    print()
    print("Usage options:")
    print("1. Import this module: from examples import global_auto_cache_config")
    print("2. Set environment: ENABLE_AUTO_CACHE=true")
    print("3. Run this script directly to patch the class")
    print()
    
    enable_global_auto_cache()
'''

    config_file = os.path.join(os.path.dirname(__file__), "global_auto_cache_config.py")

    with open(config_file, "w") as f:
        f.write(config_content)

    print(f"✓ Created global auto-cache config: {config_file}")
    return config_file


def demo_global_enabling_methods():
    """Demonstrate different methods to enable auto-cache globally"""

    print("=== Global Auto-Cache Enabling Methods ===\n")

    methods = [
        {
            "method": "Method 1: Environment Variable",
            "description": "Set ENABLE_AUTO_CACHE=true before running",
            "code": """
# In shell:
export ENABLE_AUTO_CACHE=true
python your_script.py

# Or in Python:
import os
os.environ['ENABLE_AUTO_CACHE'] = 'true'
from examples.enable_auto_cache_globally import enable_auto_cache_via_environment
enable_auto_cache_via_environment()
""",
            "pros": ["Easy to toggle", "No code changes"],
            "cons": ["Affects all processes", "Environment dependent"],
        },
        {
            "method": "Method 2: Import Patch Module",
            "description": "Import a module that patches the Content class",
            "code": """
# At the top of your main script:
from examples import global_auto_cache_config

# Now all Content-based modules have auto_cache enabled
""",
            "pros": ["Simple import", "Centralized control"],
            "cons": ["Affects all modules", "Less granular control"],
        },
        {
            "method": "Method 3: Direct Patching",
            "description": "Directly patch the Content class in your code",
            "code": """
from examples.enable_auto_cache_globally import patch_content_class_for_auto_cache

# Enable auto-cache globally
patch_content_class_for_auto_cache()

# Now create modules normally - they'll have auto_cache enabled
""",
            "pros": ["Explicit control", "Clear intent"],
            "cons": ["Requires code change", "Monkey patching"],
        },
        {
            "method": "Method 4: Configuration-Based",
            "description": "Enable via rules configuration",
            "code": """
# In your rules processing:
def process_rules(rules):
    for rule_name, rule_config in rules.items():
        if 'more' not in rule_config:
            rule_config['more'] = {}
        rule_config['more']['auto_cache'] = True
    return rules
""",
            "pros": ["Granular control", "Rule-specific"],
            "cons": ["Requires rule modification", "More complex"],
        },
    ]

    for method in methods:
        print(f"{method['method']}")
        print(f"Description: {method['description']}")
        print("Code:")
        print(method["code"])
        print("Pros:")
        for pro in method["pros"]:
            print(f"  ✓ {pro}")
        print("Cons:")
        for con in method["cons"]:
            print(f"  ✗ {con}")
        print()


def demo_selective_vs_global():
    """Compare selective vs global enabling approaches"""

    print("=== Selective vs Global Enabling ===\n")

    approaches = [
        {
            "approach": "Selective Enabling (Recommended)",
            "description": "Enable auto-cache only for specific modules/rules",
            "when_to_use": [
                "You want fine-grained control",
                "Different rules have different caching needs",
                "You want to test gradually",
                "You have mixed production/test environments",
            ],
            "how_to": [
                "Add auto_cache: true to specific rules",
                "Use setAutoCache(True) for specific modules",
                "Configure based on environment or service type",
            ],
            "example": """
# In rules:
rules = {
    'production_blog': {
        'more': {'auto_cache': True}  # Enable for production
    },
    'test_posts': {
        'more': {'auto_cache': False}  # Disable for testing
    }
}
""",
        },
        {
            "approach": "Global Enabling",
            "description": "Enable auto-cache for all modules by default",
            "when_to_use": [
                "You want caching everywhere",
                "Simple deployment with uniform behavior",
                "All your content is production-ready",
                "You want maximum data collection",
            ],
            "how_to": [
                "Patch the Content class globally",
                "Set environment variable",
                "Import global configuration module",
            ],
            "example": """
# At application startup:
from examples.enable_auto_cache_globally import patch_content_class_for_auto_cache
patch_content_class_for_auto_cache()

# Now all modules have auto_cache enabled by default
""",
        },
    ]

    for approach in approaches:
        print(f"{approach['approach']}")
        print(f"Description: {approach['description']}")
        print("When to use:")
        for when in approach["when_to_use"]:
            print(f"  • {when}")
        print("How to implement:")
        for how in approach["how_to"]:
            print(f"  • {how}")
        print("Example:")
        print(approach["example"])
        print()


def main():
    """Main function"""

    print("GLOBAL AUTO-CACHE ENABLING UTILITY")
    print("=" * 50)
    print()

    try:
        demo_global_enabling_methods()
        demo_selective_vs_global()

        print("Recommendations:")
        print("1. Start with selective enabling for better control")
        print("2. Use global enabling only if you want caching everywhere")
        print("3. Consider environment-based configuration for flexibility")
        print("4. Test thoroughly before enabling globally in production")
        print()

        # Offer to create config file
        response = input("Create global auto-cache config file? (y/n): ").lower()
        if response == "y":
            config_file = create_auto_cache_config_file()
            print(f"Config file created: {config_file}")
            print("Import it with: from examples import global_auto_cache_config")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
