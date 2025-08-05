# database.py - Database initialization and operations with location support

import sqlite3
from config import DATABASE_NAME


def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create bookings table with location field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL,
            blood_test_date TEXT,
            blood_test_time TEXT,
            blood_test_cabin INTEGER,
            consultation_date TEXT,
            consultation_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if location column exists in existing table, if not add it
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'location' not in columns:
        cursor.execute('ALTER TABLE bookings ADD COLUMN location TEXT DEFAULT "bangalore"')
    
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
            name, email, age, gender, phone, location,
            blood_test_date, blood_test_time, blood_test_cabin,
            consultation_date, consultation_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking_data['name'], booking_data['email'], booking_data['age'], 
        booking_data['gender'], booking_data['phone'], booking_data['location'],
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
        SELECT id, name, email, age, gender, phone, location,
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
