![image](/data/images/site_banner.avif)

# d4 - Video Downloader

dealer version 4 ~ includes GUI -- A video downloader.  It deals.

&nbsp;
***

# !!! ABSOLUTELY NO WARRANTY PROVIDED AT ALL !!! <br> !!! DO NOT USE FOR ANY PURPOSE !!!

&nbsp;
***

## Features

- Download videos from many sources
- Batch download support, i.e. use a file with a list of URLs to download all at once
- Configurable download options:
  - Thumbnail handling (write/embed)
  - Metadata and comments
  - Subtitles
  - Chapter splitting
  - SponsorBlock integration
  - Audio-only extraction
- SOCKS5 proxy support
- Cookie file support
- Persistent settings
- Uses download archive file to avoid re-downloading the same videos
- Deno integration (for _dealing_ with pesky youtube non-sense)
- Multi-threaded downloads with progress tracking
- Automatic dependency management (yt-dlp, aria2, etc.)
- Gud

&nbsp;
***

## Requirements
- x86_64 linux 6+
- python 3.10+


## Installation, Update, Removal
These commands take care of all the dependencies at once and install dealer to ~/zyng/apps/dealer/.  Be aware this *may* install on your system:
- git
- deno
- curl
- unzip
- python3.12-venv
- python3-pip
- ffmpeg
- python-mutagen
- brotli
- atomicparsley
- python-xattr
- python-pycryptodome
- ~~yay / pura~~ nope, this was for phantomJS, but it's not needed anymore.


## Arch based distros
Tested and works great on:
- Garuda dr460nized zen 251002
- Mercury Neo 2025-03-19
- Archcraft 2025.10.16 -- first time I've tried this -- very nice aesthetics!
- RebornOS 2025.07.09
- Manjaro Cinnamon 25.0.3-250609
- CachyOS 250828

### Install
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py install.sh && ./install.sh
```

### Update
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py && python zyngInstaller.py --config app_config.toml --skip-fonts --update-git
```

### Remove
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py && python zyngInstaller.py --config app_config.toml --skip-fonts --uninstall --remove-all
```

## Other distros...

### Ubunto based distros
Tested on Pop!_OS, TUXEDO OS, and Ubuntu.
```bash
# installer doesn't work --> n/a
```

### Fedora based distros
Tested on Fedora KDE and Bazzite.
```bash
# installer doesn't work --> n/a
```

### Suse based distros
Tested on OpenSUSE Tumbleweed.
```bash
# installer doesn't work --> n/a
```

&nbsp;
***

## TODO

- [ ]  make AppImage installer (bundle: ffmpeg, ffprobe, deno, python-certifi, brotli, websockets, requests, curl_cffi, mutagen, atomicparsley, pyxattr, pycryptodome, phantomjs, secretstorage, aria2, etc.)
- [ ]  integrate __aria2__ -- Dunno about this yet
- [ ]  ensure yt-dlp is aware of path to ffmpeg, deno, aria2, etc.
- [ ]  ~~fix deno path for ubuntu~~
- [ ]  remove fonts and just have dealer use generic monospace font -- MAKE SURE THIS ACTUALLY WORKS!!!!!!
- [X]  remove git requirement on end user's system
- [ ]  ???


