#!/usr/bin/env python3
"""
Video Downloader Application Entry Point
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from app_core import AppCore


def main():
    """Initialize and run the application"""
    # Create config directory if it doesn't exist
    config_dir = Path.home() / ".config" / "dealer"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Dealer")
    app.setOrganizationName("Dealer")

    # Initialize core and main window
    core = AppCore()
    window = MainWindow(core)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()