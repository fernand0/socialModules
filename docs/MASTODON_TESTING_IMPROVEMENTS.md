# moduleMastodon Testing Improvements

## Overview

Enhanced the `main()` function in `moduleMastodon.py` to provide comprehensive interactive testing capabilities. The new system offers a user-friendly menu-driven interface for testing various Mastodon operations, similar to the improvements made in `moduleSmtp.py`.

## New Interactive Testing Features

### **Main Menu System**
```
Available test modes:
1. Connection test
2. Posts retrieval test
3. Favorites test
4. Basic post test
5. Image post test
6. Cache integration test
7. Post deletion test
8. Favorites management test
9. Custom post
10. Browse posts
```

### **Test Scenarios**

#### **1. Connection Test**
- Validates Mastodon API connection
- Displays user account information
- Shows follower/following counts
- Verifies authentication status

```python
✓ Connected as: Display Name (@username)
  Account ID: 12345
  Followers: 150
  Following: 200
  Posts: 1250
```

#### **2. Posts Retrieval Test**
- Fetches user's recent posts
- Displays post metadata (ID, title, links)
- Shows first 5 posts with pagination info
- Tests `setPosts()` and `getPosts()` functionality

#### **3. Favorites Test**
- Retrieves user's favorited posts
- Tests favorites-specific functionality
- Shows favorite post details
- Tests `extractPostLinks()` method

#### **4. Basic Post Test**
- Creates a simple test toot
- Tests `publishPost()` method
- Offers optional post deletion
- Validates posting functionality

#### **5. Image Post Test**
- Tests image posting capabilities
- Allows custom image path input
- Includes alt-text functionality
- Tests `publishImage()` method

#### **6. Cache Integration Test**
- Tests auto-cache functionality
- Validates publication tracking
- Shows cached publication details
- Integrates with `PublicationCache`

#### **7. Post Deletion Test**
- Tests post deletion by ID
- Includes confirmation prompts
- Validates `deleteApiPosts()` method
- Safety checks for accidental deletion

#### **8. Favorites Management Test**
- Tests unfavoriting posts
- Validates `deleteApiFavs()` method
- Manages favorite status

#### **9. Custom Post**
- Interactive post composition
- User-defined content and links
- Optional auto-cache enabling
- Flexible testing scenario

#### **10. Browse Posts**
- Interactive post browsing
- Paginated post display
- Detailed post information
- User-controlled navigation

## Key Improvements Over Previous Version

### **Before (Static Tests)**
```python
testingPosts = False
testingFav = False
testingPost = True  # Hardcoded
testingCache = True  # Hardcoded
```

### **After (Interactive Menu)**
```python
print("Available test modes:")
print("1. Connection test")
print("2. Posts retrieval test")
# ... etc

choice = int(input("Select test mode (1-10): "))
```

## Enhanced Error Handling

### **Connection Errors**
```python
try:
    client = mastodon.getClient()
    if client:
        me = client.me()
        print(f"✓ Connected as: {me.get('display_name')}")
    else:
        print("✗ No Mastodon client available")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### **Post Operation Errors**
```python
try:
    result = mastodon.publishPost(title, link, '')
    print(f"Post result: {result}")
    
    if result and not str(result).startswith("Fail"):
        # Success handling
    else:
        print("Post failed")
except Exception as e:
    print(f"Error posting: {e}")
```

### **Cache Integration Errors**
```python
try:
    from socialModules.modulePublicationCache import PublicationCache
    cache = PublicationCache()
    mastodon_pubs = cache.get_publications_by_service("mastodon")
    print(f"Mastodon publications in cache: {len(mastodon_pubs)}")
except Exception as e:
    print(f"Error checking cache: {e}")
```

## User Experience Improvements

### **1. Clear Information Display**
- Rule selection with numbered options
- Account information display
- Progress indicators for operations
- Detailed result reporting

### **2. Safety Features**
- Confirmation prompts for destructive operations
- Input validation and error handling
- Graceful handling of missing files/data
- User cancellation support (Ctrl+C)

### **3. Flexible Testing**
- Optional parameters (image paths, links)
- Custom content input
- Auto-cache toggle options
- Interactive browsing controls

## Integration with Publication Cache

### **Auto-Cache Testing**
```python
# Enable auto-cache
mastodon.setAutoCache(True)
print(f"Auto-cache enabled: {mastodon.getAutoCache()}")

# Post with caching
result = mastodon.publishPost(title, link, '')

