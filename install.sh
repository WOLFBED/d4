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

#chmod +x zyngInstaller.py

# --- Run installer (auto-yes recommended to skip prompts) ---
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