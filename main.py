#!/usr/bin/env python
"""
Entry point script for running the FinalCheck application.

This script launches the Streamlit app for PDF compliance verification.
"""

import os
import sys

from finalcheck.app import main

if __name__ == "__main__":
    # Add the current directory to the path so the package can be found
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Start the Streamlit app
    main()
