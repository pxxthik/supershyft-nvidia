# config.py - Configuration settings for the booking system with location support and dynamic updates

import json
import os
from typing import List, Dict, Any

# Flask Configuration
SECRET_KEY = 'your-secret-key-change-this'  # Change this in production
ADMIN_PASSWORD = 'admin123'  # Change this to your desired password

# Configuration file path
CONFIG_FILE = 'dynamic_config.json'

# Default configuration values
DEFAULT_CONFIG = {
    # Location Configuration
    'locations': ['bangalore', 'gurugram', 'pune', 'hyderabad'],
    
    # Blood Test Configuration
    'blood_test_start_time': '09:00',
    'blood_test_end_time': '13:00',
    'blood_test_allowed_dates': ["2025-08-19", "2025-08-20", "2025-08-21", "2025-08-22"],
    'slot_duration_blood': 15,  # minutes
    'blood_test_cabins_count': 4,  # 4 cabins per location
    'people_per_blood_cabin': 4,   # 4 people per cabin per time slot
    
    # Consultation Configuration
    'consultation_start_time': '10:00',
    'consultation_end_time': '18:00',
    'slot_duration_consultation': 30,  # minutes
    'consultation_cabins_count': 4,    # 4 consultation cabins per location
    'people_per_consultation_cabin': 1,  # 1 person per cabin per time slot
    'consultation_allowed_dates': ["2025-08-25", "2025-08-26", "2025-08-28", "2025-08-29"],
}

# Database Configuration
DATABASE_NAME = 'bookings.db'


class ConfigManager:
    """Manages dynamic configuration with file persistence"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                return DEFAULT_CONFIG.copy()
        else:
            # Create file with defaults
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save to file"""
        self._config[key] = value
        self._save_config(self._config)
    
    def update_multiple(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values at once"""
        self._config.update(updates)
        self._save_config(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._config.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self._config = DEFAULT_CONFIG.copy()
        self._save_config(self._config)


# Global configuration manager instance
config_manager = ConfigManager()

# Export configuration values (for backward compatibility)
LOCATIONS = config_manager.get('locations')
BLOOD_TEST_START_TIME = config_manager.get('blood_test_start_time')
BLOOD_TEST_END_TIME = config_manager.get('blood_test_end_time')
BLOOD_TEST_ALLOWED_DATES = config_manager.get('blood_test_allowed_dates')
SLOT_DURATION_BLOOD = config_manager.get('slot_duration_blood')
BLOOD_TEST_CABINS_COUNT = config_manager.get('blood_test_cabins_count')
PEOPLE_PER_BLOOD_CABIN = config_manager.get('people_per_blood_cabin')

CONSULTATION_START_TIME = config_manager.get('consultation_start_time')
CONSULTATION_END_TIME = config_manager.get('consultation_end_time')
SLOT_DURATION_CONSULTATION = config_manager.get('slot_duration_consultation')
CONSULTATION_CABINS_COUNT = config_manager.get('consultation_cabins_count')
PEOPLE_PER_CONSULTATION_CABIN = config_manager.get('people_per_consultation_cabin')
CONSULTATION_ALLOWED_DATES = config_manager.get('consultation_allowed_dates')


def reload_config():
    """Reload configuration from file - call this after updates"""
    global LOCATIONS, BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, BLOOD_TEST_ALLOWED_DATES
    global SLOT_DURATION_BLOOD, BLOOD_TEST_CABINS_COUNT, PEOPLE_PER_BLOOD_CABIN
    global CONSULTATION_START_TIME, CONSULTATION_END_TIME, SLOT_DURATION_CONSULTATION
    global CONSULTATION_CABINS_COUNT, PEOPLE_PER_CONSULTATION_CABIN, CONSULTATION_ALLOWED_DATES
    
    config_manager._config = config_manager._load_config()
    
    LOCATIONS = config_manager.get('locations')
    BLOOD_TEST_START_TIME = config_manager.get('blood_test_start_time')
    BLOOD_TEST_END_TIME = config_manager.get('blood_test_end_time')
    BLOOD_TEST_ALLOWED_DATES = config_manager.get('blood_test_allowed_dates')
    SLOT_DURATION_BLOOD = config_manager.get('slot_duration_blood')
    BLOOD_TEST_CABINS_COUNT = config_manager.get('blood_test_cabins_count')
    PEOPLE_PER_BLOOD_CABIN = config_manager.get('people_per_blood_cabin')
    
    CONSULTATION_START_TIME = config_manager.get('consultation_start_time')
    CONSULTATION_END_TIME = config_manager.get('consultation_end_time')
    SLOT_DURATION_CONSULTATION = config_manager.get('slot_duration_consultation')
    CONSULTATION_CABINS_COUNT = config_manager.get('consultation_cabins_count')
    PEOPLE_PER_CONSULTATION_CABIN = config_manager.get('people_per_consultation_cabin')
    CONSULTATION_ALLOWED_DATES = config_manager.get('consultation_allowed_dates')
