"""
Video download logic using yt-dlp.
"""
import subprocess
import signal
import requests
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThreadPool
import math

from utils.threads import DownloadWorker
from .user_agents import UserAgents

from sys import exit, path, argv
from subprocess import run
from time import sleep
from colored import fg, bg, attr  # https://github.com/fatman2021/colored
# import ZyngMain as zyng
import re
import secrets
import json
from rich.console import Console
# from resources import *
import requests
from datetime import datetime
from pathlib import Path
import math
import os, signal, sys, subprocess, time, validators, getpass  # - don't think I need this




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
        self._ua_helper = UserAgents()
        self._ua_data = self._ua_helper.fetch_useragents_json()


    def float_to_int(self, number: float) -> int:
        """
        Converts a float to an integer.
        """
        return int(number)

    def clamp_to_range(self, int_A, int_B, int_C):
        """
        Returns int_A if it's within the range defined by int_B and int_C.
        If int_A is outside the range, it returns either int_B or int_C,
        whichever is closest to int_A.

        Args:
            int_A (int): The value to be clamped.
            int_B (int): The lower bound of the range.
            int_C (int): The upper bound of the range.

        Returns:
            int: Either int_A if it's within the range, or int_B or int_C,
                 whichever is closest to int_A.
        """
        if int_B <= int_A <= int_C:
            return int_A
        elif (int_A - int_B) < (int_C - int_A):
            return int_B
        else:
            return int_C


    def get_aria2c_params(self, avg_download_speed_mbps):
        # Convert download speed from Mbps to KBps
        avg_download_speed_kbps = avg_download_speed_mbps * 1024 / 8

        # Calculate max concurrent downloads
        max_concurrent_downloads = max(1, min(16, math.floor(avg_download_speed_kbps / 1024)))

        # Calculate max connections per server
        max_connections_per_server = max(1, min(16, math.floor(avg_download_speed_kbps / 512)))

        # Calculate min split size and split count
        if avg_download_speed_kbps <= 512:
            min_split_size = 512  # 512 KB
            split_count = 2
        elif avg_download_speed_kbps <= 1024:
            min_split_size = 1024  # 1 MB
            split_count = 3
        else:
            min_split_size = 2048  # 2 MB
            split_count = 5

        # Calculate max peers for BitTorrent
        max_bt_peers = max(10, min(100, math.floor(avg_download_speed_kbps / 50)))

        # Calculate peer speed limit for BitTorrent
        bt_peer_speed_limit_kbps = max(256, min(2048, math.floor(avg_download_speed_kbps / 2)))

        # Calculate disk cache size
        disk_cache_mb = max(8, min(64, math.floor(avg_download_speed_kbps / 256)))

        # Calculate piece length for BitTorrent
        piece_length_kb = self.clamp_to_range(max(128, min(1024, math.floor(avg_download_speed_kbps / 16))), 1048576,
                                         1073741824)

        # Construct aria2c command with calculated parameters
        # aria2c_params = f"aria2c --file-allocation=none --continue=true --max-concurrent-downloads={max_concurrent_downloads} --max-connection-per-server={max_connections_per_server} --min-split-size={min_split_size}K --split={split_count} --bt-max-peers={max_bt_peers} --bt-stop-timeout=0 --bt-request-peer-speed-limit={bt_peer_speed_limit_kbps}K --bt-seed-unverified=true --lowest-speed-limit=0 --max-overall-download-limit={avg_download_speed_kbps} --allow-overwrite=true --auto-file-renaming=false --remote-time=true --summary-interval=0 --console-log-level=warn --disk-cache={disk_cache_mb}M --enable-http-pipelining=true --enable-peer-exchange=true --ftp-reget=true --http-accept-gzip=true --http-no-cache=true --http-pipelining=true --https-pipelining=true --max-resume-failure-tries=0 --metalink-enable-unique-protocol=true --parameterized-uri=true --piece-length={piece_length_kb}K --reuse-uri=true --seed-ratio=1.0"

        # clamp_to_range(float_to_int(piece_length_kb), 1048576, 1073741824)
        # clamp_to_range(float_to_int(piece_length_kb), 1048576, 1073741824)

        # --downloader-args aria2c:"-c --max-tries=0 -k 1M -j 16 --enable-http-pipelining --stream-piece-selector=geom"

        aria2c_params = [
            # "aria2c",
            "--file-allocation=none",
            "--continue=true",
            "--uri-selector=feedback",
            f"--max-concurrent-downloads={self.float_to_int(max_concurrent_downloads)}",
            f"--max-connection-per-server={self.float_to_int(max_connections_per_server)}",
            f"--min-split-size={self.float_to_int(min_split_size)}K",
            f"--split={self.float_to_int(split_count)}",
            # f"--bt-max-peers={self.float_to_int(max_bt_peers)}",
            # "--bt-stop-timeout=0",
            # f"--bt-request-peer-speed-limit={self.float_to_int(bt_peer_speed_limit_kbps)}K",
            # "--bt-seed-unverified=true",
            "--lowest-speed-limit=0",
            "--max-tries=0",
            f"--max-overall-download-limit={self.float_to_int(avg_download_speed_kbps)}",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            "--remote-time=true",
            "--summary-interval=0",
            # "--console-log-level=warn",
            f"--disk-cache={self.float_to_int(disk_cache_mb)}M",
            "--enable-http-pipelining",
            "--stream-piece-selector=geom",
            # "--enable-http-pipelining=true",
            "--enable-peer-exchange=true",
            # "--ftp-reget=true",
            "--http-accept-gzip=true",
            "--http-no-cache=true",
            # "--http-pipelining=true",
            # "--https-pipelining=true",
            "--max-resume-failure-tries=0",
            "--metalink-enable-unique-protocol=true",
            "--parameterized-uri=true",
            f"--piece-length={self.float_to_int(piece_length_kb)}K",
            "--reuse-uri=true",
            # "--seed-ratio=1.0",
        ]
        # return aria2c_params

        # Return a single joined string
        return " ".join(aria2c_params)


    def download(self, url: str):
        # line ~88 in your file, for example:
        ua_string = self._ua_helper.choose_random_user_agent(
            self._ua_data["desktop"],
            self._ua_data["mobile"],
        )
        headers = {
            "User-Agent": ua_string,
            # ... any other headers ...
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()


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
        # cmd.extend(['-o', str(Path(output_path) / '%(title)s.%(ext)s')])
        cmd.extend(['-o', str(Path(output_path) / '%(title)s__%(upload_date)s__%(id)s.%(ext)s')])

        # Allow continuing incomplete downloads
        cmd.extend(['-c'])

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
            cmd.append('--extractor-args')
            cmd.append('youtube:max_comments=333:max_parents=111:max_comment_depth=1')   # dealerChan requirement
        if options.get('write_metadata'):
            cmd.append('--write-info-json')  # dealerChan requirement
            cmd.append('--embed-metadata')
            cmd.append('--write-description')  # dealerChan requirement

        # Subtitle options
        if options.get('write_subs'):
            cmd.append('--write-subs')
            cmd.append('--sub-langs')
            cmd.append('en.*')
            cmd.append('--write-auto-subs')  # dealerChan requirement
            # cmd.append('--embed-subs')  # Bad idea

        # Timer Optimizations   # dealerChan requirement
        cmd.append('--sleep-interval')
        cmd.append('7')
        cmd.append('--max-sleep-interval')
        cmd.append('12')
        cmd.append('--sleep-subtitles')
        cmd.append('5')

        # Nevermind, just keep going
        cmd.append('--ignore-errors')

        # Compats
        cmd.append('--progress')
        cmd.append('--compat-options')
        cmd.append('no-external-downloader-progress')

        # Chapter options
        if options.get('split_chapters'):
            cmd.append('--split-chapters')

        # SponsorBlock
        if options.get('use_sponsorblock'):
            cmd.append('--sponsorblock-remove')
            # cmd.append('--sponsorblock-mark')
            cmd.append('all')

        # Download archive
        cmd.append('--download-archive')
        cmd.append(f'{output_path}/prevDl')

        # Proxy
        if options.get('proxy'):
            cmd.extend(['--proxy', f"socks5://{options['proxy']}"])

        # Cookies
        if options.get('cookies_file'):
            cmd.extend(['--cookies', options['cookies_file']])

        print(f"aria2c path: {self.aria2_path}")
        print(f"self._ua_data: {self._ua_data}")

        ranua = self._ua_helper.choose_random_user_agent(
            self._ua_data["desktop"],
            self._ua_data["mobile"],
        )

        print(f"ranua: {ranua}")

        # aria2 integration
        if self.aria2_path and self.aria2_path.exists():
            cmd.extend(['--downloader', str(self.aria2_path)])
            # cmd.extend(['--external-downloader', str(self.aria2_path)])
            # cmd.extend(['--downloader-args', f'aria2c:c --continue=true --file-allocation=falloc --user-agent="{self.ua_string}"'])
            cmd.extend([
                '--downloader-args',
                f'aria2c:{self.get_aria2c_params(50000)} --user-agent="{ranua}"'
            ])
            # cmd.extend(['--external-downloader-args', 'aria2c:"-x 16 -s 16 -k 1M"'])

        # Progress output
        cmd.append('--newline')
        cmd.append('--progress')

        # Check if URL is a batch file
        url_path = Path(url)
        if url_path.exists() and url_path.is_file():
            cmd.extend(['--batch-file', str(url_path)])
        else:
            cmd.append(url)

        print(f"Running command: {' '.join(cmd)}")

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