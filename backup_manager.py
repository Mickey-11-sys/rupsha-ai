
"""
backup_manager.py
Google Drive backup for Google Colab. Silently skips if not in Colab.
"""

import os
import shutil
import threading
import time

# Try to import Colab-specific libraries
try:
    from google.colab import drive
    COLAB_AVAILABLE = True
except ImportError:
    COLAB_AVAILABLE = False

# Paths
LOCAL_DB = os.path.join("RUPSHA", "rupsha_memory.db")
LOCAL_VECTOR_DB = os.path.join("RUPSHA", "data", "vector_db")
DRIVE_BACKUP_DIR = "/content/drive/MyDrive/RUPSHA"
DRIVE_DB = os.path.join(DRIVE_BACKUP_DIR, "rupsha_memory.db")
DRIVE_VECTOR_ZIP = os.path.join(DRIVE_BACKUP_DIR, "vector_db_backup.zip")

_auto_save_timer = None
_auto_save_running = False

def _ensure_drive_mounted():
    if not COLAB_AVAILABLE:
        return False
    if not os.path.exists("/content/drive/MyDrive"):
        print("Mounting Google Drive...")
        drive.mount('/content/drive')
    os.makedirs(DRIVE_BACKUP_DIR, exist_ok=True)
    return True

def save_all(verbose=True):
    if not COLAB_AVAILABLE:
        if verbose:
            print("Google Drive backup only works in Colab.")
        return

    if not _ensure_drive_mounted():
        return

    if os.path.exists(LOCAL_DB):
        shutil.copy2(LOCAL_DB, DRIVE_DB)
        if verbose:
            size = os.path.getsize(DRIVE_DB) / 1024
            print(f"SQLite saved to Drive ({size:.1f} KB)")

    if os.path.exists(LOCAL_VECTOR_DB):
        if os.path.exists(DRIVE_VECTOR_ZIP):
            os.remove(DRIVE_VECTOR_ZIP)
        shutil.make_archive(DRIVE_VECTOR_ZIP.replace(".zip", ""), 'zip', LOCAL_VECTOR_DB)
        if verbose:
            size = os.path.getsize(DRIVE_VECTOR_ZIP) / 1024
            print(f"Vector DB saved to Drive ({size:.1f} KB)")

    if verbose:
        print("All memories safely backed up.")

def restore_all(verbose=True):
    if not COLAB_AVAILABLE:
        if verbose:
            print("Not in Colab — skipping Drive restore.")
        return []

    if not _ensure_drive_mounted():
        return []

    restored = []

    if os.path.exists(DRIVE_DB):
        os.makedirs(os.path.dirname(LOCAL_DB), exist_ok=True)
        shutil.copy2(DRIVE_DB, LOCAL_DB)
        size = os.path.getsize(LOCAL_DB) / 1024
        if verbose:
            print(f"SQLite restored ({size:.1f} KB)")
        restored.append("sqlite")

    if os.path.exists(DRIVE_VECTOR_ZIP):
        if os.path.exists(LOCAL_VECTOR_DB):
            shutil.rmtree(LOCAL_VECTOR_DB)
        os.makedirs(LOCAL_VECTOR_DB, exist_ok=True)
        shutil.unpack_archive(DRIVE_VECTOR_ZIP, LOCAL_VECTOR_DB)
        if verbose:
            print("Vector DB restored from Drive.")
        restored.append("vector")

    return restored

def _auto_save_loop(interval_seconds):
    global _auto_save_running, _auto_save_timer
    if not _auto_save_running or not COLAB_AVAILABLE:
        return
    try:
        save_all(verbose=False)
        print(f"[Auto-Save] {time.strftime('%H:%M:%S')} — Both databases saved.")
    except Exception as e:
        print(f"[Auto-Save Error] {e}")

    _auto_save_timer = threading.Timer(interval_seconds, _auto_save_loop, args=(interval_seconds,))
    _auto_save_timer.daemon = True
    _auto_save_timer.start()

def start_auto_save(interval_minutes=10):
    global _auto_save_running, _auto_save_timer
    if not COLAB_AVAILABLE:
        print("Auto-save only works in Google Colab.")
        return
    if _auto_save_running:
        print("Auto-save already running.")
        return
    interval_seconds = interval_minutes * 60
    _auto_save_running = True
    print(f"Auto-save started: every {interval_minutes} minute(s).")
    _auto_save_loop(interval_seconds)

def stop_auto_save():
    global _auto_save_running, _auto_save_timer
    _auto_save_running = False
    if _auto_save_timer:
        _auto_save_timer.cancel()
        _auto_save_timer = None
    print("Auto-save stopped.")

def status():
    if not COLAB_AVAILABLE:
        print("Backup manager: Colab not detected.")
        return
    _ensure_drive_mounted()
    print("=" * 42)
    print("         RUPSHA BACKUP STATUS")
    print("=" * 42)
    for label, path in [("Local SQLite", LOCAL_DB), ("Local Vector", LOCAL_VECTOR_DB),
                        ("Drive SQLite", DRIVE_DB), ("Drive Vector", DRIVE_VECTOR_ZIP)]:
        if os.path.exists(path):
            if os.path.isfile(path):
                size = os.path.getsize(path) / 1024
                print(f"{label:14s} {size:>8.1f} KB")
            else:
                total = sum(os.path.getsize(os.path.join(d, f)) for d, _, files in os.walk(path) for f in files)
                print(f"{label:14s} {total/1024:>8.1f} KB")
        else:
            print(f"{label:14s}      MISSING")
    print("-" * 42)
    state = "RUNNING" if _auto_save_running else "STOPPED"
    print(f"Auto-save:      {state:>8}")
    print("=" * 42)
