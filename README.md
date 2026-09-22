# thumbnail-polaroid-folders

<img width="467" height="165" alt="2026-09-20_12-51" src="https://github.com/user-attachments/assets/ac8ae3a8-20a0-44f2-bda6-745640b05d55" />

A modular background thumbnail generator that turns your directory icons into dynamic 3D Polaroid-style cascades of the images, videos, gifs, and SVGs contained inside them.

Designed with a decoupled architecture, the heavy image processing engine is completely independent of the file manager, making it adaptable to multiple desktop environments.
Made for linux mint, nemo file explorer. I might add support for other file explorers in the future.

## AI Disclosure
This tool was completely made by AI, using google's Gemini 3.1 pro.

## Features
* Dynamically extracts thumbnails from Images, Videos (`ffmpeg`), gifs, and SVGs.
* Fetches natively cached Nemo thumbnails when available to save processing time.
* Transparent checkerboard backgrounds for PNGs and vector graphics.

## Architecture

* **`generator.py` (Universal Core):** A standalone Python script powered by Pillow and FFmpeg that handles the math, 3D slanting, checkerboard alpha mapping, and composite rendering. It can be run manually or integrated into any workflow.

* **`auto_3d_folder.py` (File Manager Wrapper):** A lightweight extension layer currently optimized for Nemo (Linux Mint / Cinnamon), handling background events and automated UI triggers.

## Prerequisites

Ensure you have the required system dependencies installed:

```
sudo apt update
sudo apt install ffmpeg imagemagick librsvg2-bin python3-venv python3-nemo

```

## Installation

1. Clone this repository:

```
git clone https://github.com/tzomby/thumbnail-polaroid-folders.git
cd thumbnail-polaroid-folders

```

2. Run the installer:

```
./install.sh

```

## How It Works

1. The background extension listens for directory changes in your file manager.

2. When a folder with media contents is accessed, it triggers `generator.py`.

3. The script scans up to 3 media files (images, videos, gifs, or SVGs), builds a 3D slanted Polaroid card stack, and caches the result locally.

4. The directory metadata is updated on the fly to display the preview.
