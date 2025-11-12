#!/usr/bin/env python3
"""Create (or update) a per-user venv and install Python deps from requirements.txt.

Usage: setup_venv.py --repo-root /path/to/repo
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("+ ", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", required=True)
    args = p.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    venv_dir = Path.home() / ".local" / "share" / "myapp" / "venv"
    req = repo / "requirements.txt"

    if not repo.exists():
        print("Repo root does not exist:", repo)
        sys.exit(2)

    if not venv_dir.exists():
        print("Creating venv at", venv_dir)
        import venv
        venv.create(venv_dir, with_pip=True)

    pip = str(venv_dir / "bin" / "pip")
    python = str(venv_dir / "bin" / "python")

    # Upgrade pip/wheel/setuptools
    run([pip, "install", "--upgrade", "pip", "setuptools", "wheel"])

    if req.exists():
        print("Installing Python requirements from", req)
        run([pip, "install", "-r", str(req)])
    else:
        print("No requirements.txt found at", req)

    print("Venv prepared. To run the app directly: {}/python <path-to-main.py>".format(venv_dir / "bin"))


if __name__ == '__main__':
    main()