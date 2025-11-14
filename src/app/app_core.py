"""
Central controller/mediator for the d4 application.
Coordinates between GUI, downloader, and other components.
"""
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from config.settings_manager import SettingsManager
from core.dependency_manager import DependencyManager
from core.downloader import Downloader
from core.post_processor import PostProcessor


class AppCore(QObject):
    """Central controller coordinating all application components."""

    # Signals
    download_started = Signal()
    download_progress = Signal(str)  # Progress message
    download_completed = Signal(bool, str)  # success, message
    dependency_update_progress = Signal(str)  # Update message

    def __init__(self):
        super().__init__()

        # Get app root directory
        self.app_root = Path(__file__).parent
        self.external_dir = self.app_root / "external"

        # Initialize components
        self.settings_manager = SettingsManager()
        self.dependency_manager = DependencyManager(self.external_dir)
        self.downloader = None  # Created when needed
        self.post_processor = PostProcessor()

        # Connect dependency manager signals
        self.dependency_manager.update_progress.connect(self.dependency_update_progress)

    def get_settings(self):
        """Get all current settings."""
        return self.settings_manager.get_all_settings()

    def save_setting(self, key, value):
        """Save a single setting."""
        self.settings_manager.set_setting(key, value)

    def save_all_settings(self, settings_dict):
        """Save all settings at once."""
        for key, value in settings_dict.items():
            self.settings_manager.set_setting(key, value)

    # def check_dependencies(self):
    #     """Check if required dependencies are available."""
    #     return self.dependency_manager.check_dependencies()

    def check_dependencies(self, install_deno_if_missing: bool = False):
        """
        Check if required dependencies are available.

        If install_deno_if_missing is True, this will attempt to install Deno
        on supported Linux distributions when it is not found.
        """
        return self.dependency_manager.check_dependencies(
            install_deno_if_missing=install_deno_if_missing
        )

    def update_dependencies(self):
        """Update external dependencies (yt-dlp, aria2)."""
        return self.dependency_manager.update_all()




    def start_download(self, url, output_path, options):
        """
        Start a download with the given parameters.

        Args:
            url: Video URL or path to batch file
            output_path: Where to save downloaded files
            options: Dictionary of download options
        """
        # Get paths to external executables
        yt_dlp_path = self.dependency_manager.get_ytdlp_path()
        aria2_path = self.dependency_manager.get_aria2_path()

        if not yt_dlp_path:
            self.download_completed.emit(False, "yt-dlp not found. Please update dependencies.")
            return

        # Create downloader instance
        self.downloader = Downloader(yt_dlp_path, aria2_path)

        # Connect signals
        self.downloader.progress_updated.connect(self.download_progress)
        self.downloader.download_finished.connect(self._on_download_finished)

        # Start download
        self.download_started.emit()
        self.downloader.start_download(url, output_path, options)

    def stop_download(self):
        """Stop the current download."""
        if self.downloader:
            self.downloader.stop_download()

    def _on_download_finished(self, success, message):
        """Handle download completion."""
        self.download_completed.emit(success, message)

        # Clean up downloader
        if self.downloader:
            self.downloader.deleteLater()
            self.downloader = None