"""
Threading utilities for running tasks off the main thread.
"""
import subprocess
import signal
import sys
from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """Signals for worker threads."""
    progress = Signal(str)
    finished = Signal(bool, str)  # success, message
    error = Signal(str)


class DownloadWorker(QRunnable):
    """Worker for running downloads in a separate thread."""

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.signals = WorkerSignals()
        self.process = None
        self._is_running = True

    @Slot()
    def run(self):
        """Execute the download command."""
        try:
            # Start the subprocess
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Read output line by line
            for line in self.process.stdout:
                if not self._is_running:
                    break
                line = line.strip()
                if line:
                    self.signals.progress.emit(line)

            # Wait for process to complete
            return_code = self.process.wait()

            if not self._is_running:
                self.signals.finished.emit(False, "Download stopped by user")
            elif return_code == 0:
                art = r"""
        _
       /(|
      (  :
     __\  \  _____
   (____)  `|
  (____)|   |         This appears to
   (____).__|         be a done deal !
    (___)__.|_____
                    """
                # self.signals.finished.emit(True, "Download completed successfully!")
                self.signals.finished.emit(True, art)
            else:
                self.signals.finished.emit(False, f"Download failed with code {return_code}")

        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.process = None

    def stop(self):
        """Stop the download process."""
        self._is_running = False
        if self.process:
            # Terminate the process and all child processes
            if sys.platform == "win32":
                # On Windows, use taskkill to kill process tree
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                    capture_output=True
                )
            else:
                # On Unix, send SIGTERM to process group
                try:
                    self.process.send_signal(signal.SIGTERM)
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()