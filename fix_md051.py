#!/usr/bin/env python3
"""
Script to fix MD051/link-fragments issues by normalizing accented characters
"""
import os
import re
import unicodedata
from pathlib import Path


def normalize_fragment(fragment: str) -> str:
    """Normalize accented characters in fragment"""
    normalized = (
        unicodedata.normalize("NFD", fragment)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized)
    return re.sub(r"-+", "-", normalized).strip("-").lower()


def fix_md051_issues(file_path):
    """Fix MD051 link fragment issues in a single file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping {file_path} due to encoding issues")
        return False

    original_content = content

    # Fix link fragments with accents
    pattern = r"\[(.*?)\]\(([^#]*#[^)]*)\)"
    matches = re.finditer(pattern, content)

    for match in matches:
        text, full_link = match.group(1), match.group(2)
        if "#" in full_link:
            url, fragment = full_link.split("#", 1)
            normalized = normalize_fragment(fragment)
            if fragment != normalized:
                # Replace the exact link
                old_link = f"[{text}]({full_link})"
                new_link = f"[{text}]({url}#{normalized})"
                if old_link in content:
                    content = content.replace(old_link, new_link)
                    print(
                        f"Fixed fragment in {file_path}: {fragment} -> {normalized}"
                    )

    # Write back if changed
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


# Process all MD files in docs/
fixed_count = 0
for root, dirs, files in os.walk("./docs"):
    for file in files:
        if file.endswith((".md", ".markdown")):
            file_path = os.path.join(root, file)
            if fix_md051_issues(Path(file_path)):
                fixed_count += 1

print(f"Total files fixed: {fixed_count}")
