"""
External executable management.
Handles downloading and updating yt-dlp and aria2.
"""

import os
import platform
import shutil
import stat
import subprocess  # for optional Deno installation
import sys  # for interactive prompt when Deno is missing
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import QObject, Signal


class DependencyManager(QObject):
    """Manages external dependencies (yt-dlp, aria2)."""

    update_progress = Signal(str)

    def __init__(self, external_dir: Path):
        super().__init__()
        self.external_dir = Path(external_dir)
        self.external_dir.mkdir(parents=True, exist_ok=True)
        self.ytdlp_dir = self.external_dir / "yt-dlp"
        self.aria2_dir = self.external_dir / "aria2"
        self.ytdlp_dir.mkdir(exist_ok=True)
        self.aria2_dir.mkdir(exist_ok=True)

    # def check_dependencies(self) -> dict:
    #     """Check if dependencies are available."""
    #     ytdlp_available = self.get_ytdlp_path() is not None
    #     aria2_available = self.get_aria2_path() is not None
    #     deno_path = self.get_deno_path()
    #     deno_available = deno_path is not None
    #     if not deno_available:
    #         self.update_progress.emit(
    #             "Deno is not installed or not found in PATH. "
    #             "Some functionality may be unavailable."
    #         )
    #     return {
    #         "ytdlp": ytdlp_available,
    #         "aria2": aria2_available,
    #         "deno": deno_available,
    #     }

    def check_dependencies(self, install_deno_if_missing: bool = True) -> dict:
        """
        Check if dependencies are available.

        If `install_deno_if_missing` is True and Deno is not found, this will:
          * In non-interactive mode (no TTY): attempt to install Deno automatically.
          * In interactive mode (e.g. running main.py in a terminal): ask the user
            whether to attempt automatic installation, and respect their choice.
        """
        ytdlp_available = self.get_ytdlp_path() is not None
        aria2_available = self.get_aria2_path() is not None

        deno_path = self.get_deno_path()
        deno_available = deno_path is not None

        if not deno_available:
            self.update_progress.emit(
                "Deno is not installed or not found in PATH. "
                "Some functionality may be unavailable."
            )

            if install_deno_if_missing:
                # Interactive prompt only if stdin is a TTY (e.g. running main.py
                # directly in a terminal). Otherwise, proceed without prompting.
                user_wants_install = True
                if sys.stdin is not None and sys.stdin.isatty():
                    try:
                        answer = input(
                            "Deno is missing. Attempt automatic installation now? [Y/n]: "
                        ).strip().lower()
                        user_wants_install = (answer in ("", "y", "yes"))
                    except EOFError:
                        # If input is not available, fall back to auto-install
                        user_wants_install = True

                if user_wants_install:
                    self.update_progress.emit("Attempting to install Deno...")
                    deno_available = self.install_deno_if_missing()
                else:
                    self.update_progress.emit(
                        "Skipping automatic Deno installation at user request."
                    )

        return {
            "ytdlp": ytdlp_available,
            "aria2": aria2_available,
            "deno": deno_available,
        }






    # def check_dependencies(self, install_deno_if_missing: bool = False) -> dict:
    #     """
    #     Check if dependencies are available.
    #
    #     If `install_deno_if_missing` is True and Deno is not found, this will
    #     attempt to install it on supported Linux distributions (Arch, Debian,
    #     Fedora-based) using the system package manager.
    #     """
    #     ytdlp_available = self.get_ytdlp_path() is not None
    #     aria2_available = self.get_aria2_path() is not None
    #
    #     deno_path = self.get_deno_path()
    #     deno_available = deno_path is not None
    #
    #     if not deno_available:
    #         self.update_progress.emit(
    #             "Deno is not installed or not found in PATH. "
    #             "Some functionality may be unavailable."
    #         )
    #         if install_deno_if_missing:
    #             self.update_progress.emit("Attempting to install Deno...")
    #             deno_available = self.install_deno_if_missing()
    #
    #     return {
    #         "ytdlp": ytdlp_available,
    #         "aria2": aria2_available,
    #         "deno": deno_available,
    #     }


    def _get_project_root(self) -> Path:
        """
        Returns the project root directory.

        Adjust this if dependency_manager.py is not directly under the project root.
        For example, if this file is in `src/`, you may want:
            return Path(__file__).resolve().parents[1]
        """
        return Path(__file__).resolve().parent


    def get_ytdlp_path(self) -> Path:
        """Get the path to the latest yt-dlp executable."""
        return self._get_latest_executable(self.ytdlp_dir, 'yt-dlp')

    # def get_aria2_path(self) -> Path:
    #     """Get the path to the latest aria2c executable."""
    #     return self._get_latest_executable(self.aria2_dir, 'aria2c')

    def get_aria2_path(self) -> str | None:
        """
        # NOPE --- Disabling aria2 integration for now (nov 13 2025) ------------
        Determine the path to aria2c on Linux.

        Priority:
        1. Most recent aria2 under external/aria2/[date]/[version]/doc/bash_completion/aria2c
        2. System aria2c available in PATH
        """
        # project_root = self._get_project_root()
        # external_dir = project_root / "external" / "aria2"
        #
        # # 1) Look for local aria2 builds if the external directory exists
        # if external_dir.is_dir():
        #     # Date directories: external/aria2/[date]/
        #     date_dirs = [d for d in external_dir.iterdir() if d.is_dir()]
        #     if date_dirs:
        #         # Sort by directory name (assuming YYYYMMDD or similar increasing format)
        #         date_dirs_sorted = sorted(date_dirs, key=lambda p: p.name)
        #         latest_date_dir = date_dirs_sorted[-1]
        #
        #         # Version directories: external/aria2/[latest_date]/[version]/
        #         version_dirs = [d for d in latest_date_dir.iterdir() if d.is_dir()]
        #         if version_dirs:
        #             version_dirs_sorted = sorted(version_dirs, key=lambda p: p.name)
        #             latest_version_dir = version_dirs_sorted[-1]
        #
        #             candidate = (
        #                     latest_version_dir
        #                     / "doc"
        #                     / "bash_completion"
        #                     / "aria2c"
        #             )
        #             if candidate.is_file() and os.access(candidate, os.X_OK):
        #                 return str(candidate)
        #
        # # 2) Fallback to system aria2c
        # system_path = shutil.which("aria2c")
        # if system_path:
        #     return system_path
        #
        # # 3) Nothing found
        return None




    def _get_latest_executable(self, base_dir: Path, exec_name: str) -> Path:
        """Find the latest version of an executable in version subdirectories."""
        if not base_dir.exists():
            return None
        # Look for version directories
        version_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        if not version_dirs:
            return None
        # Sort by modification time (latest first)
        version_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Find the executable
        for version_dir in version_dirs:
            if platform.system() == "Windows":
                exec_path = version_dir / f"{exec_name}.exe"
            else:
                exec_path = version_dir / exec_name
            if exec_path.exists():
                return exec_path
        return None


    # def get_deno_path(self) -> Path:
    #     """Find the latest version of deno in version subdirectories."""
    #     base_dir = Path.home() / ".deno/bin"
    #     return self._find_latest_executable(base_dir, "deno")

    def get_deno_path(self) -> Path | None:
        """
        Determine the path to the Deno executable.

        Priority:
        1. System `deno` available in PATH
        2. Standard user installation under ~/.deno/bin/deno
        """
        # 1) Check system PATH
        system_path = shutil.which("deno")
        if system_path:
            return Path(system_path)

        # 2) Check typical local installation directory
        home_deno = Path.home() / ".deno" / "bin" / "deno"
        if home_deno.is_file() and os.access(home_deno, os.X_OK):
            return home_deno

        # 3) Nothing found
        return None



    def _detect_linux_family(self) -> str | None:
        """
        Detect Linux distribution family based on /etc/os-release.

        Returns one of: "arch", "debian", "fedora", or None if unknown.
        """
        if platform.system() != "Linux":
            return None

        os_release = Path("/etc/os-release")
        if not os_release.is_file():
            return None

        data: dict[str, str] = {}
        try:
            with os_release.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line or line.startswith("#"):
                        continue
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip().strip('"')
        except Exception:
            return None

        id_like = data.get("ID_LIKE", "").lower()
        distro_id = data.get("ID", "").lower()

        tokens = set((id_like + " " + distro_id).split())
        if any(t in tokens for t in ("arch", "artix", "manjaro")):
            return "arch"
        if any(t in tokens for t in ("debian", "ubuntu", "linuxmint", "pop")):
            return "debian"
        if any(t in tokens for t in ("fedora", "rhel", "centos", "rocky", "alma")):
            return "fedora"

        return None

    def install_deno_if_missing(self) -> bool:
        """
        Install Deno if it is currently missing, for supported systems.

        Currently supported:
          - Arch-based (pacman)
          - Debian-based (apt-get)
          - Fedora-based (dnf)

        Returns True if Deno is available after this call, False otherwise.
        """
        # If Deno is already present, nothing to do
        if self.get_deno_path() is not None:
            self.update_progress.emit("Deno is already installed.")
            return True

        system = platform.system()
        if system != "Linux":
            self.update_progress.emit(
                f"Automatic Deno installation is only supported on Linux. "
                f"Detected platform: {system}"
            )
            return False

        family = self._detect_linux_family()
        if family is None:
            self.update_progress.emit(
                "Could not detect a supported Linux distribution family for Deno installation. "
                "Please install Deno manually from https://deno.land/#installation."
            )
            return False

        if family == "arch":
            cmd = ["sudo", "pacman", "-S", "--noconfirm", "deno"]
        elif family == "debian":
            # Run update + install; if update fails (e.g. no sudo), installation will fail too.
            cmd = ["sudo", "apt-get", "install", "-y", "deno"]
            update_cmd = ["sudo", "apt-get", "update"]
        elif family == "fedora":
            cmd = ["sudo", "dnf", "install", "-y", "deno"]
        else:
            self.update_progress.emit(
                f"Linux family '{family}' is not supported for automatic Deno installation."
            )
            return False

        try:
            if family == "debian":
                self.update_progress.emit("Running: sudo apt-get update")
                subprocess.run(
                    update_cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            self.update_progress.emit(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if result.returncode != 0:
                self.update_progress.emit(
                    "Deno installation command failed. "
                    "You may need to run it manually in a terminal with sufficient privileges."
                )
                # Log stderr if needed for debugging; not emitted to UI here.
                return False

        except FileNotFoundError:
            # sudo or package manager not found
            self.update_progress.emit(
                "Failed to run package manager command for Deno installation. "
                "Ensure `sudo` and the appropriate package manager are installed."
            )
            return False
        except Exception as e:
            self.update_progress.emit(f"Unexpected error while installing Deno: {e}")
            return False

        # Re-check if Deno is now available
        if self.get_deno_path() is not None:
            self.update_progress.emit("Deno installed successfully.")
            return True

        self.update_progress.emit(
            "Deno installation command completed, but Deno was still not found. "
            "Please verify the installation manually."
        )
        return False


    def update_all(self) -> bool:
        """Update all dependencies."""
        ytdlp_success = self.update_ytdlp()
        aria2_success = self.update_aria2()
        return ytdlp_success and aria2_success


    def update_ytdlp(self) -> bool:
        """Download the latest yt-dlp release."""
        try:
            self.update_progress.emit("Checking for latest yt-dlp release...")
            # Get latest release info
            api_url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
            # api_url = "https://github.com/aria2/aria2/releases"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            tag_name = release_data['tag_name']
            self.update_progress.emit(f"Latest yt-dlp version: {tag_name}")
            # Determine the correct asset for the platform
            system = platform.system()
            if system == "Linux":
                asset_name = "yt-dlp"
            elif system == "Windows":
                asset_name = "yt-dlp.exe"
            elif system == "Darwin":  # macOS
                asset_name = "yt-dlp_macos"
            else:
                self.update_progress.emit(f"Unsupported platform: {system}")
                return False
            # Find the download URL
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'] == asset_name:
                    download_url = asset['browser_download_url']
                    break
            if not download_url:
                self.update_progress.emit(f"Could not find {asset_name} in release assets")
                return False
            # Create version directory
            date_str = datetime.now().strftime("%b%d-%Y").lower()
            version_dir = self.ytdlp_dir / date_str
            version_dir.mkdir(parents=True, exist_ok=True)
            # Download the executable
            exec_path = version_dir / "yt-dlp"
            self.update_progress.emit(f"Downloading yt-dlp to {exec_path}...")
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            with open(exec_path, 'wb') as f:
                f.write(response.content)
            # Make executable on Unix-like systems
            if system != "Windows":
                os.chmod(exec_path, os.stat(exec_path).st_mode | stat.S_IEXEC)
            self.update_progress.emit("yt-dlp updated successfully!")
            return True
        except Exception as e:
            self.update_progress.emit(f"Error updating yt-dlp: {e}")
            return False

    def update_aria2(self) -> bool:
        """Download the latest aria2 release and extract the aria2c executable.
        Behaviour:
        - Try to download a platform-appropriate archive.
          * On Linux: typical names like aria2-1.37.0.tar.bz2, aria2-1.37.0.tar.gz, aria2-1.37.0.tar.xz
            that are not clearly Windows/macOS/Android builds.
        - If no suitable asset exists for the current OS:
            - DO NOT fall back to another OS build.
            - Instead:
                1) Try to use an existing aria2 binary under external/aria2
                2) Otherwise, try to use a system-installed aria2c from PATH
        - Returns True if, after this call, there is at least one usable aria2 binary
          (downloaded or existing); otherwise False.
        """
        try:
            def fallback_to_existing() -> bool:
                """Use an existing aria2 binary under external dir or on system PATH."""
                # 1) Check already-downloaded versions under external/aria2
                existing = self.get_aria2_path()
                if existing is not None:
                    self.update_progress.emit(
                        f"No suitable new aria2 asset; using existing binary: {existing}"
                    )
                    return True
                # 2) Check system PATH
                system_aria2 = shutil.which("aria2c")
                if system_aria2:
                    self.update_progress.emit(
                        f"No suitable new aria2 asset; using system-installed aria2: {system_aria2}"
                    )
                    # Note: get_aria2_path() won't see this, but the system binary is usable.
                    return True
                self.update_progress.emit(
                    "No suitable aria2 asset found, and no existing aria2 binary is available"
                )
                return False
            self.update_progress.emit("Checking for latest aria2 release...")
            # Get latest release info
            api_url = "https://api.github.com/repos/aria2/aria2/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            tag_name = release_data["tag_name"]
            self.update_progress.emit(f"Latest aria2 version: {tag_name}")
            system = platform.system()
            assets = release_data.get("assets", [])
            chosen_asset = None
            def lname(a):
                return a["name"].lower()
            def has_archive_ext(a):
                return any(
                    lname(a).endswith(ext)
                    for ext in (".zip", ".tar.xz", ".tar.bz2", ".tar.gz")
                )
            def pick_best_asset(predicate):
                for a in assets:
                    if predicate(a):
                        return a
                return None
            # --- Platform-specific selection only. No cross-OS fallback. ---
            if system == "Windows":
                # Prefer 64-bit Windows first, then any Windows archive
                chosen_asset = (
                        pick_best_asset(
                            lambda a: has_archive_ext(a) and "win-64" in lname(a)
                        )
                        or pick_best_asset(
                    lambda a: has_archive_ext(a) and "win" in lname(a)
                    )
                )
            elif system == "Linux":
                # Typical official linux archives: aria2-<ver>.tar.* without OS markers
                # Avoid anything clearly for other OSes or Android.
                chosen_asset = pick_best_asset(
                    lambda a: has_archive_ext(a)
                              and lname(a).startswith("aria2-")
                              and all(
                        bad not in lname(a)
                        for bad in ("win", "osx", "darwin", "macos", "android")
                    )
                )
            elif system == "Darwin":
                # macOS / OS X builds
                chosen_asset = pick_best_asset(
                    lambda a: has_archive_ext(a)
                              and (
                                      "osx" in lname(a)
                                      or "darwin" in lname(a)
                                      or "macos" in lname(a)
                              )
                )
            else:
                self.update_progress.emit(f"Unsupported platform for aria2: {system}")
                return fallback_to_existing()
            # If nothing suitable for this OS, do NOT fallback to other OS assets.
            if not chosen_asset:
                self.update_progress.emit(
                    f"No suitable aria2 asset found for this platform ({system}) in latest release"
                )
                return fallback_to_existing()
            download_url = chosen_asset["browser_download_url"]
            asset_name = chosen_asset["name"]
            self.update_progress.emit(f"Selected aria2 asset: {asset_name}")
            # Create version directory
            date_str = datetime.now().strftime("%b%d-%Y").lower()
            version_dir = self.aria2_dir / date_str
            version_dir.mkdir(parents=True, exist_ok=True)
            archive_path = version_dir / asset_name
            self.update_progress.emit(f"Downloading aria2 archive to {archive_path}...")
            # Download the archive
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            with open(archive_path, "wb") as f:
                f.write(response.content)
                # Extract aria2c / aria2c.exe from the archive
                exec_candidates = ["aria2c", "aria2c.exe"]
                extracted_exec_path = None
                try:
                    if zipfile.is_zipfile(archive_path):
                        with zipfile.ZipFile(archive_path, "r") as zf:
                            zf.extractall(path=version_dir)
                    elif tarfile.is_tarfile(archive_path):
                        with tarfile.open(archive_path, "r:*") as tf:
                            tf.extractall(path=version_dir)
                    else:
                        self.update_progress.emit(
                            f"Unsupported aria2 asset format: {archive_path.suffix}"
                        )
                        return fallback_to_existing()
                except Exception as e:
                    self.update_progress.emit(f"Error extracting aria2 archive: {e}")
                    return fallback_to_existing()
                # --- Locate aria2c in the extracted tree ---
                try:
                    # 1) Prefer the common location: <version_dir>/doc/bash_completion/aria2c
                    common_path = version_dir / "doc" / "bash_completion" / "aria2c"
                    if common_path.exists() and common_path.is_file():
                        extracted_exec_path = common_path
                    else:
                        # 2) Fallback: search recursively for aria2c / aria2c.exe
                        candidate_paths = [
                            p
                            for p in version_dir.rglob("*")
                            if p.is_file() and p.name in exec_candidates
                        ]
                        if not candidate_paths:
                            self.update_progress.emit(
                                "Extracted aria2 archive but could not find aria2c executable"
                            )
                            return fallback_to_existing()
                        # Prefer binaries under doc/bash_completion if present,
                        # because that's the usual location for this layout.
                        bash_completion_candidates = [
                            p
                            for p in candidate_paths
                            if "doc" in p.parts and "bash_completion" in p.parts
                        ]
                        if bash_completion_candidates:
                            extracted_exec_path = bash_completion_candidates[0]
                        else:
                            # Otherwise, just pick the first candidate
                            extracted_exec_path = candidate_paths[0]
                except Exception as e:
                    self.update_progress.emit(
                        f"Error searching for aria2c executable in extracted files: {e}"
                    )
                    return fallback_to_existing()
                if not extracted_exec_path or not extracted_exec_path.exists():
                    self.update_progress.emit(
                        "Failed to locate aria2c executable after extraction"
                    )
                    return fallback_to_existing()
                # On non‑Windows, ensure it is executable
                if system != "Windows":
                    try:
                        os.chmod(
                            extracted_exec_path,
                            os.stat(extracted_exec_path).st_mode | stat.S_IEXEC,
                        )
                    except Exception as e:
                        self.update_progress.emit(
                            f"Failed to mark aria2c as executable: {e}"
                        )
                        return fallback_to_existing()
                # Explicitly report the final path to the extracted binary
                self.update_progress.emit(
                    f"aria2 updated successfully, binary path: {extracted_exec_path}"
                )
                return True
        except Exception as e:
            self.update_progress.emit(f"Error updating aria2: {e}")
            return False


    # def update_aria2(self) -> bool:
    #     """Download the latest aria2 release."""
    #     try:
    #         self.update_progress.emit("Checking for latest aria2 release...")
    #
    #         # Get latest release info
    #         api_url = "https://api.github.com/repos/aria2/aria2/releases/latest"
    #         response = requests.get(api_url, timeout=10)
    #         response.raise_for_status()
    #         release_data = response.json()
    #
    #         tag_name = release_data['tag_name']
    #         self.update_progress.emit(f"Latest aria2 version: {tag_name}")
    #
    #         # Note: aria2 releases are archives, not single executables
    #         # For simplicity, we'll just check if it exists or create a placeholder
    #         # In production, you'd download and extract the appropriate archive
    #
    #         system = platform.system()
    #         date_str = datetime.now().strftime("%b%d-%Y").lower()
    #         version_dir = self.aria2_dir / date_str
    #         version_dir.mkdir(parents=True, exist_ok=True)
    #
    #         # This is a simplified version - in production you'd download and extract
    #         self.update_progress.emit("aria2 update completed (placeholder)")
    #         return True
    #
    #     except Exception as e:
    #         self.update_progress.emit(f"Error updating aria2: {e}")
    #         return False