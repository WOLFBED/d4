#!/usr/bin/env python3
"""
enhanced_python_installer_v3
Modified to:
 - Fetch latest GitHub release instead of git clone
 - Extract archive and continue with original workflow
 - zyngInstaller should exclude installing programs from repos, this should be in the install.sh script
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile
import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def eprint(*a, **k):
    """Print messages to standard error."""
    print(*a, file=sys.stderr, **k)


def run(cmd, check=True, capture=False, env=None):
    """
    Run a subprocess command with optional output capture.

    Parameters
    ----------
    cmd:
        Command to execute, either as a list/tuple of arguments or a shell-like string.
    check:
        If True, raise CalledProcessError on non-zero exit code.
    capture:
        If True, capture stdout and stderr and return them in the CompletedProcess.
    env:
        Optional environment dict to pass to subprocess.run().

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object.
    """
    if isinstance(cmd, (list, tuple)):
        pass
    else:
        cmd = cmd.split()
    return subprocess.run(
        cmd,
        check=check,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        env=env
    )


def ensure_dir(p: Path, exist_ok=True):
    """
    Ensure that a directory exists, creating parent directories as needed.

    Parameters
    ----------
    p:
        Path of the directory to create.
    exist_ok:
        Passed through to Path.mkdir(); if False, raising on existing directory.

    Returns
    -------
    Path
        The expanded, ensured directory path.
    """
    p = Path(p).expanduser()
    p.mkdir(parents=True, exist_ok=exist_ok)
    return p


def sha256sum(path: Path):
    """
    Compute the SHA256 checksum of a file.

    Parameters
    ----------
    path:
        Path to the file to hash.

    Returns
    -------
    str
        Hex-encoded SHA256 digest of the file contents.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# -------------------------------------------------------------
