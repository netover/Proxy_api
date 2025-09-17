import glob
import re

def fix_fstrings_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError:
        print(f"Could not read file: {file_path}")
        return

    # This regex finds f-strings that do not contain any curly braces.
    # It handles both single and double quotes, and multi-line strings.
    pattern = re.compile(r'f(["\']{1,3})((?:[^{}]|(?:{{|}}))+?)\1')

    new_content, count = pattern.subn(r'\1\2\1', content)

    if count > 0:
        print(f"Found and fixed {count} malformed f-string(s) in {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except IOError:
            print(f"Could not write to file: {file_path}")

if __name__ == "__main__":
    print("Starting f-string fix scan...")
    # Use glob to find all python files recursively
    for py_file in glob.glob("**/*.py", recursive=True):
        fix_fstrings_in_file(py_file)
    print("Scan complete.")
