"""
Threading Utilities - Reusable worker classes for background operations
"""
import sys
import traceback
from typing import Callable, Any
from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Signals for worker threads
    Based on patterns from [[4]](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/)
    """
    started = Signal()
    finished = Signal(bool, str)  # success, message
    error = Signal(tuple)  # (exctype, value, traceback_str)
    result = Signal(object)
    progress = Signal(dict)  # progress information


class DownloadWorker(QRunnable):
    """
    Worker for running downloads in background thread
    Uses QRunnable for efficient thread pool management [[4]](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/)
    """

    def __init__(self, downloader, postprocessor, url_or_batch: str,
                 ytdlp_options: dict, download_options: dict):
        """
        Initialize download worker

        Args:
            downloader: VideoDownloader instance
            postprocessor: PostProcessor instance
            url_or_batch: URL or batch file path
            ytdlp_options: yt-dlp options dict
            download_options: GUI download options
        """
        super().__init__()
        self.downloader = downloader
        self.postprocessor = postprocessor
        self.url_or_batch = url_or_batch
        self.ytdlp_options = ytdlp_options
        self.download_options = download_options
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """Execute the download operation"""
        try:
            self.signals.started.emit()

            # Perform download
            success, message = self.downloader.download(
                self.url_or_batch,
                self.ytdlp_options,
                progress_callback=self._progress_callback
            )

            # Emit completion signal
            self.signals.finished.emit(success, message)

            if success:
                self.signals.result.emit(message)

        except Exception:
            # Capture and emit error
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            self.signals.finished.emit(False, f"Error: {value}")

    def _progress_callback(self, progress_info: dict):
        """Forward progress updates to signal"""
        self.signals.progress.emit(progress_info)


class GenericWorker(QRunnable):
    """
    Generic worker for running any function in background
    """

    def __init__(self, fn: Callable, *args, **kwargs):
        """
        Initialize generic worker

        Args:
            fn: Function to execute
            *args: Positional arguments for fn
            **kwargs: Keyword arguments for fn
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """Execute the function"""
        try:
            self.signals.started.emit()

            # Run the function
            result = self.fn(*self.args, **self.kwargs)

            # Emit results
            self.signals.result.emit(result)
            self.signals.finished.emit(True, "Completed successfully")

        except Exception:
            # Capture and emit error
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            self.signals.finished.emit(False, f"Error: {value}")