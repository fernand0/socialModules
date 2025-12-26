#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example of the improved unified publication functionality in moduleRules

This example demonstrates the enhanced features and better error handling
of the refactored publication methods.
"""

import logging
import os
import sys

# Add socialModules path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socialModules.moduleRules


def example_improved_error_handling():
    """
    Demonstrates improved error handling and validation
    """
    print("=== Improved Error Handling Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Test 1: Invalid destinations format
    print("\n1. Testing invalid destinations format:")
    try:
        results = rules.publish_to_multiple_destinations(
            destinations="invalid_format",  # Should be dict or list
            title="Test message",
        )
        print(f"Results: {results}")
    except Exception as e:
        print(f"Caught expected error: {e}")

    # Test 2: Empty destinations
    print("\n2. Testing empty destinations:")
    results = rules.publish_to_multiple_destinations(
        destinations={}, title="Test message"
    )
    print(f"Results: {results}")

    # Test 3: Empty title and content
    print("\n3. Testing empty title and content:")
    try:
        results = rules.publish_to_multiple_destinations(
            destinations={"twitter": "test_account"}, title="", content=""
        )
        print(f"Results: {results}")
    except ValueError as e:
        print(f"Caught expected validation error: {e}")


def example_publication_summary():
    """
    Demonstrates the new publication summary functionality
    """
    print("\n=== Publication Summary Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Simulate publication results
    destinations = {
        "mastodon": "test_account",
        "twitter": "test_account",
        "nonexistent_service": "test_account",
    }

    results = rules.publish_to_multiple_destinations(
        destinations=destinations,
        title="Test publication with summary",
        content="This is a test of the summary functionality",
    )

    # Generate summary
    summary = rules.get_publication_summary(results)

    print("Publication Results:")
    for service, result in results.items():
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {service}: {result.get('result') or result.get('error')}")

    print(f"\nSummary:")
    print(f"  Total destinations: {summary['total']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")

    if summary["successful_services"]:
        print(f"  Successful services: {', '.join(summary['successful_services'])}")

    if summary["failed_services"]:
        print(f"  Failed services: {', '.join(summary['failed_services'])}")

    if summary["errors"]:
        print("  Errors:")
        for service, error in summary["errors"].items():
            print(f"    {service}: {error}")


def example_enhanced_message_publishing():
    """
    Demonstrates enhanced message publishing with additional parameters
    """
    print("\n=== Enhanced Message Publishing Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    destinations = {"smtp": "test@example.com"}

    # Test enhanced message publishing with additional parameters
    results = rules.publish_message_to_destinations(
        destinations=destinations,
        message="Enhanced message with additional parameters",
        channel="announcements",
        from_email="sender@example.com",
        to_email="recipient@example.com",
    )

    print("Enhanced message publishing results:")
    for service, result in results.items():
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {service}: {result.get('result') or result.get('error')}")


def example_image_publishing_improvements():
    """
    Demonstrates improved image publishing with better URL extraction
    """
    print("\n=== Improved Image Publishing Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    destinations = {"mastodon": "test_account"}

    # Create a dummy image file for testing
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(b"fake image data")
        image_path = tmp_file.name

    try:
        results = rules.publish_to_multiple_destinations(
            destinations=destinations,
            title="Post with image",
            content="Testing improved image handling",
            image_path=image_path,
            alt_text="Test image for demonstration",
        )

        print("Image publishing results:")
        for service, result in results.items():
            status = "✓" if result.get("success") else "✗"
            print(
                f"  {status} {service}: {result.get('result') or result.get('error')}"
            )
            if result.get("image_url"):
                print(f"    Image URL: {result['image_url']}")

    finally:
        # Clean up temporary file
        try:
            os.unlink(image_path)
        except:
            pass


def example_flexible_destinations_format():
    """
    Demonstrates flexible destination formats
    """
    print("\n=== Flexible Destination Formats Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Test different destination formats

    # Format 1: Dictionary (original)
    destinations_dict = {"mastodon": "account1", "twitter": "account2"}

    # Format 2: List of tuples
    destinations_list = [
        ("mastodon", "account1"),
        ("twitter", "account2"),
        ("smtp", "test@example.com"),
    ]

    print("Testing dictionary format:")
    results1 = rules.publish_to_multiple_destinations(
        destinations=destinations_dict, title="Test with dict format"
    )
    summary1 = rules.get_publication_summary(results1)
    print(f"  Processed {summary1['total']} destinations")

    print("\nTesting list format:")
    results2 = rules.publish_to_multiple_destinations(
        destinations=destinations_list, title="Test with list format"
    )
    summary2 = rules.get_publication_summary(results2)
    print(f"  Processed {summary2['total']} destinations")


def example_service_configuration():
    """
    Demonstrates improved service-specific configuration
    """
    print("\n=== Service Configuration Example ===")

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    # Test service-specific configurations
    destinations = {
        "smtp": "recipient@example.com",
        "slack": "general",  # Channel-based service
    }

    results = rules.publish_to_multiple_destinations(
        destinations=destinations,
        title="Service configuration test",
        content="Testing service-specific configurations",
        channel="announcements",  # Will be applied to services that support it
        from_email="sender@example.com",
        to_email="override@example.com",
    )

    print("Service configuration results:")
    for service, result in results.items():
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {service}: {result.get('result') or result.get('error')}")


def main():
    """Main function demonstrating all improvements"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Improved Unified Publication Examples")
    print("=" * 50)

    try:
        example_improved_error_handling()
        example_publication_summary()
        example_enhanced_message_publishing()
        example_image_publishing_improvements()
        example_flexible_destinations_format()
        example_service_configuration()

        print("\n" + "=" * 50)
        print("Key Improvements:")
        print("✓ Better error handling and validation")
        print("✓ Modular code structure with helper methods")
        print("✓ Enhanced image URL extraction")
        print("✓ Publication summary generation")
        print("✓ Flexible destination formats")
        print("✓ Improved service configuration")
        print("✓ More robust result validation")
        print("✓ Better logging and debugging")

    except Exception as e:
        print(f"Error executing examples: {e}")
        logging.error(f"Error in examples: {e}")


if __name__ == "__main__":
    main()
