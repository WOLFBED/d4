"""
Main Window GUI - Primary user interface
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtGui import QMovie


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, app_core):
        """
        Initialize main window

        Args:
            app_core: AppCore instance
        """
        super().__init__()
        self.core = app_core
        self.thread_pool = QThreadPool.globalInstance()

        # Window setup
        self.setWindowTitle("Video Downloader")
        self.setMinimumSize(700, 650)

        # Check dependencies on startup
        self._check_dependencies()

        # Load saved settings
        self.settings = self.core.get_settings()

        # Setup UI
        self._setup_ui()

        # Load persistent settings into UI
        self._load_persistent_settings()

    def _setup_ui(self):
        """Setup the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === Input Fields Section ===
        input_group = QGroupBox("Input")
        input_layout = QGridLayout()

        # URL or Batch File
        input_layout.addWidget(QLabel("URL or Batch File:"), 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL or path to batch file...")
        input_layout.addWidget(self.url_input, 0, 1)
        self.browse_batch_btn = QPushButton("Browse...")
        self.browse_batch_btn.clicked.connect(self._browse_batch_file)
        input_layout.addWidget(self.browse_batch_btn, 0, 2)

        # Output Location
        input_layout.addWidget(QLabel("Output Location:"), 1, 0)
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Select download location...")
        self.output_input.textChanged.connect(self._save_output_path)
        input_layout.addWidget(self.output_input, 1, 1)
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self._browse_output_folder)
        input_layout.addWidget(self.browse_output_btn, 1, 2)

        # Proxy
        input_layout.addWidget(QLabel("SOCKS5 Proxy:"), 2, 0)
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("e.g., 127.0.0.1:1080 (optional)")
        self.proxy_input.textChanged.connect(self._save_proxy)
        input_layout.addWidget(self.proxy_input, 2, 1, 1, 2)

        # Cookies File
        input_layout.addWidget(QLabel("Cookies File:"), 3, 0)
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("Path to cookies file (optional)")
        self.cookies_input.textChanged.connect(self._save_cookies)
        input_layout.addWidget(self.cookies_input, 3, 1)
        self.browse_cookies_btn = QPushButton("Browse...")
        self.browse_cookies_btn.clicked.connect(self._browse_cookies_file)
        input_layout.addWidget(self.browse_cookies_btn, 3, 2)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # === Download Options Section ===
        options_group = QGroupBox("Download Options")
        options_layout = QGridLayout()

        self.option_audio_only = QCheckBox("Audio Only")
        self.option_write_thumbnail = QCheckBox("Write Thumbnail")
        self.option_embed_thumbnail = QCheckBox("Embed Thumbnail")
        self.option_write_metadata = QCheckBox("Write Metadata")
        self.option_write_subs = QCheckBox("Write Subtitles")
        self.option_write_comments = QCheckBox("Write Comments")
        self.option_split_chapters = QCheckBox("Split Chapters")
        self.option_sponsorblock = QCheckBox("Use SponsorBlock")

        # Add checkboxes to layout (2 columns)
        options_layout.addWidget(self.option_audio_only, 0, 0)
        options_layout.addWidget(self.option_write_thumbnail, 0, 1)
        options_layout.addWidget(self.option_embed_thumbnail, 1, 0)
        options_layout.addWidget(self.option_write_metadata, 1, 1)
        options_layout.addWidget(self.option_write_subs, 2, 0)
        options_layout.addWidget(self.option_write_comments, 2, 1)
        options_layout.addWidget(self.option_split_chapters, 3, 0)
        options_layout.addWidget(self.option_sponsorblock, 3, 1)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # === Progress Section ===
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        progress_layout.addWidget(self.status_text)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # === Action Buttons ===
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self._start_download)
        self.download_btn.setMinimumHeight(40)
        button_layout.addWidget(self.download_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_url)
        button_layout.addWidget(self.clear_btn)

        main_layout.addLayout(button_layout)

        # Store all input widgets for easy enable/disable
        self.input_widgets = [
            self.url_input, self.browse_batch_btn,
            self.output_input, self.browse_output_btn,
            self.proxy_input,
            self.cookies_input, self.browse_cookies_btn,
            self.option_audio_only, self.option_write_thumbnail,
            self.option_embed_thumbnail, self.option_write_metadata,
            self.option_write_subs, self.option_write_comments,
            self.option_split_chapters, self.option_sponsorblock,
            self.download_btn, self.clear_btn
        ]

    def _check_dependencies(self):
        """Check if required dependencies are available"""
        success, message = self.core.check_dependencies()
        if not success:
            QMessageBox.warning(
                self,
                "Missing Dependencies",
                f"{message}\n\nPlease install the required dependencies:\n"
                "- yt-dlp: pip install yt-dlp\n"
                "- ffmpeg: Install from your package manager or https://ffmpeg.org"
            )

    def _load_persistent_settings(self):
        """Load persistent settings into UI"""
        self.output_input.setText(self.settings.get('output_path', ''))
        self.proxy_input.setText(self.settings.get('proxy', ''))
        self.cookies_input.setText(self.settings.get('cookies_file', ''))

    def _save_output_path(self):
        """Save output path to persistent storage"""
        self.core.save_persistent_settings(output_path=self.output_input.text())

    def _save_proxy(self):
        """Save proxy to persistent storage"""
        self.core.save_persistent_settings(proxy=self.proxy_input.text())

    def _save_cookies(self):
        """Save cookies file to persistent storage"""
        self.core.save_persistent_settings(cookies_file=self.cookies_input.text())

    def _browse_batch_file(self):
        """Browse for batch file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Batch File",
            str(Path.home()),
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.url_input.setText(file_path)

    def _browse_output_folder(self):
        """Browse for output folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_input.text() or str(Path.home())
        )
        if folder_path:
            self.output_input.setText(folder_path)

    def _browse_cookies_file(self):
        """Browse for cookies file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            str(Path.home()),
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookies_input.setText(file_path)

    def _clear_url(self):
        """Clear the URL input field"""
        self.url_input.clear()
        self.status_text.clear()

    def _get_download_options(self) -> dict:
        """Get current download options from checkboxes"""
        return {
            'audio_only': self.option_audio_only.isChecked(),
            'write_thumbnail': self.option_write_thumbnail.isChecked(),
            'embed_thumbnail': self.option_embed_thumbnail.isChecked(),
            'write_metadata': self.option_write_metadata.isChecked(),
            'write_subs': self.option_write_subs.isChecked(),
            'write_comments': self.option_write_comments.isChecked(),
            'split_chapters': self.option_split_chapters.isChecked(),
            'sponsorblock': self.option_sponsorblock.isChecked(),
        }

    def _set_ui_enabled(self, enabled: bool):
        """Enable or disable all input widgets"""
        for widget in self.input_widgets:
            widget.setEnabled(enabled)

    def _start_download(self):
        """Start the download process"""
        # Validate inputs
        url_or_batch = self.url_input.text().strip()
        if not url_or_batch:
            QMessageBox.warning(self, "Input Required", "Please enter a URL or batch file path")
            return

        output_path = self.output_input.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Input Required", "Please select an output location")
            return

        # Create output directory if it doesn't exist
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Disable UI
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_text.clear()
        self.status_text.append("Starting download...\n")

        # Get download options
        download_options = self._get_download_options()

        # Start download in background thread
        worker = self.core.start_download(
            url_or_batch=url_or_batch,
            output_path=output_path,
            download_options=download_options,
            proxy=self.proxy_input.text().strip(),
            cookies_file=self.cookies_input.text().strip(),
            progress_callback=self._on_progress,
            finished_callback=self._on_finished
        )

        # Connect error signal
        worker.signals.error.connect(self._on_error)

        # Start the worker
        self.thread_pool.start(worker)

    @Slot(dict)
    def _on_progress(self, progress_info: dict):
        """Handle progress updates"""
        status = progress_info.get('status', '')

        if status == 'downloading':
            filename = Path(progress_info.get('filename', 'Unknown')).name
            downloaded = progress_info.get('downloaded_bytes', 0)
            total = progress_info.get('total_bytes', 0)

            if total > 0:
                percent = (downloaded / total) * 100
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(int(percent))

                # Format sizes
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)

                self.status_text.append(
                    f"Downloading: {filename} - {downloaded_mb:.1f}MB / {total_mb:.1f}MB ({percent:.1f}%)"
                )
            else:
                self.status_text.append(f"Downloading: {filename}...")

        elif status == 'finished':
            filename = Path(progress_info.get('filename', 'Unknown')).name
            self.status_text.append(f"Finished: {filename}\n")

    @Slot(bool, str)
    def _on_finished(self, success: bool, message: str):
        """Handle download completion"""
        # Re-enable UI
        self._set_ui_enabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_text.append(f"\n✓ {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_text.append(f"\n✗ {message}")
            QMessageBox.critical(self, "Error", message)

    @Slot(tuple)
    def _on_error(self, error_info: tuple):
        """Handle errors from worker thread"""
        exctype, value, traceback_str = error_info
        self.status_text.append(f"\n✗ Error: {value}\n")
        print(f"Error in worker thread:\n{traceback_str}")