# Verify cache
cache = PublicationCache()
mastodon_pubs = cache.get_publications_by_service("mastodon")
```

### **Cache Data Validation**
```python
if mastodon_pubs:
    latest = mastodon_pubs[-1]
    print(f"Latest cached publication:")
    print(f"  Title: {latest['title']}")
    print(f"  Link: {latest['original_link']}")
    print(f"  Service: {latest['service']}")
    print(f"  Response Link: {latest.get('response_link', 'None')}")
    print(f"  Date: {latest['publication_date']}")
```

## Usage Examples

### **Running Interactive Tests**
```bash
python moduleMastodon.py

# Output:
Available Mastodon rules:
0) ('mastodon', 'set', '@user@server.social', 'posts')

Which rule to use? (0-0): 0
Selected rule: ('mastodon', 'set', '@user@server.social', 'posts')
Mastodon client initialized for: @user@server.social

Available test modes:
1. Connection test
2. Posts retrieval test
...
Select test mode (1-10): 1
```

### **Connection Test Example**
```
=== Testing Mastodon Connection ===
✓ Connected as: John Doe (@johndoe)
  Account ID: 123456
  Followers: 150
  Following: 200
  Posts: 1250
```

### **Custom Post Example**
```
=== Custom Post ===
Post content: Testing the new interactive system!
Link (optional): https://example.com/test
Enable auto-cache? (y/N): y
Auto-cache enabled

Posting custom toot:
  Content: Testing the new interactive system!
  Link: https://example.com/test
Result: https://mastodon.social/@user/123456789
```

## Mastodon-Specific Features

### **1. Toot Management**
- Post creation and deletion
- Image posting with alt-text
- Link sharing capabilities
- Content formatting

### **2. Social Features**
- Favorites management
- Post browsing and discovery
- Account information display
- Follower statistics

### **3. API Integration**
- Full Mastodon API support
- Error handling for API limits
- Authentication validation
- Server communication testing

## Configuration Requirements

### **Mastodon Configuration**
```python
# Example Mastodon rule configuration
{
    'mastodon_rule': {
        'src': ('rss', 'https://example.com/feed'),
        'dst': ('mastodon', '@user@server.social'),
        'more': {
            'server': 'https://mastodon.social',
            'client_key': 'your_client_key',
            'client_secret': 'your_client_secret',
            'access_token': 'your_access_token'
        }
    }
}
```

### **Configuration File**
Create `.rssMastodon` configuration file:
```ini
[@user@server.social]
server = https://mastodon.social
client_key = your_client_key
client_secret = your_client_secret  
access_token = your_access_token
```

## Comparison with Previous Version

### **Old System**
- ❌ Hardcoded test scenarios
- ❌ Limited user interaction
- ❌ Basic error handling
- ❌ No menu system
- ❌ Fixed test parameters

### **New System**
- ✅ Interactive menu selection
- ✅ User-controlled testing
- ✅ Comprehensive error handling
- ✅ Flexible parameters
- ✅ Safety confirmations
- ✅ Cache integration testing
- ✅ Better information display

## Benefits

### **1. Developer Experience**
- Easy testing of specific functionality
- Clear feedback and error messages
- Interactive parameter input
- Comprehensive test coverage

### **2. Debugging Capabilities**
- Isolated test scenarios
- Detailed error reporting
- Connection validation
- Cache verification

### **3. Safety Features**
- Confirmation prompts for destructive actions
- Input validation
- Graceful error handling
- User cancellation support

### **4. Flexibility**
- Custom content testing
- Optional parameters
- Multiple test scenarios
- Interactive browsing

## Future Enhancements

### **Potential Improvements**
1. **Scheduled Posts** - Test scheduled toot functionality
2. **Poll Creation** - Test Mastodon poll features
3. **Media Management** - Advanced image/video testing
4. **Thread Testing** - Test toot thread creation
5. **Boost Management** - Test boost/reblog functionality

### **Advanced Features**
1. **Batch Operations** - Multiple post testing
2. **Performance Testing** - API rate limit testing
3. **Analytics Integration** - Engagement metrics
4. **Automation Testing** - Scheduled operations

## Conclusion

The enhanced `moduleMastodon.py` now provides a comprehensive, user-friendly testing framework that significantly improves the developer experience. The interactive menu system makes it easy to test specific functionality, debug issues, and validate the integration with the publication cache system.

The improvements maintain consistency with the `moduleSmtp.py` enhancements while adding Mastodon-specific features that leverage the full capabilities of the Mastodon API. This creates a uniform testing experience across different social media modules in the project.