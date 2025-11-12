"""
Dependency Manager - Manages external executables
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class DependencyManager:
    """Manages external dependencies like yt-dlp and ffmpeg"""

    def __init__(self):
        self.ytdlp_path: Optional[Path] = None
        self.ffmpeg_path: Optional[Path] = None
        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required dependencies in system PATH"""
        # Check for yt-dlp
        ytdlp = shutil.which('yt-dlp')
        if ytdlp:
            self.ytdlp_path = Path(ytdlp)

        # Check for ffmpeg
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            self.ffmpeg_path = Path(ffmpeg)

    def ytdlp_available(self) -> bool:
        """Check if yt-dlp is available"""
        return self.ytdlp_path is not None

    def ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available"""
        return self.ffmpeg_path is not None

    def get_ytdlp_version(self) -> Optional[str]:
        """Get yt-dlp version string"""
        if not self.ytdlp_available():
            return None

        try:
            result = subprocess.run(
                [str(self.ytdlp_path), '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            return None

    def get_ffmpeg_version(self) -> Optional[str]:
        """Get ffmpeg version string"""
        if not self.ffmpeg_available():
            return None

        try:
            result = subprocess.run(
                [str(self.ffmpeg_path), '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Get first line only
            return result.stdout.split('\n')[0]
        except (subprocess.SubprocessError, OSError):
            return None

    def update_ytdlp(self) -> tuple[bool, str]:
        """
        Update yt-dlp to latest version

        Returns:
            Tuple of (success, message)
        """
        if not self.ytdlp_available():
            return False, "yt-dlp not found"

        try:
            result = subprocess.run(
                [str(self.ytdlp_path), '-U'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Update timed out"
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"Update failed: {e}"