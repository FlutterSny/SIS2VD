import json
import os
from pathlib import Path
from PySide6.QtCore import QStandardPaths, QFile, QIODevice

class AppSettings:
    def __init__(self):
        # Get the application data location
        self.app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        self.settings_file = os.path.join(self.app_data_path, "settings.json")
        
        # Ensure the directory exists
        os.makedirs(self.app_data_path, exist_ok=True)
        
        # Initialize settings if they don't exist
        if not os.path.exists(self.settings_file):
            self._initialize_settings()

        # Cached ffmpeg path for this session
        self._cached_ffmpeg_path = None
    
    def _initialize_settings(self):
        """Initialize with default settings"""
        settings = {
            "language": "en",
            "onboarding_completed": False,
            "ffmpeg_path": ""
        }
        self._save_settings(settings)
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, return default settings
            self._initialize_settings()
            return {"language": "en", "onboarding_completed": False, "ffmpeg_path": ""}
    
    def _save_settings(self, settings):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_language(self):
        """Get the current language setting"""
        settings = self._load_settings()
        return settings.get("language", "en")
    
    def set_language(self, lang_code):
        """Set the language preference"""
        settings = self._load_settings()
        settings["language"] = lang_code
        self._save_settings(settings)
    
    def has_completed_onboarding(self):
        """Check if onboarding has been completed"""
        settings = self._load_settings()
        return settings.get("onboarding_completed", False)
    
    def set_onboarding_completed(self, value: bool = True):
        """Mark onboarding as completed"""
        settings = self._load_settings()
        settings["onboarding_completed"] = value
        self._save_settings(settings)

    def get_ffmpeg_path(self) -> str:
        """Get the stored FFmpeg binary path."""
        settings = self._load_settings()
        return settings.get("ffmpeg_path", "")

    def set_ffmpeg_path(self, path: str) -> None:
        """Store the resolved FFmpeg binary path."""
        settings = self._load_settings()
        settings["ffmpeg_path"] = path
        self._save_settings(settings)
        # Update session cache
        self._cached_ffmpeg_path = path

    def get_validated_ffmpeg_path(self) -> str | None:
        """
        Return the stored FFmpeg path only if it still points to a valid,
        executable file. Returns None if the stored path is empty or invalid,
        so the caller can fall back to re-detection.
        """
        # If we already validated this session, return cached result
        if self._cached_ffmpeg_path:
            return self._cached_ffmpeg_path

        stored = self.get_ffmpeg_path()
        if stored and Path(stored).is_file():
            self._cached_ffmpeg_path = stored
            return stored

        # Stored path is invalid or empty; clear it so detection re-runs
        return None
