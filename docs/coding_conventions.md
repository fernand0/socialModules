# Coding Conventions for Social Modules

This document outlines the coding conventions and best practices for the Social Modules project.

## General Principles

- Write clear, readable code that is easy to maintain
- Follow Python's PEP 8 style guide
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Document complex logic with comments

## Function Design Guidelines

### Single Return Statement Principle

Functions should have a single return statement at the end of the function when possible. This improves code readability and maintainability by:

- Making it easier to trace the flow of execution
- Reducing the cognitive load when reading functions
- Making debugging simpler by having a single exit point
- Avoiding early returns that can make code harder to follow

**Preferred approach:**
```python
def get_user_name(user):
    result = ""
    if user and hasattr(user, 'name'):
        result = user.name
    else:
        result = "Anonymous"
    return result
```

**Instead of multiple returns:**
```python
def get_user_name(user):
    if user and hasattr(user, 'name'):
        return user.name
    return "Anonymous"
```

### Loop Control Guidelines

Avoid using `break` and `continue` statements when possible. Instead, prefer:

- Restructuring loops with appropriate conditions
- Using boolean flags to control loop execution
- Extracting complex loop logic into separate functions

**Preferred approach:**
```python
found = False
for item in items:
    if not found and meets_condition(item):
        process_item(item)
        found = True
```

**Instead of break:**
```python
for item in items:
    if meets_condition(item):
        process_item(item)
        break
```

**Instead of continue:**
```python
# Instead of:
for item in items:
    if skip_condition(item):
        continue
    process_item(item)

# Use:
for item in items:
    if not skip_condition(item):
        process_item(item)
```

### Refactoring Examples

Here are examples of how to refactor code to follow these conventions:

**Refactoring multiple returns:**
```python
# Before:
def process_data(data):
    if not data:
        return None
    if len(data) > 100:
        return "Too large"
    return process_large_data(data)

# After:
def process_data(data):
    result = None
    if not data:
        result = None
    elif len(data) > 100:
        result = "Too large"
    else:
        result = process_large_data(data)
    return result
```

**Refactoring break/continue:**
```python
# Before:
def find_first_valid(items):
    for item in items:
        if is_valid(item):
            return item
    return None

# After:
def find_first_valid(items):
    result = None
    for item in items:
        if is_valid(item) and result is None:
            result = item
    return result
```

## Error Handling

- Use try/except blocks appropriately
- Handle specific exceptions rather than catching all exceptions
- Provide meaningful error messages
- Follow the single return principle even in error handling paths

## Naming Conventions

- Use descriptive names for variables, functions, and classes
- Follow PEP 8 naming conventions:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

## Documentation

- Use docstrings for all public methods and functions
- Document complex logic with inline comments
- Keep comments up-to-date with code changes