"""
Script to explicitly import all dependent packages
for troubleshooting PyInstaller dependency issues.
"""

try:
    import importlib
except ImportError as e:
    raise Exception("Cannot import importlib: " + str(e))

# List of packages that should be explicitly imported
# (add more as needed)
packages_to_import = [
    "uvicorn",
    "fastapi",
    "pydantic",
    "httpx",
    "PyYAML",
    "slowapi",
    "python_multipart",
    "structlog",
]


# Create a file containing a list of all actual imports
def diagnose_a_package(package):
    try:
        module = importlib.import_module(package)
        print(f"✅ Successfully imported: {package}")
        submodules = inspect.getmembers(module, inspect.ismodule)
        for name, submodule in submodules:
            fullname = f"{package}.{name}"
            print(f"  ✅ Submodule: {fullname}")
            return fullname
    except Exception as e:
        print(f"❌ Failed to import: {package}")
        print(f"   Error: {str(e)}")
        return None


print("Python Dependency Diagnosis\n" + "=" * 40)

diagnosed_packages = []

for package in packages_to_import:
    result = diagnose_a_package(package)
    if result:
        diagnosed_packages.append(result)

with open("dependency_report.txt", "w") as report:
    import_statement = "\n".join(
        f"from {dp.replace('.', ' import ')}" if "." in dp else f"import {dp}"
        for dp in diagnosed_packages
    )

    report.write("Successfully diagnosed packages:\n" + import_statement)
    missing_known_exprs = [
        i
        for i in packages_to_import
        if i not in import_statement.split("from")[0]
    ]
    report.write("\n\nKnown missing:\n" + "\n".join(missing_known_exprs))

print("Diagnostic report saved to dependency_report.txt")
