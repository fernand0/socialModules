#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example demonstrating optional automatic publication caching.
Shows how to enable/disable auto-caching for backward compatibility.
"""

import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialModules.modulePublicationCache import PublicationCache


def demo_optional_caching():
    """Demonstrate optional auto-caching functionality"""
    
    print("=== Optional Auto-Caching Demo ===\n")
    
    # Create a mock social media module for demonstration
    class MockSocialModule:
        def __init__(self, service_name):
            self.service = service_name
            self.user = "test_user"
            self.nick = "test_nick"
            self.indent = ""
            # Import the Content class methods
            from socialModules.moduleContent import Content
            # Copy the auto-cache functionality
            self.auto_cache = False
            self.setAutoCache = Content.setAutoCache.__get__(self, MockSocialModule)
            self.getAutoCache = Content.getAutoCache.__get__(self, MockSocialModule)
            self.publishPost = Content.publishPost.__get__(self, MockSocialModule)
            self._cache_publication_if_successful = Content._cache_publication_if_successful.__get__(self, MockSocialModule)
            self._extract_response_link_from_reply = Content._extract_response_link_from_reply.__get__(self, MockSocialModule)
        
        def getService(self):
            return self.service
        
        def getUser(self):
            return self.user
        
        def getNick(self):
            return self.nick
        
        def processReply(self, reply):
            return reply
        
        def report(self, service, title, link, exc_info):
            return f"Error in {service}: {title}"
        
        def publishApiPost(self, title, link, comment):
            # Simulate successful publication
            if self.service == 'twitter':
                return {'id': '1234567890123456789', 'text': f"{title} {link}"}
            elif self.service == 'facebook':
                return {'post_id': 'user_987654321', 'message': f"{title}\n{link}"}
            else:
                return "Published successfully"
    
    # Clear any existing cache for clean demo
    cache = PublicationCache()
    initial_count = len(cache.get_all_publications())
    
    print("1. Testing with auto-cache DISABLED (default behavior)")
    print("   This maintains backward compatibility - no caching occurs")
    
    # Create module with auto-cache disabled (default)
    twitter_module = MockSocialModule('twitter')
    print(f"   Auto-cache enabled: {twitter_module.getAutoCache()}")
    
    # Publish without caching
    result1 = twitter_module.publishPost(
        "Test post without caching",
        "https://blog.com/test-no-cache",
        "This should not be cached"
    )
    
    print(f"   Publication result: {result1}")
    
    # Check cache - should be unchanged
    after_disabled_count = len(cache.get_all_publications())
    print(f"   Publications in cache: {after_disabled_count} (unchanged from {initial_count})")
    print()
    
    print("2. Testing with auto-cache ENABLED")
    print("   This enables the new caching functionality")
    
    # Enable auto-cache
    twitter_module.setAutoCache(True)
    print(f"   Auto-cache enabled: {twitter_module.getAutoCache()}")
    
    # Publish with caching
    result2 = twitter_module.publishPost(
        "Test post with caching",
        "https://blog.com/test-with-cache",
        "This should be cached automatically"
    )
    
    print(f"   Publication result: {result2}")
    
    # Check cache - should have new entry
    after_enabled_count = len(cache.get_all_publications())
    print(f"   Publications in cache: {after_enabled_count} (increased by {after_enabled_count - after_disabled_count})")
    print()
    
    print("3. Testing configuration via setMoreValues")
    
    # Create new module and configure via setMoreValues
    facebook_module = MockSocialModule('facebook')
    
    # Configure with auto_cache enabled
    config = {
        'auto_cache': True,
        'url': 'https://facebook.com/mypage'
    }
    
    # Simulate setMoreValues (simplified version)
    for option, value in config.items():
        if option == 'auto_cache':
            facebook_module.setAutoCache(value)
    
    print(f"   Facebook module auto-cache: {facebook_module.getAutoCache()}")
    
    # Publish with configured module
    result3 = facebook_module.publishPost(
        "Facebook post with auto-cache",
        "https://blog.com/facebook-post",
        "Configured via setMoreValues"
    )
    
    print(f"   Publication result: {result3}")
    
    final_count = len(cache.get_all_publications())
    print(f"   Final cache count: {final_count}")
    print()


def demo_backward_compatibility():
    """Demonstrate that existing code continues to work unchanged"""
    
    print("=== Backward Compatibility Demo ===\n")
    
    # Simulate existing code that doesn't know about auto-cache
    class ExistingModule:
        def __init__(self):
            # Import Content functionality
            from socialModules.moduleContent import Content
            # Initialize like existing modules do
            Content.__init__(self, "")
            self.service = "existing_service"
            self.user = "existing_user"
        
        def publishApiPost(self, title, link, comment):
            return "Legacy publication successful"
        
        # Import required methods
        from socialModules.moduleContent import Content
        publishPost = Content.publishPost
        processReply = Content.processReply
        report = Content.report
        getService = Content.getService
        getUser = Content.getUser
        getNick = Content.getNick
        getAutoCache = Content.getAutoCache
    
    print("Testing existing module (should work exactly as before):")
    
    # Create existing-style module
    existing = ExistingModule()
    
    print(f"   Auto-cache (default): {existing.getAutoCache()}")
    print("   Publishing with existing code...")
    
    # Use existing publishPost method - should work without caching
    result = existing.publishPost(
        "Legacy publication",
        "https://legacy.com/post",
        "This uses existing code patterns"
    )
    
    print(f"   Result: {result}")
    print("   ✓ Existing code works unchanged")
    print("   ✓ No caching occurs (backward compatible)")
    print()


def demo_migration_path():
    """Show how to gradually migrate to using auto-cache"""
    
    print("=== Migration Path Demo ===\n")
    
    print("Step 1: Existing code (no changes)")
    print("   - All existing modules work as before")
    print("   - No caching occurs")
    print("   - Zero breaking changes")
    print()
    
    print("Step 2: Enable auto-cache selectively")
    print("   - Add setAutoCache(True) to specific modules")
    print("   - Or configure via setMoreValues({'auto_cache': True})")
    print("   - Only enabled modules start caching")
    print()
    
    print("Step 3: Gradual rollout")
    print("   - Enable for non-critical modules first")
    print("   - Monitor cache performance")
    print("   - Enable for all modules when confident")
    print()
    
    print("Step 4: Optional - Use advanced features")
    print("   - Custom configuration via publication_cache_config.py")
    print("   - Manual caching with PublisherWithCache")
    print("   - Analytics and reporting")
    print()


def demo_configuration_options():
    """Show different ways to configure auto-cache"""
    
    print("=== Configuration Options Demo ===\n")
    
    # Method 1: Direct method call
    print("Method 1: Direct method call")
    from socialModules.moduleContent import Content
    
    class TestModule(Content):
        def __init__(self):
            super().__init__()
            self.service = "test"
    
    module1 = TestModule()
    module1.setAutoCache(True)
    print(f"   setAutoCache(True): {module1.getAutoCache()}")
    
    module1.setAutoCache(False)
    print(f"   setAutoCache(False): {module1.getAutoCache()}")
    print()
    
    # Method 2: Via setMoreValues (configuration-driven)
    print("Method 2: Via configuration")
    module2 = TestModule()
    
    # Simulate configuration from file/rules
    config = {'auto_cache': True, 'url': 'https://test.com'}
    module2.setMoreValues(config)
    print(f"   Via setMoreValues: {module2.getAutoCache()}")
    print()
    
    # Method 3: Environment-based
    print("Method 3: Environment-based (example)")
    module3 = TestModule()
    
    # Example: Enable based on environment
    import os
    enable_cache = os.getenv('ENABLE_PUBLICATION_CACHE', 'false').lower() == 'true'
    module3.setAutoCache(enable_cache)
    print(f"   Environment-based: {module3.getAutoCache()} (ENABLE_PUBLICATION_CACHE={os.getenv('ENABLE_PUBLICATION_CACHE', 'false')})")
    print()


def main():
    """Main function that runs all demonstrations"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("OPTIONAL PUBLICATION CACHING SYSTEM")
    print("=" * 50)
    print()
    
    try:
        # Run demonstrations
        demo_optional_caching()
        demo_backward_compatibility()
        demo_migration_path()
        demo_configuration_options()
        
        print("All demonstrations completed successfully!")
        print("\nKey Points:")
        print("✓ Auto-cache is DISABLED by default (backward compatible)")
        print("✓ Enable with setAutoCache(True) or via configuration")
        print("✓ Existing code works unchanged")
        print("✓ Gradual migration path available")
        print("✓ Multiple configuration methods supported")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        logging.error(f"Error in demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())