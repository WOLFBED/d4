#!/usr/bin/env bash
set -e

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

echo "[*] Done."

#if [[ -d "d4" ]]; then
#    echo "[*] ~/Desktop/d4 already exists."
#    read -r -p "Delete it and continue? [y/N]: " RESP
#    case "$RESP" in
#        [yY]|[yY][eE][sS])
#            rm -rf d4
#            ;;
#        *)
#            echo "[*] Exiting installer to avoid overwriting existing directory."
#            exit 1
#            ;;
#    esac
#fi

echo "[*] d4 installer finished."

if [[ -d "$HOME/Desktop/d4" ]]; then
    echo
    read -r -p "Would you like to delete the (no longer required) ~/Desktop/d4 directory? [y/N]: " RESP
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