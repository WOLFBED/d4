![image](/data/images/site_banner.avif)

# d4 - Video Downloader

### dealer version 4 ~ includes GUI

A modern, user-friendly video downloader application.

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

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## TODO

- [ ]  integrate aria2c
- [ ]  ???

## Requirements- Python 3.10+
- linux 6+
- python 3.10+
- deno (youtube will not work well without it)
- aria2c (optional)
- ffmpeg (optional)