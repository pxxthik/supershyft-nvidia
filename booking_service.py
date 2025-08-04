# booking_service.py - Business logic for booking availability and management

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
    """Service class for blood test booking operations"""
    
    @staticmethod
    def get_cabin_availability(date: str) -> Dict:
        """Get available slots per cabin for blood tests on a given date"""
        if not is_valid_date(date):
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total time slots available for the day
        total_slots = len(generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD))
        
        # Get booked slots per cabin
        cursor.execute('''
            SELECT blood_test_cabin, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin IS NOT NULL
            GROUP BY blood_test_cabin
        ''', (date,))
        
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
    def get_available_slots(date: str, cabin: int) -> List[str]:
        """Get available time slots for a specific cabin on a given date"""
        if not is_valid_date(date):
            return []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all possible time slots
        all_slots = generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD)
        
        # Get booked slots for this cabin
        cursor.execute('''
            SELECT blood_test_time, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin = ?
            GROUP BY blood_test_time
        ''', (date, cabin))
        
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
    def get_slots_with_availability(date: str, cabin: int) -> Dict[str, int]:
        """Get time slots with availability count for a specific cabin on a given date"""
        if not is_valid_date(date):
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all possible time slots
        all_slots = generate_time_slots(BLOOD_TEST_START_TIME, BLOOD_TEST_END_TIME, SLOT_DURATION_BLOOD)
        
        # Get booked slots for this cabin
        cursor.execute('''
            SELECT blood_test_time, COUNT(*) as booked_count
            FROM bookings 
            WHERE blood_test_date = ? AND blood_test_cabin = ?
            GROUP BY blood_test_time
        ''', (date, cabin))
        
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
    """Service class for consultation booking operations"""
    
    @staticmethod
    def get_available_slots(date: str) -> List[str]:
        """Get available time slots for consultations on a given date"""
        if not is_valid_date(date):
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all possible time slots
        all_slots = generate_time_slots(CONSULTATION_START_TIME, CONSULTATION_END_TIME, SLOT_DURATION_CONSULTATION)
        
        # Get booked slots for this date
        cursor.execute('''
            SELECT consultation_time
            FROM bookings 
            WHERE consultation_date = ? AND consultation_time IS NOT NULL
        ''', (date,))
        
        booked_slots = [row[0] for row in cursor.fetchall()]
        
        # Filter available slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        conn.close()
        return available_slots


class BookingManager:
    """Main booking management class"""
    
    def __init__(self):
        self.blood_test_service = BloodTestService()
        self.consultation_service = ConsultationService()
    
    def validate_slot_availability(self, booking_data):
        """
        Validate if the selected slots are still available
        
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        # Check blood test slot availability
        blood_available = self.blood_test_service.get_available_slots(
            booking_data['blood_test_date'], 
            booking_data['blood_test_cabin']
        )
        
        if booking_data['blood_test_time'] not in blood_available:
            return False, 'Selected blood test slot is no longer available'
        
        # Check consultation slot availability if consultation is booked
        if (booking_data.get('consultation_date') and 
            booking_data.get('consultation_time')):
            
            consultation_available = self.consultation_service.get_available_slots(
                booking_data['consultation_date']
            )
            
            if booking_data['consultation_time'] not in consultation_available:
                return False, 'Selected consultation slot is no longer available'
        
        return True, None
