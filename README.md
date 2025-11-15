![image](/data/images/site_banner.avif)

# d4 - Video Downloader

dealer version 4 ~ includes GUI -- A modern, user-friendly video downloader application.

# NOTE: NO WARRANTY PROVIDED AT ALL.  DO NOT USE FOR ANY PURPOSE!!!

## Features

- Download videos from various platforms, loads
- Batch download support
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
- Multi-threaded downloads with progress tracking
- Automatic dependency management (yt-dlp, aria2)

## Installation (work in progress)
These commands take care of all the dependencies at once and install dealer to ~/zyng/apps/dealer/.

### For Arch based distros
Tested on Garuda, CachyOS, and Manjaro.
```bash
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4 && \
chmod +x zyngInstaller.py arch_install.sh && \
./arch_install.sh
```

### For Ubunto based distros
Tested on Pop!_OS, TUXEDO OS, and Ubuntu.
```bash
sudo apt update && \
sudo apt install -y git curl unzip && \
curl -fsSL https://deno.land/install.sh | sh && \
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4 && \
chmod +x zyngInstaller.py ubuntu_install.sh && \
./ubuntu_install.sh
```

### For Fedora based distros
Tested on Fedora KDE and Bazzite.
```bash
sudo dnf update && \
sudo dnf install -y git curl unzip && \
curl -fsSL https://deno.land/install.sh | sh && \
cd "$HOME/Desktop" && git clone https://github.com/wolfbed/d4 && cd d4 && \
chmod +x zyngInstaller.py fedora_install.sh && \
./fedora_install.sh
```

### For Suse based distros
Tested on OpenSUSE Tumbleweed.
```bash
sudo zypper refresh && \
sudo zypper install -y git curl unzip && \
curl -fsSL https://deno.land/install.sh | sh && \
git clone https://github.com/wolfbed/d4 && \ cd d4 && \ 
chmod +x zyngInstaller.py suse_install.sh && \
./suse_install.sh
```

## TODO

- [ ]  integrate aria2c
- [ ]  ???

## Requirements
- x86_64 linux 6+
- python 3.10+ & pip
- deno (youtube will not work well without it)
- aria2c (optional)
- ffmpeg (optional)
- git
- ~~rust~~ _(not yet needed)_

tested on:
Fedora KDE 43 -- !! zyngInstaller doesn't work on this one - couldn't install deno !!
Manjaro Cinammon 25.0.3
Pop!_OS 22.04 LTS -- !! zyngInstaller doesn't work on this one - couldn't install deno !!
TUXEDO OS 2025-11-06-1317
Ubuntu 24.04.3 -- !! zyngInstaller doesn't work on this one - couldn't install deno !!
