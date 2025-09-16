#!/usr/bin/env python3
"""
Simple script to fix all MD051 link fragments in a single file
"""
import unicodedata


def normalize_fragment(text):
    """Normalize accented characters to ASCII"""
    return (
        "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace("_", "-")
        .replace(" ", "-")
        .lower()
    )


def fix_file(filepath):
    """Fix accented link fragments in one file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return False

    original = content

    import re

    # Find all links with fragments
    pattern = r"\[(.*?)\]\((.*?)(#[^)]*)\)"

    def replace_match(match):
        text, base_url, fragment = match.groups()
        normalized = normalize_fragment(fragment)
        if fragment != normalized:
            return f"[{text}]({base_url}{normalized})"
        return match.group(0)

    new_content = re.sub(pattern, replace_match, content)

    if new_content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✓ Fixed links in {filepath}")
        return True

    return False


# Fix the specific file
if fix_file("docs/FILE_REFERENCE.md"):
    print("MD051 link fragments fixed!")
else:
    print("No MD051 issues found.")
