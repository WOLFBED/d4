"""
d4 - Video Downloader Application
Main entry point for the application.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the app directory to the path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app_core import AppCore
from gui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("d4")
    app.setOrganizationName("d4")

    # Initialize the core controller
    app_core = AppCore()

    # Create and show the main window
    main_window = MainWindow(app_core)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()