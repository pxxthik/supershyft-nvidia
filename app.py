# app.py - Main Flask application with modular structure, location support, and dynamic configuration

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
)
from datetime import datetime, timedelta

# Import our modules
from config import (
    SECRET_KEY, ADMIN_PASSWORD, config_manager, reload_config
)
from database import (
    init_db,
    save_booking,
    get_booking_by_id,
    get_all_bookings,
    delete_booking_by_id,
)
from utils import admin_required, validate_booking_data
from booking_service import BookingManager
from config_validator import ConfigValidator


# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize booking manager
booking_manager = BookingManager()


def get_current_config():
    """Get current configuration values (refreshed)"""
    reload_config()
    return {
        'locations': config_manager.get('locations'),
        'blood_test_allowed_dates': config_manager.get('blood_test_allowed_dates'),
        'consultation_allowed_dates': config_manager.get('consultation_allowed_dates')
    }


def validate_blood_test_date(date_str):
    """Validate if the date is within the allowed blood test dates"""
    try:
        # Check if the format is valid
        datetime.strptime(date_str, "%Y-%m-%d")
        # Get current allowed dates
        current_dates = config_manager.get('blood_test_allowed_dates')
        return date_str in current_dates
    except ValueError:
        return False


def validate_consultation_date(date_str):
    """Validate if the date is within allowed consultation range"""
    try:
        # Check if the format is valid
        datetime.strptime(date_str, "%Y-%m-%d")
        # Get current allowed dates
        current_dates = config_manager.get('consultation_allowed_dates')
        return date_str in current_dates
    except ValueError:
        return False


def validate_location(location):
    """Validate if the location is one of the allowed locations"""
    current_locations = config_manager.get('locations')
    return location in current_locations


@app.route("/allowed_blood_test_dates")
def get_allowed_blood_test_dates():
    current_dates = config_manager.get('blood_test_allowed_dates')
    return jsonify({"allowed_dates": current_dates})


@app.route("/allowed_consultation_dates")
def get_allowed_consultation_dates():
    current_dates = config_manager.get('consultation_allowed_dates')
    return jsonify({"allowed_dates": current_dates})


# Main Routes
@app.route("/")
def index():
    """Main registration form"""
    current_locations = config_manager.get('locations')
    return render_template("index.html", locations=current_locations)


@app.route("/booking_success/<int:booking_id>")
def booking_success(booking_id):
    """Display booking confirmation"""
    booking = get_booking_by_id(booking_id)

    if not booking:
        print("Booking not found")
        return redirect(url_for("index"))

    return render_template("success.html", booking=booking)


# API Routes for Blood Test Booking
@app.route("/get_blood_test_cabins")
def get_blood_test_cabins():
    """API endpoint to get available cabins for blood tests"""
    date_param = request.args.get("date")
    location_param = request.args.get("location")

    if not date_param or not location_param:
        return jsonify({"error": "Date and location parameters are required"})

    # Validate location
    if not validate_location(location_param):
        return jsonify({"error": "Invalid location"})

    # Validate blood test date
    if not validate_blood_test_date(date_param):
        return jsonify(
            {
                "error": "Invalid date. Please select from the available blood test dates"
            }
        )

    cabin_availability = booking_manager.blood_test_service.get_cabin_availability(
        date_param, location_param
    )

    if not cabin_availability:
        return jsonify({"error": "Invalid date or date is in the past"})

    return jsonify(cabin_availability)


