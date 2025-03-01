from flask import Blueprint, request, jsonify, current_app
from app.models.user import User
from app.models.device import Device
from app import db
import logging

logger = logging.getLogger(__name__)

ussd_bp = Blueprint('ussd', __name__, url_prefix='/ussd')

class USSDMenuState:
    """USSD menu state management"""
    WELCOME = "welcome"
    MAIN_MENU = "main_menu"
    POWER_SUMMARY = "power_summary"
    DEVICE_LIST = "device_list"
    DEVICE_CONTROL = "device_control"
    POWER_ALERT = "power_alert"

class USSDSession:
    """Simple USSD session manager"""
    sessions = {}  # In production, use Redis or another persistent store

    @classmethod
    def get_session(cls, session_id):
        return cls.sessions.get(session_id, {})

    @classmethod
    def set_session(cls, session_id, data):
        cls.sessions[session_id] = data
        return cls.sessions[session_id]

    @classmethod
    def clear_session(cls, session_id):
        if session_id in cls.sessions:
            del cls.sessions[session_id]
            return True
        return False

@ussd_bp.route('/callback', methods=['POST'])
def ussd_callback():
    """USSD callback endpoint"""
    # Get the USSD parameters
    session_id = request.form.get('sessionId')
    service_code = request.form.get('serviceCode')
    phone_number = request.form.get('phoneNumber')
    text = request.form.get('text', '')

    logger.info(f"USSD request: session_id={session_id}, phone={phone_number}, text={text}")

    # Get or initialize session
    session = USSDSession.get_session(session_id) or {
        'state': USSDMenuState.WELCOME,
        'phone': phone_number,
        'selected_device': None
    }

    # Handle based on the current state and user input
    response = handle_ussd_menu(session, text)

    # Save the updated session
    USSDSession.set_session(session_id, session)

    # Return the response (must start with "CON " for continuing or "END " for ending)
    return response

def handle_ussd_menu(session, text):
    """Handle USSD menu navigation based on session state and user input"""
    state = session.get('state')
    phone = session.get('phone')

    # Check if this is a new session or has no input
    if not text:
        # Find the user by phone number
        user = User.query.filter_by(phone_number=phone.replace('+', '')).first()
        if not user:
            return "END Sorry, your phone number is not registered in our system."

        session['user_id'] = user.id
        return show_welcome_menu(user)

    # Process input based on current state
    if state == USSDMenuState.WELCOME or state == USSDMenuState.MAIN_MENU:
        return handle_main_menu(session, text)
    elif state == USSDMenuState.DEVICE_LIST:
        return handle_device_list(session, text)
    elif state == USSDMenuState.DEVICE_CONTROL:
        return handle_device_control(session, text)
    elif state == USSDMenuState.POWER_SUMMARY:
        return handle_power_summary(session, text)

    # Default response if state is unknown
    session['state'] = USSDMenuState.MAIN_MENU
    return "CON An error occurred. Returning to main menu.\n1. View power summary\n2. Control devices\n3. Exit"

def show_welcome_menu(user):
    """Show welcome menu for the user"""
    welcome_text = f"CON Welcome to Smart Farm Power Control, {user.full_name}\n"
    menu_text = "1. View power summary\n2. Control devices\n3. Exit"
    return welcome_text + menu_text

