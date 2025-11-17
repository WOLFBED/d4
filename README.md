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

### N.B. I'm currently working on making an AppImage for this, that will be way easier and cleaner to install.  The following only partially works and will dirty-up your system.  Avoid for now unless you really know what you're doing.
These commands take care of all the dependencies at once and install dealer to ~/zyng/apps/dealer/.  Be aware this *may* install on your system:
- git
- deno
- curl
- unzip
- python3.12-venv
- python3-pip
- ffmpeg

### Install - Arch based distros
Tested on Garuda, CachyOS, and Manjaro --> works great!
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py install.sh && ./install.sh
```

### Update - Arch based distros
Tested on Garuda, CachyOS, and Manjaro --> works great!
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
python zyngInstaller.py --config app_config.toml --skip-fonts --update-git
```

### Update - Arch based distros
Tested on Garuda, CachyOS, and Manjaro --> works great!
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4/ \
&& chmod +x zyngInstaller.py install.sh && ./install.sh
```

### For Ubunto based distros
Tested on Pop!_OS, TUXEDO OS, and Ubuntu.
```bash
# no success with these.  sorry.
```

### For Fedora based distros
Tested on Fedora KDE and Bazzite.
```bash
# no success with these.  sorry.
```

### For Suse based distros
Tested on OpenSUSE Tumbleweed.
```bash
# no success with these.  sorry.
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


