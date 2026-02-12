#!/usr/bin/env python3
"""
Custom linter to check for multiple return statements and break/continue usage.
"""

import ast
import sys
from pathlib import Path


class ConventionChecker(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.issues = []
        self.current_function = None

    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
        breaks = [n for n in ast.walk(node) if isinstance(n, ast.Break)]
        continues = [n for n in ast.walk(node) if isinstance(n, ast.Continue)]

        # Check for multiple returns
        if len(returns) > 1:
            for ret in returns:
                self.issues.append(
                    f"{self.filename}:{ret.lineno}: Function '{node.name}' has multiple return statements. "
                    f"Consider restructuring to have a single return at the end."
                )

        # Check for break statements
        for brk in breaks:
            self.issues.append(
                f"{self.filename}:{brk.lineno}: Function '{node.name}' uses 'break'. "
                f"Consider restructuring the loop to avoid break statements."
            )

        # Check for continue statements
        for cont in continues:
            self.issues.append(
                f"{self.filename}:{cont.lineno}: Function '{node.name}' uses 'continue'. "
                f"Consider restructuring the loop to avoid continue statements."
            )

        # Continue visiting child nodes
        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        # Handle async functions the same way
        self.visit_FunctionDef(node)


def check_file(filepath):
    """Check a single Python file for convention violations."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(filepath))
        checker = ConventionChecker(filepath)
        checker.visit(tree)
        return checker.issues
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []


def main():
    """Main function to check all Python files in the project."""
    if len(sys.argv) > 1:
        # Check specific files provided as arguments
        files_to_check = [Path(f) for f in sys.argv[1:]]
    else:
        # Check all Python files in src directory
        project_root = Path(__file__).parent
        files_to_check = list((project_root / "src").rglob("*.py"))

    all_issues = []
    for filepath in files_to_check:
        if filepath.suffix == '.py':
            issues = check_file(filepath)
            all_issues.extend(issues)

    # Print all issues
    for issue in all_issues:
        print(issue)

    # Exit with error code if there are issues
    if all_issues:
        print(f"\nFound {len(all_issues)} convention violations.")
        return 1
    else:
        print("No convention violations found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())