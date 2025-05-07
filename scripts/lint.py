#!/usr/bin/env python
"""
Run linting and style checks on the codebase.
"""

import os
import subprocess
import sys
from typing import List, Tuple


def run_command(command: List[str]) -> Tuple[int, str]:
    """Run a command and return its exit code and output."""
    process = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return process.returncode, process.stdout


def main():
    """Run all linting and style checks."""
    exit_code = 0
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("Running black...")
    black_code, black_output = run_command(["black", "--check", "."])
    if black_code != 0:
        print(f"Black failed with code {black_code}:")
        print(black_output)
        print("To fix, run: black .")
        exit_code = 1
    else:
        print("Black passed!")

    print("\nRunning isort...")
    isort_code, isort_output = run_command(["isort", "--check", "."])
    if isort_code != 0:
        print(f"isort failed with code {isort_code}:")
        print(isort_output)
        print("To fix, run: isort .")
        exit_code = 1
    else:
        print("isort passed!")

    print("\nRunning flake8...")
    flake8_code, flake8_output = run_command(["flake8", "paysafe", "tests", "examples"])
    if flake8_code != 0:
        print(f"flake8 failed with code {flake8_code}:")
        print(flake8_output)
        exit_code = 1
    else:
        print("flake8 passed!")

    print("\nRunning mypy...")
    mypy_code, mypy_output = run_command(["mypy", "paysafe"])
    if mypy_code != 0:
        print(f"mypy failed with code {mypy_code}:")
        print(mypy_output)
        exit_code = 1
    else:
        print("mypy passed!")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()