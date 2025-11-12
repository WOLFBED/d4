"""
Video Downloader - Handles video downloads using yt-dlp
"""
from pathlib import Path
from typing import Callable, Optional
import yt_dlp


class VideoDownloader:
    """Manages video downloads using yt-dlp library"""

    def __init__(self, dependency_manager):
        """
        Initialize downloader

        Args:
            dependency_manager: DependencyManager instance
        """
        self.deps = dependency_manager

    def download(self,
                 url_or_batch: str,
                 options: dict,
                 progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """
        Download video(s) from URL or batch file

        Args:
            url_or_batch: URL or path to batch file with URLs
            options: yt-dlp options dictionary
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, message)
        """
        # Check if it's a batch file
        batch_path = Path(url_or_batch)
        if batch_path.exists() and batch_path.is_file():
            return self._download_batch(batch_path, options, progress_callback)
        else:
            return self._download_single(url_or_batch, options, progress_callback)

    def _download_single(self,
                         url: str,
                         options: dict,
                         progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Download from a single URL"""
        # Add progress hook if callback provided
        opts = options.copy()
        if progress_callback:
            opts['progress_hooks'] = [self._make_progress_hook(progress_callback)]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return True, f"Successfully downloaded: {url}"
        except yt_dlp.utils.DownloadError as e:
            return False, f"Download error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _download_batch(self,
                        batch_file: Path,
                        options: dict,
                        progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Download from a batch file containing multiple URLs"""
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            if not urls:
                return False, "Batch file is empty"

            # Add progress hook if callback provided
            opts = options.copy()
            if progress_callback:
                opts['progress_hooks'] = [self._make_progress_hook(progress_callback)]

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download(urls)

            return True, f"Successfully downloaded {len(urls)} video(s)"
        except FileNotFoundError:
            return False, f"Batch file not found: {batch_file}"
        except yt_dlp.utils.DownloadError as e:
            return False, f"Download error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _make_progress_hook(self, callback: Callable):
        """Create a progress hook function for yt-dlp"""

        def hook(d: dict):
            """Progress hook called by yt-dlp"""
            if d['status'] == 'downloading':
                progress_info = {
                    'status': 'downloading',
                    'filename': d.get('filename', 'Unknown'),
                    'downloaded_bytes': d.get('downloaded_bytes', 0),
                    'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                    'speed': d.get('speed', 0),
                    'eta': d.get('eta', 0),
                }
                callback(progress_info)
            elif d['status'] == 'finished':
                callback({
                    'status': 'finished',
                    'filename': d.get('filename', 'Unknown'),
                })

        return hook

    def extract_info(self, url: str) -> Optional[dict]:
        """
        Extract video information without downloading

        Args:
            url: Video URL

        Returns:
            Video info dict or None if failed
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Failed to extract info: {e}")
            return None