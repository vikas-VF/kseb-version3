#!/usr/bin/env python3
"""
Platform verification script for KSEB Windows build.

This script verifies the build logic without actually creating executables.
Use this to test on non-Windows platforms.

On Windows, use build_windows_exe.py instead.
"""

import os
import sys
import platform
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def check_platform():
    """Check if we're on Windows."""
    print_header("PLATFORM VERIFICATION")

    current_platform = platform.system()
    print(f"Current Platform: {Colors.BOLD}{current_platform}{Colors.ENDC}")
    print(f"Python Version: {Colors.BOLD}{sys.version.split()[0]}{Colors.ENDC}")
    print(f"Architecture: {Colors.BOLD}{platform.machine()}{Colors.ENDC}")

    if current_platform == "Windows":
        print_success("Running on Windows - can build .exe files")
        return True
    else:
        print_error(f"Running on {current_platform} - CANNOT build Windows .exe files")
        print_warning("PyInstaller creates executables for the platform it runs on")
        print_info("To build Windows .exe files, you need a Windows machine")
        return False

def verify_project_structure():
    """Verify project structure exists."""
    print_header("PROJECT STRUCTURE VERIFICATION")

    project_root = Path.cwd()

    required_items = {
        "backend_fastapi": "directory",
        "backend_fastapi/main.py": "file",
        "backend_fastapi/requirements.txt": "file",
        "frontend": "directory",
        "frontend/package.json": "file",
        "frontend/src": "directory",
    }

    all_ok = True

    for item, item_type in required_items.items():
        item_path = project_root / item

        if item_type == "directory":
            if item_path.is_dir():
                print_success(f"Found directory: {item}")
            else:
                print_error(f"Missing directory: {item}")
                all_ok = False
        else:  # file
            if item_path.is_file():
                print_success(f"Found file: {item}")
            else:
                print_error(f"Missing file: {item}")
                all_ok = False

    return all_ok

def check_dependencies():
    """Check if required dependencies are available."""
    print_header("DEPENDENCY VERIFICATION")

    dependencies = {
        "Python packages": [
            ("pyinstaller", "pip install pyinstaller"),
            ("fastapi", "pip install fastapi"),
            ("uvicorn", "pip install uvicorn"),
        ],
        "Node.js tools": [
            ("node", "Install from nodejs.org"),
            ("npm", "Install from nodejs.org"),
        ],
    }

    all_ok = True

    for category, deps in dependencies.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.ENDC}")

        for dep, install_cmd in deps:
            # Check if command exists
            import shutil
            if shutil.which(dep):
                print_success(f"{dep} is available")
            else:
                print_error(f"{dep} is NOT installed")
                print_info(f"  Install: {install_cmd}")
                all_ok = False

    return all_ok

def verify_build_script():
    """Verify build script exists and is valid."""
    print_header("BUILD SCRIPT VERIFICATION")

    build_script = Path("build_windows_exe.py")

    if not build_script.exists():
        print_error("build_windows_exe.py not found")
        return False

    print_success("build_windows_exe.py exists")

    # Check if script is valid Python
    try:
        with open(build_script) as f:
            compile(f.read(), build_script, 'exec')
        print_success("build_windows_exe.py is valid Python code")
    except SyntaxError as e:
        print_error(f"Syntax error in build_windows_exe.py: {e}")
        return False

    return True

def show_recommendations():
    """Show recommendations based on current platform."""
    print_header("RECOMMENDATIONS")

    current_platform = platform.system()

    if current_platform == "Windows":
        print_success("You can proceed with building:")
        print("  python build_windows_exe.py --clean")
    else:
        print_warning(f"You are on {current_platform}, not Windows")
        print("\nTo build Windows .exe files, you have these options:\n")

        print(f"{Colors.BOLD}Option 1: Use a Windows Machine{Colors.ENDC}")
        print("  1. Get access to a Windows 10/11 machine")
        print("  2. Clone this repository")
        print("  3. Run: python build_windows_exe.py --clean")

        print(f"\n{Colors.BOLD}Option 2: Use a Windows VM{Colors.ENDC}")
        print("  1. Install VirtualBox or VMware")
        print("  2. Create Windows 10/11 VM")
        print("  3. Clone repository inside VM")
        print("  4. Run: python build_windows_exe.py --clean")

        print(f"\n{Colors.BOLD}Option 3: Use GitHub Actions (Recommended){Colors.ENDC}")
        print("  1. Push code to GitHub")
        print("  2. Create GitHub Actions workflow (I can create this)")
        print("  3. GitHub will build on Windows automatically")
        print("  4. Download .exe from GitHub Releases")

        print(f"\n{Colors.BOLD}Option 4: Test Logic Only{Colors.ENDC}")
        print("  You can verify the build logic runs without errors:")
        print("  python build_windows_exe.py --help")
        print("\n  But this will NOT create Windows .exe files!")

def main():
    """Main verification function."""
    print_header("KSEB ENERGY ANALYTICS - BUILD VERIFICATION")

    print(f"{Colors.BOLD}This script verifies if you can build Windows executables{Colors.ENDC}\n")

    # Run all checks
    is_windows = check_platform()
    structure_ok = verify_project_structure()
    script_ok = verify_build_script()
    deps_ok = check_dependencies()

    # Summary
    print_header("VERIFICATION SUMMARY")

    checks = [
        ("Platform is Windows", is_windows),
        ("Project structure", structure_ok),
        ("Build script", script_ok),
        ("Dependencies", deps_ok),
    ]

    all_passed = all(result for _, result in checks)

    for check_name, result in checks:
        if result:
            print_success(f"{check_name}: PASS")
        else:
            print_error(f"{check_name}: FAIL")

    print()

    if all_passed and is_windows:
        print_success("✓ ALL CHECKS PASSED - You can build Windows executables!")
        print_info("Run: python build_windows_exe.py --clean")
    elif structure_ok and script_ok:
        print_warning("⚠ BUILD SCRIPT IS READY - But you need Windows to create .exe files")
        show_recommendations()
    else:
        print_error("✗ SOME CHECKS FAILED - Fix issues before building")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
