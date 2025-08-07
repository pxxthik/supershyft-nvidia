# booking_service.py - Business logic for booking availability and management with dynamic configuration

from typing import Dict, List
from database import get_db_connection
from utils import generate_time_slots, is_valid_date
from config import config_manager


class BloodTestService:
    """Service class for blood test booking operations with dynamic configuration support"""
    
    @staticmethod
    def get_cabin_availability(date: str, location: str) -> Dict:
        """Get available slots per cabin for blood tests on a given date and location"""
        if not is_valid_date(date):
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get dynamic configuration values
        start_time = config_manager.get('blood_test_start_time')
        end_time = config_manager.get('blood_test_end_time')
        slot_duration = config_manager.get('slot_duration_blood')
        cabins_count = config_manager.get('blood_test_cabins_count')
        people_per_cabin = config_manager.get('people_per_blood_cabin')
        
        # Get total time slots available for the day
        total_slots = len(generate_time_slots(start_time, end_time, slot_duration))
        
        # Get booked slots per cabin for specific location
        cursor.execute('''
            SELECT blood_test_cabin, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin IS NOT NULL AND location = ?
            GROUP BY blood_test_cabin
        ''', (date, location))
        
        booked_per_cabin = dict(cursor.fetchall())
        
        # Calculate available slots per cabin
        cabin_availability = {}
        for cabin in range(1, cabins_count + 1):
            booked_count = booked_per_cabin.get(cabin, 0)
            available_slots = (total_slots * people_per_cabin) - booked_count
            cabin_availability[cabin] = max(0, available_slots)
        
        conn.close()
        return cabin_availability
    
    @staticmethod
    def get_available_slots(date: str, cabin: int, location: str) -> List[str]:
        """Get available time slots for a specific cabin on a given date and location"""
        if not is_valid_date(date):
            return []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get dynamic configuration values
        start_time = config_manager.get('blood_test_start_time')
        end_time = config_manager.get('blood_test_end_time')
        slot_duration = config_manager.get('slot_duration_blood')
        people_per_cabin = config_manager.get('people_per_blood_cabin')
        
        # Get all possible time slots
        all_slots = generate_time_slots(start_time, end_time, slot_duration)
        
        # Get booked slots for this cabin and location
        cursor.execute('''
            SELECT blood_test_time, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin = ? AND location = ?
            GROUP BY blood_test_time
        ''', (date, cabin, location))
        
        booked_slots = dict(cursor.fetchall())
        
        # Filter available slots
        available_slots = []
        for slot in all_slots:
            booked_count = booked_slots.get(slot, 0)
            if booked_count < people_per_cabin:
                available_slots.append(slot)
        
        conn.close()
        return available_slots
    
    @staticmethod
    def get_slots_with_availability(date: str, cabin: int, location: str) -> Dict[str, int]:
        """Get time slots with availability count for a specific cabin on a given date and location"""
        if not is_valid_date(date):
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get dynamic configuration values
        start_time = config_manager.get('blood_test_start_time')
        end_time = config_manager.get('blood_test_end_time')
        slot_duration = config_manager.get('slot_duration_blood')
        people_per_cabin = config_manager.get('people_per_blood_cabin')
        
        # Get all possible time slots
        all_slots = generate_time_slots(start_time, end_time, slot_duration)
        
        # Get booked slots for this cabin and location
        cursor.execute('''
            SELECT blood_test_time, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin = ? AND location = ?
            GROUP BY blood_test_time
        ''', (date, cabin, location))
        
        booked_slots = dict(cursor.fetchall())
        
        # Create slots with availability
        slots_with_availability = {}
        for slot in all_slots:
            booked_count = booked_slots.get(slot, 0)
            available_count = people_per_cabin - booked_count
            slots_with_availability[slot] = max(0, available_count)
        
        conn.close()
        return slots_with_availability


class ConsultationService:
    """Service class for consultation booking operations with dynamic configuration support"""
    
    @staticmethod
    def get_available_slots(date: str, location: str) -> List[str]:
        """Get available time slots for consultations on a given date and location"""
        if not is_valid_date(date):
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get dynamic configuration values
        start_time = config_manager.get('consultation_start_time')
        end_time = config_manager.get('consultation_end_time')
        slot_duration = config_manager.get('slot_duration_consultation')
        cabins_count = config_manager.get('consultation_cabins_count')
        people_per_cabin = config_manager.get('people_per_consultation_cabin')
        
        # Get all possible time slots
        all_slots = generate_time_slots(start_time, end_time, slot_duration)
        
        # Get booked slots for this date and location
        cursor.execute('''
            SELECT consultation_time
            FROM bookings 
            WHERE consultation_date = ? AND consultation_time IS NOT NULL AND location = ?
        ''', (date, location))
        
        booked_slots = [row[0] for row in cursor.fetchall()]
        
        # Calculate available slots considering multiple cabins
        available_slots = []
        for slot in all_slots:
            booked_count = booked_slots.count(slot)
            # Each location has configurable consultation cabins, each can handle configurable people per slot
            if booked_count < cabins_count * people_per_cabin:
                available_slots.append(slot)
        
        conn.close()
        return available_slots


class BookingManager:
    """Main booking management class with dynamic configuration support"""
    
    def __init__(self):
        self.blood_test_service = BloodTestService()
        self.consultation_service = ConsultationService()
    
    def validate_slot_availability(self, booking_data):
        """
        Validate if the selected slots are still available for the specified location
        
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        location = booking_data.get('location')
        if not location:
            return False, 'Location is required'
        
        # Validate location against current configuration
        current_locations = config_manager.get('locations')
        if location not in current_locations:
            return False, 'Invalid location selected'
        
        # Check blood test slot availability
        blood_available = self.blood_test_service.get_available_slots(
            booking_data['blood_test_date'], 
            booking_data['blood_test_cabin'],
            location
        )
        
        if booking_data['blood_test_time'] not in blood_available:
            return False, f'Selected blood test slot is no longer available in {location.title()}'
        
        # Check consultation slot availability if consultation is booked
        if (booking_data.get('consultation_date') and 
            booking_data.get('consultation_time')):
            
            consultation_available = self.consultation_service.get_available_slots(
                booking_data['consultation_date'],
                location
            )
            
            if booking_data['consultation_time'] not in consultation_available:
                return False, f'Selected consultation slot is no longer available in {location.title()}'
        
        return True, None
