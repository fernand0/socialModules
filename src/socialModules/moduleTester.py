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
        logging.info("Start setup")
        import socialModules.moduleRules
        import sys
        from io import StringIO

        # Redirect stdout
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        rules = socialModules.moduleRules.moduleRules()
        rules.checkRules()

        # Restore stdout
        sys.stdout = old_stdout

        name = self.module.getService()
        rulesList = rules.selectRule(name)

        final_rules_with_type = []
        seen_rules = set()

        for rule in rulesList:
            if not name.lower() in rule and rule in rules.rules:
                for sub_rule in rules.rules[rule]:
                    if name.lower() in sub_rule and sub_rule not in seen_rules:
                        final_rules_with_type.append((sub_rule, 'dst'))
                        seen_rules.add(sub_rule)
            elif rule not in seen_rules:
                final_rules_with_type.append((rule, 'src'))
                seen_rules.add(rule)

        for i, (rule_name, rule_type) in enumerate(final_rules_with_type):
            print(f"{i}) {rule_name} ({rule_type})")

        if not final_rules_with_type:
            sel = int(input(f"Which rule to use? (0-{len(final_rules_with_type)-1}): "))
            if sel < 0 or sel >= len(final_rules_with_type):
                print("Invalid selection")
                return False

        try:
            sel = int(input(f"Which rule to use? (0-{len(final_rules_with_type)-1}): "))
            if sel < 0 or sel >= len(final_rules_with_type):
                print("Invalid selection")

            selected_rule, rule_type = final_rules_with_type[sel]
        except (ValueError, IndexError):
            print("Invalid input, using first rule")
            selected_rule, rule_type = final_rules_with_type[0]

        print(f"Selected rule: {selected_rule} (Type: {rule_type})")

        try:
            if rule_type == 'src':
                self.api_src = rules.readConfigSrc("", selected_rule, rules.more[selected_rule])
            elif rule_type == 'dst':
                self.api_src = rules.readConfigDst("", selected_rule, None, None)

            if self.api_src:
                print(f"{name} client initialized for: {self.api_src.user}")
                return True
            else:
                print(f"Error: Could not initialize API for rule '{selected_rule}'")
                return False
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
        self.add_test("Edit post test", self.test_edit_post)
        self.add_test("Favorites management test", self.test_favorites_management)
        self.add_test("Cache content verification", self.test_cache_content)

    def register_specific_tests(self, tester):
        # Default: no specific tests for now
        pass

    def run(self):
        if not self.setup():
            return

        self.register_common_tests()
        if hasattr(self.module, 'register_specific_tests'):
            self.module.register_specific_tests(self)

        while True:
            print(f"\n=== Interactive {self.module.getService()} Testing ===")
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

    def test_edit_post(self, apiSrc):
        testing_utils.test_edit_post(apiSrc)

    def test_favorites_management(self, apiSrc):
        testing_utils.test_favorites_management(apiSrc)

    def test_cache_content(self, apiSrc):
        testing_utils.test_cache_content(apiSrc)
