"""
Main GUI window for the d4 video downloader.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QTextEdit, QFileDialog, QGroupBox, QMessageBox,
    QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QTextEdit, QFileDialog, QGroupBox, QMessageBox,
    QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFontDatabase, QFont


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, app_core):
        super().__init__()
        self.app_core = app_core
        self.is_downloading = False

        # Connect core signals
        self.app_core.download_started.connect(self._on_download_started)
        self.app_core.download_progress.connect(self._on_download_progress)
        self.app_core.download_completed.connect(self._on_download_completed)
        self.app_core.dependency_update_progress.connect(self._on_dependency_update)

        self._setup_ui()
        self._load_settings()

        # Check dependencies on startup
        QTimer.singleShot(100, self._check_dependencies)

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("dealer")
        self.setMinimumSize(800, 700)

        # Try to load icon
        icon_path = Path(__file__).parent.parent.parent.parent / "data" / "icons" / "d4.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # URL/Batch file input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL / Batch File:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL or path to batch file...")
        url_layout.addWidget(self.url_input, stretch=1)

        self.browse_batch_btn = QPushButton("Browse")
        self.browse_batch_btn.clicked.connect(self._browse_batch_file)
        url_layout.addWidget(self.browse_batch_btn)

        main_layout.addLayout(url_layout)

        # Output path
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Path:"))
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Download location...")
        output_layout.addWidget(self.output_input, stretch=1)

        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_btn)

        main_layout.addLayout(output_layout)

        # Proxy
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("SOCKS5 Proxy:"))
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("e.g., 127.0.0.1:1080 (optional)")
        proxy_layout.addWidget(self.proxy_input, stretch=1)
        main_layout.addLayout(proxy_layout)

        # Cookies file
        cookies_layout = QHBoxLayout()
        cookies_layout.addWidget(QLabel("Cookies File:"))
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("Path to cookies file (optional)")
        cookies_layout.addWidget(self.cookies_input, stretch=1)

        self.browse_cookies_btn = QPushButton("Browse")
        self.browse_cookies_btn.clicked.connect(self._browse_cookies)
        cookies_layout.addWidget(self.browse_cookies_btn)

        main_layout.addLayout(cookies_layout)

        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout()

        # First row of options
        row1 = QHBoxLayout()
        self.write_thumbnail_cb = QCheckBox("Write Thumbnail")
        self.embed_thumbnail_cb = QCheckBox("Embed Thumbnail")
        self.write_comments_cb = QCheckBox("Write Comments")
        self.write_metadata_cb = QCheckBox("Write Metadata")
        row1.addWidget(self.write_thumbnail_cb)
        row1.addWidget(self.embed_thumbnail_cb)
        row1.addWidget(self.write_comments_cb)
        row1.addWidget(self.write_metadata_cb)
        row1.addStretch()
        options_layout.addLayout(row1)

        # Second row of options
        row2 = QHBoxLayout()
        self.write_subs_cb = QCheckBox("Write Subtitles")
        self.split_chapters_cb = QCheckBox("Split Chapters")
        self.use_sponsorblock_cb = QCheckBox("Use SponsorBlock")
        self.audio_only_cb = QCheckBox("Audio Only")
        row2.addWidget(self.write_subs_cb)
        row2.addWidget(self.split_chapters_cb)
        row2.addWidget(self.use_sponsorblock_cb)
        row2.addWidget(self.audio_only_cb)
        row2.addStretch()
        options_layout.addLayout(row2)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Progress area
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(200)
        progress_layout.addWidget(self.progress_text)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("Download")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.clicked.connect(self._start_download)
        button_layout.addWidget(self.download_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.clicked.connect(self._stop_download)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear_url)
        button_layout.addWidget(self.clear_btn)

        self.update_deps_btn = QPushButton("Update Dependencies")
        self.update_deps_btn.setMinimumHeight(40)
        self.update_deps_btn.clicked.connect(self._update_dependencies)
        button_layout.addWidget(self.update_deps_btn)

        main_layout.addLayout(button_layout)

        # Apply custom font to progress output box
        self._setup_progress_font()

    def _setup_progress_font(self):
        """Load and apply Victor Mono font to the progress output box."""
        font_path = "gui/fonts/VictorMono/VictorMono-Light.otf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            # Font could not be loaded; keep default font
            return
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            return
        family = families[0]
        font = QFont(family)
        # You can tweak this size if needed
        font.setPointSize(10)
        self.progress_text.setFont(font)

    def _load_settings(self):
        """Load saved settings into UI."""
        settings = self.app_core.get_settings()

        self.output_input.setText(settings.get('output_path', ''))
        self.proxy_input.setText(settings.get('proxy', ''))
        self.cookies_input.setText(settings.get('cookies_file', ''))
        self.url_input.setText(settings.get('last_url', ''))

        self.write_thumbnail_cb.setChecked(settings.get('write_thumbnail', True))
        self.embed_thumbnail_cb.setChecked(settings.get('embed_thumbnail', True))
        self.write_comments_cb.setChecked(settings.get('write_comments', False))
        self.write_metadata_cb.setChecked(settings.get('write_metadata', True))
        self.write_subs_cb.setChecked(settings.get('write_subs', False))
        self.split_chapters_cb.setChecked(settings.get('split_chapters', False))
        self.use_sponsorblock_cb.setChecked(settings.get('use_sponsorblock', False))
        self.audio_only_cb.setChecked(settings.get('audio_only', False))

    def _save_settings(self):
        """Save current UI state to settings."""
        settings = {
            'output_path': self.output_input.text(),
            'proxy': self.proxy_input.text(),
            'cookies_file': self.cookies_input.text(),
            'last_url': self.url_input.text(),
            'write_thumbnail': self.write_thumbnail_cb.isChecked(),
            'embed_thumbnail': self.embed_thumbnail_cb.isChecked(),
            'write_comments': self.write_comments_cb.isChecked(),
            'write_metadata': self.write_metadata_cb.isChecked(),
            'write_subs': self.write_subs_cb.isChecked(),
            'split_chapters': self.split_chapters_cb.isChecked(),
            'use_sponsorblock': self.use_sponsorblock_cb.isChecked(),
            'audio_only': self.audio_only_cb.isChecked(),
        }
        self.app_core.save_all_settings(settings)

    def _browse_batch_file(self):
        """Open file dialog to select batch file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Batch File",
            str(Path.home()),
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.url_input.setText(file_path)

    def _browse_output(self):
        """Open directory dialog to select output path."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_input.text() or str(Path.home())
        )
        if dir_path:
            self.output_input.setText(dir_path)

    def _browse_cookies(self):
        """Open file dialog to select cookies file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            str(Path.home()),
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookies_input.setText(file_path)

    def _check_dependencies(self):
        """Check if dependencies are available."""
        deps = self.app_core.check_dependencies()
        if not deps['ytdlp']:
            reply = QMessageBox.question(
                self,
                "Missing Dependencies",
                "yt-dlp not found. Would you like to download it now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._update_dependencies()

    def _update_dependencies(self):
        """Update external dependencies."""
        self._disable_ui(True)
        self.progress_text.clear()
        self.progress_text.append("Updating dependencies...")

        # Run update in a separate thread
        from utils.threads import WorkerSignals
        from PySide6.QtCore import QRunnable, QThreadPool

        class UpdateWorker(QRunnable):
            def __init__(self, app_core):
                super().__init__()
                self.app_core = app_core
                self.signals = WorkerSignals()

            def run(self):
                try:
                    success = self.app_core.update_dependencies()
                    self.signals.finished.emit(success, "Update complete" if success else "Update failed")
                except Exception as e:
                    self.signals.error.emit(str(e))

        worker = UpdateWorker(self.app_core)
        worker.signals.finished.connect(self._on_update_finished)
        worker.signals.error.connect(lambda e: self.progress_text.append(f"Error: {e}"))
        QThreadPool.globalInstance().start(worker)

    def _on_update_finished(self, success, message):
        """Handle dependency update completion."""
        self.progress_text.append(message)
        self._disable_ui(False)
        if success:
            QMessageBox.information(self, "Success", "Dependencies updated successfully!")

    def _start_download(self):
        """Start the download process."""
        # Validate inputs
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL or batch file path")
            return

        output_path = self.output_input.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please select an output directory")
            return

        # Create output directory if it doesn't exist
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Save settings
        self._save_settings()

        # Gather options
        options = {
            'proxy': self.proxy_input.text().strip(),
            'cookies_file': self.cookies_input.text().strip(),
            'write_thumbnail': self.write_thumbnail_cb.isChecked(),
            'embed_thumbnail': self.embed_thumbnail_cb.isChecked(),
            'write_comments': self.write_comments_cb.isChecked(),
            'write_metadata': self.write_metadata_cb.isChecked(),
            'write_subs': self.write_subs_cb.isChecked(),
            'split_chapters': self.split_chapters_cb.isChecked(),
            'use_sponsorblock': self.use_sponsorblock_cb.isChecked(),
            'audio_only': self.audio_only_cb.isChecked(),
        }

        # Clear progress
        self.progress_text.clear()

        # Start download
        self.app_core.start_download(url, output_path, options)

    def _stop_download(self):
        """Stop the current download."""
        self.app_core.stop_download()

    def _clear_url(self):
        """Clear the URL input field."""
        self.url_input.clear()
        self.app_core.save_setting('last_url', '')

    def _on_download_started(self):
        """Handle download start."""
        self.is_downloading = True
        self._disable_ui(True)
        self.progress_bar.show()
        self.progress_text.append("Download started...")

    def _on_download_progress(self, message):
        """Handle download progress update."""
        self.progress_text.append(message)
        # Auto-scroll to bottom
        self.progress_text.verticalScrollBar().setValue(
            self.progress_text.verticalScrollBar().maximum()
        )

    def _on_download_completed(self, success, message):
        """Handle download completion."""
        self.is_downloading = False
        self._disable_ui(False)
        self.progress_bar.hide()
        self.progress_text.append(f"\n{message}")

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Download Failed", message)

    def _on_dependency_update(self, message):
        """Handle dependency update progress."""
        self.progress_text.append(message)

    def _disable_ui(self, disabled):
        """Enable or disable UI elements during operations."""
        self.url_input.setEnabled(not disabled)
        self.output_input.setEnabled(not disabled)
        self.proxy_input.setEnabled(not disabled)
        self.cookies_input.setEnabled(not disabled)
        self.browse_batch_btn.setEnabled(not disabled)
        self.browse_output_btn.setEnabled(not disabled)
        self.browse_cookies_btn.setEnabled(not disabled)
        self.write_thumbnail_cb.setEnabled(not disabled)
        self.embed_thumbnail_cb.setEnabled(not disabled)
        self.write_comments_cb.setEnabled(not disabled)
        self.write_metadata_cb.setEnabled(not disabled)
        self.write_subs_cb.setEnabled(not disabled)
        self.split_chapters_cb.setEnabled(not disabled)
        self.use_sponsorblock_cb.setEnabled(not disabled)
        self.audio_only_cb.setEnabled(not disabled)
        self.download_btn.setEnabled(not disabled)
        self.clear_btn.setEnabled(not disabled)
        self.update_deps_btn.setEnabled(not disabled)
        self.stop_btn.setEnabled(disabled)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_downloading:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A download is in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.app_core.stop_download()

        self._save_settings()
        event.accept()