# Installer Class
# -------------------------------------------------------------
class Installer:
    """High-level orchestrator for installing a Python application from a release archive."""

    def __init__(self, cfg_path: Path, args):
        """
        Initialize the installer from a TOML configuration file and CLI arguments.

        Parameters
        ----------
        cfg_path:
            Path to the TOML configuration file.
        args:
            Parsed argparse.Namespace containing CLI options.
        """
        self.args = args
        self.cfg_path = cfg_path.expanduser()
        self.load_config()
        self.tmpdir = Path(tempfile.mkdtemp(prefix="installer_"))
        self.appname = self.config["name"]
        self.version = self.config["version"]
        self.install_root = Path(
            self.config.get("default_install_root", "~/.local/share/" + self.appname + "-installs")
        ).expanduser()

        if args.install_root:
            self.install_root = Path(args.install_root).expanduser()

        ensure_dir(self.install_root)
        self.versioned_dir = self.install_root / f"{self.appname}-{self.version}"
        self.current_symlink = self.install_root / f"{self.appname}-current"
        self.archives_dir = self.install_root / "archives"
        ensure_dir(self.archives_dir)

        self.local_bin = Path("~/.local/bin").expanduser()
        ensure_dir(self.local_bin)

        self.source_root = None
        self.vpython = sys.executable

    def load_config(self):
        """
        Load and validate the installer configuration from disk.

        Raises
        ------
        SystemExit
            If the configuration file is missing or required keys are absent.
        """
        if not self.cfg_path.exists():
            raise SystemExit(f"Config file not found: {self.cfg_path}")
        with open(self.cfg_path, "rb") as f:
            self.config = tomllib.load(f)

        for key in ("name", "version", "source"):
            if key not in self.config:
                raise SystemExit(f"Missing required config key: {key}")

        self.source_cfg = self.config["source"]

    # -------------------------------------------------------------
    # Fetch Latest GitHub Release (NEW)
    # -------------------------------------------------------------
    def fetch_latest_github_release(self, repo: str) -> Path:
        """
        Download the newest GitHub release archive for a repository.

        Parameters
        ----------
        repo:
            Repository in the form ``'OWNER/REPO'``.

        Returns
        -------
        Path
            Local filesystem path to the downloaded archive.

        Raises
        ------
        SystemExit
            If the release has no assets or no suitable archive asset.
        """
        api = f"https://api.github.com/repos/{repo}/releases/latest"
        print(f"[+] querying GitHub releases: {api}")

        req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req) as r:
            meta = json.load(r)

        assets = meta.get("assets", [])
        if not assets:
            raise SystemExit("No assets found in the latest GitHub release.")

        # Choose an archive asset
        archive = None
        for a in assets:
            name = a["name"].lower()
            if name.endswith((".zip", ".tar.gz", ".tgz", ".tar.xz")):
                archive = a
                break

        if not archive:
            raise SystemExit("No installable archive asset found in the latest release.")

        url = archive["browser_download_url"]
        dest = self.tmpdir / archive["name"]

        print(f"[+] downloading release asset: {url}")
        urllib.request.urlretrieve(url, dest)

        print(f"[+] downloaded to: {dest}")
        return dest

    # -------------------------------------------------------------
    # Required App Logic (no package manager usage)
    # -------------------------------------------------------------
    def _get_required_apps(self) -> list[str]:
        """
        Resolve the list of required external applications from the config.

        Returns
        -------
        list[str]
            List of application names that must be present on PATH.
        """
        section = self.config.get("required_apps") or {}
        if not isinstance(section, dict):
            return []
        apps = section.get("apps") or section.get("name") or []
        if isinstance(apps, str):
            apps = [apps]
        return [a for a in apps if isinstance(a, str) and a.strip()]

    def ensure_required_apps(self):
        """
        Check that required external apps are present on PATH.

        NOTE: This does not install anything via a package manager.
        Any installation of system packages should be handled by
        install.sh or similar scripts.

        Raises
        ------
        SystemExit
            If required applications are missing.
        """
        required = self._get_required_apps()
        if not required:
            return

        print("[+] Checking required applications …")
        missing = [a for a in required if not shutil.which(a)]

        if not missing:
            print("  - all required applications are present")
            return

        eprint("[!] Missing required applications:")
        for app in missing:
            eprint(f"    - {app}")
        eprint("[!] Please install the missing applications using your system package manager")
        eprint("    (typically from install.sh) and re-run the installer.")
        raise SystemExit("Unmet required applications.")

    # -------------------------------------------------------------
    # Source Preparation (MODIFIED)
    # -------------------------------------------------------------
    def prepare_source(self):
        """
        Fetch and unpack the application source according to the configuration.

        For ``type="git"`` this downloads the latest GitHub release archive.
        For ``type="url"`` or ``"archive"`` this downloads or copies the given location,
        verifies the checksum if provided, and extracts the archive.

        Returns
        -------
        Path
            Path to the extracted source root directory.

        Raises
        ------
        SystemExit
            If the source type is unknown or checksum verification fails.
        """
        stype = self.source_cfg.get("type", "git")
        loc = self.source_cfg["location"]

        print(f"[+] preparing source (type={stype})")

        if stype == "git":
            # Now: fetch latest GitHub release instead of git clone
            archive = self.fetch_latest_github_release(loc)
            return self.extract_archive(archive)

        elif stype in ("url", "archive"):
            path = self.download_or_copy(loc)
            expected_sha = self.source_cfg.get("sha256")
            if expected_sha:
                print("  - verifying SHA256 …")
                actual = sha256sum(path)
                if actual.lower() != expected_sha.lower():
                    raise SystemExit("SHA256 mismatch")
                print("  - checksum OK")
            return self.extract_archive(path)

        else:
            raise SystemExit(f"Unknown source type: {stype}")

    def download_or_copy(self, loc):
        """
        Download a remote file or copy a local file into the temporary directory.

        Parameters
        ----------
        loc:
            URL or local filesystem path to the archive.

        Returns
        -------
        Path
            Destination path of the downloaded or copied file.

        Raises
        ------
        SystemExit
            If a local source path does not exist.
        """
        dest = self.tmpdir / "download"
        if loc.startswith(("http://", "https://")):
            print(f"  - downloading {loc}")
            urllib.request.urlretrieve(loc, dest)
        else:
            src = Path(loc).expanduser()
            if not src.exists():
                raise SystemExit(f"Source not found: {src}")
            shutil.copy2(src, dest)
        return dest

    # -------------------------------------------------------------
    # Archive Extraction (unchanged)
    # -------------------------------------------------------------
    def extract_archive(self, pathobj):
        """
        Extract a supported archive into the temporary source directory.

        Parameters
        ----------
        pathobj:
            Path-like object pointing to the archive file.

        Returns
        -------
        Path
            The resolved source root directory inside the extraction directory.

        Raises
        ------
        SystemExit
            If the archive format is unsupported or the app structure is invalid.
        """
        path = Path(pathobj)
        print(f"  - extracting {path}")

        extract_dir = self.tmpdir / "src"
        ensure_dir(extract_dir)

        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, "r") as z:
                z.extractall(path=extract_dir)
        elif tarfile.is_tarfile(path):
            with tarfile.open(path, "r:*") as t:
                t.extractall(path=extract_dir)
        else:
            raise SystemExit(f"Unknown archive format: {path}")

        entries = [p for p in extract_dir.iterdir() if p.name != "__MACOSX"]
        root = entries[0] if len(entries) == 1 and entries[0].is_dir() else extract_dir

        self.validate_app_structure(root)
        self.source_root = root

        print(f"  - source root: {root}")
        return root

    def validate_app_structure(self, root: Path):
        """
        Validate that the extracted source tree has the expected layout.

        Parameters
        ----------
        root:
            Path to the extracted source root directory.

        Raises
        ------
        SystemExit
            If required directories are missing.
        """
        for r in ("src", "data"):
            if not (root / r).exists():
                raise SystemExit(f"Invalid app structure: missing {r}/")

        if not (root / "requirements.txt").exists():
            eprint("Warning: no requirements.txt found")

    # -------------------------------------------------------------
    # Installation (unchanged)
    # -------------------------------------------------------------
    def atomic_move_into_place(self):
        """
        Move the prepared source tree into the versioned install directory.

        Existing versions are archived into the ``archives`` directory and the
        ``-current`` symlink is updated to point to the new version.
        """
        if self.versioned_dir.exists():
            ts = time.strftime("%Y%m%d%H%M%S")
            archive_target = self.archives_dir / f"{self.appname}-{self.version}-{ts}"
            print(f"[!] existing version found; archiving → {archive_target}")
            shutil.move(str(self.versioned_dir), str(archive_target))

        print(f"[+] installing to {self.versioned_dir}")
        shutil.move(str(self.source_root), str(self.versioned_dir))

        if self.current_symlink.exists() or self.current_symlink.is_symlink():
            self.current_symlink.unlink(missing_ok=True)

        self.current_symlink.symlink_to(
            self.versioned_dir, target_is_directory=True
        )

    def setup_venv_and_requirements(self):
        """
        Optionally create a virtual environment and install Python dependencies.

        Returns
        -------
        Path | None
            Path to the created virtual environment, or None if disabled.
        """
        if not self.config.get("setup_venv", True):
            return None

        venv_path = self.versioned_dir / "venv"
        print(f"[+] creating venv: {venv_path}")
        run([self.vpython, "-m", "venv", str(venv_path)])

        req = self.versioned_dir / "requirements.txt"
        if req.exists():
            pip = venv_path / "bin" / "pip"
            print("[+] installing requirements …")
            run([pip, "install", "--upgrade", "pip"])
            run([pip, "install", "-r", str(req)])

        return venv_path

    def install_fonts(self):
        """
        Optionally install bundled fonts into the user's font directory.

        Fonts are copied under ``~/.local/share/fonts/<appname>-<version>`` and
        the font cache is refreshed.
        """
        fonts_dir = self.versioned_dir / "data" / "fonts"
        if not fonts_dir.exists():
            return
        if not self.prompt_yesno("Install included fonts to user font dir?", True):
            return

        target = Path("~/.local/share/fonts").expanduser() / f"{self.appname}-{self.version}"
        ensure_dir(target)

        print(f"[+] copying fonts → {target}")
        for root, _, files in os.walk(fonts_dir):
            for f in files:
                src = Path(root) / f
                rel = Path(root).relative_to(fonts_dir)
                dst = target / rel
                ensure_dir(dst)
                shutil.copy2(src, dst / f)

        run(["fc-cache", "-f", str(target)], check=False)

    def create_launcher(self, venv_path=None):
        """
        Create a launcher script in ``~/.local/bin`` for the installed application.

        Parameters
        ----------
        venv_path:
            Optional path to a virtual environment whose activation should be
            sourced before running the app.

        Returns
        -------
        Path
            Path to the created launcher script.
        """
        entry = self.config.get("entrypoint", "src/app/zyngInstaller.py")
        launcher = self.local_bin / self.appname

        with open(launcher, "w") as f:
            f.write("#!/usr/bin/env bash\nset -euo pipefail\n")
            f.write(f"APP_DIR=\"{self.current_symlink}\"\n")
            if venv_path:
                f.write("source \"$APP_DIR/venv/bin/activate\"\n")
            f.write("cd \"$APP_DIR\"\n")
            f.write(f"exec python3 {entry} \"$@\"\n")

        launcher.chmod(0o755)
        print(f"[+] launcher created: {launcher}")
        return launcher

    def create_desktop_entry(self, launcher):
        """
        Create a ``.desktop`` entry for the application in the user's applications directory.

        Parameters
        ----------
        launcher:
            Path to the launcher script that should be invoked by the desktop entry.
        """
        desktop_dir = Path("~/.local/share/applications").expanduser()
        ensure_dir(desktop_dir)

        desktop = desktop_dir / f"{self.appname}-{self.version}.desktop"

        icon_path = self.config.get("icon", "")
        if icon_path:
            icon_abs = self.versioned_dir / icon_path
            if not icon_abs.exists():
                eprint(f"[!] icon not found: {icon_abs}")
                icon_abs = ""
        else:
            icon_abs = ""

        with open(desktop, "w") as f:
            f.write("[Desktop Entry]\n")
            f.write("Type=Application\n")
            f.write(f"Name={self.appname}\n")
            f.write(f"Exec={launcher} %U\n")
            f.write(f"Icon={icon_abs}\n")
            f.write("Terminal=false\n")
            f.write("Categories=Internet;Utility;Application;\n")

        desktop.chmod(0o644)
        print(f"[+] desktop entry: {desktop}")

    # -------------------------------------------------------------
    # Cleanup & Rollback (unchanged)
    # -------------------------------------------------------------
    def clean_old_archives(self, keep):
        """
        Remove old archived versions, keeping only the newest ``keep`` entries.

        Parameters
        ----------
        keep:
            Number of archives to retain.
        """
        entries = sorted(self.archives_dir.glob(f"{self.appname}-*"),
                         key=os.path.getmtime,
                         reverse=True)

        if len(entries) <= keep:
            return

        for old in entries[keep:]:
            print(f"[-] removing old archive: {old}")
            shutil.rmtree(old, ignore_errors=True)

    def rollback(self):
        print("[+] Rollback mode active")

        archives = sorted(
            self.archives_dir.glob(f"{self.appname}-*"),
            key=os.path.getmtime,
            reverse=True
        )

        if not archives:
            raise SystemExit("No archived versions exist.")

        print("Available versions:")
        for i, arch in enumerate(archives):
            print(f"  [{i}] {arch.name}")

        choice = int(input("Select index: ").strip())
        if choice < 0 or choice >= len(archives):
            raise SystemExit("Invalid selection.")

        target = archives[choice]
        print(f"[+] Rolling back to {target}")

        if self.current_symlink.exists() and self.current_symlink.is_symlink():
            curr = self.current_symlink.resolve()
            ts = time.strftime("%Y%m%d%H%M%S")
            failed = self.archives_dir / f"{curr.name}-failed-{ts}"
            shutil.move(str(curr), str(failed))

        if self.current_symlink.exists():
            self.current_symlink.unlink(missing_ok=True)

        self.current_symlink.symlink_to(target, target_is_directory=True)

        print("[+] Rollback complete.")

    # -------------------------------------------------------------
    # Installation Orchestration
    # -------------------------------------------------------------
    def install(self):
        """
        Perform a full installation run using the current configuration.

        Steps:
          1. Prepare and extract the source.
          2. Move it into place as the new version.
          3. Optionally create a virtualenv and install requirements.
          4. Optionally install fonts.
          5. Create launcher and desktop entry.
          6. Optionally prune old archives.
        """
        self.prepare_source()
        self.atomic_move_into_place()
        venv = self.setup_venv_and_requirements()
        self.install_fonts()
        launcher = self.create_launcher(venv)
        self.create_desktop_entry(launcher)
        print("[+] Installation successful.")

        if self.args.auto_clean_archives:
            self.clean_old_archives(self.args.keep)

    def uninstall(self, remove_all=False):
        """
        Uninstall the application.

        Parameters
        ----------
        remove_all:
            If True, remove the entire install root; otherwise only the configured version.
        """
        if remove_all:
            shutil.rmtree(self.install_root, ignore_errors=True)
        else:
            if self.versioned_dir.exists():
                shutil.rmtree(self.versioned_dir, ignore_errors=True)
        print("[+] Uninstall complete.")

    def prompt_yesno(self, q, default=True):
        """
        Prompt the user with a yes/no question, honoring the ``--yes`` flag.

        Parameters
        ----------
        q:
            Question to display.
        default:
            Default answer if the user just presses Enter.

        Returns
        -------
        bool
            True for yes, False for no.
        """
        if self.args.yes:
            return default
        while True:
            yn = input(f"{q} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
            if yn == "":
                return default
            if yn in ("y", "yes"):
                return True
            if yn in ("n", "no"):
                return False


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
def main():
    """
    Command-line entry point for the installer script.

    Parses arguments, constructs an Installer, and dispatches to install,
    uninstall, or rollback operations.
    """
    ap = argparse.ArgumentParser(description="Installer for Python apps with GitHub-release fetch")
    ap.add_argument("--config", "-c", required=True)
    ap.add_argument("--install-root")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--remove-all", action="store_true")
    ap.add_argument("--auto-clean-archives", action="store_true")
    ap.add_argument("--keep", type=int, default=3)
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    inst = Installer(Path(args.config), args)

    if args.rollback:
        inst.rollback()
    elif args.uninstall:
        inst.uninstall(remove_all=args.remove_all)
    else:
        if not args.yes:
            print(f"Default install root: {inst.install_root}")
            custom = input("Install here? (enter to accept or specify another): ").strip()
            if custom:
                inst.install_root = Path(custom).expanduser()
                ensure_dir(inst.install_root)

        # Only *checks* required apps; does not install via a package manager.
        # inst.ensure_required_apps()  # <-- this is now handled by the installer.py script -- actuly, just not doing this
        inst.install()


if __name__ == "__main__":
    main()










# #!/usr/bin/env python3
# """
# enhanced_python_installer_v3
# Modified to:
#  - Fetch latest GitHub release instead of git clone
#  - Extract archive and continue with original workflow
#  - zyngInstaller should exclude installing programs from repos, this should be in the install.sh script
# """
#
# import argparse
# import hashlib
# import os
# import shutil
# import subprocess
# import sys
# import tarfile
# import tempfile
# import time
# import urllib.request
# import zipfile
# import json
# from pathlib import Path
#
# try:
#     import tomllib
# except ImportError:
#     import tomli as tomllib
#
# def eprint(*a, **k):
#     print(*a, file=sys.stderr, **k)
#
# def run(cmd, check=True, capture=False, env=None):
#     if isinstance(cmd, (list, tuple)):
#         pass
#     else:
#         cmd = cmd.split()
#     return subprocess.run(
#         cmd,
#         check=check,
#         stdout=subprocess.PIPE if capture else None,
#         stderr=subprocess.PIPE if capture else None,
#         env=env
#     )
#
# def ensure_dir(p: Path, exist_ok=True):
#     p = Path(p).expanduser()
#     p.mkdir(parents=True, exist_ok=exist_ok)
#     return p
#
# def sha256sum(path: Path):
#     h = hashlib.sha256()
#     with open(path, "rb") as f:
#         for chunk in iter(lambda: f.read(8192), b""):
#             h.update(chunk)
#     return h.hexdigest()
#
# # -------------------------------------------------------------
# # Installer Class
# # -------------------------------------------------------------
# class Installer:
#     def __init__(self, cfg_path: Path, args):
#         self.args = args
#         self.cfg_path = cfg_path.expanduser()
#         self.load_config()
#         self.tmpdir = Path(tempfile.mkdtemp(prefix="installer_"))
#         self.appname = self.config["name"]
#         self.version = self.config["version"]
#         self.install_root = Path(
#             self.config.get("default_install_root", "~/.local/share/" + self.appname + "-installs")
#         ).expanduser()
#
#         if args.install_root:
#             self.install_root = Path(args.install_root).expanduser()
#
#         ensure_dir(self.install_root)
#         self.versioned_dir = self.install_root / f"{self.appname}-{self.version}"
#         self.current_symlink = self.install_root / f"{self.appname}-current"
#         self.archives_dir = self.install_root / "archives"
#         ensure_dir(self.archives_dir)
#
#         self.local_bin = Path("~/.local/bin").expanduser()
#         ensure_dir(self.local_bin)
#
#         self.source_root = None
#         self.vpython = sys.executable
#
#     def load_config(self):
#         if not self.cfg_path.exists():
#             raise SystemExit(f"Config file not found: {self.cfg_path}")
#         with open(self.cfg_path, "rb") as f:
#             self.config = tomllib.load(f)
#
#         for key in ("name", "version", "source"):
#             if key not in self.config:
#                 raise SystemExit(f"Missing required config key: {key}")
#
#         self.source_cfg = self.config["source"]
#
#     # -------------------------------------------------------------
#     # Fetch Latest GitHub Release (NEW)
#     # -------------------------------------------------------------
#     def fetch_latest_github_release(self, repo: str) -> Path:
#         """
#         repo format: 'WOLFBED/d4'
#         Downloads the newest release archive and returns the local file path.
#         """
#         api = f"https://api.github.com/repos/{repo}/releases/latest"
#         print(f"[+] querying GitHub releases: {api}")
#
#         req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json"})
#         with urllib.request.urlopen(req) as r:
#             meta = json.load(r)
#
#         assets = meta.get("assets", [])
#         if not assets:
#             raise SystemExit("No assets found in the latest GitHub release.")
#
#         # Choose an archive asset
#         archive = None
#         for a in assets:
#             name = a["name"].lower()
#             if name.endswith((".zip", ".tar.gz", ".tgz", ".tar.xz")):
#                 archive = a
#                 break
#
#         if not archive:
#             raise SystemExit("No installable archive asset found in the latest release.")
#
#         url = archive["browser_download_url"]
#         dest = self.tmpdir / archive["name"]
#
#         print(f"[+] downloading release asset: {url}")
#         urllib.request.urlretrieve(url, dest)
#
#         print(f"[+] downloaded to: {dest}")
#         return dest
#
#     # -------------------------------------------------------------
#     # Required App Logic (unchanged)
#     # -------------------------------------------------------------
#     def _detect_distro_family(self) -> str | None:
#         os_release = Path("/etc/os-release")
#         if not os_release.exists():
#             return None
#
#         data = {}
#         with os_release.open() as f:
#             for line in f:
#                 line = line.strip()
#                 if not line or "=" not in line:
#                     continue
#                 k, v = line.split("=", 1)
#                 v = v.strip().strip('"').strip("'")
#                 data[k] = v
#
#         ids = set()
#         if "ID" in data:
#             ids.add(data["ID"].lower())
#         if "ID_LIKE" in data:
#             for part in data["ID_LIKE"].split():
#                 ids.add(part.lower())
#
#         if ids & {"arch", "manjaro", "endeavouros", "cachyos"}:
#             return "arch"
#         if ids & {"debian", "ubuntu", "linuxmint", "raspbian", "tuxedo os", "suse", "opensuse", "popos"}:
#             return "debian"
#         if ids & {"fedora", "rhel", "centos", "rocky", "almalinux", "bazzite"}:
#             return "fedora"
#         return None
#
#     def _get_required_apps(self) -> list[str]:
#         section = self.config.get("required_apps") or {}
#         if not isinstance(section, dict):
#             return []
#         apps = section.get("apps") or section.get("name") or []
#         if isinstance(apps, str):
#             apps = [apps]
#         return [a for a in apps if isinstance(a, str) and a.strip()]
#
#     def _install_single_app(self, app: str, family: str) -> bool:
#         if shutil.which(app):
#             return True
#
#         use_sudo = os.geteuid() != 0
#         sudo_bin = shutil.which("sudo") if use_sudo else None
#         prefix = [sudo_bin] if sudo_bin else []
#         if use_sudo and not sudo_bin:
#             eprint(f"[!] {app} is missing and 'sudo' not found.")
#             return False
#
#         if family == "arch":
#             base = ["pacman", "-S", "--needed"]
#             if self.args.yes:
#                 base.append("--noconfirm")
#             cmd = prefix + base + [app]
#         elif family == "debian":
#             cmd = prefix + ["apt-get", "install"] + (["-y", app] if self.args.yes else [app])
#         elif family == "fedora":
#             base = ["dnf", "install"]
#             if self.args.yes:
#                 base.append("-y")
#             cmd = prefix + base + [app]
#         else:
#             eprint(f"[!] Unknown distro family.")
#             return False
#
#         print(f"[+] Installing '{app}' → {' '.join(cmd)}")
#         try:
#             run(cmd, check=True)
#         except subprocess.CalledProcessError:
#             return False
#
#         return shutil.which(app) is not None
#
#     def ensure_required_apps(self):
#         required = self._get_required_apps()
#         if not required:
#             return
#
#         print("[+] Checking required applications …")
#         missing = [a for a in required if not shutil.which(a)]
#
#         if not missing:
#             print("  - all present")
#             return
#
#         family = self._detect_distro_family()
#         if family is None:
#             raise SystemExit("Missing apps and cannot auto-install.")
#
#         print(f"  - distro family detected: {family}")
#
#         failed = []
#         for a in missing:
#             if not self._install_single_app(a, family):
#                 failed.append(a)
#
#         if failed:
#             raise SystemExit("Unmet required applications.")
#
#     # -------------------------------------------------------------
#     # Source Preparation (MODIFIED)
#     # -------------------------------------------------------------
#     def prepare_source(self):
#         stype = self.source_cfg.get("type", "git")
#         loc = self.source_cfg["location"]
#
#         print(f"[+] preparing source (type={stype})")
#
#         if stype == "git":
#             archive = self.fetch_latest_github_release(loc)
#             return self.extract_archive(archive)
#
#         elif stype in ("url", "archive"):
#             path = self.download_or_copy(loc)
#             expected_sha = self.source_cfg.get("sha256")
#             if expected_sha:
#                 print("  - verifying SHA256 …")
#                 actual = sha256sum(path)
#                 if actual.lower() != expected_sha.lower():
#                     raise SystemExit("SHA256 mismatch")
#                 print("  - checksum OK")
#             return self.extract_archive(path)
#
#         else:
#             raise SystemExit(f"Unknown source type: {stype}")
#
#     def download_or_copy(self, loc):
#         dest = self.tmpdir / "download"
#         if loc.startswith(("http://", "https://")):
#             print(f"  - downloading {loc}")
#             urllib.request.urlretrieve(loc, dest)
#         else:
#             src = Path(loc).expanduser()
#             if not src.exists():
#                 raise SystemExit(f"Source not found: {src}")
#             shutil.copy2(src, dest)
#         return dest
#
#     # -------------------------------------------------------------
#     # Archive Extraction (unchanged)
#     # -------------------------------------------------------------
#     def extract_archive(self, pathobj):
#         path = Path(pathobj)
#         print(f"  - extracting {path}")
#
#         extract_dir = self.tmpdir / "src"
#         ensure_dir(extract_dir)
#
#         if zipfile.is_zipfile(path):
#             with zipfile.ZipFile(path, "r") as z:
#                 z.extractall(path=extract_dir)
#         elif tarfile.is_tarfile(path):
#             with tarfile.open(path, "r:*") as t:
#                 t.extractall(path=extract_dir)
#         else:
#             raise SystemExit(f"Unknown archive format: {path}")
#
#         entries = [p for p in extract_dir.iterdir() if p.name != "__MACOSX"]
#         root = entries[0] if len(entries) == 1 and entries[0].is_dir() else extract_dir
#
#         self.validate_app_structure(root)
#         self.source_root = root
#
#         print(f"  - source root: {root}")
#         return root
#
#     def validate_app_structure(self, root: Path):
#         for r in ("src", "data"):
#             if not (root / r).exists():
#                 raise SystemExit(f"Invalid app structure: missing {r}/")
#
#         if not (root / "requirements.txt").exists():
#             eprint("Warning: no requirements.txt found")
#
#     # -------------------------------------------------------------
#     # Installation (unchanged)
#     # -------------------------------------------------------------
#     def atomic_move_into_place(self):
#         if self.versioned_dir.exists():
#             ts = time.strftime("%Y%m%d%H%M%S")
#             archive_target = self.archives_dir / f"{self.appname}-{self.version}-{ts}"
#             print(f"[!] existing version found; archiving → {archive_target}")
#             shutil.move(str(self.versioned_dir), str(archive_target))
#
#         print(f"[+] installing to {self.versioned_dir}")
#         shutil.move(str(self.source_root), str(self.versioned_dir))
#
#         if self.current_symlink.exists() or self.current_symlink.is_symlink():
#             self.current_symlink.unlink(missing_ok=True)
#
#         self.current_symlink.symlink_to(
#             self.versioned_dir, target_is_directory=True
#         )
#
#     def setup_venv_and_requirements(self):
#         if not self.config.get("setup_venv", True):
#             return None
#
#         venv_path = self.versioned_dir / "venv"
#         print(f"[+] creating venv: {venv_path}")
#         run([self.vpython, "-m", "venv", str(venv_path)])
#
#         req = self.versioned_dir / "requirements.txt"
#         if req.exists():
#             pip = venv_path / "bin" / "pip"
#             print("[+] installing requirements …")
#             run([pip, "install", "--upgrade", "pip"])
#             run([pip, "install", "-r", str(req)])
#
#         return venv_path
#
#     def install_fonts(self):
#         fonts_dir = self.versioned_dir / "data" / "fonts"
#         if not fonts_dir.exists():
#             return
#         if not self.prompt_yesno("Install included fonts to user font dir?", True):
#             return
#
#         target = Path("~/.local/share/fonts").expanduser() / f"{self.appname}-{self.version}"
#         ensure_dir(target)
#
#         print(f"[+] copying fonts → {target}")
#         for root, _, files in os.walk(fonts_dir):
#             for f in files:
#                 src = Path(root) / f
#                 rel = Path(root).relative_to(fonts_dir)
#                 dst = target / rel
#                 ensure_dir(dst)
#                 shutil.copy2(src, dst / f)
#
#         run(["fc-cache", "-f", str(target)], check=False)
#
#     def create_launcher(self, venv_path=None):
#         entry = self.config.get("entrypoint", "src/app/zyngInstaller.py")
#         launcher = self.local_bin / self.appname
#
#         with open(launcher, "w") as f:
#             f.write("#!/usr/bin/env bash\nset -euo pipefail\n")
#             f.write(f"APP_DIR=\"{self.current_symlink}\"\n")
#             if venv_path:
#                 f.write("source \"$APP_DIR/venv/bin/activate\"\n")
#             f.write("cd \"$APP_DIR\"\n")
#             f.write(f"exec python3 {entry} \"$@\"\n")
#
#         launcher.chmod(0o755)
#         print(f"[+] launcher created: {launcher}")
#         return launcher
#
#     def create_desktop_entry(self, launcher):
#         desktop_dir = Path("~/.local/share/applications").expanduser()
#         ensure_dir(desktop_dir)
#
#         desktop = desktop_dir / f"{self.appname}-{self.version}.desktop"
#
#         icon_path = self.config.get("icon", "")
#         if icon_path:
#             icon_abs = self.versioned_dir / icon_path
#             if not icon_abs.exists():
#                 eprint(f"[!] icon not found: {icon_abs}")
#                 icon_abs = ""
#         else:
#             icon_abs = ""
#
#         with open(desktop, "w") as f:
#             f.write("[Desktop Entry]\n")
#             f.write("Type=Application\n")
#             f.write(f"Name={self.appname}\n")
#             f.write(f"Exec={launcher} %U\n")
#             f.write(f"Icon={icon_abs}\n")
#             f.write("Terminal=false\n")
#             f.write("Categories=Internet;Utility;Application;\n")
#
#         desktop.chmod(0o644)
#         print(f"[+] desktop entry: {desktop}")
#
#     # -------------------------------------------------------------
#     # Cleanup & Rollback (unchanged)
#     # -------------------------------------------------------------
#     def clean_old_archives(self, keep):
#         entries = sorted(self.archives_dir.glob(f"{self.appname}-*"),
#                          key=os.path.getmtime,
#                          reverse=True)
#
#         if len(entries) <= keep:
#             return
#
#         for old in entries[keep:]:
#             print(f"[-] removing old archive: {old}")
#             shutil.rmtree(old, ignore_errors=True)
#
#     def rollback(self):
#         print("[+] Rollback mode active")
#
#         archives = sorted(
#             self.archives_dir.glob(f"{self.appname}-*"),
#             key=os.path.getmtime,
#             reverse=True
#         )
#
#         if not archives:
#             raise SystemExit("No archived versions exist.")
#
#         print("Available versions:")
#         for i, arch in enumerate(archives):
#             print(f"  [{i}] {arch.name}")
#
#         choice = int(input("Select index: ").strip())
#         if choice < 0 or choice >= len(archives):
#             raise SystemExit("Invalid selection.")
#
#         target = archives[choice]
#         print(f"[+] Rolling back to {target}")
#
#         if self.current_symlink.exists() and self.current_symlink.is_symlink():
#             curr = self.current_symlink.resolve()
#             ts = time.strftime("%Y%m%d%H%M%S")
#             failed = self.archives_dir / f"{curr.name}-failed-{ts}"
#             shutil.move(str(curr), str(failed))
#
#         if self.current_symlink.exists():
#             self.current_symlink.unlink(missing_ok=True)
#
#         self.current_symlink.symlink_to(target, target_is_directory=True)
#
#         print("[+] Rollback complete.")
#
#     # -------------------------------------------------------------
#     # Installation Orchestration
#     # -------------------------------------------------------------
#     def install(self):
#         self.prepare_source()
#         self.atomic_move_into_place()
#         venv = self.setup_venv_and_requirements()
#         self.install_fonts()
#         launcher = self.create_launcher(venv)
#         self.create_desktop_entry(launcher)
#         print("[+] Installation successful.")
#
#         if self.args.auto_clean_archives:
#             self.clean_old_archives(self.args.keep)
#
#     def uninstall(self, remove_all=False):
#         if remove_all:
#             shutil.rmtree(self.install_root, ignore_errors=True)
#         else:
#             if self.versioned_dir.exists():
#                 shutil.rmtree(self.versioned_dir, ignore_errors=True)
#         print("[+] Uninstall complete.")
#
#     def prompt_yesno(self, q, default=True):
#         if self.args.yes:
#             return default
#         while True:
#             yn = input(f"{q} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
#             if yn == "":
#                 return default
#             if yn in ("y", "yes"):
#                 return True
#             if yn in ("n", "no"):
#                 return False
#
# # -------------------------------------------------------------
# # Main
# # -------------------------------------------------------------
# def main():
#     ap = argparse.ArgumentParser(description="Installer for Python apps with GitHub-release fetch")
#     ap.add_argument("--config", "-c", required=True)
#     ap.add_argument("--install-root")
#     ap.add_argument("--uninstall", action="store_true")
#     ap.add_argument("--remove-all", action="store_true")
#     ap.add_argument("--auto-clean-archives", action="store_true")
#     ap.add_argument("--keep", type=int, default=3)
#     ap.add_argument("--rollback", action="store_true")
#     ap.add_argument("--yes", action="store_true")
#     args = ap.parse_args()
#
#     inst = Installer(Path(args.config), args)
#
#     if args.rollback:
#         inst.rollback()
#     elif args.uninstall:
#         inst.uninstall(remove_all=args.remove_all)
#     else:
#         if not args.yes:
#             print(f"Default install root: {inst.install_root}")
#             custom = input("Install here? (enter to accept or specify another): ").strip()
#             if custom:
#                 inst.install_root = Path(custom).expanduser()
#                 ensure_dir(inst.install_root)
#
#         inst.ensure_required_apps()
#         inst.install()
#
#
# if __name__ == "__main__":
#     main()













































# #!/usr/bin/env python3
# """
# enhanced_python_installer_v2
# zyngInstaller.py
# Features:
#  - TOML config
#  - SHA256 verification
#  - GPG signature verification
#  - auto-clean archives
#  - rollback capability
#  - icon support
#  - desktop entry creation
#  - venv creation
#  - requirements.txt support
#  - custom entrypoint
#  - custom install root
#  - custom default install root
#  - custom icon path
#  - custom entrypoint
#  - custom install root
#
# HAS BUGS:::
# -
# """
# import argparse
# import hashlib
# import os
# import shutil
# import subprocess
# import sys
# import tarfile
# import tempfile
# import time
# import urllib.request
# import zipfile
# from pathlib import Path
#
# try:
#     import tomllib
# except ImportError:
#     import tomli as tomllib  # for older Python
#
# # Utility functions
# def eprint(*a, **k):
#     print(*a, file=sys.stderr, **k)
#
# def run(cmd, check=True, capture=False, env=None):
#     if isinstance(cmd, (list,tuple)):
#         pass
#     else:
#         cmd = cmd.split()
#     return subprocess.run(cmd, check=check, stdout=subprocess.PIPE if capture else None,
#                           stderr=subprocess.PIPE if capture else None, env=env)
#
# def ensure_dir(p: Path, exist_ok=True):
#     p = Path(p).expanduser()
#     p.mkdir(parents=True, exist_ok=exist_ok)
#     return p
#
# def sha256sum(path: Path):
#     h = hashlib.sha256()
#     with open(path, "rb") as f:
#         for chunk in iter(lambda: f.read(8192), b""):
#             h.update(chunk)
#     return h.hexdigest()
#
# # Installer class
# class Installer:
#     def __init__(self, cfg_path: Path, args):
#         self.args = args
#         self.cfg_path = cfg_path.expanduser()
#         self.load_config()
#         self.tmpdir = Path(tempfile.mkdtemp(prefix="installer_"))
#         self.appname = self.config["name"]
#         self.version = self.config["version"]
#         self.install_root = Path(self.config.get("default_install_root", "~/.local/share/"+self.appname+"-installs")).expanduser()
#         if args.install_root:
#             self.install_root = Path(args.install_root).expanduser()
#         ensure_dir(self.install_root)
#         self.versioned_dir = self.install_root / f"{self.appname}-{self.version}"
#         self.current_symlink = self.install_root / f"{self.appname}-current"
#         self.archives_dir = self.install_root / "archives"
#         ensure_dir(self.archives_dir)
#         self.local_bin = Path("~/.local/bin").expanduser()
#         ensure_dir(self.local_bin)
#         self.source_root = None
#         self.vpython = sys.executable
#
#     def load_config(self):
#         if not self.cfg_path.exists():
#             raise SystemExit(f"Config file not found: {self.cfg_path}")
#         with open(self.cfg_path, "rb") as f:
#             self.config = tomllib.load(f)
#         for key in ("name","version","source"):
#             if key not in self.config:
#                 raise SystemExit(f"Missing required config key: {key}")
#         self.source_cfg = self.config["source"]
#
#     # --- required apps handling -------------------------------------------------
#     def _detect_distro_family(self) -> str | None:
#         """
#         Try to detect a high‑level distro family: 'arch', 'debian', 'fedora', or None.
#         """
#         os_release = Path("/etc/os-release")
#         if not os_release.exists():
#             return None
#
#         data = {}
#         with os_release.open() as f:
#             for line in f:
#                 line = line.strip()
#                 if not line or "=" not in line:
#                     continue
#                 k, v = line.split("=", 1)
#                 v = v.strip().strip('"').strip("'")
#                 data[k] = v
#
#         ids = set()
#         if "ID" in data:
#             ids.add(data["ID"].lower())
#         if "ID_LIKE" in data:
#             for part in data["ID_LIKE"].split():
#                 ids.add(part.lower())
#
#         if ids & {"arch", "manjaro", "endeavouros", "cachyos"}:
#             return "arch"
#         if ids & {"debian", "ubuntu", "linuxmint", "raspbian", "tuxedo os", "suse", "opensuse", "popos"}:
#             return "debian"
#         if ids & {"fedora", "rhel", "centos", "rocky", "almalinux", "bazzite"}:
#             return "fedora"
#         return None
#
#     def _get_required_apps(self) -> list[str]:
#         section = self.config.get("required_apps") or {}
#         if not isinstance(section, dict):
#             return []
#         apps = section.get("apps") or section.get("name") or []
#         if isinstance(apps, str):
#             apps = [apps]
#         return [a for a in apps if isinstance(a, str) and a.strip()]
#
#     def _install_single_app(self, app: str, family: str) -> bool:
#         """
#         Attempt to install a single app for the given distro family.
#         Returns True on (likely) success, False on failure.
#         """
#         if shutil.which(app):
#             return True  # already present
#
#         # If we're already root, we don't need sudo
#         use_sudo = os.geteuid() != 0
#         sudo_bin = shutil.which("sudo") if use_sudo else None
#         prefix = [sudo_bin] if sudo_bin else []
#         if use_sudo and not sudo_bin:
#             eprint(f"[!] {app} is missing and 'sudo' not found; cannot auto‑install.")
#             return False
#
#         # Construct package manager command
#         if family == "arch":
#             # pacman uses --noconfirm for non‑interactive mode
#             base_cmd = ["pacman", "-S", "--needed"]
#             if self.args.yes:
#                 base_cmd.append("--noconfirm")
#             cmd = prefix + base_cmd + [app]
#         elif family == "debian":
#             base_cmd = ["apt-get", "install", "-y" if self.args.yes else app]
#             # If not auto‑yes, drop the -y we just added
#             if not self.args.yes:
#                 base_cmd = ["apt-get", "install", app]
#             cmd = prefix + base_cmd
#         elif family == "fedora":
#             base_cmd = ["dnf", "install"]
#             if self.args.yes:
#                 base_cmd.append("-y")
#             cmd = prefix + base_cmd + [app]
#         else:
#             eprint(f"[!] Unknown distro family '{family}', cannot auto‑install {app}.")
#             return False
#
#         print(f"[+] Attempting to install missing required app '{app}' using: {' '.join(cmd)}")
#         try:
#             run(cmd, check=True)
#         except subprocess.CalledProcessError as exc:
#             eprint(f"[!] Failed to install required app '{app}': {exc}")
#             return False
#
#         if not shutil.which(app):
#             eprint(f"[!] '{app}' still not found on PATH after installation attempt.")
#             return False
#
#         print(f"[+] Installed required app '{app}'.")
#         return True
#
#     def ensure_required_apps(self):
#         required = self._get_required_apps()
#         if not required:
#             return
#
#         print("[+] Checking required external applications …")
#         missing = [a for a in required if not shutil.which(a)]
#         if not missing:
#             print("  - all required applications are already installed.")
#             return
#
#         family = self._detect_distro_family()
#         if family is None:
#             eprint("[!] Unable to detect distro family; cannot auto‑install:")
#             for app in missing:
#                 eprint(f"    - {app}")
#             raise SystemExit("Missing required applications and auto‑install is not available.")
#
#         print(f"  - detected distro family: {family}")
#         failed: list[str] = []
#         for app in missing:
#             if not self._install_single_app(app, family):
#                 failed.append(app)
#
#         if failed:
#             eprint("[!] The following required applications are missing and could not be installed:")
#             for app in failed:
#                 eprint(f"    - {app}")
#             raise SystemExit("Unmet required applications; aborting installation.")
#         else:
#             print("[+] All required applications are available.")
#
#     def prompt_yesno(self, q, default=True):
#         if self.args.yes:
#             return default
#         while True:
#             yn = input(f"{q} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
#             if yn == "":
#                 return default
#             if yn in ("y", "yes"):
#                 return True
#             if yn in ("n", "no"):
#                 return False
#
#     # def prompt_yesno(self, q, default=True):
#     #     if self.args.yes:
#     #         return default
#     #     while True:
#     #         yn = input(f"{q} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
#     #         if yn=="":
#     #             return default
#     #         if yn in ("y","yes"):
#     #             return True
#     #         if yn in ("n","no"):
#     #             return False
#
#     def prepare_source(self):
#         stype = self.source_cfg.get("type","git")
#         loc = self.source_cfg["location"]
#         print(f"[+] preparing source (type={stype})")
#         if stype == "git":
#             return self.clone_git(loc, self.source_cfg.get("ref"))
#         elif stype in ("url","archive"):
#             path = self.download_or_copy(loc)
#             expected_sha = self.source_cfg.get("sha256")
#             if expected_sha:
#                 print("  - verifying SHA256 …")
#                 actual = sha256sum(path)
#                 if actual.lower() != expected_sha.lower():
#                     raise SystemExit(f"SHA256 mismatch: expected {expected_sha}, got {actual}")
#                 print("  - checksum OK")
#             # GPG verification
#             gpg_key = self.source_cfg.get("gpg_key")
#             gpg_sig = self.source_cfg.get("gpg_signature")
#             if gpg_key or gpg_sig:
#                 self.verify_gpg(path, gpg_key, gpg_sig)
#             return self.extract_archive(path)
#         else:
#             raise SystemExit(f"Unknown source type: {stype}")
#
#     def clone_git(self, url, ref=None):
#         git_bin = shutil.which("git")
#         if not git_bin:
#             raise SystemExit("git not found; required for git source type.")
#         clone_dir = self.tmpdir / "src"
#         print(f"  - git clone {url} → {clone_dir}")
#         run([git_bin,"clone","--depth","1",url,str(clone_dir)])
#         if ref:
#             try:
#                 run([git_bin,"-C",str(clone_dir),"fetch","--depth","1","origin",ref])
#                 run([git_bin,"-C",str(clone_dir),"checkout",ref])
#             except subprocess.CalledProcessError:
#                 eprint("Warning: failed to fetch/ref; using HEAD")
#         self.source_root = clone_dir
#         return clone_dir
#
#     def download_or_copy(self, loc):
#         dest = self.tmpdir / "download"
#         if loc.startswith(("http://","https://")):
#             print(f"  - downloading {loc}")
#             urllib.request.urlretrieve(loc, str(dest))
#         else:
#             srcp = Path(loc).expanduser()
#             if not srcp.exists():
#                 raise SystemExit(f"Source not found: {srcp}")
#             print(f"  - copying local source {srcp}")
#             shutil.copy2(str(srcp), str(dest))
#         return dest
#
#     def verify_gpg(self, archive_path: Path, gpg_key: str=None, gpg_sig: str=None):
#         gpg_bin = shutil.which("gpg") or shutil.which("gpg2")
#         if not gpg_bin:
#             raise SystemExit("gpg executable not found; cannot verify signature.")
#         print("  - performing GPG verification …")
#         # prepare temporary GNUPGHOME
#         ghome = self.tmpdir / "gnupghome"
#         ensure_dir(ghome)
#         os.environ["GNUPGHOME"] = str(ghome)
#         if gpg_key:
#             keyloc = self.download_or_copy(gpg_key) if gpg_key.startswith(("http://","https://")) else Path(gpg_key).expanduser()
#             print(f"    importing public key: {keyloc}")
#             run([gpg_bin,"--homedir",str(ghome),"--import",str(keyloc)])
#         if not gpg_sig:
#             raise SystemExit("gpg_signature not provided; cannot verify signature without detached signature.")
#         sigloc = self.download_or_copy(gpg_sig) if gpg_sig.startswith(("http://","https://")) else Path(gpg_sig).expanduser()
#         print(f"    verifying signature: {sigloc} vs {archive_path}")
#         res = run([gpg_bin, "--homedir", str(ghome), "--verify", str(sigloc), str(archive_path)], check=False, capture=True)
#         if res.returncode != 0:
#             raise SystemExit(f"GPG signature verification failed: {res.stderr}")
#         print("    ✅ GPG signature valid")
#
#     def extract_archive(self, pathobj):
#         path = Path(pathobj)
#         print(f"  - extracting {path}")
#         extract_dir = self.tmpdir / "src"
#         ensure_dir(extract_dir)
#         if zipfile.is_zipfile(path):
#             with zipfile.ZipFile(path, "r") as z:
#                 z.extractall(path=extract_dir)
#         elif tarfile.is_tarfile(path):
#             with tarfile.open(path, "r:*") as t:
#                 t.extractall(path=extract_dir)
#         else:
#             raise SystemExit(f"Unrecognized archive format: {path}")
#         entries = [p for p in extract_dir.iterdir() if p.name != "__MACOSX"]
#         root = entries[0] if len(entries)==1 and entries[0].is_dir() else extract_dir
#         self.validate_app_structure(root)
#         self.source_root = root
#         print(f"  - source root is {root}")
#         return root
#
#     def validate_app_structure(self, root: Path):
#         required = ["src","data"]
#         for r in required:
#             if not (root / r).exists():
#                 raise SystemExit(f"Invalid app structure: missing {r}/ under {root}")
#         # requirements.txt is optional; if missing, warn
#         if not (root / "requirements.txt").exists():
#             eprint("Warning: no requirements.txt found; skipping dependencies")
#
#     def atomic_move_into_place(self):
#         if self.versioned_dir.exists():
#             ts = time.strftime("%Y%m%d%H%M%S")
#             archive_target = self.archives_dir / f"{self.appname}-{self.version}-{ts}"
#             print(f"[!] existing version present; archival → {archive_target}")
#             shutil.move(str(self.versioned_dir), str(archive_target))
#         print(f"[+] installing to {self.versioned_dir}")
#         shutil.move(str(self.source_root), str(self.versioned_dir))
#         if self.current_symlink.exists() or self.current_symlink.is_symlink():
#             self.current_symlink.unlink(missing_ok=True)
#         self.current_symlink.symlink_to(self.versioned_dir, target_is_directory=True)
#
#     def setup_venv_and_requirements(self):
#         if not self.config.get("setup_venv", True):
#             return None
#         venv_path = self.versioned_dir / "venv"
#         print(f"[+] creating venv: {venv_path}")
#         run([self.vpython, "-m", "venv", str(venv_path)])
#         req = self.versioned_dir / "requirements.txt"
#         if req.exists():
#             pip = venv_path / "bin" / "pip"
#             print("[+] installing requirements …")
#             run([str(pip), "install", "--upgrade", "pip"])
#             run([str(pip), "install", "-r", str(req)])
#         return venv_path
#
#     def install_fonts(self):
#         fonts_dir = self.versioned_dir / "data" / "fonts"
#         if not fonts_dir.exists():
#             return
#         if not self.prompt_yesno("Install included fonts to user font dir?", True):
#             return
#         target = Path("~/.local/share/fonts").expanduser() / f"{self.appname}-{self.version}"
#         ensure_dir(target)
#         print(f"[+] copying fonts → {target}")
#         for root, _, files in os.walk(fonts_dir):
#             for f in files:
#                 srcf = Path(root) / f
#                 rel = Path(root).relative_to(fonts_dir)
#                 dst = target / rel
#                 ensure_dir(dst)
#                 shutil.copy2(srcf, dst / f)
#         run(["fc-cache","-f",str(target)], check=False)
#
#     def create_launcher(self, venv_path=None):
#         entry = self.config.get("entrypoint","src/app/zyngInstaller.py")
#         launcher = self.local_bin / self.appname
#         with open(launcher,"w") as f:
#             f.write("#!/usr/bin/env bash\nset -euo pipefail\n")
#             f.write(f"APP_DIR=\"{self.current_symlink}\"\n")
#             if venv_path:
#                 f.write("source \"$APP_DIR/venv/bin/activate\"\n")
#             f.write("cd \"$APP_DIR\"\n")
#             f.write(f"exec python3 {entry} \"$@\"\n")
#         launcher.chmod(0o755)
#         print(f"[+] launcher: {launcher}")
#         return launcher
#
#     def create_desktop_entry(self, launcher_path):
#         desktop_dir = Path("~/.local/share/applications").expanduser()
#         ensure_dir(desktop_dir)
#         desktop_file = desktop_dir / f"{self.appname}-{self.version}.desktop"
#
#         # Resolve icon path
#         icon_path = self.config.get("icon")
#         if icon_path:
#             icon_abs = self.versioned_dir / icon_path
#             if not icon_abs.exists():
#                 eprint(f"[!] Warning: icon file not found: {icon_abs}")
#                 icon_abs = ""
#         else:
#             icon_abs = ""
#
#         with open(desktop_file, "w") as f:
#             f.write("[Desktop Entry]\n")
#             f.write("Type=Application\n")
#             # f.write(f"Name={self.appname} {self.version}\n")
#             f.write(f"Name={self.appname}\n")
#             f.write(f"Exec={launcher_path} %U\n")
#             f.write(f"Icon={icon_abs}\n")
#             f.write("Terminal=false\n")
#             f.write("Categories=Utility;Application;\n")
#         desktop_file.chmod(0o644)
#         print(f"[+] .desktop entry created: {desktop_file}")
#
#     def clean_old_archives(self, keep: int):
#         entries = sorted(self.archives_dir.glob(f"{self.appname}-*"), key=os.path.getmtime, reverse=True)
#         if len(entries) <= keep:
#             return
#         for old in entries[keep:]:
#             print(f"[-] removing old archive: {old}")
#             shutil.rmtree(old, ignore_errors=True)
#
#     def rollback(self):
#         print("[+] Rollback mode engaged")
#         # list archives:
#         archives = sorted(self.archives_dir.glob(f"{self.appname}-*"), key=os.path.getmtime, reverse=True)
#         if not archives:
#             raise SystemExit("No archived versions found; cannot rollback.")
#         print("Available archived versions:")
#         for idx, arch in enumerate(archives):
#             print(f"  [{idx}] {arch.name}")
#         choice = input(f"Select index to rollback to (0..{len(archives)-1}): ").strip()
#         try:
#             i = int(choice)
#             if i<0 or i>=len(archives):
#                 raise ValueError()
#         except ValueError:
#             raise SystemExit("Invalid selection; aborting rollback.")
#         target = archives[i]
#         print(f"[+] Rolling back to: {target}")
#         # move current to failed-<timestamp>
#         if self.current_symlink.exists() and self.current_symlink.is_symlink():
#             curr = self.current_symlink.resolve()
#             ts = time.strftime("%Y%m%d%H%M%S")
#             failed = self.archives_dir / f"{curr.name}-failed-{ts}"
#             print(f"    archiving current version to {failed}")
#             shutil.move(str(curr), str(failed))
#         # now link current to target
#         if self.current_symlink.exists() or self.current_symlink.is_symlink():
#             self.current_symlink.unlink(missing_ok=True)
#         self.current_symlink.symlink_to(target, target_is_directory=True)
#         print(f"[+] Rollback complete: current → {target}")
#
#     def install(self):
#         self.prepare_source()
#         self.atomic_move_into_place()
#         venv = self.setup_venv_and_requirements()
#         self.install_fonts()
#         self.create_launcher(venv)
#         self.create_desktop_entry(self.local_bin / self.appname)
#         print("[+] Installation successful.")
#         if self.args.auto_clean_archives:
#             self.clean_old_archives(self.args.keep)
#
#     def uninstall(self, remove_all=False):
#         if remove_all:
#             print(f"[+] Removing install root {self.install_root}")
#             shutil.rmtree(self.install_root, ignore_errors=True)
#         else:
#             if self.versioned_dir.exists():
#                 print(f"[+] Removing version {self.versioned_dir}")
#                 shutil.rmtree(self.versioned_dir, ignore_errors=True)
#         print("[+] Uninstall done.")
#
# # CLI interface
# def main():
#     ap = argparse.ArgumentParser(description="Installer for Python apps with GPG & rollback")
#     ap.add_argument("--config","-c", required=True, help="TOML config file path")
#     ap.add_argument("--install-root", help="override default install root")
#     ap.add_argument("--uninstall", action="store_true", help="uninstall version in config")
#     ap.add_argument("--remove-all", action="store_true", help="with --uninstall: remove everything")
#     ap.add_argument("--auto-clean-archives", action="store_true", help="auto prune old archives")
#     ap.add_argument("--keep", type=int, default=3, help="how many archives to keep when auto-cleaning")
#     ap.add_argument("--rollback", action="store_true", help="rollback to a previous version")
#     ap.add_argument("--yes", action="store_true", help="assume yes to prompts")
#     args = ap.parse_args()
#
#     inst = Installer(Path(args.config), args)
#     if args.rollback:
#         inst.rollback()
#     elif args.uninstall:
#         inst.uninstall(remove_all=args.remove_all)
#     else:
#         # ask for install‐root if interactive
#         if not args.yes:
#             print(f"Default install root: {inst.install_root}")
#             custom = input("Install into this location? (enter to accept or specify another): ").strip()
#             if custom:
#                 inst.install_root = Path(custom).expanduser()
#                 ensure_dir(inst.install_root)
#         # ensure external dependencies before doing any real work
#         inst.ensure_required_apps()
#         inst.install()
#
# if __name__ == "__main__":
#     main()
