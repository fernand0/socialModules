#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module to manage a publication cache that stores:
- Publication title
- Original link
- Service response link (if available)
- Service where it was published
- Publication date
"""

import json
import os
import shutil
import sys
import logging
from datetime import datetime
from socialModules.configMod import DATADIR


class PublicationCache:

    def __init__(self, cache_file=None):
        """
        Initialize the publication cache

        Args:
            cache_file: File to store the cache. If not specified,
                       uses a default file in DATADIR
        """
        if cache_file:
            self.cache_file = cache_file
        else:
            self.cache_file = os.path.join(DATADIR, "publication_cache.json")

        self.publications = self._load_cache()

    def _load_cache(self):
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error loading cache: {e}. Starting empty cache.")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.publications, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logging.error(f"Error saving cache: {e}")
            return False

    def add_publication(self, title, original_link, service, source_service=None, response_link=None,
                       publication_date=None, user=None):
        """
        Add a new publication to the cache

        Args:
            title: Publication title
            original_link: Original content link
            service: Service where it was published (twitter, facebook, etc.)
            source_service: Service from where the content was obtained (optional)
            response_link: Service response link (optional)
            publication_date: Publication date (optional, uses current date if not specified)
            user: User account used for publication (optional)

        Returns:
            str: Unique ID of the added publication
        """
        if publication_date is None:
            publication_date = datetime.now().isoformat()

        logging.info(f"Adding publication with title: {title}, service: {service}, user: {user}")

        # Generate unique ID based on timestamp and service
        pub_id = f"{service}_{int(datetime.now().timestamp())}"

        publication = {
            'id': pub_id,
            'title': title,
            'original_link': original_link,
            'source_service': source_service,
            'service': service,
            'user': user,
            'response_link': response_link,
            'publication_date': publication_date
        }

        logging.debug(f"Publication data: {publication}")

        self.publications[pub_id] = publication

        if self._save_cache():
            logging.info(f"Publication added: {title} in {service}")
            return pub_id
        else:
            logging.error(f"Error saving publication: {title}")
            return None

    def update_response_link(self, pub_id, response_link):
        """
        Update the response link of an existing publication

        Args:
            pub_id: Publication ID
            response_link: New response link

        Returns:
            bool: True if updated successfully
        """
        if pub_id in self.publications:
            self.publications[pub_id]['response_link'] = response_link
            if self._save_cache():
                logging.info(f"Response link updated for {pub_id}")
                return True

        logging.warning(f"Publication {pub_id} not found")
        return False

    def get_publication(self, pub_id):
        """
        Get a publication by its ID

        Args:
            pub_id: Publication ID

        Returns:
            dict: Publication data or None if it doesn't exist
        """
        return self.publications.get(pub_id)

    def get_publications_by_service(self, service):
        """
        Get all publications from a specific service

        Args:
            service: Service name

        Returns:
            list: List of publications from the service
        """
        return [pub for pub in self.publications.values() if pub['service'] == service]

    def get_publications_by_original_link(self, original_link):
        """
        Search publications by original link

        Args:
            original_link: Original link to search for

        Returns:
            list: List of publications with that original link
        """
        return [pub for pub in self.publications.values()
                if pub['original_link'] == original_link]

    def search_publications(self, query, field='title'):
        """
        Search publications by text in a specific field

        Args:
            query: Text to search for
            field: Field to search in ('title', 'original_link', 'service')

        Returns:
            list: List of matching publications
        """
        results = []
        query_lower = query.lower()

        for pub in self.publications.values():
            if field in pub and query_lower in str(pub[field]).lower():
                results.append(pub)

        return results

    def delete_publication(self, pub_id):
        """
        Delete a publication from the cache

        Args:
            pub_id: ID of the publication to delete

        Returns:
            bool: True if deleted successfully
        """
        if pub_id in self.publications:
            del self.publications[pub_id]
            if self._save_cache():
                logging.info(f"Publication {pub_id} deleted")
                return True

        logging.warning(f"Publication {pub_id} not found for deletion")
        return False

    def get_all_publications(self, sort_by='publication_date', reverse=True):
        """
        Get all publications sorted

        Args:
            sort_by: Field to sort by
            reverse: Whether to sort in descending order

        Returns:
            list: Sorted list of publications
        """
        publications = list(self.publications.values())

        try:
            publications.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
        except (TypeError, KeyError):
            logging.warning(f"Could not sort by {sort_by}")

        return publications

    def get_stats(self):
        """
        Get cache statistics

        Returns:
            dict: Publication statistics by service
        """
        stats = {}

        for pub in self.publications.values():
            service = pub['service']
            if service not in stats:
                stats[service] = {
                    'total': 0,
                    'with_response_link': 0,
                    'without_response_link': 0
                }

            stats[service]['total'] += 1

            if pub.get('response_link'):
                stats[service]['with_response_link'] += 1
            else:
                stats[service]['without_response_link'] += 1

        return stats

    def export_to_csv(self, filename=None):
        """
        Export publications to a CSV file

        Args:
            filename: CSV filename (optional)

        Returns:
            str: Path of the created file or None if there was an error
        """
        import csv

        if filename is None:
            filename = os.path.join(DATADIR, "publications_export.csv")

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'title', 'original_link', 'source_service', 'service', 'user',
                             'response_link', 'publication_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for pub in self.publications.values():
                    row = {field: pub.get(field, '') for field in fieldnames}
                    writer.writerow(row)

            logging.info(f"Publications exported to {filename}")
            return filename

        except IOError as e:
            logging.error(f"Error exporting to CSV: {e}")
            return None

    def show_info(self):
        """Display information about the cache file and location"""
        
        print("=== Cache Information ===\n")
        
        cache_file = self.cache_file
        
        print(f"Cache file location: {cache_file}")
        print(f"DATADIR: {DATADIR})")
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
            publications = self.get_all_publications()
            print(f"Total publications: {len(publications)}")
            
            # Statistics by service
            stats = self.get_stats()
            if stats:
                print("\nPublications by service:")
                for service, data in stats.items():
                    print(f"  {service}: {data['total']} publications")
        else:
            print("Cache file does not exist yet (will be created on first publication)")
        
        print()

    def backup(self):
        """Create a backup of the cache file"""
        
        print("=== Backup Cache ===\n")
        
        cache_file = self.cache_file
        
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

    def restore(self, backup_file):
        """Restore cache from a backup file"""
        
        print(f"=== Restore Cache from {backup_file} ===\n")
        
        if not os.path.exists(backup_file):
            print(f"Backup file not found: {backup_file}")
            return False
        
        cache_file = self.cache_file
        
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
            self.publications = self._load_cache()
            publications = self.get_all_publications()
            print(f"  Restored {len(publications)} publications")
            
            return True
            
        except Exception as e:
            print(f"✗ Restore failed: {e}")
            return False

    def export_formats(self):
        """Export cache to different formats"""
        
        print("=== Export Cache ===\n")
        
        publications = self.get_all_publications()
        
        if not publications:
            print("No publications to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export to CSV
        csv_file = self.export_to_csv(f"publications_export_{timestamp}.csv")
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
                
                stats = self.get_stats()
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

    def clean(self):
        """Clean old or invalid entries from cache"""
        
        print("=== Clean Cache ===\n")
        
        publications = self.get_all_publications()
        
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
            self.publications = {pub['id']: pub for pub in valid_publications}
            self._save_cache()
            
            print(f"✓ Cleaned {cleaned_count} invalid entries")
            print(f"  Before: {original_count} publications")
            print(f"  After: {len(valid_publications)} publications")
        else:
            print("✓ No invalid entries found - cache is clean")

    def show_statistics(self):
        """Show detailed cache statistics"""
        from collections import defaultdict
        from urllib.parse import urlparse

        print("=== Cache Statistics ===\n")
        
        publications = self.get_all_publications()
        
        if not publications:
            print("No publications in cache")
            return
        
        # Basic stats
        print(f"Total publications: {len(publications)}")
        
        # By site
        stats = self.get_stats()
        print("\nBy service:")
        for service, data in stats.items():
            success_rate = (data['with_response_link'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {service}: {data['total']} total, {data['with_response_link']} with links ({success_rate:.1f}%)")

        # By domain
        domain_counts = defaultdict(int)
        for pub in publications:
            link = pub.get('original_link')
            if link:
                try:
                    domain = urlparse(link).netloc
                    if domain:
                        domain_counts[domain] += 1
                except Exception:
                    pass  # Ignore parsing errors

        if domain_counts:
            print("\nBy domain:")
            sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains:
                print(f"  {domain}: {count} publications")
        
        # By date
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

    def list_backups(self):
        """List available backup files"""
        
        print("=== Available Backup Files ===\n")
        
        cache_dir = os.path.dirname(self.cache_file)
        cache_name = os.path.basename(self.cache_file)
        
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

    def interactive_restore(self):
        """Interactive backup restoration"""
        
        print("=== Restore from Backup ===\n")
        
        cache_dir = os.path.dirname(self.cache_file)
        
        # List backups
        self.list_backups()
        
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
            self.restore(backup_file)
        else:
            print("Restoration cancelled")

def interactive_menu():
    """Interactive menu for cache management"""
    
    cache = PublicationCache()
    
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
            cache.show_info()
        elif choice == '2':
            cache.show_statistics()
        elif choice == '3':
            cache.backup()
        elif choice == '4':
            cache.export_formats()
        elif choice == '5':
            cache.clean()
        elif choice == '6':
            cache.list_backups()
        elif choice == '7':
            cache.interactive_restore()
        else:
            print("Invalid option. Please try again.")

def main():
    """Main function for CLI operations"""

    # Configure logging (if not already configured)
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')

    cache = PublicationCache() # Create an instance here

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'info':
            cache.show_info()
        elif command == 'stats':
            cache.show_statistics()
        elif command == 'backup':
            cache.backup()
        elif command == 'export':
            cache.export_formats()
        elif command == 'clean':
            cache.clean()
        elif command == 'list-backups':
            cache.list_backups()
        elif command == 'restore': # Add restore command
            if len(sys.argv) > 2:
                backup_file = sys.argv[2]
                cache.restore(backup_file)
            else:
                print("Usage: python modulePublicationCache.py restore <backup_file>")
                return 1
        else:
            print(f"Unknown command: {command}")
            print("Available commands: info, stats, backup, export, clean, list-backups, restore")
            return 1
    else:
        interactive_menu() # Call the interactive menu

    return 0


if __name__ == "__main__":
    sys.exit(main())
