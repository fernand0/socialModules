# socialModules Style Guide

This document provides a style guide and conventions for developing new modules for the `socialModules` project.
Following these guidelines will help ensure that the codebase is consistent, readable, and maintainable.

## Module Structure

Each new module should be a Python class that inherits from `socialModules.moduleContent.Content`.
The module file should be named `module<YourServiceName>.py` (e.g., `moduleTwitter.py`).

The class should implement the methods defined in `src/socialModules/module_skeleton.py`.
This skeleton file provides a template with all the required methods.

### Basic Methods

These methods are essential for the basic functionality of a module.

- `__init__(self, ...)`: The constructor for your module. It should call the parent constructor: `super().__init__(...)`.
- `getKeys(self, config)`: Reads the API keys and other credentials from the configuration object.
- `initApi(self, keys)`: Initializes the API client with the given keys.
- `setApiPosts(self)`: Fetches a list of posts from the service.
- `setApiFavs(self)`: Fetches a list of favorite/liked posts.
- `publishApiPost(self, *args, **kwargs)`: Publishes content to the service.
    This method should return a dictionary with the following structure:
    ```python
    {
        "success": bool,          # True if the publication was successful, False otherwise.
        "post_url": str,          # The URL of the newly created post, if available. Empty string if not.
        "error_message": str,     # A descriptive error message if the publication failed. Empty string if successful.
        "raw_response": Any       # The raw response object from the API, for debugging.
    }
    ```
- `deleteApiPosts(self, idPost)`: Deletes a post.
- `getPostId(self, post)`: Returns the unique ID of a post.
- `getPostTitle(self, post)`: Returns the title of a post.
- `getPostLink(self, post)`: Returns a permalink to the post.
- `getPostContent(self, post)`: Returns the content of a post.

### Channel/Folder-based Methods

If the service supports channels, folders, or similar content containers (like Slack or IMAP), you should implement these methods:

- `getChannels(self)`: Returns a list of available channels/folders.
- `setChannel(self, channel)`: Sets the current channel/folder.
- `getChannel(self)`: Gets the current channel/folder.
- `createChannel(self, channel_name)`: Creates a new channel/folder.
- `deleteChannel(self, channel_name)`: Deletes a channel/folder.

When `setChannel` is called, `setApiPosts` should fetch posts from the selected channel.

### Naming Conventions

- Class names should be in `CamelCase` (e.g., `moduleTwitter`).
- Method and function names should be in `camelCase` to follow the existing convention in the project (e.g., `getApiPosts`).
- Variable names should be in `snake_case` (e.g., `api_client`).

### Docstrings

All modules, classes, and methods should have docstrings that explain their purpose, arguments, and return values. Use Google-style docstrings.

Example:
```python
def getKeys(self, config):
    """Retrieves the API keys for the service.

    Args:
        config: The configuration object containing the API keys.

    Returns:
        A tuple of API keys.
    """
    # ...
```

### Error Handling

Use `try...except` blocks to handle potential API errors, network issues, or other exceptions. Log errors using the `logging` module.

### Testing

Each module should have a `main()` function that allows it to be run as a standalone script for testing purposes.
The `main()` function should use the `ModuleTester` class to run a series of tests on the module.

You should also implement the `register_specific_tests` method to add tests that are specific to your module's functionality.

## Code Example

Refer to the `src/socialModules/module_skeleton.py` file for a complete template.
You can also look at existing modules like `moduleMastodon.py` or `moduleSlack.py` for examples.
