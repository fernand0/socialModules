"""
Module for managing email filter rules.

This module provides infrastructure for storing and managing email organization rules.
Rules are stored in JSON format for safety and portability.

The module follows the socialModules pattern where:
- setApiPosts() loads rules from storage
- updatePosts() saves rules to storage
- Rules are treated as "posts" that can be managed
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from socialModules.configMod import logMsg, DATADIR
from socialModules.moduleContent import Content


logger = logging.getLogger(__name__)


@dataclass
class EmailFilterRule:
    """Represents a single email filtering rule.

    Attributes:
        keyword: The email header keyword to match (e.g., 'From', 'Subject')
        pattern: The pattern to search for in the header value
        folder: The destination folder for matching emails
    """

    keyword: str
    pattern: str
    folder: str

    @classmethod
    def from_tuple(cls, rule_tuple: tuple) -> "EmailFilterRule":
        """Create an EmailFilterRule from a tuple format.

        Args:
            rule_tuple: A tuple of (keyword, pattern, folder)

        Returns:
            An EmailFilterRule instance
        """
        return cls(keyword=rule_tuple[0], pattern=rule_tuple[1], folder=rule_tuple[2])

    def to_tuple(self) -> tuple:
        """Convert to tuple format for compatibility.

        Returns:
            A tuple of (keyword, pattern, folder)
        """
        return (self.keyword, self.pattern, self.folder)

    def matches(self, header_value: str) -> bool:
        """Check if this rule matches the given header value.

        Args:
            header_value: The header value to check against

        Returns:
            True if the pattern matches, False otherwise
        """
        return self.pattern.lower() in header_value.lower()

    def __eq__(self, other) -> bool:
        """Check equality with another rule."""
        if not isinstance(other, EmailFilterRule):
            return False
        return (
            self.keyword == other.keyword
            and self.pattern == other.pattern
            and self.folder == other.folder
        )

    def __hash__(self) -> int:
        """Generate hash for use in sets and as dict keys."""
        return hash((self.keyword, self.pattern, self.folder))


class moduleFilterManager(Content):
    """Manages email filter rules for automated email organization.

    Rules are categorized into:
    - 'always': Rules that are applied automatically without confirmation
    - 'sometimes': Rules that require user confirmation before applying

    This module follows the socialModules Content pattern, treating rules
    as posts that can be loaded, modified, and saved.

    Example usage:
        >>> filter_mgr = moduleFilterManager()
        >>> filter_mgr.setClient("user@example.com")
        >>> filter_mgr.setApiPosts()  # Load rules
        >>> rules = filter_mgr.getPosts()
        >>> filter_mgr.updatePosts()  # Save rules
    """

    RULES_VERSION = "1.0"

    def __init__(self, indent: str = ""):
        """Initialize the filter rule manager.

        Args:
            indent: Indentation string for logging
        """
        super().__init__(indent)
        self.service = "FilterManager"
        self.rules_file: Optional[str] = None
        self.rules: Dict[str, List[EmailFilterRule]] = {"always": [], "sometimes": []}
        self.posts = self.rules  # Treat rules as posts for Content compatibility
        self.channel: Optional[str] = None  # Current channel (rule category)
        self.fileName = "rulesFilter"

    def getChannels(self) -> List[str]:
        """Get the list of available channels (rule categories).

        Returns:
            List of available channel names
        """
        return list(self.rules.keys())

    def setPage(self, channel: str) -> None:
        self.setChannel(channel)

    def setChannel(self, channel: str) -> None:
        """Set the current channel (rule category) to work with.

        When a channel is set, getPosts() will return only rules from that category.

        Args:
            channel: Channel name ('always' or 'sometimes')

        Raises:
            ValueError: If channel name is invalid
        """
        if channel not in self.rules:
            raise ValueError(f"Invalid channel '{channel}'. Available channels: {self.getChannels()}")

        self.channel = channel
        self._log_msg(f"Channel set to: {channel}", 1)

        # Update posts to point to the selected channel's rules
        self.posts = self.rules[channel]

    def getChannel(self) -> Optional[str]:
        """Get the current channel (rule category).

        Returns:
            Current channel name or None if no channel is set
        """
        return self.channel

    def getKeys(self, config) -> Optional[str]:
        return None

    def initApi(self, keys) -> "moduleFilterManager":
        """Initialize the API with the rules file path.

        Args:
            keys: Rules file path from getKeys()

        Returns:
            Self for method chaining
        """
        self.rules_file = f"{DATADIR}/rulesFilter.json"
        self._log_msg(f"Initializing with rules file: {self.rules_file}", 2)
        return self

    def _log_msg(self, msg: str, level: int = 1, console: bool = False) -> None:
        """Log a message using socialModules logging convention.

        Args:
            msg: Message to log
            level: Log level (1=info, 2=debug, 3=warning)
            console: Whether to print to console
        """
        logMsg(f"{self.indent}{msg}", level, console)

    def setApiPosts(self, channel: Optional[str] = None) -> Dict[str, List[EmailFilterRule]] | List[EmailFilterRule]:
        """Load rules from JSON file (equivalent to _load_rules).

        This method follows the socialModules pattern where setApiPosts()
        is responsible for fetching/loading data.

        Args:
            channel: Optional channel to set after loading rules.

        Returns:
            If channel specified: List of rules from that channel.
            Otherwise: Dictionary of all rules by channel.
        """
        if self.rules_file is None:
            raise RuntimeError("rules_file is not initialized. Call initApi() or setClient() first.")

        self._log_msg(f"Loading rules from {self.rules_file}", 2)

        self.rules = {"always": [], "sometimes": []} # Initialize with empty rules

        if not os.path.exists(self.rules_file):
            self._log_msg(f"No rules file found at {self.rules_file}, starting with empty rules", 1)
            # No rules file, so posts remain empty as initialized
            self.posts = self.rules
            if channel:
                self.setChannel(channel)
            return self.rules

        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    # Empty file, start with default rules
                    self._log_msg("Rules file is empty, starting with empty rules", 1)
                    self.posts = self.rules
                else:
                    data = json.loads(content)
                    if "version" not in data or data["version"] != self.RULES_VERSION:
                        raise ValueError(
                            f"Incompatible rules file version. Expected {self.RULES_VERSION}, "
                            f"got {data.get('version', 'N/A')}"
                        )
                    self._parse_json_rules(data)
                    self._log_msg("Loaded rules from JSON file", 1)
                    self.posts = self.rules
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            self._log_msg(f"Failed to load rules: {e}", 3)
            raise
        except ValueError: # Specifically for version mismatch
            raise
        except Exception as e:
            self._log_msg(f"An unexpected error occurred while reading rules from {self.rules_file}: {e}", 3)
            raise

        # Set channel if specified
        if channel:
            self.setChannel(channel)

        return self.posts if self.channel else self.rules

    def _parse_json_rules(self, data: Dict[str, Any]) -> None:
        """Parse JSON format rules into EmailFilterRule objects.

        Args:
            data: Dictionary containing rule data
        """
        self.rules = {"always": [], "sometimes": []}

        for category in ["always", "sometimes"]:
            if category in data:
                for rule_data in data[category]:
                    if isinstance(rule_data, dict):
                        rule = EmailFilterRule(
                            keyword=rule_data["keyword"],
                            pattern=rule_data["pattern"],
                            folder=rule_data["folder"]
                        )
                        self.rules[category].append(rule)
                    elif isinstance(rule_data, (tuple, list)):
                        # Handle tuple/list format for backward compatibility
                        rule = EmailFilterRule.from_tuple(tuple(rule_data))
                        self.rules[category].append(rule)





    def updatePosts(self) -> str:
        """Save rules to JSON file (equivalent to save_rules).

        This method follows the socialModules pattern where updatePosts()
        is responsible for persisting data.

        Returns:
            "Ok" if successful, error message otherwise
        """
        self._log_msg(f"Saving rules to {self.rules_file}", 1)
        try:
            data = {
                "version": self.RULES_VERSION,
                "always": [asdict(rule) for rule in self.rules.get("always", [])],
                "sometimes": [asdict(rule) for rule in self.rules.get("sometimes", [])]
            }
            
            with open(self.rules_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            self._log_msg(f"Rules successfully written to {self.rules_file}", 2)
            return "Ok"
        except Exception as e:
            self._log_msg(f"Failed to save rules: {e}", 3)
            return f"Error: {e}"

    def getApiPostTitle(self, post):
        self.indent = f"{self.indent} "
        msgLog = (f"{self.indent} Start getPostTitle {post}.")
        logMsg(msgLog, 2, False)
        title = ""
        if post:
            title = f"{post.keyword}={post.pattern}->{post.folder}"
        return title

    def add_rule(self, rule: tuple | EmailFilterRule, rule_type: Optional[str] = None) -> None:
        """Add a new rule to the specified category.

        Args:
            rule: EmailFilterRule instance or tuple of (keyword, pattern, folder)
            rule_type: Category type ('always' or 'sometimes'). If None, uses current channel.

        Raises:
            ValueError: If no rule_type specified and no channel is set
        """
        # Use current channel if rule_type not specified
        if rule_type is None:
            if self.channel:
                rule_type = self.channel
            else:
                raise ValueError("No rule_type specified and no channel is set. "
                               "Use setChannel() or specify rule_type.")

        if rule_type not in self.rules:
            self.rules[rule_type] = []

        # Convert tuple to EmailFilterRule if needed
        if isinstance(rule, tuple):
            rule = EmailFilterRule.from_tuple(rule)

        # Check for duplicates
        if rule not in self.rules[rule_type]:
            self.rules[rule_type].append(rule)
            self._log_msg(f"Added rule to {rule_type}: {rule.keyword} -> {rule.folder}", 1)
            # Update posts if we're on this channel
            if self.channel == rule_type:
                self.posts = self.rules[rule_type]

    def remove_rule(self, rule: tuple | EmailFilterRule, rule_type: Optional[str] = None) -> bool:
        """Remove a rule from the specified category.

        Args:
            rule: EmailFilterRule instance or tuple of (keyword, pattern, folder)
            rule_type: Category type ('always' or 'sometimes'). If None, uses current channel.

        Returns:
            True if rule was removed, False if not found

        Raises:
            ValueError: If no rule_type specified and no channel is set
        """
        # Use current channel if rule_type not specified
        if rule_type is None:
            if self.channel:
                rule_type = self.channel
            else:
                raise ValueError("No rule_type specified and no channel is set. "
                               "Use setChannel() or specify rule_type.")

        # Convert tuple to EmailFilterRule if needed
        if isinstance(rule, tuple):
            rule = EmailFilterRule.from_tuple(rule)

        if rule_type in self.rules and rule in self.rules[rule_type]:
            self.rules[rule_type].remove(rule)
            self._log_msg(f"Removed rule from {rule_type}: {rule.keyword} -> {rule.folder}", 1)
            # Update posts if we're on this channel
            if self.channel == rule_type:
                self.posts = self.rules[rule_type]
            return True
        return False

    def get_rules(self, rule_type: Optional[str] = None) -> Dict[str, List[EmailFilterRule]] | List[EmailFilterRule]:
        """Get rules, optionally filtered by type.

        Args:
            rule_type: Optional category type to filter by

        Returns:
            All rules as dict, or filtered list if rule_type specified
        """
        if rule_type:
            return self.rules.get(rule_type, [])
        return self.rules

    def display_rules(self) -> None:
        """Display all rules in a formatted way."""
        for category, rules in self.rules.items():
            print(f"\n{category.upper()} Rules:")
            if not rules:
                print("  No rules in this category.")
            for i, rule in enumerate(rules):
                print(f"  {i}: {rule.keyword}='{rule.pattern}' -> {rule.folder}")

    def get_rule_by_index(self, category: str, index: int) -> Optional[EmailFilterRule]:
        """Get a rule by category and index.

        Args:
            category: Category type ('always' or 'sometimes')
            index: Index of the rule in the category

        Returns:
            EmailFilterRule if found, None otherwise
        """
        rules = self.rules.get(category, [])
        if 0 <= index < len(rules):
            return rules[index]
        return None

    def move_rule(self, rule: EmailFilterRule, from_category: str, to_category: str) -> bool:
        """Move a rule from one category to another.

        Args:
            rule: EmailFilterRule to move
            from_category: Source category
            to_category: Destination category

        Returns:
            True if rule was moved, False otherwise
        """
        if self.remove_rule(rule, from_category):
            self.add_rule(rule, to_category)
            return True
        return False

    def clear_rules(self, rule_type: Optional[str] = None) -> None:
        """Clear all rules, or rules of a specific type.

        Args:
            rule_type: Optional category type to clear. If None, clears all.
        """
        if rule_type:
            self.rules[rule_type] = []
            self._log_msg(f"Cleared all '{rule_type}' rules", 1)
        else:
            self.rules = {"always": [], "sometimes": []}
            self._log_msg("Cleared all rules", 1)
        self.posts = self.rules  # Keep posts in sync

    def getPosts(self, channel: Optional[str] = None) -> Dict[str, List[EmailFilterRule]] | List[EmailFilterRule]:
        """Get the current rules (posts).

        If a channel is set (via setChannel), returns rules from that channel.
        Otherwise, returns all rules organized by channel.

        Args:
            channel: Optional channel to get rules from. If None, uses current channel.

        Returns:
            If channel is specified or set: List of rules from that channel.
            Otherwise: Dictionary of all rules by channel.
        """
        if channel:
            return self.rules.get(channel, [])
        elif self.channel:
            return self.posts if isinstance(self.posts, list) else self.rules.get(self.channel, [])
        else:
            return self.posts if self.posts else self.rules

    def assignPosts(self, posts: Dict[str, List[EmailFilterRule]]) -> None:
        """Set the rules (posts).

        Args:
            posts: Dictionary of rules by category
        """
        self.posts = posts
        self.rules = posts
        # If a channel is set, update posts to point to that channel
        if self.channel and self.channel in posts:
            self.posts = posts[self.channel]

    def register_specific_tests(self, tester):
        """Register specific tests for moduleFilterManager.

        Args:
            tester: ModuleTester instance to register tests with
        """
        tester.add_test("Rule creation test", self._test_rule_creation)
        tester.add_test("Rule loading test", self._test_rule_loading)
        tester.add_test("Rule saving test", self._test_rule_saving)
        tester.add_test("Rule management test", self._test_rule_management)

    def _test_rule_creation(self, api_src=None):
        """Test creating and adding rules."""
        print("\n=== Testing Rule Creation ===")

        # Clear existing rules
        self.clear_rules()

        # Add a test rule
        test_rule = EmailFilterRule(
            keyword="From",
            pattern="test@example.com",
            folder="TestFolder"
        )
        self.add_rule(test_rule, "always")

        # Verify rule was added
        rules = self.get_rules("always")
        assert len(rules) == 1, f"Expected 1 rule, got {len(rules)}"
        assert rules[0] == test_rule, "Rule doesn't match"

        print("✓ Rule creation test passed")
        print(f"  Added rule: {test_rule.keyword}='{test_rule.pattern}' -> {test_rule.folder}")

    def _test_rule_loading(self, api_src=None):
        """Test loading rules from file."""
        print("\n=== Testing Rule Loading ===")

        # setApiPosts is called during setup, rules should be loaded
        all_rules = self.get_rules()
        print(f"✓ Rule loading test passed")
        print(f"  Loaded {len(all_rules['always'])} 'always' rules")
        print(f"  Loaded {len(all_rules['sometimes'])} 'sometimes' rules")

    def _test_rule_saving(self, api_src=None):
        """Test saving rules to file."""
        print("\n=== Testing Rule Saving ===")

        # Add a rule and save
        test_rule = EmailFilterRule(
            keyword="Subject",
            pattern="Test Subject",
            folder="TestFolder"
        )
        self.add_rule(test_rule, "sometimes")

        result = self.updatePosts()
        assert result == "Ok", f"Save failed: {result}"

        # Reload and verify
        self.setApiPosts()
        rules = self.get_rules("sometimes")
        assert any(r.pattern == "Test Subject" for r in rules), "Saved rule not found"

        print("✓ Rule saving test passed")
        print(f"  Saved rules to: {self.rules_file}")

    def _test_rule_management(self, api_src=None):
        """Test rule management operations."""
        print("\n=== Testing Rule Management ===")

        # Clear and add test rules
        self.clear_rules()
        rule1 = EmailFilterRule("From", "test1@example.com", "Folder1")
        rule2 = EmailFilterRule("From", "test2@example.com", "Folder2")
        self.add_rule(rule1, "always")
        self.add_rule(rule2, "sometimes")

        # Test move_rule
        moved = self.move_rule(rule1, "always", "sometimes")
        assert moved, "Failed to move rule"
        assert len(self.get_rules("always")) == 0, "Rule not removed from source"
        assert len(self.get_rules("sometimes")) == 2, "Rule not added to destination"

        # Test remove_rule
        removed = self.remove_rule(rule1, "sometimes")
        assert removed, "Failed to remove rule"

        # Test clear_rules
        self.clear_rules()
        assert len(self.get_rules("always")) == 0, "Clear failed for always"
        assert len(self.get_rules("sometimes")) == 0, "Clear failed for sometimes"

        print("✓ Rule management test passed")
        print("  Tested: add, move, remove, clear operations")


def main():
    """
    Main function for standalone testing of moduleFilterManager.
    Provides an interactive menu to test rule management operations.
    """
    import logging
    import os
    import sys
    from socialModules.configMod import DATADIR, CONFIGDIR

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    print("\n=== moduleFilterManager Standalone Test ===\n")

    # Initialize filter manager
    filter_manager = moduleFilterManager()

    # Try to load configuration from .rssBlogs first
    rules_file = None
    rssblogs_file = f"{CONFIGDIR}/.rssBlogs"

    if os.path.exists(rssblogs_file):
        import configparser
        config = configparser.ConfigParser()
        config.read(rssblogs_file)

        # Look for filterManager sections
        for section in config.sections():
            service = config.get(section, 'service', fallback='')
            if service.lower() == 'filtermanager':
                print(f"Found filterManager config in section: [{section}]")
                rules_file = config.get(section, 'rules_file', fallback=None)
                channel = config.get(section, 'channel', fallback='always')
                print(f"  rules_file: {rules_file}")
                print(f"  channel: {channel}")

                if rules_file:
                    filter_manager.rules_file = rules_file
                    try:
                        filter_manager.setApiPosts(channel=channel)
                        print(f"\nRules loaded from .rssBlogs configuration\n")
                        break
                    except Exception as e:
                        print(f"Error loading rules: {e}")

    # If no .rssBlogs config, use default location
    if not filter_manager.rules_file:
        rules_file = f"{DATADIR}/rulesFilter.json"
        print(f"No .rssBlogs configuration found.")
        print(f"Using default rules file: {rules_file}")
        filter_manager.rules_file = rules_file

        # Load existing rules or start fresh
        try:
            filter_manager.setApiPosts()
            print("Rules loaded successfully\n")
        except FileNotFoundError:
            print("No existing rules file found, starting with empty rules\n")

    while True:
        print("\n--- Menu ---")
        print("1. Show all rules")
        print("2. Show 'always' rules")
        print("3. Show 'sometimes' rules")
        print("4. Add rule to 'always'")
        print("5. Add rule to 'sometimes'")
        print("6. Delete rule")
        print("7. Move rule between categories")
        print("8. Clear all rules")
        print("9. Save rules")
        print("10. Reload rules")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        try:
            if choice == "1":
                filter_manager.display_rules()

            elif choice == "2":
                filter_manager.setChannel("always")
                rules = filter_manager.getPosts()
                print(f"\nALWAYS Rules ({len(rules)}):")
                for i, rule in enumerate(rules):
                    print(f"  {i}: {rule.keyword}='{rule.pattern}' -> {rule.folder}")

            elif choice == "3":
                filter_manager.setChannel("sometimes")
                rules = filter_manager.getPosts()
                print(f"\nSOMETIMES Rules ({len(rules)}):")
                for i, rule in enumerate(rules):
                    print(f"  {i}: {rule.keyword}='{rule.pattern}' -> {rule.folder}")

            elif choice == "4":
                keyword = input("Header keyword (e.g., From, Subject): ").strip() or "From"
                pattern = input("Pattern to match: ").strip()
                folder = input("Destination folder: ").strip()
                if pattern and folder:
                    filter_manager.setChannel("always")
                    filter_manager.add_rule((keyword, pattern, folder))
                    print(f"✓ Rule added to 'always': {keyword}='{pattern}' -> {folder}")
                else:
                    print("Pattern and folder are required")

            elif choice == "5":
                keyword = input("Header keyword (e.g., From, Subject): ").strip() or "From"
                pattern = input("Pattern to match: ").strip()
                folder = input("Destination folder: ").strip()
                if pattern and folder:
                    filter_manager.setChannel("sometimes")
                    filter_manager.add_rule((keyword, pattern, folder))
                    print(f"✓ Rule added to 'sometimes': {keyword}='{pattern}' -> {folder}")
                else:
                    print("Pattern and folder are required")

            elif choice == "6":
                filter_manager.display_rules()
                category = input("Category (always/sometimes): ").strip().lower()
                if category in ["always", "sometimes"]:
                    try:
                        idx = int(input("Rule number to delete: ").strip())
                        rules = filter_manager.get_rules(category)
                        if 0 <= idx < len(rules):
                            filter_manager.remove_rule(rules[idx], category)
                            print(f"✓ Rule deleted from '{category}'")
                        else:
                            print("Invalid rule number")
                    except ValueError:
                        print("Invalid number")
                else:
                    print("Invalid category")

            elif choice == "7":
                filter_manager.display_rules()
                from_cat = input("From category (always/sometimes): ").strip().lower()
                if from_cat in ["always", "sometimes"]:
                    try:
                        idx = int(input("Rule number to move: ").strip())
                        rules = filter_manager.get_rules(from_cat)
                        if 0 <= idx < len(rules):
                            to_cat = input("To category (always/sometimes): ").strip().lower()
                            if to_cat in ["always", "sometimes"] and to_cat != from_cat:
                                filter_manager.move_rule(rules[idx], from_cat, to_cat)
                                print(f"✓ Rule moved from '{from_cat}' to '{to_cat}'")
                            else:
                                print("Invalid destination category")
                        else:
                            print("Invalid rule number")
                    except ValueError:
                        print("Invalid number")
                else:
                    print("Invalid source category")

            elif choice == "8":
                confirm = input("Clear ALL rules? (y/n): ").strip().lower()
                if confirm == "y":
                    filter_manager.clear_rules()
                    print("✓ All rules cleared")

            elif choice == "9":
                result = filter_manager.updatePosts()
                print(f"Save result: {result}")

            elif choice == "10":
                filter_manager.setApiPosts()
                print("✓ Rules reloaded")
                filter_manager.display_rules()

            elif choice == "0":
                save = input("Save rules before exiting? (y/n): ").strip().lower()
                if save == "y":
                    result = filter_manager.updatePosts()
                    print(f"Save result: {result}")
                print("Goodbye!")
                break

            else:
                print("Invalid option")

        except Exception as e:
            print(f"Error: {e}")
            logging.exception("Detailed error:")


if __name__ == "__main__":
    main()
