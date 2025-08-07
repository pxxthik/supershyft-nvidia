# config_validator.py - Utility to validate configuration changes

from datetime import datetime
from typing import Dict, List, Tuple, Any


class ConfigValidator:
    """Validates configuration changes before applying them"""
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time_range(start_time: str, end_time: str) -> bool:
        """Validate that start time is before end time"""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            return start < end
        except ValueError:
            return False
    
    @staticmethod
    def validate_positive_integer(value: Any, min_val: int = 1, max_val: int = None) -> bool:
        """Validate positive integer within range"""
        try:
            int_val = int(value)
            if int_val < min_val:
                return False
            if max_val and int_val > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_locations(locations: List[str]) -> Tuple[bool, str]:
        """Validate location list"""
        if not locations:
            return False, "At least one location is required"
        
        # Check for duplicates
        if len(locations) != len(set(locations)):
            return False, "Duplicate locations are not allowed"
        
        # Check for valid location names (alphanumeric and basic characters)
        for location in locations:
            if not location.strip():
                return False, "Empty location names are not allowed"
            
            if not location.replace('_', '').replace('-', '').replace(' ', '').isalnum():
                return False, f"Invalid location name: {location}"
        
        return True, ""
    
    @staticmethod
    def validate_dates_list(dates: List[str]) -> Tuple[bool, str]:
        """Validate dates list"""
        if not dates:
            return False, "At least one date is required"
        
        # Check for duplicates
        if len(dates) != len(set(dates)):
            return False, "Duplicate dates are not allowed"
        
        # Validate date formats
        for date_str in dates:
            if not ConfigValidator.validate_date_format(date_str):
                return False, f"Invalid date format: {date_str}"
        
        return True, ""
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate entire configuration
        
        Returns:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Validate locations
        if 'locations' in config:
            valid, error = cls.validate_locations(config['locations'])
            if not valid:
                errors.append(f"Locations: {error}")
        
        # Validate blood test configuration
        if 'blood_test_start_time' in config:
            if not cls.validate_time_format(config['blood_test_start_time']):
                errors.append("Invalid blood test start time format")
        
        if 'blood_test_end_time' in config:
            if not cls.validate_time_format(config['blood_test_end_time']):
                errors.append("Invalid blood test end time format")
        
        if ('blood_test_start_time' in config and 'blood_test_end_time' in config):
            if not cls.validate_time_range(config['blood_test_start_time'], config['blood_test_end_time']):
                errors.append("Blood test start time must be before end time")
        
        if 'slot_duration_blood' in config:
            if not cls.validate_positive_integer(config['slot_duration_blood'], 5, 120):
                errors.append("Blood test slot duration must be between 5-120 minutes")
        
        if 'blood_test_cabins_count' in config:
            if not cls.validate_positive_integer(config['blood_test_cabins_count'], 1, 20):
                errors.append("Blood test cabins count must be between 1-20")
        
        if 'people_per_blood_cabin' in config:
            if not cls.validate_positive_integer(config['people_per_blood_cabin'], 1, 10):
                errors.append("People per blood cabin must be between 1-10")
        
        if 'blood_test_allowed_dates' in config:
            valid, error = cls.validate_dates_list(config['blood_test_allowed_dates'])
            if not valid:
                errors.append(f"Blood test dates: {error}")
        
        # Validate consultation configuration
        if 'consultation_start_time' in config:
            if not cls.validate_time_format(config['consultation_start_time']):
                errors.append("Invalid consultation start time format")
        
        if 'consultation_end_time' in config:
            if not cls.validate_time_format(config['consultation_end_time']):
                errors.append("Invalid consultation end time format")
        
        if ('consultation_start_time' in config and 'consultation_end_time' in config):
            if not cls.validate_time_range(config['consultation_start_time'], config['consultation_end_time']):
                errors.append("Consultation start time must be before end time")
        
        if 'slot_duration_consultation' in config:
            if not cls.validate_positive_integer(config['slot_duration_consultation'], 15, 120):
                errors.append("Consultation slot duration must be between 15-120 minutes")
        
        if 'consultation_cabins_count' in config:
            if not cls.validate_positive_integer(config['consultation_cabins_count'], 1, 20):
                errors.append("Consultation cabins count must be between 1-20")
        
        if 'people_per_consultation_cabin' in config:
            if not cls.validate_positive_integer(config['people_per_consultation_cabin'], 1, 5):
                errors.append("People per consultation cabin must be between 1-5")
        
        if 'consultation_allowed_dates' in config:
            valid, error = cls.validate_dates_list(config['consultation_allowed_dates'])
            if not valid:
                errors.append(f"Consultation dates: {error}")
        
        return len(errors) == 0, errors
