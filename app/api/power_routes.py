from flask import jsonify, request
from datetime import datetime
import logging

from app.api import api_bp
from app.api.routes import token_required
from app.models.power_usage import PowerReading, PowerSummary, EnergyRate
from app.models.device import Device
from app.iot.sensor_data import get_device_power_stats, get_farm_power_summary
from app import db

logger = logging.getLogger(__name__)

@api_bp.route('/power/summary', methods=['GET'])
@token_required
def get_power_summary(current_user):
    """
    Get farm-wide power usage summary

    Query Parameters:
        period (str): 'day', 'week', 'month', or 'custom'
        start_date (str): Start date for custom period (YYYY-MM-DD)
        end_date (str): End date for custom period (YYYY-MM-DD)

    Returns:
        JSON: Power usage summary
    """
    period = request.args.get('period', 'day')

    start_date = None
    end_date = None

    if period == 'custom':
        try:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')

            if not start_date_str or not end_date_str:
                return jsonify({'error': 'Start date and end date required for custom period'}), 400

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get power summary data
    summary = get_farm_power_summary(current_user.id, period, start_date, end_date)

    if 'error' in summary:
        return jsonify({'error': summary['error']}), 400

    return jsonify(summary)

@api_bp.route('/power/devices/<int:device_id>', methods=['GET'])
@token_required
def get_device_power(current_user, device_id):
    """
    Get power statistics for a specific device

    Args:
        device_id (int): Device ID

    Query Parameters:
        period (str): 'day', 'week', or 'month'

    Returns:
        JSON: Device power statistics
    """
    # Verify device belongs to user
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found or unauthorized'}), 404

    period = request.args.get('period', 'day')

    # Get device power stats
    stats = get_device_power_stats(device_id, period)

    return jsonify(stats)

@api_bp.route('/power/readings', methods=['GET'])
@token_required
def get_power_readings(current_user):
    """
    Get power readings for all devices or a specific device

    Query Parameters:
        device_id (int): Optional device ID
        start_time (str): Start time (ISO format)
        end_time (str): End time (ISO format)
        limit (int): Maximum number of readings to return

    Returns:
        JSON: Power readings
    """
    # Parse query parameters
    device_id = request.args.get('device_id', type=int)
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    limit = request.args.get('limit', 100, type=int)

    # Build query
    query = PowerReading.query

    # Filter by device
    if device_id:
        # Verify device belongs to user
        device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({'error': 'Device not found or unauthorized'}), 404

        query = query.filter_by(device_id=device_id)
    else:
        # Get all devices for this user
        devices = Device.query.filter_by(user_id=current_user.id).all()
        device_ids = [d.id for d in devices]
        query = query.filter(PowerReading.device_id.in_(device_ids))

    # Filter by time range
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
            query = query.filter(PowerReading.timestamp >= start_time)
        except ValueError:
            return jsonify({'error': 'Invalid start_time format. Use ISO format'}), 400

    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str)
            query = query.filter(PowerReading.timestamp <= end_time)
        except ValueError:
            return jsonify({'error': 'Invalid end_time format. Use ISO format'}), 400

    # Order by timestamp (descending)
    query = query.order_by(PowerReading.timestamp.desc())

    # Apply limit
    query = query.limit(limit)

    # Execute query
    readings = query.all()

    return jsonify({
        'readings': [reading.to_dict() for reading in readings],
        'count': len(readings)
    })

@api_bp.route('/power/rates', methods=['GET'])
@token_required
def get_energy_rates(current_user):
    """
    Get energy rates

    Returns:
        JSON: Energy rates
    """
    rates = EnergyRate.query.all()

    return jsonify({
        'rates': [{
            'id': rate.id,
            'name': rate.name,
            'rate_per_kwh': rate.rate_per_kwh,
            'currency': rate.currency,
            'valid_from': rate.valid_from.isoformat(),
            'valid_to': rate.valid_to.isoformat() if rate.valid_to else None,
            'is_time_of_use': rate.is_time_of_use,
            'peak_start_time': rate.peak_start_time.strftime('%H:%M') if rate.peak_start_time else None,
            'peak_end_time': rate.peak_end_time.strftime('%H:%M') if rate.peak_end_time else None,
            'peak_rate': rate.peak_rate,
            'off_peak_rate': rate.off_peak_rate
        } for rate in rates]
    })

