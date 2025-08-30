#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cache management utility for the publication cache system.
Provides tools to inspect, backup, and manage the cache file.
"""

import json
import os
import shutil
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialModules.modulePublicationCache import PublicationCache
from socialModules.configMod import DATADIR


def show_cache_info():
    """Display information about the cache file and location"""
    
    print("=== Cache Information ===\n")
    
    cache = PublicationCache()
    cache_file = cache.cache_file
    
    print(f"Cache file location: {cache_file}")
    print(f"DATADIR: {DATADIR}")
    print(f"Cache file exists: {os.path.exists(cache_file)}")
    
    if os.path.exists(cache_file):
        # File size
        size_bytes = os.path.getsize(cache_file)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb > 1:
            size_str = f"{size_mb:.2f} MB"
        elif size_kb > 1:
            size_str = f"{size_kb:.2f} KB"
        else:
            size_str = f"{size_bytes} bytes"
        
        print(f"Cache file size: {size_str}")
        
        # Last modified
        mtime = os.path.getmtime(cache_file)
        last_modified = datetime.fromtimestamp(mtime)
        print(f"Last modified: {last_modified}")
        
        # Number of publications
        publications = cache.get_all_publications()
        print(f"Total publications: {len(publications)}")
        
        # Statistics by service
        stats = cache.get_stats()
        if stats:
            print("\nPublications by service:")
            for service, data in stats.items():
                print(f"  {service}: {data['total']} publications")
    else:
        print("Cache file does not exist yet (will be created on first publication)")
    
    print()


def backup_cache():
    """Create a backup of the cache file"""
    
    print("=== Backup Cache ===\n")
    
    cache = PublicationCache()
    cache_file = cache.cache_file
    
    if not os.path.exists(cache_file):
        print("No cache file to backup")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{cache_file}.backup_{timestamp}"
    
    try:
        shutil.copy2(cache_file, backup_file)
        print(f"✓ Cache backed up to: {backup_file}")
        
        # Show backup info
        size_bytes = os.path.getsize(backup_file)
        print(f"  Backup size: {size_bytes} bytes")
        
        return backup_file
        
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False


def restore_cache(backup_file):
    """Restore cache from a backup file"""
    
    print(f"=== Restore Cache from {backup_file} ===\n")
    
    if not os.path.exists(backup_file):
        print(f"Backup file not found: {backup_file}")
        return False
    
    cache = PublicationCache()
    cache_file = cache.cache_file
    
    try:
        # Create backup of current cache if it exists
        if os.path.exists(cache_file):
            current_backup = f"{cache_file}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(cache_file, current_backup)
            print(f"Current cache backed up to: {current_backup}")
        
        # Restore from backup
        shutil.copy2(backup_file, cache_file)
        print(f"✓ Cache restored from: {backup_file}")
        
        # Verify restoration
        cache = PublicationCache()  # Reload
        publications = cache.get_all_publications()
        print(f"  Restored {len(publications)} publications")
        
        return True
        
    except Exception as e:
        print(f"✗ Restore failed: {e}")
        return False


def export_cache_formats():
    """Export cache to different formats"""
    
    print("=== Export Cache ===\n")
    
    cache = PublicationCache()
    publications = cache.get_all_publications()
    
    if not publications:
        print("No publications to export")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export to CSV
    csv_file = cache.export_to_csv(f"publications_export_{timestamp}.csv")
    if csv_file:
        print(f"✓ Exported to CSV: {csv_file}")
    
    # Export to JSON (pretty formatted)
    json_file = f"publications_export_{timestamp}.json"
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(publications, f, indent=2, ensure_ascii=False, default=str)
        print(f"✓ Exported to JSON: {json_file}")
    except Exception as e:
        print(f"✗ JSON export failed: {e}")
    
    # Export summary
    summary_file = f"publications_summary_{timestamp}.txt"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("PUBLICATION CACHE SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            stats = cache.get_stats()
            f.write(f"Total publications: {len(publications)}\n")
            f.write(f"Export date: {datetime.now()}\n\n")
            
            f.write("Publications by service:\n")
            for service, data in stats.items():
                f.write(f"  {service}: {data['total']} publications\n")
            
            f.write("\nRecent publications:\n")
            for pub in publications[-10:]:
                f.write(f"  {pub['publication_date']}: {pub['title']} ({pub['service']})\n")
        
        print(f"✓ Exported summary: {summary_file}")
        
    except Exception as e:
        print(f"✗ Summary export failed: {e}")


def clean_cache():
    """Clean old or invalid entries from cache"""
    
    print("=== Clean Cache ===\n")
    
    cache = PublicationCache()
    publications = cache.get_all_publications()
    
    if not publications:
        print("No publications to clean")
        return
    
    original_count = len(publications)
    cleaned_count = 0
    
    # Remove entries without required fields
    valid_publications = []
    for pub in publications:
        if pub.get('title') and pub.get('original_link') and pub.get('service'):
            valid_publications.append(pub)
        else:
            cleaned_count += 1
            print(f"Removed invalid entry: {pub.get('id', 'unknown')}")
    
    if cleaned_count > 0:
        # Update cache with cleaned data
        cache.publications = {pub['id']: pub for pub in valid_publications}
        cache._save_cache()
        
        print(f"✓ Cleaned {cleaned_count} invalid entries")
        print(f"  Before: {original_count} publications")
        print(f"  After: {len(valid_publications)} publications")
    else:
        print("✓ No invalid entries found - cache is clean")


def show_cache_statistics():
    """Show detailed cache statistics"""
    
    print("=== Cache Statistics ===\n")
    
    cache = PublicationCache()
    publications = cache.get_all_publications()
    
    if not publications:
        print("No publications in cache")
        return
    
    # Basic stats
    print(f"Total publications: {len(publications)}")
    
    # By site
    stats = cache.get_stats()
    print("\nBy service:")
    for service, data in stats.items():
        success_rate = (data['with_response_link'] / data['total'] * 100) if data['total'] > 0 else 0
        print(f"  {service}: {data['total']} total, {data['with_response_link']} with links ({success_rate:.1f}%)")
    
    # By date
    from collections import defaultdict
    by_date = defaultdict(int)
    
    for pub in publications:
        try:
            date_str = pub['publication_date'][:10]  # YYYY-MM-DD
            by_date[date_str] += 1
        except Exception:
            by_date['unknown'] += 1
    
    print("\nBy date (last 7 days):")
    sorted_dates = sorted(by_date.items(), reverse=True)
    for date, count in sorted_dates[:7]:
        print(f"  {date}: {count} publications")
    
    # Most active links
    link_counts = defaultdict(int)
    for pub in publications:
        link_counts[pub.get('original_link', 'unknown')] += 1
    
    print("\nMost published links:")
    sorted_links = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)
    for link, count in sorted_links[:5]:
        if count > 1:
            print(f"  {count}x: {link}")


def interactive_menu():
    """Interactive menu for cache management"""
    
    while True:
        print("\n" + "=" * 50)
        print("PUBLICATION CACHE MANAGEMENT")
        print("=" * 50)
        print("1. Show cache information")
        print("2. Show cache statistics")
        print("3. Backup cache")
        print("4. Export cache (CSV, JSON, summary)")
        print("5. Clean cache")
        print("6. List backup files")
        print("7. Restore from backup")
        print("0. Exit")
        print()
        
        choice = input("Select option (0-7): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            show_cache_info()
        elif choice == '2':
            show_cache_statistics()
        elif choice == '3':
            backup_cache()
        elif choice == '4':
            export_cache_formats()
        elif choice == '5':
            clean_cache()
        elif choice == '6':
            list_backup_files()
        elif choice == '7':
            restore_from_backup_interactive()
        else:
            print("Invalid option. Please try again.")


def list_backup_files():
    """List available backup files"""
    
    print("=== Available Backup Files ===\n")
    
    cache = PublicationCache()
    cache_dir = os.path.dirname(cache.cache_file)
    cache_name = os.path.basename(cache.cache_file)
    
    backup_files = []
    
    try:
        for file in os.listdir(cache_dir):
            if file.startswith(cache_name) and 'backup' in file:
                backup_path = os.path.join(cache_dir, file)
                mtime = os.path.getmtime(backup_path)
                size = os.path.getsize(backup_path)
                backup_files.append((file, mtime, size))
        
        if backup_files:
            backup_files.sort(key=lambda x: x[1], reverse=True)  # Sort by date
            
            for i, (file, mtime, size) in enumerate(backup_files, 1):
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                print(f"{i}. {file}")
                print(f"   Date: {date_str}, Size: {size_str}")
        else:
            print("No backup files found")
            
    except Exception as e:
        print(f"Error listing backups: {e}")


def restore_from_backup_interactive():
    """Interactive backup restoration"""
    
    print("=== Restore from Backup ===\n")
    
    cache = PublicationCache()
    cache_dir = os.path.dirname(cache.cache_file)
    
    # List backups
    list_backup_files()
    
    backup_file = input("\nEnter backup filename (or full path): ").strip()
    
    if not backup_file:
        print("No file specified")
        return
    
    # If just filename, assume it's in cache directory
    if not os.path.dirname(backup_file):
        backup_file = os.path.join(cache_dir, backup_file)
    
    if not os.path.exists(backup_file):
        print(f"Backup file not found: {backup_file}")
        return
    
    # Confirm restoration
    confirm = input(f"Restore from {backup_file}? This will replace current cache (y/N): ").lower()
    
    if confirm == 'y':
        restore_cache(backup_file)
    else:
        print("Restoration cancelled")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'info':
            show_cache_info()
        elif command == 'stats':
            show_cache_statistics()
        elif command == 'backup':
            backup_cache()
        elif command == 'export':
            export_cache_formats()
        elif command == 'clean':
            clean_cache()
        elif command == 'list-backups':
            list_backup_files()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: info, stats, backup, export, clean, list-backups")
            return 1
    else:
        interactive_menu()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
