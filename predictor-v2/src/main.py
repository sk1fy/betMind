#!/usr/bin/env python3
"""CS2 Match Prediction System v2.0 — Entry point."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.menus import Application


def main():
    try:
        app = Application()
        app.run()
    except KeyboardInterrupt:
        print("\n\n  \033[2mGoodbye!\033[0m\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
