# utils.py - Utility functions for date and time operations with dynamic location support

from datetime import datetime, timedelta, date
from typing import List
from functools import wraps
from flask import session, redirect, url_for
from config import config_manager


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_date(date_string: str) -> bool:
    """Check if the date string is valid and not in the past"""
    try:
        input_date = datetime.strptime(date_string, '%Y-%m-%d').date()
        today = date.today()
        return input_date >= today
    except ValueError:
        return False


def is_weekend(date_string: str) -> bool:
    """Check if the date falls on a weekend"""
    try:
        input_date = datetime.strptime(date_string, '%Y-%m-%d').date()
        return input_date.weekday() >= 5  # Saturday = 5, Sunday = 6
    except ValueError:
        return True  # If invalid date, treat as weekend (not available)


def generate_time_slots(start_time: str, end_time: str, duration: int) -> List[str]:
    """Generate time slots between start and end time with given duration"""
    slots = []
    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')
    
    current = start
    while current + timedelta(minutes=duration) <= end:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=duration)
    
    return slots


def validate_booking_data(form_data):
    """
    Validate booking form data with dynamic location support
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None, processed_data: dict)
    """
    try:
        # Extract required fields
        name = form_data.get('name')
        email = form_data.get('email')
        age = form_data.get('age')
        gender = form_data.get('gender')
        phone = form_data.get('phone')
        location = form_data.get('location')
        blood_test_date = form_data.get('blood_test_date')
        blood_test_time = form_data.get('blood_test_time')
        blood_test_cabin = form_data.get('blood_test_cabin')
        
        # Optional consultation fields
        consultation_date = form_data.get('consultation_date')
        consultation_time = form_data.get('consultation_time')
        
        # Validate required fields
        if not all([name, email, age, gender, phone, location]):
            return False, 'Please fill in all required fields', None
        
        # Validate location using dynamic configuration
        current_locations = config_manager.get('locations')
        if location not in current_locations:
            return False, 'Invalid location selected', None
        
        # Convert and validate numeric fields
        try:
            age = int(age)
        except ValueError:
            return False, 'Invalid age or cabin number', None
        
        # Validate blood test date
        if blood_test_date:
            blood_test_cabin = int(blood_test_cabin)

            if not is_valid_date(blood_test_date):
                return False, 'Invalid blood test date or date is in the past', None
        
        # Validate consultation date if provided
        if consultation_date and not is_valid_date(consultation_date):
            return False, 'Invalid consultation date or date is in the past', None
        
        # Prepare processed data
        processed_data = {
            'name': name,
            'email': email,
            'age': age,
            'gender': gender,
            'phone': phone,
            'location': location,
            'blood_test_date': blood_test_date,
            'blood_test_time': blood_test_time,
            'blood_test_cabin': blood_test_cabin,
            'consultation_date': consultation_date,
            'consultation_time': consultation_time
        }
        
        return True, None, processed_data
        
    except Exception as e:
        return False, f'Error validating data: {str(e)}', None
