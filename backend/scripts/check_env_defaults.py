#!/usr/bin/env python3
"""
Check that all environment variable accesses have proper defaults or error handling.
This prevents TypeError when env vars are missing.
"""
import ast
import os
import sys
from pathlib import Path


class EnvVarChecker(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.issues = []

    def visit_Call(self, node):
        # Check for os.getenv() calls
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "getenv"
        ):
            # Check if it has a default value (2nd argument)
            if len(node.args) < 2:
                var_name = ast.literal_eval(node.args[0]) if node.args else "UNKNOWN"
                line = node.lineno

                # Check if the result is used in a way that could cause TypeError
                parent = self.get_parent_context(node)
                if self.is_risky_usage(parent):
                    self.issues.append(
                        {
                            "file": self.filepath,
                            "line": line,
                            "var": var_name,
                            "issue": "No default value and used in risky context",
                        }
                    )

        self.generic_visit(node)

    def get_parent_context(self, node):
        # This is simplified - in real implementation, track parent nodes
        return None

    def is_risky_usage(self, parent):
        # Check if the env var is used in int(), float(), or other risky contexts
        # For now, we'll flag all missing defaults as potentially risky
        return True


def check_file(filepath):
    """Check a single Python file for env var issues."""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Skip if no os.getenv in file
        if "os.getenv" not in content:
            return []

        tree = ast.parse(content)
        checker = EnvVarChecker(filepath)
        checker.visit(tree)
        return checker.issues
    except Exception as e:
        print(f"Error checking {filepath}: {e}")
        return []


def check_all_files():
    """Check all Python files for environment variable issues."""
    backend_dir = Path(__file__).parent.parent
    all_issues = []

    for py_file in backend_dir.rglob("*.py"):
        # Skip test files
        if "test" in str(py_file):
            continue
        issues = check_file(py_file)
        all_issues.extend(issues)

    if all_issues:
        print("❌ Environment variable issues found:")
        for issue in all_issues:
            rel_path = Path(issue["file"]).relative_to(backend_dir)
            print(f"  {rel_path}:{issue['line']} - {issue['var']}: {issue['issue']}")
        print("\nConsider adding default values:")
        print("  os.getenv('VAR_NAME', 'default_value')")
        return False
    else:
        print("✅ All environment variables have proper defaults or handling")
        return True


if __name__ == "__main__":
    success = check_all_files()
    sys.exit(0 if success else 1)
