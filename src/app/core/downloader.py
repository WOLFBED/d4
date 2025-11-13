"""
Video download logic using yt-dlp.
"""
import subprocess
import signal
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThreadPool

from utils.threads import DownloadWorker


class Downloader(QObject):
    """Handles video downloading via yt-dlp."""

    progress_updated = Signal(str)
    download_finished = Signal(bool, str)  # success, message

    def __init__(self, ytdlp_path: Path, aria2_path: Path = None):
        super().__init__()
        self.ytdlp_path = Path(ytdlp_path)
        self.aria2_path = Path(aria2_path) if aria2_path else None
        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker = None

    def start_download(self, url: str, output_path: str, options: dict):
        """
        Start downloading video(s).

        Args:
            url: Video URL or path to batch file
            output_path: Output directory
            options: Dictionary of download options
        """
        # Build yt-dlp command
        cmd = [str(self.ytdlp_path)]

        # Output template
        cmd.extend(['-o', str(Path(output_path) / '%(title)s.%(ext)s')])

        # Format selection
        if options.get('audio_only'):
            cmd.extend(['-f', 'bestaudio/best', '-x'])
        else:
            cmd.extend(['-f', options.get('format', 'bestvideo+bestaudio/best')])

        # Thumbnail options
        if options.get('write_thumbnail'):
            cmd.append('--write-thumbnail')
        if options.get('embed_thumbnail'):
            cmd.append('--embed-thumbnail')

        # Metadata options
        if options.get('write_comments'):
            cmd.append('--write-comments')
        if options.get('write_metadata'):
            cmd.append('--write-info-json')
            cmd.append('--embed-metadata')

        # Subtitle options
        if options.get('write_subs'):
            cmd.append('--write-subs')
            cmd.append('--embed-subs')

        # Chapter options
        if options.get('split_chapters'):
            cmd.append('--split-chapters')

        # SponsorBlock
        if options.get('use_sponsorblock'):
            cmd.append('--sponsorblock-mark')
            cmd.append('all')

        # Proxy
        if options.get('proxy'):
            cmd.extend(['--proxy', f"socks5://{options['proxy']}"])

        # Cookies
        if options.get('cookies_file'):
            cmd.extend(['--cookies', options['cookies_file']])

        # aria2 integration
        if self.aria2_path and self.aria2_path.exists():
            cmd.extend(['--external-downloader', str(self.aria2_path)])
            cmd.extend(['--external-downloader-args', 'aria2c:"-x 16 -s 16 -k 1M"'])

        # Progress output
        cmd.append('--newline')
        cmd.append('--progress')

        # Check if URL is a batch file
        url_path = Path(url)
        if url_path.exists() and url_path.is_file():
            cmd.extend(['--batch-file', str(url_path)])
        else:
            cmd.append(url)

        # Create and start worker
        self.current_worker = DownloadWorker(cmd)
        self.current_worker.signals.progress.connect(self.progress_updated)
        self.current_worker.signals.finished.connect(self._on_worker_finished)
        self.current_worker.signals.error.connect(self._on_worker_error)

        self.thread_pool.start(self.current_worker)

    def stop_download(self):
        """Stop the current download."""
        if self.current_worker:
            self.current_worker.stop()
            self.progress_updated.emit("Download stopped by user")

    def _on_worker_finished(self, success, message):
        """Handle worker completion."""
        self.download_finished.emit(success, message)
        self.current_worker = None

    def _on_worker_error(self, error_msg):
        """Handle worker error."""
        self.progress_updated.emit(f"Error: {error_msg}")
        self.download_finished.emit(False, error_msg)
        self.current_worker = None