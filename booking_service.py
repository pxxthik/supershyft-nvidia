# booking_service.py - Business logic for booking availability and management with location support

from typing import Dict, List
from database import get_db_connection
from utils import generate_time_slots, is_valid_date
from config import (
    BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD,
    CONSULTATION_START_TIME, CONSULTATION_END_TIME, SLOT_DURATION_CONSULTATION,
    BLOOD_TEST_CABINS_COUNT, CONSULTATION_CABINS_COUNT,
    PEOPLE_PER_BLOOD_CABIN, PEOPLE_PER_CONSULTATION_CABIN
)


class BloodTestService:
    """Service class for blood test booking operations with location support"""
    
    @staticmethod
    def get_cabin_availability(date: str, location: str) -> Dict:
        """Get available slots per cabin for blood tests on a given date and location"""
        if not is_valid_date(date):
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total time slots available for the day
        total_slots = len(generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD))
        
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
        for cabin in range(1, BLOOD_TEST_CABINS_COUNT + 1):
            booked_count = booked_per_cabin.get(cabin, 0)
            available_slots = (total_slots * PEOPLE_PER_BLOOD_CABIN) - booked_count
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
        
        # Get all possible time slots
        all_slots = generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD)
        
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
            if booked_count < PEOPLE_PER_BLOOD_CABIN:
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
        
        # Get all possible time slots
        all_slots = generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD)
        
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
            available_count = PEOPLE_PER_BLOOD_CABIN - booked_count
            slots_with_availability[slot] = max(0, available_count)
        
        conn.close()
        return slots_with_availability


class ConsultationService:
    """Service class for consultation booking operations with location support"""
    
    @staticmethod
    def get_available_slots(date: str, location: str) -> List[str]:
        """Get available time slots for consultations on a given date and location"""
        if not is_valid_date(date):
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all possible time slots
        all_slots = generate_time_slots(CONSULTATION_START_TIME, CONSULTATION_END_TIME, SLOT_DURATION_CONSULTATION)
        
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
            # Each location has 4 consultation cabins, each can handle 1 person per slot
            if booked_count < CONSULTATION_CABINS_COUNT * PEOPLE_PER_CONSULTATION_CABIN:
                available_slots.append(slot)
        
        conn.close()
        return available_slots


class BookingManager:
    """Main booking management class with location support"""
    
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
