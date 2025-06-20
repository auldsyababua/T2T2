#!/usr/bin/env python3
"""Fix all relative imports in the backend to use absolute imports."""
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix imports in a single Python file."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Fix common relative imports to absolute imports
    replacements = [
        (r"from utils\.", "from backend.utils."),
        (r"from api\.", "from backend.api."),
        (r"from db\.", "from backend.db."),
        (r"from models\.", "from backend.models."),
        (r"from services\.", "from backend.services."),
        (r"from config\.", "from backend.config."),
        (r"import utils\.", "import backend.utils."),
        (r"import api\.", "import backend.api."),
        (r"import db\.", "import backend.db."),
        (r"import models\.", "import backend.models."),
        (r"import services\.", "import backend.services."),
        (r"import config\.", "import backend.config."),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Fix imports in all Python files in the backend directory."""
    backend_dir = Path(__file__).parent.parent / "backend"

    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        return

    fixed_files = []

    for py_file in backend_dir.rglob("*.py"):
        # Skip __pycache__ directories
        if "__pycache__" in str(py_file):
            continue

        if fix_imports_in_file(py_file):
            fixed_files.append(py_file)
            print(f"Fixed imports in: {py_file.relative_to(backend_dir.parent)}")

    print(f"\nFixed {len(fixed_files)} files")


if __name__ == "__main__":
    main()
