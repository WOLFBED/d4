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

## Installation, Updates, Removal
These commands take care of all the dependencies at once and install dealer to ~/zyng/apps/dealer/.  Be aware this *may* install on your system:
- git
- deno
- curl
- unzip
- python3.12-venv
- python3-pip
- ffmpeg
- among other things...

## Arch based distros
Tested on Garuda, CachyOS, and Manjaro --> works great!

### Install
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py install.sh && ./install.sh
```

### Update
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
python zyngInstaller.py --config app_config.toml --skip-fonts --update-git
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
- [ ]  remove git requirement on end user's system
- [ ]  ???

## Requirements
- x86_64 linux 6+
- python 3.10+ & pip


