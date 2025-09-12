#!/usr/bin/env python

import logging
from socialModules.test_utils import testing_utils


class TestOption:
    def __init__(self, name, test_function):
        self.name = name
        self.test_function = test_function

    def run(self):
        print(f"\n=== Testing {self.name} ===")
        try:
            self.test_function()
        except Exception as e:
            print(f"Error in {self.name} test: {e}")


class ModuleTester:
    def __init__(self, module_instance):
        self.module = module_instance
        self.api_src = None
        self.test_options = []

    def setup(self):
        # Common setup logic, like initializing rules and selecting a rule
        import socialModules.moduleRules

        rules = socialModules.moduleRules.moduleRules()
        rules.checkRules()

        name = self.module.get_name()
        # This part needs to be more generic
        rulesList = rules.selectRule(
            name, self.module.get_default_user(), self.module.get_default_post_type()
        )

        print(f"Available {name} rules:")
        for i, rule in enumerate(rulesList):
            if not name.lower() in rule:
                for rule_index, rule_key in enumerate(sorted(rules.rules.keys())):
                    rule_metadata = (
                        rules.more[rule_key] if rule_key in rules.more else None
                    )
                    rule_actions = rules.rules[rule_key]
                    for action_index, rule_action in enumerate(rule_actions):
                        if name.lower() in rule_action:
                            print(f"{i}) {rule_action}")
            else:
                print(f"{i}) {rule}")

        if not rulesList:
            print(f"No {name} rules found. Please configure {name} in your rules.")
            return False

        try:
            sel = int(input(f"Which rule to use? (0-{len(rulesList)-1}): "))
            if sel < 0 or sel >= len(rulesList):
                print("Invalid selection")
                return False
            key = rulesList[sel]
        except (ValueError, IndexError):
            print("Invalid input, using first rule")
            key = rulesList[0]

        print(f"Selected rule: {key}")

        try:
            if not name.lower() in key:
                rule_actions = rules.rules[key]
                print(f"Actions: {rule_actions}")
                for action_index, rule_action in enumerate(rule_actions):
                    if name.lower() in rule_action:
                        print(f"Selected rule: {rule_action}")
                        self.api_src = rules.readConfigDst("", rule_action, None, None)
            else:
                self.api_src = rules.readConfigSrc("", key, None)
            print(f"{name} client initialized for: {self.api_src.user}")
            return True
        except Exception as e:
            print(f"Error initializing {name}: {e}")
            return False

    def add_test(self, name, test_function):
        self.test_options.append(TestOption(name, lambda: test_function(self.api_src)))

    def register_common_tests(self):
        self.add_test("Connection test", self.test_connection)
        self.add_test("Posts retrieval test", self.test_posts_retrieval)
        self.add_test("Favorites test", self.test_favorites)
        self.add_test("Basic post test", self.test_basic_post)
        self.add_test("Image post test", self.test_image_post)
        self.add_test("Cache integration test", self.test_cache_integration)
        self.add_test("Post deletion test", self.test_deletion)
        self.add_test("Favorites management test", self.test_favorites_management)
        self.add_test("Cache content verification", self.test_cache_content)

    def run(self):
        if not self.setup():
            return

        self.register_common_tests()
        self.module.register_specific_tests(self)

        while True:
            print(f"\n=== Interactive {self.module.get_name()} Testing ===")
            for i, option in enumerate(self.test_options):
                print(f"{i+1}. {option.name}")
            print("0. Exit")

            try:
                choice = int(input(f"Select test mode (0-{len(self.test_options)}): "))
                if choice == 0:
                    break
                if 1 <= choice <= len(self.test_options):
                    self.test_options[choice - 1].run()
                else:
                    print("Invalid choice")
            except ValueError:
                print("Invalid input")
            except KeyboardInterrupt:
                print("\nTest cancelled by user")
                break

    # --- Common test implementations ---

    def test_connection(self, apiSrc):
        testing_utils.test_connection(apiSrc, self.module.get_user_info)

    def test_posts_retrieval(self, apiSrc):
        testing_utils.test_posts_retrieval(apiSrc)

    def test_favorites(self, apiSrc):
        testing_utils.test_favorites(apiSrc)

    def test_basic_post(self, apiSrc):
        testing_utils.test_basic_post(apiSrc, self.module.get_post_id_from_result)

    def test_image_post(self, apiSrc):
        testing_utils.test_image_post(apiSrc, self.module.get_post_id_from_result)

    def test_cache_integration(self, apiSrc):
        testing_utils.test_cache_integration(apiSrc)

    def test_deletion(self, apiSrc):
        testing_utils.test_deletion(apiSrc)

    def test_favorites_management(self, apiSrc):
        testing_utils.test_favorites_management(apiSrc)

    def test_cache_content(self, apiSrc):
        testing_utils.test_cache_content(apiSrc)
