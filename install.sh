#!/usr/bin/env bash
set -e

APP_NAME="MyApp"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_NAME.desktop"
VENV_DIR="$INSTALL_DIR/venv"

# --- Detect distribution ---
if [ -f /etc/arch-release ]; then
    PKG_MANAGER="sudo pacman -S --needed"
    DISTRO="Arch"
elif [ -f /etc/debian_version ]; then
    PKG_MANAGER="sudo apt install -y"
    DISTRO="Debian"
elif [ -f /etc/redhat-release ]; then
    PKG_MANAGER="sudo dnf install -y"
    DISTRO="RedHat"
else
    echo "Unsupported distribution"
    exit 1
fi

echo "Detected $DISTRO-based system."

# --- Check for Python ---
if ! command -v python3 &>/dev/null; then
    echo "Python3 not found. Installing..."
    $PKG_MANAGER python3 python3-venv python3-pip
fi

# --- Create install dir and venv ---
mkdir -p "$INSTALL_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# --- Install Python deps ---
pip install --upgrade pip
pip install -r requirements.txt

# --- Check external dependencies ---
python3 setup_env.py check_system_reqs || {
    echo "Some system dependencies are missing."
    read -p "Install them using $DISTRO package manager? [Y/n] " answer
    case $answer in
        [Yy]* ) python3 setup_env.py install_system_reqs ;;
        * ) echo "Skipping system packages." ;;
    esac
}

# --- Create desktop entry ---
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=$VENV_DIR/bin/python -m app.main
Icon=$INSTALL_DIR/resources/icons/app.png
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"
update-desktop-database ~/.local/share/applications/ || true

echo "$APP_NAME installed successfully."
