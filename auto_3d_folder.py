import os
import hashlib
import subprocess
import threading
from urllib.parse import unquote
from gi.repository import Nemo, GObject, GLib

class Auto3DFolderExtension(GObject.GObject, Nemo.InfoProvider):
    def __init__(self):
        super().__init__()
        self.venv_python = os.path.expanduser("~/.local/share/nemo-3d-previews/venv/bin/python3")
        self.script_path = os.path.expanduser("~/.local/share/nemo-3d-previews/generator.py")
        self.cache_dir = os.path.expanduser("~/.cache/nemo-3d-previews")
        os.makedirs(self.cache_dir, exist_ok=True)

    def update_file_info(self, file):
        if not file.is_directory():
            return
        
        uri = file.get_uri()
        if not uri.startswith("file://"):
            return
            
        path = unquote(uri[7:])
        
        # Skip hidden directories and system directories
        if "/." in path or not path.startswith(os.path.expanduser("~")):
            return

        path_hash = hashlib.md5(path.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{path_hash}.png")

        try:
            dir_mtime = os.path.getmtime(path)
            if os.path.exists(cache_file):
                cache_mtime = os.path.getmtime(cache_file)
                if cache_mtime >= dir_mtime:
                    return
        except Exception:
            return

        # Touch the cache file immediately to prevent Nemo from triggering duplicate processes
        open(cache_file, 'a').close()
        os.utime(cache_file, None)

        def background_task():
            # Run the PIL processing script silently
            subprocess.run([self.venv_python, self.script_path, path, cache_file],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Queue a redraw command directly into Nemo's main UI thread
            GLib.idle_add(file.invalidate_extension_info)

        # Spawn the thread so Nemo's interface doesn't freeze while images process
        threading.Thread(target=background_task, daemon=True).start()
