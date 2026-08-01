import json
import os
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
    
    def _initialize_settings(self):
        """Initialize with default settings"""
        settings = {
            "language": "en",
            "onboarding_completed": False
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
            return {"language": "en", "onboarding_completed": False}
    
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
    
    def set_onboarding_completed(self):
        """Mark onboarding as completed"""
        settings = self._load_settings()
        settings["onboarding_completed"] = True
        self._save_settings(settings)