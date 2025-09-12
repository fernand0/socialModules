#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Information about cache storage location and management.
This script provides detailed information about where and how the cache is stored.
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialModules.modulePublicationCache import PublicationCache
from socialModules.configMod import DATADIR, APPDIR, HOME


def show_storage_locations():
    """Show all relevant storage locations"""

    print("=== Publication Cache Storage Information ===\n")

    print("Directory Structure:")
    print(f"HOME: {HOME}")
    print(f"├── .mySocial/ (APPDIR): {APPDIR}")
    print(f"    ├── config/ (CONFIGDIR): {APPDIR}/config")
    print(f"    └── data/ (DATADIR): {DATADIR}")
    print(f"        └── publication_cache.json ← Cache file")
    print()

    # Check if directories exist
    print("Directory Status:")
    directories = [("HOME", HOME), ("APPDIR", APPDIR), ("DATADIR", DATADIR)]

    for name, path in directories:
        exists = os.path.exists(path)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {name}: {status} - {path}")

    print()

    # Cache file info
    cache = PublicationCache()
    cache_file = cache.cache_file

    print("Cache File Information:")
    print(f"  Location: {cache_file}")
    print(f"  Exists: {'✓ YES' if os.path.exists(cache_file) else '✗ NO'}")

    if os.path.exists(cache_file):
        size = os.path.getsize(cache_file)
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
        print(f"  Size: {size} bytes ({size/1024:.1f} KB)")
        print(f"  Last modified: {mtime}")

        # Count publications
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            print(f"  Publications: {len(data)}")
        except:
            print(f"  Publications: Unable to read")

    print()


def show_cache_file_structure():
    """Show the structure of the cache file"""

    print("=== Cache File Structure ===\n")

    print("File Format: JSON")
    print("Encoding: UTF-8")
    print("Structure:")

    example_structure = {
        "publication_id": {
            "id": "site_timestamp",
            "title": "Publication title",
            "original_link": "https://source.com/article",
            "service": "twitter|facebook|linkedin|etc",
            "response_link": "https://platform.com/post/id",
            "publication_date": "ISO 8601 timestamp",
        }
    }

    print(json.dumps(example_structure, indent=2))
    print()


def show_storage_options():
    """Show different storage configuration options"""

    print("=== Storage Configuration Options ===\n")

    options = [
        {
            "option": "Default Location",
            "description": "Use system default location",
            "code": "cache = PublicationCache()",
            "location": "~/.mySocial/data/publication_cache.json",
            "pros": ["Automatic setup", "Consistent with other app data"],
            "cons": ["Fixed location", "Requires .mySocial directory"],
        },
        {
            "option": "Custom File Path",
            "description": "Specify custom cache file location",
            "code": 'cache = PublicationCache("/custom/path/cache.json")',
            "location": "User-specified path",
            "pros": ["Full control", "Can use any location", "Easy backup"],
            "cons": ["Manual path management", "Need to ensure directory exists"],
        },
        {
            "option": "Temporary Location",
            "description": "Use temporary directory (not persistent)",
            "code": 'cache = PublicationCache("/tmp/temp_cache.json")',
            "location": "/tmp/temp_cache.json",
            "pros": ["No permanent storage", "Good for testing"],
            "cons": ["Data lost on reboot", "Not suitable for production"],
        },
        {
            "option": "Project-Specific",
            "description": "Store cache within project directory",
            "code": 'cache = PublicationCache("./project_cache.json")',
            "location": "Current directory",
            "pros": ["Portable with project", "Version control friendly"],
            "cons": ["Multiple cache files", "Needs project structure"],
        },
    ]

    for i, option in enumerate(options, 1):
        print(f"{i}. {option['option']}")
        print(f"   Description: {option['description']}")
        print(f"   Code: {option['code']}")
        print(f"   Location: {option['location']}")
        print("   Pros:")
        for pro in option["pros"]:
            print(f"     ✓ {pro}")
        print("   Cons:")
        for con in option["cons"]:
            print(f"     ✗ {con}")
        print()


