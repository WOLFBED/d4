"""
Settings Manager - Handles persistent user configuration
"""
import json
from pathlib import Path
from typing import Any, Optional


class SettingsManager:
    """Manages application settings with JSON persistence"""

    DEFAULT_SETTINGS = {
        'output_path': str(Path.home() / 'Downloads'),
        'proxy': '',
        'cookies_file': '',
        'last_url': '',
    }

    def __init__(self, config_file: Path):
        """
        Initialize settings manager

        Args:
            config_file: Path to JSON config file
        """
        self.config_file = config_file
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings: {e}")
                # Keep defaults

    def save(self):
        """Save current settings to config file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Error: Could not save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value

    def get_all(self) -> dict:
        """Get all settings"""
        return self.settings.copy()

    def reset(self):
        """Reset to default settings"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()