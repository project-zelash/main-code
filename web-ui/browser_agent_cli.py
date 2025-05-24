#!/usr/bin/env python3
"""
Browser Agent CLI

A command-line interface for running browser agent tasks using the helper functions.
This script makes it easy to run tasks, check status, and retrieve logs.
"""

import sys
import os
import argparse
from src.helpers.utils import main as utils_main

if __name__ == "__main__":
    # Add the project root to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run the main function from utils
    utils_main()
