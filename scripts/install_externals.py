#!/usr/bin/env python3
"""Install any external (non-distro) binaries needed by the app.

This script demonstrates:
 - how to download a vendor tarball and its .asc signature
 - verify it with GPG before extracting/installing
 - fallback to prompting the user to use their distro package manager when possible

NOTE: This is illustrative. For real vendors, update the URLs and expected file names,
and establish a secure key management policy for vendor public keys.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

EXTERNALS = [
    {
        'name': 'ffmpeg-static-example',
        'type': 'tarball',
        'url': 'https://example.com/ffmpeg-linux-x86_64.tar.xz',
        'sig_url': 'https://example.com/ffmpeg-linux-x86_64.tar.xz.asc',
        'pubkey_url': 'https://example.com/keys/ffmpeg-pubkey.asc',
        'install_subdir': 'bin',
    },
]


def run(cmd, **kwargs):
    print('>',' '.join(cmd))
    subprocess.check_call(cmd, **kwargs)


def verify_signature(artifact: Path, sig: Path, pubkey_url: str) -> bool:
    # Ensure gpg exists
    if shutil.which('gpg') is None:
        print('gpg not installed; cannot verify signatures')
        return False

    home = Path.home() / '.local' / 'share' / 'myapp' / 'gpg'
    home.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env['GNUPGHOME'] = str(home)

    # Import the vendor public key
    keyfile = home / 'vendor_pubkey.asc'
    print('Downloading vendor public key:', pubkey_url)
    urlretrieve(pubkey_url, str(keyfile))
    run(['gpg', '--import', str(keyfile)], env=env)

    try:
        run(['gpg', '--verify', str(sig), str(artifact)], env=env)
        print('GPG signature verification: OK')
        return True
    except subprocess.CalledProcessError:
        print('GPG signature verification: FAILED')
        return False


def install_external(entry, repo_root: Path):
    name = entry['name']
    print('\nProcessing external:', name)
    tmp = repo_root / 'tmp' / name
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    artifact = tmp / Path(entry['url']).name
    sig = tmp / Path(entry['sig_url']).name

    print('Downloading', entry['url'])
    urlretrieve(entry['url'], str(artifact))
    print('Downloading signature', entry['sig_url'])
    urlretrieve(entry['sig_url'], str(sig))

    ok = verify_signature(artifact, sig, entry['pubkey_url'])
    if not ok:
        print('Signature verification failed for', name)
        return False

    # extract tarball and copy the binary files into ~/.local/share/myapp/bin
    target = Path.home() / '.local' / 'share' / 'myapp' / entry.get('install_subdir', '')
    target.mkdir(parents=True, exist_ok=True)

    run(['tar', 'xJf', str(artifact), '-C', str(tmp)])
    # naive copy: find executables and copy to target
    for root, dirs, files in os.walk(tmp):
        for f in files:
            fp = Path(root) / f
            if os.access(fp, os.X_OK) and not fp.is_dir():
                shutil.copy2(fp, target / f)
                (target / f).chmod(0o755)
                print('Installed', f, 'to', target)

    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', required=True)
    args = p.parse_args()

    repo_root = Path(args.repo_root)
    for e in EXTERNALS:
        try:
            ok = install_external(e, repo_root)
            if not ok:
                print('Failed to install external:', e['name'])
        except Exception as exc:
            print('Error while installing', e['name'], exc)


if __name__ == '__main__':
    main()