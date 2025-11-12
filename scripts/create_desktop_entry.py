#!/usr/bin/env python3
"""Create a .desktop launcher that points at the per-user venv and resources.
Usage: create_desktop_entry.py --repo-root /path/to/repo
"""
import argparse
import os
from pathlib import Path

TEMPLATE = """[Desktop Entry]
Name=MyApp
Comment=My PySide6 application
Exec={venv}/python {main}
Icon={icon}
Terminal=false
Type=Application
Categories=Utility;
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', required=True)
    args = p.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    venv = Path.home() / '.local' / 'share' / 'myapp' / 'venv' / 'bin'
    main = repo / 'src' / 'myapp' / 'main.py'
    icon = repo / 'data' / 'icons' / 'myapp.png'

    desktop = TEMPLATE.format(venv=str(venv), main=str(main), icon=str(icon))

    dest = Path.home() / '.local' / 'share' / 'applications' / 'myapp.desktop'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(desktop)
    dest.chmod(0o755)
    print('Installed desktop entry to', dest)


if __name__ == '__main__':
    main()
