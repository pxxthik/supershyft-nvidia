# config.py - Configuration settings for the booking system with location support

# Flask Configuration
SECRET_KEY = 'your-secret-key-change-this'  # Change this in production
ADMIN_PASSWORD = 'admin123'  # Change this to your desired password

# Location Configuration
LOCATIONS = ['bangalore', 'gurugram', 'pune', 'hyderabad']

# Blood Test Configuration
BLOOD_TEST_START_TIME = '09:00'
BLOOD_TEST_END_TIME = '13:00'
BLOOD_TEST_ALLOWED_DATES = ["2025-08-19", "2025-08-20", "2025-08-21", "2025-08-22"]

SLOT_DURATION_BLOOD = 15  # minutes
BLOOD_TEST_CABINS_COUNT = 4  # 4 cabins per location
PEOPLE_PER_BLOOD_CABIN = 4   # 4 people per cabin per time slot

# Consultation Configuration
CONSULTATION_START_TIME = '10:00'
CONSULTATION_END_TIME = '18:00'
SLOT_DURATION_CONSULTATION = 30  # minutes
CONSULTATION_CABINS_COUNT = 4    # 4 consultation cabins per location
PEOPLE_PER_CONSULTATION_CABIN = 1  # 1 person per cabin per time slot

CONSULTATION_ALLOWED_DATES = ["2025-08-25", "2025-08-26", "2025-08-28", "2025-08-29"]

# Database Configuration
DATABASE_NAME = 'bookings.db'
