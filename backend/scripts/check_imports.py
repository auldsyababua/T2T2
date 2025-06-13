#!/usr/bin/env python3
"""
Check that all Python imports in the codebase are satisfied by requirements.txt
This helps catch missing dependencies before they fail in CI.
"""
import ast
import os
import re
import sys
from pathlib import Path


def get_imports_from_file(filepath):
    """Extract all import statements from a Python file."""
    imports = set()
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return imports


def get_installed_packages():
    """Get packages from requirements.txt."""
    packages = set()
    req_file = Path(__file__).parent.parent / "requirements.txt"

    if not req_file.exists():
        print("requirements.txt not found!")
        return packages

    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name (before any version specifier)
                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if match:
                    package = match.group(1).lower()
                    packages.add(package)
                    # Add common import name variations
                    if package == "pillow":
                        packages.add("pil")
                    elif package == "pyjwt":
                        packages.add("jwt")
                    elif package == "python-telegram-bot":
                        packages.add("telegram")
                    elif package == "open-clip-torch":
                        packages.add("open_clip")
                        packages.add("torch")  # Included with open-clip-torch
                    elif package == "python-dotenv":
                        packages.add("dotenv")
                    elif package == "langchain-openai":
                        packages.add("langchain_openai")
                    elif package == "upstash-redis":
                        packages.add("upstash_redis")
                    elif package == "fastapi":
                        packages.add("starlette")  # FastAPI includes Starlette

    return packages


def get_stdlib_modules():
    """Get a list of Python standard library modules."""
    # This is a simplified list - in production, use stdlib_list package
    return {
        "os",
        "sys",
        "time",
        "datetime",
        "json",
        "re",
        "ast",
        "math",
        "random",
        "collections",
        "itertools",
        "functools",
        "pathlib",
        "typing",
        "enum",
        "dataclasses",
        "abc",
        "asyncio",
        "unittest",
        "logging",
        "warnings",
        "io",
        "string",
        "textwrap",
        "hashlib",
        "hmac",
        "secrets",
        "base64",
        "urllib",
        "http",
        "email",
        "contextlib",
        "copy",
        "pickle",
        "sqlite3",
        "csv",
        "configparser",
        "__future__",  # Special import for Python 2/3 compatibility
    }


def check_missing_imports():
    """Check for imports not covered by requirements.txt."""
    backend_dir = Path(__file__).parent.parent
    all_imports = set()

    # Scan all Python files
    for py_file in backend_dir.rglob("*.py"):
        # Skip test files and this script
        if "test" in str(py_file) or py_file == Path(__file__):
            continue
        all_imports.update(get_imports_from_file(py_file))

    # Get installed packages and stdlib
    installed = get_installed_packages()
    stdlib = get_stdlib_modules()

    # Local imports (from our own codebase)
    local_modules = {"api", "db", "models", "services", "utils", "main", "rate_limit"}

    # Find missing imports
    missing = []
    for imp in sorted(all_imports):
        imp_lower = imp.lower()
        if (
            imp_lower not in installed
            and imp not in stdlib
            and imp not in local_modules
        ):
            missing.append(imp)

    if missing:
        print("❌ Missing packages in requirements.txt:")
        for pkg in missing:
            print(f"  - {pkg}")
        return False
    else:
        print("✅ All imports are covered by requirements.txt")
        return True


if __name__ == "__main__":
    success = check_missing_imports()
    sys.exit(0 if success else 1)
