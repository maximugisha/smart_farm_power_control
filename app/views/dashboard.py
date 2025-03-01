from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from app.models.device import Device
from app.models.power_usage import PowerReading, PowerSummary
from app.models.notification import Notification, NotificationSetting
from app.models.schedule import Schedule
from app import db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Get user's devices
    devices = Device.query.filter_by(user_id=current_user.id).all()

    # Get today's date
    today = datetime.utcnow().date()

    # Get today's power summary
    today_summary = PowerSummary.query.filter(
        PowerSummary.device_id == None,  # Farm-wide summary
        PowerSummary.date == today
    ).first()

    # If no summary for today yet, get yesterday's
    if not today_summary:
        yesterday = today - timedelta(days=1)
        today_summary = PowerSummary.query.filter(
            PowerSummary.device_id == None,
            PowerSummary.date == yesterday
        ).first()

    # Get unread notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.timestamp.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        devices=devices,
        today_summary=today_summary,
        notifications=notifications
    )

@dashboard_bp.route('/devices')
@login_required
def devices():
    """Devices management page"""
    # Get user's devices
    devices = Device.query.filter_by(user_id=current_user.id).all()

    # Get device types for adding new devices
    from app.models.device import DeviceType
    device_types = DeviceType.query.all()

    return render_template(
        'dashboard/devices.html',
        devices=devices,
        device_types=device_types
    )

@dashboard_bp.route('/power-usage')
@login_required
def power_usage():
    """Power usage analytics page"""
    # Get date range parameters
    period = request.args.get('period', 'week')

    # Set default date range based on period
    today = datetime.utcnow().date()
    if period == 'day':
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == 'week':
        start_date = today - timedelta(days=6)
        end_date = today + timedelta(days=1)
    elif period == 'month':
        start_date = today - timedelta(days=29)
        end_date = today + timedelta(days=1)
    elif period == 'custom':
        # Parse custom date range
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date() + timedelta(days=1)
        except (ValueError, TypeError):
            start_date = today - timedelta(days=6)
            end_date = today + timedelta(days=1)
            period = 'week'  # Fall back to weekly view
    else:
        start_date = today - timedelta(days=6)
        end_date = today + timedelta(days=1)

    # Get user's devices
    devices = Device.query.filter_by(user_id=current_user.id).all()

    # Get daily summaries for the date range
    daily_summaries = PowerSummary.query.filter(
        PowerSummary.date >= start_date,
        PowerSummary.date < end_date,
        PowerSummary.summary_type == 'daily'
    ).all()

    # Group summaries by device and date
    device_summaries = {}
    farm_summary = {}

    for summary in daily_summaries:
        date_str = summary.date.isoformat()

        if summary.device_id is None:
            # Farm-wide summary
            farm_summary[date_str] = {
                'date': date_str,
                'total_energy': summary.total_energy,
                'peak_power': summary.peak_power,
                'cost_estimate': summary.cost_estimate
            }
        else:
            # Device-specific summary
            if summary.device_id not in device_summaries:
                device_summaries[summary.device_id] = {}

            device_summaries[summary.device_id][date_str] = {
                'date': date_str,
                'total_energy': summary.total_energy,
                'peak_power': summary.peak_power,
                'cost_estimate': summary.cost_estimate
            }

    # Prepare data for charts
    dates = []
    farm_energy = []
    farm_cost = []

    curr_date = start_date
    while curr_date < end_date:
        date_str = curr_date.isoformat()
        dates.append(date_str)

        if date_str in farm_summary:
            farm_energy.append(farm_summary[date_str]['total_energy'])
            farm_cost.append(farm_summary[date_str]['cost_estimate'])
        else:
            farm_energy.append(0)
            farm_cost.append(0)

        curr_date += timedelta(days=1)

    # Prepare device data for charts
    device_data = []
    for device in devices:
        device_energy = []

        curr_date = start_date
        while curr_date < end_date:
            date_str = curr_date.isoformat()

            if device.id in device_summaries and date_str in device_summaries[device.id]:
                device_energy.append(device_summaries[device.id][date_str]['total_energy'])
            else:
                device_energy.append(0)

            curr_date += timedelta(days=1)

        device_data.append({
            'id': device.id,
            'name': device.name,
            'energy': device_energy,
            'total_energy': sum(device_energy)
        })

    # Sort devices by total energy
    device_data.sort(key=lambda x: x['total_energy'], reverse=True)

    # Calculate period totals
    total_energy = sum(farm_energy)
    total_cost = sum(farm_cost)
    avg_daily_energy = total_energy / len(dates) if dates else 0

    return render_template(
        'dashboard/power_usage.html',
        period=period,
        start_date=start_date.isoformat(),
        end_date=(end_date - timedelta(days=1)).isoformat(),
        dates=json.dumps(dates),
        farm_energy=json.dumps(farm_energy),
        farm_cost=json.dumps(farm_cost),
        device_data=json.dumps(device_data),
        devices=devices,
        total_energy=total_energy,
        total_cost=total_cost,
        avg_daily_energy=avg_daily_energy
    )

@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """Notifications and alerts page"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Get user's notifications
    pagination = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.timestamp.desc()) \
        .paginate(page=page, per_page=per_page)
    notifications = pagination.items

    return render_template(
        'dashboard/alerts.html',
        notifications=notifications,
        pagination=pagination
    )

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    # Get user's notification settings
    notification_settings = NotificationSetting.query.filter_by(user_id=current_user.id).first()

    # Create default settings if none exist
    if not notification_settings:
        from app.config import Config
        notification_settings = NotificationSetting(
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
        db.session.add(notification_settings)
        db.session.commit()

    return render_template(
        'dashboard/settings.html',
        notification_settings=notification_settings
    )

@dashboard_bp.route('/schedules')
@login_required
def schedules():
    """Device schedules management page"""
    # Get user's devices
    devices = Device.query.filter_by(user_id=current_user.id).all()

    # Get all schedules for user's devices
    schedules = Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time).all()

    # Group schedules by device
    device_schedules = {}
    for device in devices:
        device_schedules[device.id] = [s for s in schedules if s.device_id == device.id]

    return render_template(
        'dashboard/schedules.html',
        devices=devices,
        schedules=schedules,
        device_schedules=device_schedules
    )

# AJAX routes for dashboard
@dashboard_bp.route('/api/device/<int:device_id>/control', methods=['POST'])
@login_required
def device_control(device_id):
    """AJAX endpoint to control a device"""
    # Get device
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    data = request.get_json()

    if not data or 'command' not in data:
        return jsonify({'error': 'Command is required'}), 400

    command = data['command']
    value = data.get('value')

    # Send command to device via MQTT
    from app.iot.mqtt_client import send_device_control
    success = send_device_control(device.device_id, command, value)

    if not success:
        return jsonify({'error': 'Failed to send command to device'}), 500

    # If the command is to turn power on/off, update the device state
    if command == 'power':
        if isinstance(value, bool):
            device.update_power_state(value)
        elif value in ['on', 'off']:
            device.update_power_state(value == 'on')

    return jsonify({
        'message': f'Command {command} sent successfully to device',
        'device_id': device_id,
        'status': device.status,
        'power_state': device.power_state
    })