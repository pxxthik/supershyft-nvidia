# app.py - Main Flask application with modular structure and location support

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session,
)
from datetime import datetime, timedelta

# Import our modules
from config import SECRET_KEY, ADMIN_PASSWORD, LOCATIONS, BLOOD_TEST_ALLOWED_DATES, CONSULTATION_ALLOWED_DATES
from database import (
    init_db,
    save_booking,
    get_booking_by_id,
    get_all_bookings,
    delete_booking_by_id,
)
from utils import admin_required, validate_booking_data
from booking_service import BookingManager


# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize booking manager
booking_manager = BookingManager()


def validate_blood_test_date(date_str):
    """Validate if the date is within the allowed blood test dates"""
    try:
        # Check if the format is valid
        datetime.strptime(date_str, "%Y-%m-%d")

        # Check if the date is in the allowed list
        return date_str in BLOOD_TEST_ALLOWED_DATES
    except ValueError:
        return False


def validate_consultation_date(date_str):
    """Validate if the date is within allowed consultation range"""
    try:
        # Check if the format is valid
        datetime.strptime(date_str, "%Y-%m-%d")

        # Check if the date is in the allowed list
        return date_str in CONSULTATION_ALLOWED_DATES
    except ValueError:
        return False

@app.route("/allowed_blood_test_dates")
def get_allowed_blood_test_dates():
    return jsonify({"allowed_dates": BLOOD_TEST_ALLOWED_DATES})

@app.route("/allowed_consultation_dates")
def get_allowed_consultation_dates():
    return jsonify({"allowed_dates": CONSULTATION_ALLOWED_DATES})


def validate_location(location):
    """Validate if the location is one of the allowed locations"""
    return location in LOCATIONS


# Main Routes
@app.route("/")
def index():
    """Main registration form"""
    return render_template("index.html", locations=LOCATIONS)


@app.route("/booking_success/<int:booking_id>")
def booking_success(booking_id):
    """Display booking confirmation"""
    booking = get_booking_by_id(booking_id)

    if not booking:
        flash("Booking not found")
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
                "error": "Invalid date. Blood tests are only available from 19th-22nd August 2025"
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
                "error": "Invalid date. Blood tests are only available from 19th-22nd August 2025"
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
                "error": "Invalid date. Consultations are only available from 25th-29th August 2025 (excluding 27th - Holiday)"
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
            flash(error_message)
            return redirect(url_for("index"))

        # Validate location
        if not validate_location(booking_data.get("location")):
            flash("Invalid location selected.")
            return redirect(url_for("index"))

        # Additional date validation for blood test
        if not validate_blood_test_date(booking_data["blood_test_date"]):
            flash(
                "Invalid blood test date. Blood tests are only available from 19th-22nd August 2025."
            )
            return redirect(url_for("index"))

        # Additional date validation for consultation (if selected)
        if booking_data.get("consultation_date") and not validate_consultation_date(
            booking_data["consultation_date"]
        ):
            flash(
                "Invalid consultation date. Consultations are only available from 25th-29th August 2025 (excluding 27th - Holiday)."
            )
            return redirect(url_for("index"))

        # Check if selected slots are still available
        slot_valid, slot_error = booking_manager.validate_slot_availability(
            booking_data
        )

        if not slot_valid:
            flash(slot_error)
            return redirect(url_for("index"))

        # Save booking to database
        booking_id = save_booking(booking_data)

        # Create success message
        location_title = booking_data["location"].title()
        success_message = f'Booking confirmed for {location_title}! Your booking ID is {booking_id}. Blood test assigned to Cabin {booking_data["blood_test_cabin"]}.'
        if booking_data.get("consultation_date"):
            success_message += f' Consultation scheduled for {booking_data["consultation_date"]} at {booking_data["consultation_time"]}.'

        flash(success_message)
        return redirect(url_for("booking_success", booking_id=booking_id))

    except Exception as e:
        flash(f"Error processing booking: {str(e)}")
        return redirect(url_for("index"))


# Admin Routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            flash("Login successful!")
            return redirect(url_for("admin"))
        else:
            flash("Invalid password. Please try again.")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop("admin_authenticated", None)
    flash("You have been logged out.")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():
    """Admin panel to view all bookings"""
    bookings = get_all_bookings()
    return render_template("admin.html", bookings=bookings, locations=LOCATIONS)


@app.route("/admin/delete_booking/<int:booking_id>", methods=["POST"])
@admin_required
def delete_booking(booking_id):
    """Delete a specific booking record"""
    try:
        success, booking_name = delete_booking_by_id(booking_id)

        if success:
            flash(
                f"Booking #{booking_id} for {booking_name} has been successfully deleted."
            )
        else:
            flash("Booking not found.")

    except Exception as e:
        flash(f"Error deleting booking: {str(e)}")

    return redirect(url_for("admin"))


@app.route("/admin/delete_records")
@admin_required
def delete_records():
    """Show all bookings for deletion management"""
    bookings = get_all_bookings()
    return render_template("delete_records.html", bookings=bookings)


# init db
init_db()

# Initialize database and run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
