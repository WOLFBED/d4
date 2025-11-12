"""
Post Processor - Handles optional post-processing tasks
"""
import subprocess
from pathlib import Path
from typing import Optional


class PostProcessor:
    """Handles post-processing of downloaded videos"""

    def __init__(self, dependency_manager):
        """
        Initialize post processor

        Args:
            dependency_manager: DependencyManager instance
        """
        self.deps = dependency_manager

    def process(self, file_path: Path, options: dict) -> tuple[bool, str]:
        """
        Apply post-processing to a downloaded file

        Args:
            file_path: Path to the downloaded file
            options: Processing options dict

        Returns:
            Tuple of (success, message)
        """
        # Most post-processing is handled by yt-dlp itself
        # This method is for any additional custom processing

        if not file_path.exists():
            return False, f"File not found: {file_path}"

        # Example: Additional custom processing could go here
        # For now, we rely on yt-dlp's built-in postprocessors

        return True, "Post-processing complete"

    def convert_audio(self,
                      input_path: Path,
                      output_format: str = 'mp3',
                      bitrate: str = '192') -> tuple[bool, str]:
        """
        Convert audio file to different format

        Args:
            input_path: Input file path
            output_format: Target format (mp3, m4a, opus, etc.)
            bitrate: Audio bitrate

        Returns:
            Tuple of (success, message)
        """
        if not self.deps.ffmpeg_available():
            return False, "ffmpeg not available"

        if not input_path.exists():
            return False, f"Input file not found: {input_path}"

        output_path = input_path.with_suffix(f'.{output_format}')

        try:
            cmd = [
                str(self.deps.ffmpeg_path),
                '-i', str(input_path),
                '-b:a', f'{bitrate}k',
                '-vn',  # No video
                str(output_path),
                '-y'  # Overwrite output
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return True, f"Converted to: {output_path}"
            else:
                return False, f"Conversion failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Conversion timed out"
        except Exception as e:
            return False, f"Conversion error: {e}"

    def embed_thumbnail(self, video_path: Path, thumbnail_path: Path) -> tuple[bool, str]:
        """
        Embed thumbnail into video file (for formats that support it)

        Args:
            video_path: Path to video file
            thumbnail_path: Path to thumbnail image

        Returns:
            Tuple of (success, message)
        """
        if not self.deps.ffmpeg_available():
            return False, "ffmpeg not available"

        if not video_path.exists():
            return False, f"Video file not found: {video_path}"

        if not thumbnail_path.exists():
            return False, f"Thumbnail not found: {thumbnail_path}"

        # Note: yt-dlp handles this better with its built-in postprocessor
        # This is just an example of how it could be done manually

        return True, "Use yt-dlp's EmbedThumbnail postprocessor instead"