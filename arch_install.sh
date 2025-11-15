#!/usr/bin/env bash
set -e

echo "[*] Updating system…"
#sudo pacman -Syu --noconfirm
sudo pacman -Syu

echo "[*] Installing packages…"
sudo pacman -S git curl unzip base-devel
#sudo pacman -S --noconfirm git curl unzip base-devel

echo "[*] Installing Deno…"
curl -fsSL https://deno.land/install.sh | sh

DENO_BIN="$HOME/.deno/bin"

echo "[*] Checking PATH for Deno…"
if [[ ":$PATH:" != *":$DENO_BIN:"* ]]; then
    echo "[*] Adding Deno to PATH…"
    echo 'export PATH="$HOME/.deno/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.deno/bin:$PATH"' >> "$HOME/.zshrc"
fi

echo "[*] Reloading shell configuration…"
if [[ -n "$BASH_VERSION" ]]; then
    source "$HOME/.bashrc"
elif [[ -n "$ZSH_VERSION" ]]; then
    source "$HOME/.zshrc"
fi

echo "[*] Verifying Deno installation…"
deno --version

echo "[*] Continuing with d4 setup…"

chmod +x zyngInstaller.py && \
python zyngInstaller.py --config app_config.toml

echo "[*] d4 installer finished."

if [[ -d "$HOME/Desktop/d4" ]]; then
    echo
    read -r -p "Would you like to delete the ~/Desktop/d4 directory? [y/N]: " RESP
    case "$RESP" in
        [yY]|[yY][eE][sS])
            echo "[*] Removing directory…"
            rm -rf "$HOME/Desktop/d4"
            echo "[*] Cleanup complete."
            ;;
        *)
            echo "[*] Leaving directory intact."
            ;;
    esac
fi