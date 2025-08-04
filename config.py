# config.py - Configuration settings for the booking system

# Flask Configuration
SECRET_KEY = 'your-secret-key-change-this'  # Change this in production
ADMIN_PASSWORD = 'admin123'  # Change this to your desired password

# Blood Test Configuration
BLOOD_TEST_START_TIME = '09:00'
BLOOD_TEST_END_TIME = '13:00'
SLOT_DURATION_BLOOD = 15  # minutes
BLOOD_TEST_CABINS_COUNT = 4
PEOPLE_PER_BLOOD_CABIN = 4

# Consultation Configuration
CONSULTATION_START_TIME = '10:00'
CONSULTATION_END_TIME = '18:00'
SLOT_DURATION_CONSULTATION = 30  # minutes
CONSULTATION_CABINS_COUNT = 4
PEOPLE_PER_CONSULTATION_CABIN = 1

# Database Configuration
DATABASE_NAME = 'bookings.db'
