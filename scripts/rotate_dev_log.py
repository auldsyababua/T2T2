#!/usr/bin/env python3
"""
Dev Log Rotation Script
Keeps recent entries in dev_log.md and archives older ones
Run this when dev_log.md exceeds 500 lines
"""

import re
from datetime import datetime
from pathlib import Path


def rotate_dev_log(max_entries=10):
    """Keep only the most recent N session entries"""

    # Read current dev log
    dev_log_path = Path(__file__).parent.parent / "dev_log.md"
    if not dev_log_path.exists():
        print("No dev_log.md found")
        return

    with open(dev_log_path, "r") as f:
        content = f.read()

    # Split into header and entries
    parts = content.split("\n---\n", 1)
    if len(parts) < 2:
        print("No entries found")
        return

    header = parts[0]
    entries_section = parts[1]

    # Split entries by session markers (## YYYY-MM-DD)
    entry_pattern = r"(## \d{4}-\d{2}-\d{2}.*?)(?=## \d{4}-\d{2}-\d{2}|$)"
    entries = re.findall(entry_pattern, entries_section, re.DOTALL)

    if len(entries) <= max_entries:
        print(f"Only {len(entries)} entries, no rotation needed")
        return

    # Archive old entries
    archive_dir = Path(__file__).parent.parent / "archive"
    archive_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = archive_dir / f"dev_log_archive_{timestamp}.md"

    archived_entries = entries[:-max_entries]
    with open(archive_path, "w") as f:
        f.write("# Archived Dev Log Entries\n\n")
        f.write(f"Archived on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        for entry in archived_entries:
            f.write(entry)
            f.write("\n")

    # Write updated dev log with recent entries only
    recent_entries = entries[-max_entries:]
    with open(dev_log_path, "w") as f:
        f.write(header)
        f.write("\n\n---\n\n")
        for entry in recent_entries:
            f.write(entry)
            f.write("\n")

    # Add rotation notice
    with open(dev_log_path, "a") as f:
        f.write("\n---\n\n## Log Rotated\n\n")
        f.write(f"Older entries archived to: archive/{archive_path.name}\n")
        f.write(f"Rotation performed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"✓ Archived {len(archived_entries)} entries to {archive_path}")
    print(f"✓ Kept {len(recent_entries)} recent entries in dev_log.md")


def create_summary():
    """Create a summary of all dev log entries for quick reference"""

    dev_log_path = Path(__file__).parent.parent / "dev_log.md"
    archive_dir = Path(__file__).parent.parent / "archive"
    summary_path = Path(__file__).parent.parent / "DEV_LOG_SUMMARY.md"

    summary_content = ["# Dev Log Summary\n\n"]
    summary_content.append("Quick reference of all development sessions\n\n")

    # Process current dev log
    if dev_log_path.exists():
        with open(dev_log_path, "r") as f:
            content = f.read()

        # Extract session headers and key points
        sessions = re.findall(
            r"## (\d{4}-\d{2}-\d{2}.*?)\n\n### What Was Done:(.*?)(?=\n###|\n---|\Z)",
            content,
            re.DOTALL,
        )

        for date, tasks in sessions:
            summary_content.append(f"## {date}\n")
            # Extract bullet points
            bullets = re.findall(r"^\d+\. \*\*(.*?)\*\*:", tasks, re.MULTILINE)
            for bullet in bullets[:3]:  # First 3 items
                summary_content.append(f"- {bullet}\n")
            summary_content.append("\n")

    # Process archives
    if archive_dir.exists():
        for archive_file in sorted(archive_dir.glob("dev_log_archive_*.md")):
            summary_content.append(f"### Archived: {archive_file.name}\n\n")

    with open(summary_path, "w") as f:
        f.writelines(summary_content)

    print(f"✓ Created summary at {summary_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        create_summary()
    else:
        rotate_dev_log()
        create_summary()
