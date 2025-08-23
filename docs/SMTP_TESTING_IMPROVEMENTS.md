# moduleSmtp Testing Improvements

## Overview

Enhanced the `main()` function in `moduleSmtp.py` to provide comprehensive testing capabilities similar to `moduleMastodon.py`. The new testing framework offers multiple test scenarios and better error handling.

## New Testing Features

### 1. **Interactive Test Menu**
```
Available test modes:
1. Basic email test
2. HTML email test
3. Web content email
4. Cache integration test
5. Multiple emails test
6. Connection test
7. Error handling test
8. Custom email
```

### 2. **Test Scenarios**

#### **Connection Testing**
- Tests SMTP server connectivity
- Validates authentication
- Checks server response with NOOP command

#### **Basic Email Testing**
- Sends simple text emails
- Tests basic functionality
- Validates email delivery

#### **HTML Email Testing**
- Sends formatted HTML emails
- Tests rich content support
- Validates HTML rendering

#### **Web Content Testing**
- Fetches content from URLs
- Sends web content via email
- Tests content integration

#### **Cache Integration Testing**
- Tests auto-cache functionality
- Validates publication tracking
- Checks cache storage

#### **Multiple Emails Testing**
- Sends batch emails
- Tests bulk operations
- Validates sequential sending

#### **Error Handling Testing**
- Tests invalid recipients
- Validates error responses
- Tests failure scenarios

#### **Custom Email Testing**
- Interactive email composition
- User-defined content
- Flexible testing

### 3. **New Helper Methods**

#### **`getPostTitle(post)`**
```python
def getPostTitle(self, post):
    """Extract title from email post data"""
    if isinstance(post, dict):
        return post.get('subject', post.get('title', ''))
    elif isinstance(post, str):
        lines = post.split('\n')
        return lines[0] if lines else post[:50]
    return str(post)[:50]
```

#### **`getPostLink(post)`**
```python
def getPostLink(self, post):
    """Extract link from email post data"""
    if isinstance(post, dict):
        return post.get('url', post.get('link', ''))
    return ''
```

#### **`getPostContent(post)`**
```python
def getPostContent(self, post):
    """Extract content from email post data"""
    if isinstance(post, dict):
        return post.get('content', post.get('body', ''))
    elif isinstance(post, str):
        return post
    return str(post)
```

#### **`testConnection()`**
```python
def testConnection(self):
    """Test SMTP connection"""
    try:
        if self.client:
            resp = self.client.noop()
            return True, f"Connection OK: {resp}"
        else:
            return False, "No client available"
    except Exception as e:
        return False, f"Connection failed: {e}"
```

## Usage Examples

### Running Tests

```bash
# Run the module directly
python moduleSmtp.py

# Select a rule and test mode
Which rule to use? 0
Which action? 0
Select test mode (1-8): 1
```

### Test Scenarios

#### 1. Basic Email Test
```python
# Sends a simple test email
title = "Test Email from moduleSmtp"
link = "https://example.com/test"
comment = "This is a test email sent from the SMTP module."
```

#### 2. HTML Email Test
```python
# Sends formatted HTML email
htmlContent = '''
<html>
<body>
    <h2>Test HTML Email</h2>
    <p>This is a <strong>test email</strong> with HTML content.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>
'''
```

#### 3. Cache Integration Test
```python
# Enable auto-cache and test
apiDst.setAutoCache(True)
result = apiDst.publishPost(title, link, comment)

# Check cached publications
cache = PublicationCache()
smtp_pubs = cache.get_publications_by_service("smtp")
```

## Configuration Requirements

### SMTP Configuration
The module requires proper SMTP configuration in the rules:

```python
# Example SMTP configuration
{
    'smtp_rule': {
        'src': ('rss', 'https://example.com/feed'),
        'dst': ('smtp', 'email_config'),
        'more': {
            'server': 'smtp.gmail.com',
            'port': 587,
            'user': 'your_email@gmail.com',
            'token': 'your_app_password'
        }
    }
}
```

### Configuration File
Create `.rssSmtp` configuration file:

```ini
[your_email@gmail.com]
server = smtp.gmail.com
port = 587
user = your_email@gmail.com
token = your_app_password
```

## Error Handling

### Connection Errors
```python
try:
    if apiDst.client:
        resp = apiDst.client.noop()
        print(f"✓ SMTP connection is working: {resp}")
    else:
        print("✗ No SMTP client available")
except Exception as e:
    print(f"✗ SMTP connection failed: {e}")
```

### Email Sending Errors
```python
try:
    result = apiDst.publishPost(title, link, comment)
    if "Fail" in result:
        print(f"✗ Email sending failed: {result}")
    else:
        print(f"✓ Email sent successfully: {result}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
```

## Integration with Publication Cache

### Auto-Cache Support
```python
# Enable automatic caching
apiDst.setAutoCache(True)

# Send email (automatically cached)
result = apiDst.publishPost(title, link, comment)

# Check cache
from socialModules.modulePublicationCache import PublicationCache
cache = PublicationCache()
smtp_publications = cache.get_publications_by_service("smtp")
```

### Cache Data Structure
```json
{
  "smtp_1642234567": {
    "id": "smtp_1642234567",
    "title": "Test Email Subject",
    "original_link": "https://example.com/article",
    "service": "smtp",
    "response_link": null,
    "publication_date": "2024-01-15T10:30:00",
    "metadata": {
      "service": "smtp",
      "user": "sender@example.com",
      "recipient": "recipient@example.com"
    }
  }
}
```

## Comparison with moduleMastodon

### Similar Features
- ✅ Interactive test menu
- ✅ Multiple test scenarios
- ✅ Connection testing
- ✅ Error handling
- ✅ Cache integration
- ✅ Helper methods for post data

### SMTP-Specific Features
- 📧 **Email-specific testing** (HTML, attachments)
- 🔗 **Web content fetching** and emailing
- 📬 **Batch email testing**
- ⚙️ **SMTP connection validation**
- 📝 **Custom email composition**

### Key Differences
- **Mastodon**: Tests social media posting, favorites, deletion
- **SMTP**: Tests email sending, HTML content, web integration
- **Mastodon**: Has post/favorite management
- **SMTP**: Focuses on email delivery and formatting

## Benefits

### 1. **Comprehensive Testing**
- Multiple test scenarios cover different use cases
- Interactive menu makes testing user-friendly
- Error handling validates robustness

### 2. **Better Debugging**
- Connection testing helps diagnose issues
- Detailed error messages aid troubleshooting
- Step-by-step validation process

### 3. **Cache Integration**
- Tests publication tracking
- Validates cache functionality
- Ensures data consistency

### 4. **Consistency**
- Similar structure to other modules
- Standardized testing approach
- Uniform error handling

## Future Enhancements

### Potential Improvements
1. **Attachment Testing** - Test email attachments
2. **Template Support** - Test email templates
3. **Bulk Operations** - Test mailing lists
4. **Performance Testing** - Test high-volume sending
5. **Security Testing** - Test authentication methods

### Integration Opportunities
1. **Newsletter Module** - Integration with newsletter systems
2. **Notification System** - Email notifications for events
3. **Report Generation** - Automated email reports
4. **Alert System** - Email alerts for monitoring

## Conclusion

The enhanced `moduleSmtp.py` now provides comprehensive testing capabilities that match the quality and functionality of `moduleMastodon.py`. The new testing framework makes it easier to validate SMTP functionality, debug issues, and ensure reliable email delivery.

The improvements maintain consistency with the existing codebase while adding SMTP-specific features that enhance the module's utility and reliability.