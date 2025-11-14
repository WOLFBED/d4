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

## Installation

1. open your terminal in your downloads directory (or wherever you prefer)
2. run:
```bash
git clone https://github.com/wolfbed/d4 && cd d4 && chmod +x zyngInstaller.py && python zyngInstaller.py --config app_config.toml
```
3. by default it will install to ~/zyng/apps/dealer/ which is okay.
4. if the above command gives you an error, try this instead:
```bash
git clone https://github.com/wolfbed/d4 && cd d4 && chmod +x zyngInstaller.py && python3 zyngInstaller.py --config app_config.toml
```
5. it should have created a link in your applications menu


## TODO

- [ ]  integrate aria2c
- [ ]  ???

## Requirements
- x86_64 linux 6+
- python 3.10+ & pip
- deno (youtube will not work well without it)
- aria2c (optional)
- ffmpeg (optional)
- Arch | Ubuntu | Suse | Fedora based distro
- git
- ~~rust~~ _(not yet needed)_
