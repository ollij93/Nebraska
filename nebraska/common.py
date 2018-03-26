"""
Private common utilities for the banking package
"""
import os

NEBRASKA_DIR = os.path.join(os.path.expanduser("~"), ".nebraska")

CATEGORIES_FILE = os.path.join(NEBRASKA_DIR, "known_descriptions.json")
CONFIG_FILE = os.path.join(NEBRASKA_DIR, "config.json")
CACHE_FILE = os.path.join(NEBRASKA_DIR, "cache.json")
