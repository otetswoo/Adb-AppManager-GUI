#!/usr/bin/env python3
"""
Android App Manager - Main entry point
Запуск модульной версии приложения из src/android_manager/
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

# Import and run main from android_manager package
from android_manager.main import main

if __name__ == "__main__":
    main()