def handle_main_menu(session, text):
    """Handle main menu selection"""
    user_id = session.get('user_id')

    # Update the session state based on selection
    if text == "1":
        # Power Summary
        session['state'] = USSDMenuState.POWER_SUMMARY
        # Get power summary data
        from app.models.power_usage import PowerSummary
        import datetime

        today = datetime.date.today()
        summary = PowerSummary.query.filter_by(
            summary_type='daily',
            date=today
        ).first()

        if not summary:
            return "END No power data available for today. Please check again later."

        return (
            f"CON Today's Power Summary:\n"
            f"Total Usage: {summary.total_energy:.2f} kWh\n"
            f"Peak Power: {summary.peak_power:.2f} W\n"
            f"Est. Cost: ${summary.cost_estimate:.2f}\n\n"
            f"0. Back to main menu"
        )

    elif text == "2":
        # Device Control - Show device list
        session['state'] = USSDMenuState.DEVICE_LIST
        devices = Device.query.filter_by(user_id=user_id).all()

        if not devices:
            return "END You don't have any devices registered yet."

        response = "CON Select a device to control:\n"
        for i, device in enumerate(devices, 1):
            status = "ON" if device.power_state else "OFF"
            response += f"{i}. {device.name} [{status}]\n"

        response += "0. Back to main menu"
        session['devices'] = [d.id for d in devices]
        return response

    elif text == "3":
        # Exit
        return "END Thank you for using Smart Farm Power Control. Goodbye!"

    else:
        # Invalid selection
        return "CON Invalid selection. Please try again:\n1. View power summary\n2. Control devices\n3. Exit"

def handle_device_list(session, text):
    """Handle device selection from the list"""
    if text == "0":
        # Back to main menu
        session['state'] = USSDMenuState.MAIN_MENU
        return "CON Main Menu:\n1. View power summary\n2. Control devices\n3. Exit"

    try:
        selection = int(text.split('*')[-1])
        devices = session.get('devices', [])

        if 1 <= selection <= len(devices):
            device_id = devices[selection - 1]
            device = Device.query.get(device_id)

            if not device:
                return "END Device not found. Please try again later."

            session['selected_device'] = device_id
            session['state'] = USSDMenuState.DEVICE_CONTROL

            status = "ON" if device.power_state else "OFF"
            return (
                f"CON Device: {device.name}\n"
                f"Status: {status}\n"
                f"Current Power: {device.current_power:.2f} W\n\n"
                f"1. Turn {('OFF' if device.power_state else 'ON')}\n"
                f"2. View device details\n"
                f"0. Back to device list"
            )
        else:
            return "CON Invalid selection. Please select a valid device number or 0 to go back."

    except ValueError:
        return "CON Invalid input. Please select a valid device number or 0 to go back."

def handle_device_control(session, text):
    """Handle device control operations"""
    device_id = session.get('selected_device')
    device = Device.query.get(device_id)

    if not device:
        session['state'] = USSDMenuState.DEVICE_LIST
        return "CON Device not found. Returning to device list."

    # Get the last input (after the last *)
    last_input = text.split('*')[-1]

    if last_input == "0":
        # Back to device list
        session['state'] = USSDMenuState.DEVICE_LIST
        session['selected_device'] = None
        return handle_device_list(session, "")

    elif last_input == "1":
        # Toggle power state
        new_state = not device.power_state
        device.update_power_state(new_state)

        status = "ON" if new_state else "OFF"
        return f"END Device '{device.name}' has been turned {status}."

    elif last_input == "2":
        # View device details
        return (
            f"END Device Details: {device.name}\n"
            f"Type: {device.device_type}\n"
            f"Location: {device.location}\n"
            f"Status: {device.status}\n"
            f"Power State: {'ON' if device.power_state else 'OFF'}\n"
            f"Current Power: {device.current_power:.2f} W\n"
            f"Max Power: {device.max_power:.2f} W\n"
            f"Last Updated: {device.last_updated.strftime('%Y-%m-%d %H:%M')}"
        )

    else:
        return (
            f"CON Device: {device.name}\n"
            f"Status: {'ON' if device.power_state else 'OFF'}\n"
            f"Current Power: {device.current_power:.2f} W\n\n"
            f"1. Turn {('OFF' if device.power_state else 'ON')}\n"
            f"2. View device details\n"
            f"0. Back to device list"
        )

def handle_power_summary(session, text):
    """Handle power summary view"""
    last_input = text.split('*')[-1]

    if last_input == "0":
        # Back to main menu
        session['state'] = USSDMenuState.MAIN_MENU
        return "CON Main Menu:\n1. View power summary\n2. Control devices\n3. Exit"

    else:
        # Any other input also goes back to main menu
        session['state'] = USSDMenuState.MAIN_MENU
        return "CON Main Menu:\n1. View power summary\n2. Control devices\n3. Exit"