"""
FFmpeg Locator - Detects and provides access to FFmpeg binary.

This module handles detection only. The download functionality has been
moved to the dedicated ffmpeg_downloader module.

Priority order:
  1. Portable binary in app data directory (if already downloaded)
  2. System PATH ffmpeg (via shutil.which)
  3. None if neither exists
"""
import shutil
from pathlib import Path
from PySide6.QtCore import QStandardPaths

# Re-export downloader components for convenience
from src.ffmpeg_downloader import (
    FFmpegDownloadWorker,
    app_data_path,
    ffmpeg_data_dir,
    get_download_url,
    is_download_supported,
)


# ── Constants ───────────────────────────────────────────────────────────

# Directory name inside AppDataLocation where portable FFmpeg is stored
_FFMPEG_DIR_NAME = "ffmpeg"
_FFMPEG_BINARY_NAME = "ffmpeg.exe" if __import__("platform").system() == "Windows" else "ffmpeg"


# ── Helper: app data path ──────────────────────────────────────────────

def _ffmpeg_data_dir() -> Path:
    """Return the FFmpeg data directory (delegates to downloader module)."""
    return ffmpeg_data_dir()


def get_portable_ffmpeg_path() -> Path | None:
    """
    Return the portable FFmpeg binary path if it already exists in the
    app data directory, else None.
    """
    binary = _ffmpeg_data_dir() / _FFMPEG_BINARY_NAME
    return binary if binary.is_file() else None


# ── System PATH check ─────────────────────────────────────────────────

def check_system_ffmpeg() -> str | None:
    """
    Look for 'ffmpeg' in the system PATH via shutil.which.
    Returns the absolute path string if found, else None.
    """
    return shutil.which("ffmpeg")


# ── Main entry point ──────────────────────────────────────────────────

def get_ffmpeg_path() -> str | None:
    """
    Return the FFmpeg binary path to use, in priority order:
      1. Portable binary (if already downloaded)
      2. System PATH ffmpeg
      3. None
    """
    # Priority 1: portable
    portable = get_portable_ffmpeg_path()
    if portable:
        return str(portable)

    # Priority 2: system PATH
    system = check_system_ffmpeg()
    if system:
        return system

    # Priority 3: nothing
    return None