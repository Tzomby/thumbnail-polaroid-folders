#!/usr/bin/env python3
import sys, os, subprocess, tempfile, hashlib
from urllib.parse import quote
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ICON_SIZE = 256
MAX_THUMBNAILS = 3
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
SVG_EXTS = {'.svg'}

def create_checkerboard(w, h, size=8):
    cb = Image.new('RGBA', (w, h), (210, 210, 210, 255))
    draw = ImageDraw.Draw(cb)
    gray = (170, 170, 170, 255)
    for y in range(0, h, size):
        for x in range(0, w, size):
            if (x // size + y // size) % 2 == 1:
                draw.rectangle([x, y, x + size - 1, y + size - 1], fill=gray)
    return cb

def apply_3d_slant(image_path, target_w, target_h, scale_x, slant_y):
    img = Image.open(image_path)
    
    has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
    img = img.convert('RGBA')
    
    pad_x = 4
    pad_top = 4
    pad_bottom = 16
    
    inner_w = target_w - (pad_x * 2)
    inner_h = target_h - pad_top - pad_bottom
    
    cropped = ImageOps.fit(img, (inner_w, inner_h), method=Image.Resampling.LANCZOS)
    
    polaroid = Image.new('RGBA', (target_w, target_h), (250, 250, 250, 255))
    draw = ImageDraw.Draw(polaroid)
    draw.rectangle([(0, 0), (target_w - 1, target_h - 1)], outline=(200, 200, 200, 255), width=1)
    
    if has_alpha:
        cb = create_checkerboard(inner_w, inner_h)
        polaroid.paste(cb, (pad_x, pad_top))
        polaroid.paste(cropped, (pad_x, pad_top), cropped)
    else:
        polaroid.paste(cropped, (pad_x, pad_top))
    
    out_w = max(1, int(target_w * scale_x))
    out_h = target_h + slant_y
    
    a = target_w / out_w
    b = 0, 0
    d = -slant_y / out_w
    e = 1.0
    f = 0
    
    return polaroid.transform(
        (out_w, out_h), Image.AFFINE, (a, b[0], b[1], d, e, f),
        resample=Image.BICUBIC, fillcolor=(0,0,0,0)
    )

def get_slot_positions(num_slots):
    w, h = 175, 130
    scale_x, slant = 0.75, 45       
    
    if num_slots == 1: return [(40, 60, w, h, 255, scale_x, slant)]
    if num_slots == 2: return [(100, 50, w, h, 255, scale_x, slant), (15, 75, w, h, 255, scale_x, slant)]
    if num_slots == 3: return [(125, 45, w, h, 255, scale_x, slant), (62, 60, w, h, 255, scale_x, slant), (0, 75, w, h, 255, scale_x, slant)]
    return []

def extract_thumbnail(file_path):
    abs_path = os.path.abspath(file_path)
    uri = f"file://{quote(abs_path)}"
    uri_hash = hashlib.md5(uri.encode('utf-8')).hexdigest()
    
    for size in ['large', 'normal']:
        cached_thumb = os.path.expanduser(f'~/.cache/thumbnails/{size}/{uri_hash}.png')
        if os.path.exists(cached_thumb):
            return cached_thumb, False

    ext = Path(file_path).suffix.lower()
    try:
        fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
        if ext in VIDEO_EXTS:
            subprocess.run(['ffmpeg', '-y', '-i', str(file_path), '-ss', '00:00:01', '-vframes', '1',
                           '-q:v', '2', temp_path], check=True, capture_output=True, timeout=30)
        elif ext in SVG_EXTS:
            try: subprocess.run(['rsvg-convert', '-w', '512', str(file_path), '-o', temp_path], check=True, capture_output=True, timeout=10)
            except FileNotFoundError: subprocess.run(['convert', '-background', 'none', str(file_path), temp_path], check=True, capture_output=True, timeout=10)
                               
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            return temp_path, True
        return None, False
    except Exception:
        return None, False

def discover_media_files(folder_path, limit=MAX_THUMBNAILS):
    path = Path(folder_path)
    files = []
    try:
        for item in sorted(path.iterdir()):
            if not item.is_file() or item.name.startswith('.'): continue
            if item.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS | SVG_EXTS:
                files.append(item)
                if len(files) >= limit: break
    except Exception: pass
    return files

def compose_folder_icon(thumbnails, requested_slots=3):
    icon = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    actual_slots = min(len(thumbnails), requested_slots)
    slots = get_slot_positions(actual_slots)
    thumbs_to_draw = list(reversed(thumbnails[:actual_slots]))
    
    for i, thumb_path in enumerate(thumbs_to_draw):
        if not os.path.exists(thumb_path): continue
        slot_x, slot_y, slot_w, slot_h, opacity, scale_x, slant_y = slots[i]
        
        try:
            slanted_img = apply_3d_slant(thumb_path, slot_w, slot_h, scale_x, slant_y)
            if opacity < 255:
                r, g, b, a = slanted_img.split()
                a = a.point(lambda p: int(p * opacity / 255))
                slanted_img = Image.merge('RGBA', (r, g, b, a))
            icon.alpha_composite(slanted_img, (slot_x, slot_y))
        except Exception: pass
    return icon

def reset_and_refresh(folder_path, cache_file):
    import time
    subprocess.run(['gio', 'set', '-t', 'unset', folder_path, 'metadata::custom-icon'])
    if os.path.exists(cache_file):
        try: os.remove(cache_file)
        except: pass
    try:
        now = time.time()
        os.utime(folder_path, (now, now))
    except: pass

def main():
    import time
    if len(sys.argv) < 3: sys.exit(1)
        
    folder_path = sys.argv[1]
    cache_file = sys.argv[2]
    
    media_files = discover_media_files(folder_path)
    if not media_files:
        reset_and_refresh(folder_path, cache_file)
        sys.exit(0)
        
    thumbs, temps = [], []
    for mf in media_files:
        ext = mf.suffix.lower()
        if ext in VIDEO_EXTS or ext in SVG_EXTS:
            frame, is_temp = extract_thumbnail(mf)
            if frame:
                thumbs.append(frame)
                if is_temp: temps.append(frame)
        else: thumbs.append(str(mf))
            
    if not thumbs:
        reset_and_refresh(folder_path, cache_file)
        sys.exit(1)
        
    icon = compose_folder_icon(thumbs, requested_slots=3)
    icon.save(cache_file, 'PNG')
    
    subprocess.run(['gio', 'set', folder_path, 'metadata::custom-icon', f"file://{cache_file}"])
        
    # Touch the parent directory to force Nemo's active view to redraw immediately
    parent_dir = os.path.dirname(folder_path)
    try:
        now = time.time()
        os.utime(parent_dir, (now, now))
        os.utime(cache_file, (now + 2, now + 2))
    except:
        try: os.utime(cache_file, None)
        except: pass
        
    for t in temps:
        try: os.remove(t)
        except: pass

    # Nudge the folder timestamp to broadcast an inotify event, forcing Nemo to redraw
    try:
        now = time.time()
        os.utime(folder_path, (now, now))
        # Ensure the cache file timestamp sits 2 seconds in the future to prevent the Nemo extension from looping
        os.utime(cache_file, (now + 2, now + 2))
    except:
        try: os.utime(cache_file, None)
        except: pass
        
    for t in temps:
        try: os.remove(t)
        except: pass

if __name__ == '__main__':
    main()
