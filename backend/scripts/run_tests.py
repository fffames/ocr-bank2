#!/usr/bin/env python3
"""
Convenience script for running tests with various options.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --api              # Run only API tests
"""
import sys
import subprocess
from pathlib import Path


def run_tests(args):
    """Run pytest with specified arguments."""
    # Base pytest command
    cmd = ["pytest", "tests/"]

    # Add options
    if "--unit" in args:
        cmd.extend(["-m", "unit"])
    elif "--integration" in args:
        cmd.extend(["-m", "integration"])
    elif "--api" in args:
        cmd.extend(["-m", "api"])

    if "--coverage" in args:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    if "--verbose" in args:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    if "--fast" in args:
        cmd.extend(["-m", "not slow"])

    # Run tests
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    # Print coverage report location if generated
    if "--coverage" in args and result.returncode == 0:
        print("\n" + "="*70)
        print("Coverage report generated: htmlcov/index.html")
        print("="*70)

    return result.returncode


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        # Default: run all tests with standard output
        args = ["-v"]

    # Help flag
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
