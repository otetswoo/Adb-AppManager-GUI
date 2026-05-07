#!/usr/bin/env python3
"""
Android App Manager - Main entry point
GUI application for managing Android applications via ADB
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Enable High DPI scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from .ui.main_window import MainWindow


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