@api_bp.route('/power/rates', methods=['POST'])
@token_required
def create_energy_rate(current_user):
    """
    Create a new energy rate (admin only)

    Returns:
        JSON: New energy rate
    """
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Validate required fields
    required_fields = ['name', 'rate_per_kwh', 'valid_from']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    try:
        # Parse dates
        valid_from = datetime.fromisoformat(data['valid_from'])
        valid_to = datetime.fromisoformat(data['valid_to']) if 'valid_to' in data and data['valid_to'] else None

        # Parse times if time-of-use
        peak_start_time = None
        peak_end_time = None

        if data.get('is_time_of_use', False):
            if 'peak_start_time' in data and data['peak_start_time']:
                peak_start_time = datetime.strptime(data['peak_start_time'], '%H:%M').time()

            if 'peak_end_time' in data and data['peak_end_time']:
                peak_end_time = datetime.strptime(data['peak_end_time'], '%H:%M').time()

        # Create energy rate
        rate = EnergyRate(
            name=data['name'],
            rate_per_kwh=float(data['rate_per_kwh']),
            currency=data.get('currency', 'USD'),
            valid_from=valid_from,
            valid_to=valid_to,
            is_time_of_use=data.get('is_time_of_use', False),
            peak_start_time=peak_start_time,
            peak_end_time=peak_end_time,
            peak_rate=float(data.get('peak_rate', 0.0)),
            off_peak_rate=float(data.get('off_peak_rate', 0.0))
        )

        db.session.add(rate)
        db.session.commit()

        return jsonify({
            'message': 'Energy rate created successfully',
            'id': rate.id
        }), 201

    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating energy rate: {str(e)}")
        return jsonify({'error': 'Failed to create energy rate'}), 500

@api_bp.route('/power/dashboard', methods=['GET'])
@token_required
def get_power_dashboard(current_user):
    """
    Get power dashboard data for the current user

    Returns:
        JSON: Dashboard data
    """
    # Get all devices for this user
    devices = Device.query.filter_by(user_id=current_user.id).all()

    # Get current power usage for each device
    device_power = [{
        'id': device.id,
        'name': device.name,
        'current_power': device.current_power,
        'status': device.status,
        'power_state': device.power_state,
        'last_updated': device.last_updated.isoformat() if device.last_updated else None
    } for device in devices]

    # Sort by power usage (descending)
    device_power.sort(key=lambda x: x['current_power'], reverse=True)

    # Get today's power summary
    today = datetime.utcnow().date()
    today_summary = PowerSummary.query.filter_by(
        date=today,
        summary_type='daily',
        device_id=None  # Farm-wide summary
    ).first()

    # If no summary for today yet, get yesterday's
    if not today_summary:
        yesterday = today - datetime.timedelta(days=1)
        today_summary = PowerSummary.query.filter_by(
            date=yesterday,
            summary_type='daily',
            device_id=None
        ).first()

    # Today's usage stats
    today_stats = {
        'total_energy': today_summary.total_energy if today_summary else 0,
        'peak_power': today_summary.peak_power if today_summary else 0,
        'cost_estimate': today_summary.cost_estimate if today_summary else 0
    }

    # Get last 7 days of power summaries
    last_7_days = []
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        summary = PowerSummary.query.filter_by(
            date=date,
            summary_type='daily',
            device_id=None
        ).first()

        if summary:
            last_7_days.append({
                'date': date.isoformat(),
                'total_energy': summary.total_energy,
                'cost_estimate': summary.cost_estimate
            })

    return jsonify({
        'current_power': {
            'devices': device_power,
            'total': sum(d['current_power'] for d in device_power)
        },
        'today': today_stats,
        'last_7_days': last_7_days,
        'timestamp': datetime.utcnow().isoformat()
    })