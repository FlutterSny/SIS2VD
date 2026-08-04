"""
FFmpeg Locator - Detects and provides access to FFmpeg binary.

This module handles detection only. The download functionality has been
moved to the dedicated ffmpeg_downloader module.

Priority order (with persistence):
  1. Stored FFmpeg path from AppSettings (validated at each launch)
  2. Portable binary in app data directory (if already downloaded)
  3. System PATH ffmpeg (via shutil.which)
  4. None if neither exists

When a valid path is found, it is persisted to AppSettings so the next
launch can skip re-detection.
"""
import shutil
from pathlib import Path

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


# ── Lazy singleton for AppSettings ─────────────────────────────────────

def _settings():
    """Lazily import and return a single AppSettings instance."""
    # Lazy import to avoid circular dependency at module load time
    from src.app_settings import AppSettings
    return AppSettings()


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
      1. Stored path from AppSettings (validated; returns quickly if still valid)
      2. Portable binary (if already downloaded)
      3. System PATH ffmpeg
      4. None

    When a path is resolved (priority 2 or 3), it is persisted to
    AppSettings for the next launch.
    """
    # Priority 1: stored and validated path
    settings = _settings()
    stored = settings.get_validated_ffmpeg_path()
    if stored:
        return stored

    # Priority 2: portable binary in app data dir
    portable = get_portable_ffmpeg_path()
    if portable:
        resolved = str(portable)
        settings.set_ffmpeg_path(resolved)
        return resolved

    # Priority 3: system PATH ffmpeg
    system = check_system_ffmpeg()
    if system:
        settings.set_ffmpeg_path(system)
        return system

    # Priority 4: nothing found
    return None


def clear_stored_ffmpeg_path() -> None:
    """Clear the stored FFmpeg path so detection re-runs next time."""
    _settings().set_ffmpeg_path("")
