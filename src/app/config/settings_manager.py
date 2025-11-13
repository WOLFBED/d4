"""
Persistent settings management for the d4 application.
Stores user preferences in YAML format.
"""
import yaml
from pathlib import Path
from typing import Any, Dict


class SettingsManager:
    """Manages application settings with persistence."""

    def __init__(self):
        # Settings directory: ~/.config/d4/
        self.config_dir = Path.home() / ".config" / "d4"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "settings.yaml"
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self._get_default_settings()
        else:
            return self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Return default settings."""
        return {
            'output_path': str(Path.home() / "Downloads"),
            'proxy': '',
            'cookies_file': '',
            'write_thumbnail': True,
            'embed_thumbnail': True,
            'write_comments': False,
            'write_metadata': True,
            'write_subs': False,
            'split_chapters': False,
            'use_sponsorblock': False,
            'audio_only': False,
            'format': 'bestvideo+bestaudio/best',
            'last_url': '',
        }

    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.settings, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, key: str, default=None) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set a specific setting and save."""
        self.settings[key] = value
        self.save_settings()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()