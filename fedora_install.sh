#!/usr/bin/env bash
set -euo pipefail

installer_dir=dealer_install

# --- Fedora prerequisites ---
sudo dnf install -y git python3.12-venv python3-pip ffmpeg

# --- Install Deno (optional dependency you had in your original commands) ---
curl -fsSL https://deno.land/install.sh | sh

# --- Prepare workspace ---
cd "$HOME/Desktop/"
mkdir -p $installer_dir
cd $installer_dir

# --- Download your modified installer + config ---
#curl -L -o app_config.toml https://raw.githubusercontent.com/WOLFBED/d4/refs/heads/master/app_config.toml
curl -L https://github.com/WOLFBED/d4/archive/refs/tags/tempo.zip -o dealer.zip && \
unzip dealer.zip
cd dealer

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

chmod +x zyngInstaller.py

# --- Run installer (auto-yes recommended to skip prompts) ---
python3 zyngInstaller.py --config app_config.toml

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

##!/usr/bin/env bash
#set -e
#
#DENO_BIN="$HOME/.deno/bin"
#
#echo "[*] Checking PATH for Deno…"
#if [[ ":$PATH:" != *":$DENO_BIN:"* ]]; then
#    echo "[*] Adding Deno to PATH…"
#    echo 'export PATH="$HOME/.deno/bin:$PATH"' >> "$HOME/.bashrc"
#    echo 'export PATH="$HOME/.deno/bin:$PATH"' >> "$HOME/.zshrc"
#fi
#
#echo "[*] Reloading shell configuration…"
#if [[ -n "$BASH_VERSION" ]]; then
#    source "$HOME/.bashrc"
#elif [[ -n "$ZSH_VERSION" ]]; then
#    source "$HOME/.zshrc"
#fi
#
#echo "[*] Verifying Deno installation…"
#deno --version
#
#echo "[*] Continuing with d4 setup…"
#
#python zyngInstaller.py --config app_config.toml
#
#echo "[*] d4 installer finished."
#
#if [[ -d "$HOME/Desktop/d4" ]]; then
#    echo
#    read -r -p "Would you like to delete the (no longer required) ~/Desktop/d4 directory? [y/N]: " RESP
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
