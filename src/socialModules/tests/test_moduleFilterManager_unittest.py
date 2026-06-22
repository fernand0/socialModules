"""
Unit tests for moduleFilterManager.

This file contains unittest-style tests for the moduleFilterManager module,
following the same pattern as test_moduleHtml.py and other module tests.
"""

import json
import os
import tempfile
import unittest

from socialModules.moduleFilterManager import EmailFilterRule, moduleFilterManager


class TestModuleFilterManager(unittest.TestCase):
    """Unit tests for the moduleFilterManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.filter_manager = moduleFilterManager()
        self.filter_manager.rules_file = self.temp_file.name
        self.filter_manager.setApiPosts()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_getApiPosts(self):
        """Test setApiPosts loads rules correctly."""
        # Create test data
        data = {
            "version": "1.0",
            "always": [
                {"keyword": "From", "pattern": "test@test.com", "folder": "Inbox"}
            ],
            "sometimes": []
        }
        with open(self.temp_file.name, 'w') as f:
            json.dump(data, f)

        # Load rules
        self.filter_manager.setApiPosts()
        rules = self.filter_manager.get_rules()

        self.assertEqual(len(rules["always"]), 1)
        self.assertEqual(rules["always"][0].pattern, "test@test.com")

    def test_updatePosts(self):
        """Test updatePosts saves rules correctly."""
        # Add a rule
        rule = EmailFilterRule("Subject", "Test", "TestFolder")
        self.filter_manager.add_rule(rule, "always")

        # Save rules
        result = self.filter_manager.updatePosts()
        self.assertEqual(result, "Ok")

        # Verify file exists and contains data
        self.assertTrue(os.path.exists(self.temp_file.name))
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        self.assertEqual(len(data["always"]), 1)
        self.assertEqual(data["always"][0]["pattern"], "Test")

    def test_getPosts(self):
        """Test getPosts returns an empty list when no channel is set."""
        rule = EmailFilterRule("From", "test@example.com", "Inbox")
        self.filter_manager.add_rule(rule, "always")

        posts = self.filter_manager.getPosts()
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 0)

        # When channel is set, it should return the list of rules
        self.filter_manager.setChannel("always")
        posts = self.filter_manager.getPosts()
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 1)

    def test_assignPosts(self):
        """Test assignPosts sets rules."""
        new_rules = {
            "always": [EmailFilterRule("Subject", "Test", "Folder")],
            "sometimes": []
        }

        self.filter_manager.assignPosts(new_rules)
        # posts should be an empty list because no channel is set
        self.assertIsInstance(self.filter_manager.posts, list)
        self.assertEqual(len(self.filter_manager.posts), 0)
        self.assertEqual(self.filter_manager.rules, new_rules)

    def test_register_specific_tests(self):
        """Test register_specific_tests adds test options."""
        # Create a mock tester
        class MockTester:
            def __init__(self):
                self.tests = []

            def add_test(self, name, func):
                self.tests.append(name)

        mock_tester = MockTester()
        self.filter_manager.register_specific_tests(mock_tester)

        # Verify tests were registered
        expected_tests = [
            "Rule creation test",
            "Rule loading test",
            "Rule saving test",
            "Rule management test"
        ]
        self.assertEqual(mock_tester.tests, expected_tests)

    def test_email_filter_rule_matches(self):
        """Test EmailFilterRule.matches method."""
        rule = EmailFilterRule("From", "github", "Dev")

        # Test case-insensitive matching
        self.assertTrue(rule.matches("notifications@github.com"))
        self.assertTrue(rule.matches("GITHUB"))
        self.assertFalse(rule.matches("gitlab.com"))

    def test_email_filter_rule_from_tuple(self):
        """Test EmailFilterRule.from_tuple class method."""
        rule_tuple = ("Subject", "Invoice", "Billing")
        rule = EmailFilterRule.from_tuple(rule_tuple)

        self.assertEqual(rule.keyword, "Subject")
        self.assertEqual(rule.pattern, "Invoice")
        self.assertEqual(rule.folder, "Billing")

    def test_email_filter_rule_to_tuple(self):
        """Test EmailFilterRule.to_tuple method."""
        rule = EmailFilterRule("From", "test@test.com", "Inbox")
        result = rule.to_tuple()

        self.assertEqual(result, ("From", "test@test.com", "Inbox"))

    def test_get_channels(self):
        """Test getChannels returns available channels."""
        channels = self.filter_manager.getChannels()
        self.assertIn("always", channels)
        self.assertIn("sometimes", channels)
        self.assertEqual(len(channels), 2)

    def test_set_channel(self):
        """Test setChannel switches between rule categories."""
        # Add rules to both channels
        self.filter_manager.add_rule(EmailFilterRule("From", "test1@test.com", "Inbox"), "always")
        self.filter_manager.add_rule(EmailFilterRule("From", "test2@test.com", "Inbox"), "sometimes")

        # Set channel to always
        self.filter_manager.setChannel("always")
        self.assertEqual(self.filter_manager.getChannel(), "always")
        posts = self.filter_manager.getPosts()
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 1)

        # Set channel to sometimes
        self.filter_manager.setChannel("sometimes")
        self.assertEqual(self.filter_manager.getChannel(), "sometimes")
        posts = self.filter_manager.getPosts()
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 1)

    def test_set_channel_invalid(self):
        """Test setChannel raises error for invalid channel."""
        with self.assertRaises(ValueError):
            self.filter_manager.setChannel("invalid_channel")

    def test_add_rule_uses_current_channel(self):
        """Test add_rule uses current channel when rule_type not specified."""
        self.filter_manager.setChannel("always")
        rule = EmailFilterRule("From", "test@test.com", "Inbox")
        
        # Should use current channel
        self.filter_manager.add_rule(rule)
        
        self.assertEqual(len(self.filter_manager.rules["always"]), 1)
        self.assertEqual(len(self.filter_manager.rules["sometimes"]), 0)

    def test_add_rule_no_channel_raises_error(self):
        """Test add_rule raises error when no channel set and no rule_type."""
        rule = EmailFilterRule("From", "test@test.com", "Inbox")
        
        with self.assertRaises(ValueError):
            self.filter_manager.add_rule(rule)


class TestModuleFilterManagerIntegration(unittest.TestCase):
    """Integration tests for moduleFilterManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_full_workflow(self):
        """Test complete workflow: create, save, load, modify, delete."""
        # Create manager and add rules
        manager = moduleFilterManager()
        manager.rules_file = self.temp_file.name
        manager.setApiPosts()

        # Add rules
        rule1 = EmailFilterRule("From", "test1@example.com", "Folder1")
        rule2 = EmailFilterRule("From", "test2@example.com", "Folder2")
        manager.add_rule(rule1, "always")
        manager.add_rule(rule2, "sometimes")

        # Save rules
        result = manager.updatePosts()
        self.assertEqual(result, "Ok")

        # Create new manager and load rules
        manager2 = moduleFilterManager()
        manager2.rules_file = self.temp_file.name
        manager2.setApiPosts()

        # Verify rules loaded
        rules = manager2.get_rules()
        self.assertEqual(len(rules["always"]), 1)
        self.assertEqual(len(rules["sometimes"]), 1)

        # Modify rules
        manager2.remove_rule(rule1, "always")
        manager2.updatePosts()

        # Reload and verify
        manager3 = moduleFilterManager()
        manager3.rules_file = self.temp_file.name
        manager3.setApiPosts()

        rules = manager3.get_rules()
        self.assertEqual(len(rules["always"]), 0)
        self.assertEqual(len(rules["sometimes"]), 1)


if __name__ == "__main__":
    unittest.main()
