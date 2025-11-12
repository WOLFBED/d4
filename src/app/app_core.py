"""
Application Core - Controller/Mediator
Manages communication between GUI and backend components
"""
from pathlib import Path
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal

from config.settings_manager import SettingsManager
from core.dependency_manager import DependencyManager
from core.downloader import VideoDownloader
from core.post_processor import PostProcessor
from utils.threads import DownloadWorker


class AppCore(QObject):
    """Central controller for the application"""

    # Signals for GUI updates
    download_started = Signal()
    download_progress = Signal(dict)  # Progress info dict
    download_completed = Signal(bool, str)  # success, message

    def __init__(self):
        super().__init__()

        # Initialize settings manager
        config_dir = Path.home() / ".config" / "dealer"
        self.settings = SettingsManager(config_dir / "settings.json")

        # Initialize dependency manager
        self.deps = DependencyManager()

        # Initialize downloader and postprocessor
        self.downloader = VideoDownloader(self.deps)
        self.postprocessor = PostProcessor(self.deps)

        # Track current download worker
        self.current_worker: Optional[DownloadWorker] = None

    def get_settings(self) -> dict:
        """Get all current settings"""
        return self.settings.get_all()

    def save_persistent_settings(self, output_path: str = None,
                                 proxy: str = None,
                                 cookies_file: str = None):
        """Save settings that persist across sessions"""
        if output_path is not None:
            self.settings.set("output_path", output_path)
        if proxy is not None:
            self.settings.set("proxy", proxy)
        if cookies_file is not None:
            self.settings.set("cookies_file", cookies_file)
        self.settings.save()

    def start_download(self,
                      url_or_batch: str,
                      output_path: str,
                      download_options: dict,
                      proxy: str = "",
                      cookies_file: str = "",
                      progress_callback: Callable = None,
                      finished_callback: Callable = None) -> DownloadWorker:
        """
        Start a download operation in a background thread

        Args:
            url_or_batch: URL or path to batch file
            output_path: Where to save downloads
            download_options: Dict of yt-dlp options
            proxy: SOCKS5 proxy address
            cookies_file: Path to cookies file
            progress_callback: Function to call with progress updates
            finished_callback: Function to call when download completes

        Returns:
            DownloadWorker instance
        """
        # Build yt-dlp options
        yt_dlp_opts = self._build_ytdlp_options(
            output_path, download_options, proxy, cookies_file
        )

        # Create worker
        worker = DownloadWorker(
            self.downloader,
            self.postprocessor,
            url_or_batch,
            yt_dlp_opts,
            download_options
        )

        # Connect signals if callbacks provided
        if progress_callback:
            worker.signals.progress.connect(progress_callback)
        if finished_callback:
            worker.signals.finished.connect(finished_callback)

        # Store reference
        self.current_worker = worker

        return worker

    def _build_ytdlp_options(self, output_path: str,
                            download_options: dict,
                            proxy: str,
                            cookies_file: str) -> dict:
        """Build yt-dlp options dictionary from GUI options"""
        opts = {
            'outtmpl': str(Path(output_path) / '%(title)s.%(ext)s'),
            'progress_hooks': [],
        }

        # Add proxy if specified
        if proxy:
            opts['proxy'] = f'socks5://{proxy}'

        # Add cookies if specified
        if cookies_file and Path(cookies_file).exists():
            opts['cookiefile'] = cookies_file

        # Add ffmpeg location
        if self.deps.ffmpeg_path:
            opts['ffmpeg_location'] = str(self.deps.ffmpeg_path.parent)

        # Map GUI options to yt-dlp options
        if download_options.get('audio_only'):
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            opts['format'] = 'bestvideo+bestaudio/best'

        if download_options.get('write_thumbnail'):
            opts['writethumbnail'] = True

        if download_options.get('embed_thumbnail'):
            opts['writethumbnail'] = True
            opts['postprocessors'] = opts.get('postprocessors', [])
            opts['postprocessors'].append({
                'key': 'FFmpegEmbedSubtitle',
            })
            opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
            })

        if download_options.get('write_subs'):
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = ['en']

        if download_options.get('write_metadata'):
            opts['writethumbnail'] = True
            opts['writeinfojson'] = True
            opts['writedescription'] = True

        if download_options.get('write_comments'):
            opts['getcomments'] = True
            opts['writeinfojson'] = True

        if download_options.get('split_chapters'):
            opts['split_chapters'] = True

        if download_options.get('sponsorblock'):
            opts['postprocessors'] = opts.get('postprocessors', [])
            opts['postprocessors'].append({
                'key': 'SponsorBlock',
                'categories': ['sponsor', 'intro', 'outro', 'selfpromo',
                             'interaction', 'preview', 'music_offtopic']
            })
            opts['postprocessors'].append({
                'key': 'ModifyChapters',
                'remove_sponsor_segments': ['sponsor'],
            })

        return opts

    def check_dependencies(self) -> tuple[bool, str]:
        """
        Check if required dependencies are available

        Returns:
            Tuple of (success, message)
        """
        missing = []

        if not self.deps.ytdlp_available():
            missing.append("yt-dlp")

        if not self.deps.ffmpeg_available():
            missing.append("ffmpeg")

        if missing:
            return False, f"Missing dependencies: {', '.join(missing)}"

        return True, "All dependencies available"