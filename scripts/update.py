#!/usr/bin/env python3
"""Simple updater that performs a git pull and upgrades Python deps in the venv.

Note: for packaged installs (deb/rpm/AppImage/Flatpak) use those mechanisms instead.
"""
import subprocess
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
venv = Path.home() / '.local' / 'share' / 'myapp' / 'venv'

subprocess.run(['git', '-C', str(repo), 'pull'], check=True)
if venv.exists():
    pip = str(venv / 'bin' / 'pip')
    subprocess.run([pip, 'install', '--upgrade', '-r', str(repo / 'requirements.txt')], check=True)
print('Update complete.')
