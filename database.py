# database.py - Database initialization and operations

import sqlite3
from config import DATABASE_NAME


def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            blood_test_date TEXT,
            blood_test_time TEXT,
            blood_test_cabin INTEGER,
            consultation_date TEXT,
            consultation_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_NAME)


def save_booking(booking_data):
    """
    Save booking to database
    
    Args:
        booking_data (dict): Dictionary containing booking information
    
    Returns:
        int: Booking ID if successful
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO bookings (
            name, email, age, gender, phone, 
            blood_test_date, blood_test_time, blood_test_cabin,
            consultation_date, consultation_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking_data['name'], booking_data['email'], booking_data['age'], 
        booking_data['gender'], booking_data['phone'],
        booking_data['blood_test_date'], booking_data['blood_test_time'], 
        booking_data['blood_test_cabin'],
        booking_data.get('consultation_date'), booking_data.get('consultation_time')
    ))
    
    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()
    
    return booking_id


def get_booking_by_id(booking_id):
    """Get booking details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    
    return booking


def get_all_bookings():
    """Get all bookings ordered by creation time"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, email, age, gender, phone, 
               blood_test_date, blood_test_time, blood_test_cabin,
               consultation_date, consultation_time,
               created_at
        FROM bookings 
        ORDER BY created_at DESC
    ''')
    bookings = cursor.fetchall()
    conn.close()
    
    return bookings


def delete_booking_by_id(booking_id):
    """
    Delete booking by ID
    
    Returns:
        tuple: (success: bool, booking_name: str or None)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, check if the booking exists
    cursor.execute('SELECT name FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()
    
    if not booking:
        conn.close()
        return False, None
    
    # Delete the booking
    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    success = cursor.rowcount > 0
    
    conn.close()
    return success, booking[0] if success else None