@app.route("/get_blood_test_slots")
def get_blood_test_slots():
    """API endpoint to get available time slots for a specific blood test cabin"""
    date_param = request.args.get("date")
    cabin_param = request.args.get("cabin")
    location_param = request.args.get("location")

    if not date_param or not cabin_param or not location_param:
        return jsonify({"error": "Date, cabin, and location parameters are required"})

    # Validate location
    if not validate_location(location_param):
        return jsonify({"error": "Invalid location"})

    # Validate blood test date
    if not validate_blood_test_date(date_param):
        return jsonify(
            {
                "error": "Invalid date. Please select from the available blood test dates"
            }
        )

    try:
        cabin = int(cabin_param)
    except ValueError:
        return jsonify({"error": "Invalid cabin number"})

    # Return slots with availability count
    slots_with_availability = (
        booking_manager.blood_test_service.get_slots_with_availability(
            date_param, cabin, location_param
        )
    )

    if not slots_with_availability:
        return jsonify({"error": "Invalid date or date is in the past"})

    return jsonify(slots_with_availability)


# API Routes for Consultation Booking
@app.route("/get_consultation_slots")
def get_consultation_slots():
    """API endpoint to get available time slots for consultations"""
    date_param = request.args.get("date")
    location_param = request.args.get("location")

    if not date_param or not location_param:
        return jsonify({"error": "Date and location parameters are required"})

    # Validate location
    if not validate_location(location_param):
        return jsonify({"error": "Invalid location"})

    # Validate consultation date
    if not validate_consultation_date(date_param):
        return jsonify(
            {
                "error": "Invalid date. Please select from the available consultation dates"
            }
        )

    available_slots = booking_manager.consultation_service.get_available_slots(
        date_param, location_param
    )

    if available_slots is None:
        return jsonify({"error": "Invalid date or date is in the past"})

    return jsonify(available_slots)


# Booking Submission Route
@app.route("/submit_booking", methods=["POST"])
def submit_booking():
    """Handle form submission and create booking"""
    try:
        # Validate form data
        is_valid, error_message, booking_data = validate_booking_data(request.form)

        if not is_valid:
            print(error_message)
            return redirect(url_for("index"))

        # Validate location
        if not validate_location(booking_data.get("location")):
            print("Invalid location selected.")
            return redirect(url_for("index"))

        # Additional date validation for blood test
        if booking_data.get("blood_test_date") and not validate_blood_test_date(booking_data["blood_test_date"]):
            print("Invalid blood test date. Please select from the available dates.")
            return redirect(url_for("index"))

        # Additional date validation for consultation (if selected)
        if booking_data.get("consultation_date") and not validate_consultation_date(
            booking_data["consultation_date"]
        ):
            print("Invalid consultation date. Please select from the available dates.")
            return redirect(url_for("index"))

        # Check if selected slots are still available
        slot_valid, slot_error = booking_manager.validate_slot_availability(
            booking_data
        )

        if not slot_valid:
            print(slot_error)
            return redirect(url_for("index"))

        # Save booking to database
        booking_id = save_booking(booking_data)

        # Create success message
        location_title = booking_data["location"].title()
        success_message = f'Booking confirmed for {location_title}!\n\n'

        if booking_data.get("blood_test_date"):
            success_message += f' Blood test scheduled for {booking_data["blood_test_date"]} at {booking_data["blood_test_time"]} in {booking_data["blood_test_cabin"]}.\n'

        if booking_data.get("consultation_date"):
            success_message += f' Consultation scheduled for {booking_data["consultation_date"]} at {booking_data["consultation_time"]}.'

        print(success_message)
        return redirect(url_for("booking_success", booking_id=booking_id))

    except Exception as e:
        print(f"Error processing booking: {str(e)}")
        return redirect(url_for("index"))


# Admin Routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            print("Login successful!")
            return redirect(url_for("admin"))
        else:
            print("Invalid password. Please try again.")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop("admin_authenticated", None)
    print("You have been logged out.")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():
    """Admin panel to view all bookings"""
    bookings = get_all_bookings()
    current_locations = config_manager.get('locations')
    return render_template("admin.html", bookings=bookings, locations=current_locations)


