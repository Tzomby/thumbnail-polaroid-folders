#!/bin/bash

echo "Installing Nemo 3D Folder Previews (Native Extension)..."

# Install Nemo Python bindings
echo "Requesting sudo privileges to install python3-nemo..."
sudo apt-get update
sudo apt-get install -y python3-nemo python3-venv

INSTALL_DIR="$HOME/.local/share/nemo-3d-previews"
EXT_DIR="$HOME/.local/share/nemo-python/extensions"
CACHE_DIR="$HOME/.cache/nemo-3d-previews"

mkdir -p "$INSTALL_DIR"
mkdir -p "$EXT_DIR"
mkdir -p "$CACHE_DIR"

# Copy files
cp generator.py "$INSTALL_DIR/"
cp auto_3d_folder.py "$EXT_DIR/"
chmod +x "$INSTALL_DIR/generator.py"

echo "Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install Pillow

echo "Restarting Nemo..."
nemo -q
nemo -n &
echo "Installation complete. Scroll through your folders to watch them generate!"
