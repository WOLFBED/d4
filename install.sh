#!/usr/bin/env bash
# this for arch-based: garuda, manjaro, cachyos
set -euo pipefail

installer_dir="d4"

# --- Prepare workspace ---
#cd "$HOME/Desktop/"
#mkdir -p $installer_dir
#installer_dir = "$HOME/Desktop/$installer_dir"
#cd $installer_dir

# Path to the TOML file
TOML_FILE="app_config.toml"

## Function: get_value <key>
#get_value() {
#    local key="$1"
#    grep -E "^${key} = " "$TOML_FILE" \
#        | sed -E 's/^[^=]+= *"(.*)"/\1/'
#}
#
#installer_dir=$(get_value "installer_dir")
#
##echo "installer_dir = $installer_dir"

#
## --- Download your modified installer + config ---
#curl -L -o zyngInstaller.py https://raw.githubusercontent.com/WOLFBED/d4/main/zyngInstaller.py
#curl -L -o app_config.toml       https://raw.githubusercontent.com/WOLFBED/d4/main/app_config.toml


#certifi* - Provides Mozilla's root certificate bundle. Licensed under MPLv2
#https://github.com/certifi/python-certifi
#
#brotli* or brotlicffi - Brotli content encoding support. Both licensed under MIT 1 2
#https://github.com/google/brotli
#
#websockets* - For downloading over websocket. Licensed under BSD-3-Clause
#https://github.com/aaugustin/websockets
#
#requests* - HTTP library. For HTTPS proxy and persistent connections support. Licensed under Apache-2.0
#https://github.com/psf/requests
#
#curl_cffi (recommended) - Python binding for curl-impersonate. Provides impersonation targets for Chrome, Edge and Safari. Licensed under MIT
#    Can be installed with the curl-cffi group, e.g. pip install "yt-dlp[default,curl-cffi]"
#    Currently included in most builds except yt-dlp (Unix zipimport binary), yt-dlp_x86 (Windows 32-bit) and yt-dlp_musllinux_aarch64
#https://github.com/lexiforest/curl_cffi
#
#mutagen* - For --embed-thumbnail in certain formats. Licensed under GPLv2+
#https://github.com/quodlibet/mutagen
#
#AtomicParsley - For --embed-thumbnail in mp4/m4a files when mutagen/ffmpeg cannot. Licensed under GPLv2+
#https://github.com/wez/atomicparsley
#
#xattr, pyxattr or setfattr - For writing xattr metadata (--xattrs) on Mac and BSD. Licensed under MIT, LGPL2.1 and GPLv2+ respectively
#https://github.com/xattr/xattr
#
#pycryptodomex* - For decrypting AES-128 HLS streams and various other data. Licensed under BSD-2-Clause
#https://github.com/Legrandin/pycryptodome
#
#phantomjs - Used in some extractors where JavaScript needs to be run. No longer used for YouTube. To be deprecated in the near future. Licensed under BSD-3-Clause
# *** phantomjs is defunct ***
#https://github.com/ariya/phantomjs
#
#secretstorage* - For --cookies-from-browser to access the Gnome keyring while decrypting cookies of Chromium-based browsers on Linux. Licensed under BSD-3-Clause
# *** NOT CURRENTLY USING THIS ***
#https://github.com/mitya57/secretstorage
#




echo "[+] Installing dependencies…"
sudo pacman -S --noconfirm \
    git curl unzip ffmpeg python python-pip python-virtualenv python-mutagen deno brotli atomicparsley python-xattr python-pycryptodome
yay -S phantomjs --noconfirm --nodiffmenu --noeditmenu --nocleanmenu


# --- Run installer (auto-yes recommended to skip prompts) ---
echo "[+] Running Zyng installer…"
python zyngInstaller.py --config app_config.toml --skip-fonts

echo "[*] d4 installer finished."

if [[ -d "$HOME/Desktop/$installer_dir" ]]; then
    echo
    read -r -p "Would you like to delete the temporary directory? [y/N]: " RESP
    case "$RESP" in
        [yY]|[yY][eE][sS])
            echo "[*] Removing directory…"
            rm -rf "$HOME/Desktop/$installer_dir"
            echo "[*] Cleanup complete."
            ;;
        *)
            echo "[*] Leaving directory intact."
            ;;
    esac
fi































#
#
#set -euo pipefail
#
#echo "[+] Updating Arch system packages…"
#sudo pacman -Syu --noconfirm
#
#echo "[+] Installing dependencies…"
#sudo pacman -S --noconfirm \
#    git curl unzip ffmpeg python python-pip python-virtualenv deno
#
#echo "[+] Running Zyng installer…"
#python3 zyngInstaller.py
#
#echo "[*] d4 installer finished."
#
#if [[ -d "$HOME/Desktop/d4" ]]; then
#    echo
#    read -r -p "Would you like to delete the temporary ~/Desktop/d4 directory? [y/N]: " RESP
#    case "$RESP" in
#        [yY]|[yY][eE][sS])
#            echo "[*] Removing directory…"
#            rm -rf "$HOME/Desktop/d4"
#            echo "[*] Cleanup complete."
#            ;;
#        *)
#            echo "[*] Leaving directory intact."
#            ;;
#    esac
#fi