@app.route("/admin/delete_booking/<int:booking_id>", methods=["POST"])
@admin_required
def delete_booking(booking_id):
    """Delete a specific booking record"""
    try:
        success, booking_name = delete_booking_by_id(booking_id)

        if success:
            print(
                f"Booking #{booking_id} for {booking_name} has been successfully deleted."
            )
        else:
            print("Booking not found.")

    except Exception as e:
        print(f"Error deleting booking: {str(e)}")

    return redirect(url_for("admin"))


@app.route("/admin/delete_records")
@admin_required
def delete_records():
    """Show all bookings for deletion management"""
    bookings = get_all_bookings()
    return render_template("delete_records.html", bookings=bookings)


# Configuration Management Routes
@app.route("/admin/config")
@admin_required
def admin_config():
    """Admin configuration management page"""
    config = config_manager.get_all()
    return render_template("admin_config.html", config=config)


@app.route("/admin/config", methods=["POST"])
@admin_required
def admin_config_save():
    """Save configuration changes"""
    try:
        # Collect form data
        config_updates = {}
        
        # Handle locations (array)
        locations = request.form.getlist('locations[]')
        locations = [loc.strip() for loc in locations if loc.strip()]
        if not locations:
            print("At least one location is required")
            return redirect(url_for("admin_config"))
        config_updates['locations'] = locations
        
        # Handle blood test configuration
        config_updates['blood_test_start_time'] = request.form.get('blood_test_start_time')
        config_updates['blood_test_end_time'] = request.form.get('blood_test_end_time')
        config_updates['slot_duration_blood'] = int(request.form.get('slot_duration_blood'))
        config_updates['blood_test_cabins_count'] = int(request.form.get('blood_test_cabins_count'))
        config_updates['people_per_blood_cabin'] = int(request.form.get('people_per_blood_cabin'))
        
        # Handle blood test allowed dates (array)
        blood_dates = request.form.getlist('blood_test_allowed_dates[]')
        blood_dates = [date.strip() for date in blood_dates if date.strip()]
        if not blood_dates:
            print("At least one blood test date is required")
            return redirect(url_for("admin_config"))
        config_updates['blood_test_allowed_dates'] = blood_dates
        
        # Handle consultation configuration
        config_updates['consultation_start_time'] = request.form.get('consultation_start_time')
        config_updates['consultation_end_time'] = request.form.get('consultation_end_time')
        config_updates['slot_duration_consultation'] = int(request.form.get('slot_duration_consultation'))
        config_updates['consultation_cabins_count'] = int(request.form.get('consultation_cabins_count'))
        config_updates['people_per_consultation_cabin'] = int(request.form.get('people_per_consultation_cabin'))
        
        # Handle consultation allowed dates (array)
        consultation_dates = request.form.getlist('consultation_allowed_dates[]')
        consultation_dates = [date.strip() for date in consultation_dates if date.strip()]
        if not consultation_dates:
            print("At least one consultation date is required")
            return redirect(url_for("admin_config"))
        config_updates['consultation_allowed_dates'] = consultation_dates
        
        # Validate configuration using ConfigValidator
        is_valid, validation_errors = ConfigValidator.validate_config(config_updates)
        if not is_valid:
            for error in validation_errors:
                print(f"Validation Error: {error}")
            return redirect(url_for("admin_config"))
        
        # Update configuration
        config_manager.update_multiple(config_updates)
        
        # Reload configuration in the application
        reload_config()
        
        print("Configuration updated successfully!")
        return redirect(url_for("admin_config"))
        
    except ValueError as e:
        print(f"Invalid input: {str(e)}")
        return redirect(url_for("admin_config"))
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        return redirect(url_for("admin_config"))


@app.route("/admin/config/reset")
@admin_required
def admin_config_reset():
    """Reset configuration to defaults"""
    try:
        config_manager.reset_to_defaults()
        reload_config()
        print("Configuration has been reset to default values!")
    except Exception as e:
        print(f"Error resetting configuration: {str(e)}")
    
    return redirect(url_for("admin_config"))

init_db()

# Initialize database and run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
