#!/usr/bin/env python3
"""Checks for required system commands and offers to install missing ones using the
current distro's package manager. For external binaries that are not packaged, it
only reports them and the installer later handles downloads + signature checks.
"""
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_BINARIES = [
    # Examples: adjust to your app's real external requirements
    "ffmpeg",
    "gpg",
]

# Binaries which will be installed via package manager if missing.
PKG_TO_BINARY = {
    "ffmpeg": "ffmpeg",
    "gpg": "gnupg",
}


def detect_distro():
    try:
        data = Path('/etc/os-release').read_text()
    except Exception:
        return 'unknown'
    if 'Arch' in data or 'arch' in data:
        return 'arch'
    if 'Ubuntu' in data or 'Debian' in data:
        return 'debian'
    if 'Fedora' in data or 'Red Hat' in data or 'rhel' in data:
        return 'redhat'
    return 'unknown'


def prompt_install(packages, distro):
    if not packages:
        return
    print('\nThe following system packages are missing and recommended:')
    print('  ' + ', '.join(packages))
    ans = input('Install them now using the system package manager? [y/N] ').strip().lower()
    if not ans.startswith('y'):
        print('Skipping automatic installation. You can install them manually later.')
        return

    if distro == 'arch':
        cmd = ['pkexec', 'pacman', '-S', '--noconfirm'] + packages
    elif distro == 'debian':
        cmd = ['pkexec', 'apt', 'update', '&&', 'pkexec', 'apt', 'install', '-y'] + packages
        # Using shell for compose commands; prefer prompting the user for sudo in graphical envs.
        subprocess.run(' '.join(cmd), shell=True, check=True)
        return
    elif distro == 'redhat':
        cmd = ['pkexec', 'dnf', 'install', '-y'] + packages
    else:
        print('Unsupported or unknown distro. Please install the packages manually:', packages)
        return

    if isinstance(cmd, list):
        subprocess.run(cmd, check=True)


def main():
    distro = detect_distro()
    missing = [b for b in REQUIRED_BINARIES if shutil.which(b) is None]
    if not missing:
        print('All required system binaries present.')
        return

    print('Missing system binaries:', missing)

    # map binaries to packages where possible
    packages = [PKG_TO_BINARY.get(b, b) for b in missing]
    prompt_install(packages, distro)


if __name__ == '__main__':
    main()
