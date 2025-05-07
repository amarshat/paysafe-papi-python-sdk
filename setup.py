#!/usr/bin/env python

import os
import re
from setuptools import setup, find_packages

# Read version from module without importing
with open("paysafe/version.py", "r") as f:
    version_match = re.search(r"VERSION = ['\"]([^'\"]*)['\"]", f.read())
    if version_match:
        version = version_match.group(1)
    else:
        version = "0.1.0"

# Read README for long description
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="paysafe",
    version=version,
    description="Python SDK for the Paysafe API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Amar Akshat",
    author_email="amar.akshat@paysafe.com",
    url="https://github.com/paysafe/paysafe-sdk-python",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "requests>=2.22.0",
        "pydantic>=1.8.0"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