def show_backup_strategies():
    """Show different backup strategies for the cache"""

    print("=== Backup Strategies ===\n")

    strategies = [
        {
            "strategy": "Manual Backup",
            "description": "Create backups manually when needed",
            "method": "Copy cache file with timestamp",
            "frequency": "On-demand",
            "automation": "Manual",
            "example": "cp ~/.mySocial/data/publication_cache.json backup_20240115.json",
        },
        {
            "strategy": "Automatic Backup",
            "description": "Script-based automatic backups",
            "method": "Cron job or scheduled task",
            "frequency": "Daily/Weekly",
            "automation": "Automated",
            "example": "python examples/cache_management.py backup",
        },
        {
            "strategy": "Version Control",
            "description": "Store cache in git repository",
            "method": "Git commits of cache file",
            "frequency": "On changes",
            "automation": "Semi-automated",
            "example": "git add publication_cache.json && git commit -m 'Update cache'",
        },
        {
            "strategy": "Export-Based",
            "description": "Regular exports to different formats",
            "method": "Export to CSV/JSON periodically",
            "frequency": "Weekly/Monthly",
            "automation": "Automated",
            "example": "python examples/cache_management.py export",
        },
    ]

    for strategy in strategies:
        print(f"Strategy: {strategy['strategy']}")
        print(f"  Description: {strategy['description']}")
        print(f"  Method: {strategy['method']}")
        print(f"  Frequency: {strategy['frequency']}")
        print(f"  Automation: {strategy['automation']}")
        print(f"  Example: {strategy['example']}")
        print()


def show_maintenance_tips():
    """Show cache maintenance tips"""

    print("=== Cache Maintenance Tips ===\n")

    tips = [
        {
            "tip": "Regular Monitoring",
            "description": "Monitor cache size and performance",
            "actions": [
                "Check file size regularly",
                "Monitor publication count growth",
                "Watch for performance issues",
            ],
        },
        {
            "tip": "Periodic Cleanup",
            "description": "Clean invalid or old entries",
            "actions": [
                "Remove entries with missing required fields",
                "Archive old publications if needed",
                "Validate JSON structure integrity",
            ],
        },
        {
            "tip": "Backup Management",
            "description": "Maintain proper backup procedures",
            "actions": [
                "Create backups before major changes",
                "Test backup restoration procedures",
                "Keep multiple backup versions",
            ],
        },
        {
            "tip": "Performance Optimization",
            "description": "Optimize for large datasets",
            "actions": [
                "Consider database backend for >10k publications",
                "Implement pagination for large queries",
                "Use indexing for frequent searches",
            ],
        },
    ]

    for tip in tips:
        print(f"{tip['tip']}: {tip['description']}")
        for action in tip["actions"]:
            print(f"  • {action}")
        print()


def check_storage_permissions():
    """Check if we have proper permissions for cache storage"""

    print("=== Storage Permissions Check ===\n")

    cache = PublicationCache()
    cache_file = cache.cache_file
    cache_dir = os.path.dirname(cache_file)

    checks = [
        ("Cache directory exists", os.path.exists(cache_dir)),
        (
            "Cache directory writable",
            os.access(cache_dir, os.W_OK) if os.path.exists(cache_dir) else False,
        ),
        ("Cache file exists", os.path.exists(cache_file)),
        (
            "Cache file readable",
            os.access(cache_file, os.R_OK) if os.path.exists(cache_file) else True,
        ),
        (
            "Cache file writable",
            os.access(cache_file, os.W_OK) if os.path.exists(cache_file) else True,
        ),
    ]

    all_good = True

    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {check_name}: {status}")
        if not result:
            all_good = False

    print()

    if all_good:
        print("✓ All permission checks passed - cache should work properly")
    else:
        print("✗ Some permission issues detected")
        print("\nTroubleshooting:")
        print("  • Ensure ~/.mySocial/data/ directory exists")
        print("  • Check directory permissions (should be writable)")
        print("  • Verify disk space availability")
        print("  • Consider using custom cache location if needed")

    print()


def main():
    """Main function"""

    print("PUBLICATION CACHE STORAGE INFORMATION")
    print("=" * 60)
    print()

    try:
        show_storage_locations()
        show_cache_file_structure()
        show_storage_options()
        show_backup_strategies()
        show_maintenance_tips()
        check_storage_permissions()

        print("Summary:")
        print("• Cache stored at: ~/.mySocial/data/publication_cache.json")
        print("• Format: JSON (human-readable)")
        print("• Customizable location available")
        print("• Management tools provided")
        print("• Backup and export capabilities included")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
