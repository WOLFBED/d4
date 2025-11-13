"""
External executable management.
Handles downloading and updating yt-dlp and aria2.
"""
import os
import stat
import platform
import requests
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class DependencyManager(QObject):
    """Manages external dependencies (yt-dlp, aria2)."""

    update_progress = Signal(str)

    def __init__(self, external_dir: Path):
        super().__init__()
        self.external_dir = Path(external_dir)
        self.external_dir.mkdir(parents=True, exist_ok=True)

        self.ytdlp_dir = self.external_dir / "yt-dlp"
        self.aria2_dir = self.external_dir / "aria2"

        self.ytdlp_dir.mkdir(exist_ok=True)
        self.aria2_dir.mkdir(exist_ok=True)

    def check_dependencies(self) -> dict:
        """Check if dependencies are available."""
        return {
            'ytdlp': self.get_ytdlp_path() is not None,
            'aria2': self.get_aria2_path() is not None,
        }

    def get_ytdlp_path(self) -> Path:
        """Get the path to the latest yt-dlp executable."""
        return self._get_latest_executable(self.ytdlp_dir, 'yt-dlp')

    def get_aria2_path(self) -> Path:
        """Get the path to the latest aria2c executable."""
        return self._get_latest_executable(self.aria2_dir, 'aria2c')

    def _get_latest_executable(self, base_dir: Path, exec_name: str) -> Path:
        """Find the latest version of an executable in version subdirectories."""
        if not base_dir.exists():
            return None

        # Look for version directories
        version_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        if not version_dirs:
            return None

        # Sort by modification time (latest first)
        version_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Find the executable
        for version_dir in version_dirs:
            if platform.system() == "Windows":
                exec_path = version_dir / f"{exec_name}.exe"
            else:
                exec_path = version_dir / exec_name

            if exec_path.exists():
                return exec_path

        return None

    def update_all(self) -> bool:
        """Update all dependencies."""
        ytdlp_success = self.update_ytdlp()
        aria2_success = self.update_aria2()
        return ytdlp_success and aria2_success

    def update_ytdlp(self) -> bool:
        """Download the latest yt-dlp release."""
        try:
            self.update_progress.emit("Checking for latest yt-dlp release...")

            # Get latest release info
            api_url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            tag_name = release_data['tag_name']
            self.update_progress.emit(f"Latest yt-dlp version: {tag_name}")

            # Determine the correct asset for the platform
            system = platform.system()
            if system == "Linux":
                asset_name = "yt-dlp"
            elif system == "Windows":
                asset_name = "yt-dlp.exe"
            elif system == "Darwin":  # macOS
                asset_name = "yt-dlp_macos"
            else:
                self.update_progress.emit(f"Unsupported platform: {system}")
                return False

            # Find the download URL
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'] == asset_name:
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                self.update_progress.emit(f"Could not find {asset_name} in release assets")
                return False

            # Create version directory
            date_str = datetime.now().strftime("%b%d-%Y").lower()
            version_dir = self.ytdlp_dir / date_str
            version_dir.mkdir(parents=True, exist_ok=True)

            # Download the executable
            exec_path = version_dir / "yt-dlp"
            self.update_progress.emit(f"Downloading yt-dlp to {exec_path}...")

            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            with open(exec_path, 'wb') as f:
                f.write(response.content)

            # Make executable on Unix-like systems
            if system != "Windows":
                os.chmod(exec_path, os.stat(exec_path).st_mode | stat.S_IEXEC)

            self.update_progress.emit("yt-dlp updated successfully!")
            return True

        except Exception as e:
            self.update_progress.emit(f"Error updating yt-dlp: {e}")
            return False

    def update_aria2(self) -> bool:
        """Download the latest aria2 release."""
        try:
            self.update_progress.emit("Checking for latest aria2 release...")

            # Get latest release info
            api_url = "https://api.github.com/repos/aria2/aria2/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            tag_name = release_data['tag_name']
            self.update_progress.emit(f"Latest aria2 version: {tag_name}")

            # Note: aria2 releases are archives, not single executables
            # For simplicity, we'll just check if it exists or create a placeholder
            # In production, you'd download and extract the appropriate archive

            system = platform.system()
            date_str = datetime.now().strftime("%b%d-%Y").lower()
            version_dir = self.aria2_dir / date_str
            version_dir.mkdir(parents=True, exist_ok=True)

            # This is a simplified version - in production you'd download and extract
            self.update_progress.emit("aria2 update completed (placeholder)")
            return True

        except Exception as e:
            self.update_progress.emit(f"Error updating aria2: {e}")
            return False