from flask import jsonify, request
from app.api import api_bp
from app.api.routes import token_required
from app.models.user import User
from app.models.notification import NotificationSetting
from app import db

import logging
logger = logging.getLogger(__name__)

@api_bp.route('/user/profile', methods=['GET'])
@token_required
def get_user_profile(current_user):
    """
    Get current user profile

    Returns:
        JSON: User profile
    """
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'phone_number': current_user.phone_number,
            'farm_name': current_user.farm_name,
            'is_admin': current_user.is_admin,
            'created_at': current_user.created_at.isoformat(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
    })

@api_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_user_profile(current_user):
    """
    Update user profile

    Returns:
        JSON: Updated user profile
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Update user fields
    if 'full_name' in data:
        current_user.full_name = data['full_name']

    if 'phone_number' in data:
        current_user.phone_number = data['phone_number']

    if 'farm_name' in data:
        current_user.farm_name = data['farm_name']

    # Email update requires verification in a real app
    if 'email' in data and data['email'] != current_user.email:
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        current_user.email = data['email']

    # Password update
    if 'current_password' in data and 'new_password' in data:
        if not current_user.verify_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400

        current_user.password = data['new_password']

    db.session.commit()

    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'phone_number': current_user.phone_number,
            'farm_name': current_user.farm_name
        }
    })

@api_bp.route('/user/notification-settings', methods=['GET'])
@token_required
def get_notification_settings(current_user):
    """
    Get user notification settings

    Returns:
        JSON: Notification settings
    """
    settings = NotificationSetting.query.filter_by(user_id=current_user.id).first()

    # Create default settings if none exist
    if not settings:
        from app.config import Config
        settings = NotificationSetting(
            user_id=current_user.id,
            power_threshold_warning=Config.POWER_WARNING_THRESHOLD,
            power_threshold_critical=Config.POWER_CRITICAL_THRESHOLD,
            alert_on_high_power=True,
            alert_on_device_offline=True,
            alert_on_schedule_failure=True,
            receive_sms=True,
            receive_email=True,
            receive_push=True
        )
        db.session.add(settings)
        db.session.commit()

    return jsonify({
        'settings': {
            'id': settings.id,
            'power_threshold_warning': settings.power_threshold_warning,
            'power_threshold_critical': settings.power_threshold_critical,
            'alert_on_high_power': settings.alert_on_high_power,
            'alert_on_device_offline': settings.alert_on_device_offline,
            'alert_on_schedule_failure': settings.alert_on_schedule_failure,
            'receive_sms': settings.receive_sms,
            'receive_email': settings.receive_email,
            'receive_push': settings.receive_push,
            'quiet_hours_start': settings.quiet_hours_start.strftime('%H:%M') if settings.quiet_hours_start else None,
            'quiet_hours_end': settings.quiet_hours_end.strftime('%H:%M') if settings.quiet_hours_end else None
        }
    })

@api_bp.route('/user/notification-settings', methods=['PUT'])
@token_required
def update_notification_settings(current_user):
    """
    Update user notification settings

    Returns:
        JSON: Updated notification settings
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    settings = NotificationSetting.query.filter_by(user_id=current_user.id).first()

    # Create settings if none exist
    if not settings:
        from app.config import Config
        settings = NotificationSetting(user_id=current_user.id)
        db.session.add(settings)

    # Update settings
    if 'power_threshold_warning' in data:
        settings.power_threshold_warning = float(data['power_threshold_warning'])

    if 'power_threshold_critical' in data:
        settings.power_threshold_critical = float(data['power_threshold_critical'])

    if 'alert_on_high_power' in data:
        settings.alert_on_high_power = bool(data['alert_on_high_power'])

    if 'alert_on_device_offline' in data:
        settings.alert_on_device_offline = bool(data['alert_on_device_offline'])

    if 'alert_on_schedule_failure' in data:
        settings.alert_on_schedule_failure = bool(data['alert_on_schedule_failure'])

    if 'receive_sms' in data:
        settings.receive_sms = bool(data['receive_sms'])

    if 'receive_email' in data:
        settings.receive_email = bool(data['receive_email'])

    if 'receive_push' in data:
        settings.receive_push = bool(data['receive_push'])

    if 'quiet_hours_start' in data and data['quiet_hours_start']:
        try:
            from datetime import datetime
            settings.quiet_hours_start = datetime.strptime(data['quiet_hours_start'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid quiet_hours_start format. Use HH:MM'}), 400

    if 'quiet_hours_end' in data and data['quiet_hours_end']:
        try:
            from datetime import datetime
            settings.quiet_hours_end = datetime.strptime(data['quiet_hours_end'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid quiet_hours_end format. Use HH:MM'}), 400

    db.session.commit()

    return jsonify({
        'message': 'Notification settings updated successfully',
        'settings': {
            'id': settings.id,
            'power_threshold_warning': settings.power_threshold_warning,
            'power_threshold_critical': settings.power_threshold_critical,
            'alert_on_high_power': settings.alert_on_high_power,
            'alert_on_device_offline': settings.alert_on_device_offline,
            'alert_on_schedule_failure': settings.alert_on_schedule_failure,
            'receive_sms': settings.receive_sms,
            'receive_email': settings.receive_email,
            'receive_push': settings.receive_push,
            'quiet_hours_start': settings.quiet_hours_start.strftime('%H:%M') if settings.quiet_hours_start else None,
            'quiet_hours_end': settings.quiet_hours_end.strftime('%H:%M') if settings.quiet_hours_end else None
        }
    })