from flask import jsonify, request, current_app
from app.api import api_bp
from app.api.routes import token_required
from app.models.device import Device, DeviceType
from app.iot.mqtt_client import send_device_control
from app import db

import logging
logger = logging.getLogger(__name__)

@api_bp.route('/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    """
    Get all devices for the current user

    Returns:
        JSON: List of devices
    """
    devices = Device.query.filter_by(user_id=current_user.id).all()

    return jsonify({
        'devices': [device.to_dict() for device in devices]
    })

@api_bp.route('/devices/<int:device_id>', methods=['GET'])
@token_required
def get_device(current_user, device_id):
    """
    Get a specific device by ID

    Args:
        device_id (int): Device ID

    Returns:
        JSON: Device details
    """
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    return jsonify({
        'device': device.to_dict()
    })

@api_bp.route('/devices', methods=['POST'])
@token_required
def create_device(current_user):
    """
    Create a new device

    Returns:
        JSON: New device details
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Validate required fields
    required_fields = ['name', 'device_type', 'device_id', 'max_power']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Check if device_id already exists
    if Device.query.filter_by(device_id=data['device_id']).first():
        return jsonify({'error': 'Device ID already exists'}), 400

    # Create new device
    device = Device(
        name=data['name'],
        device_type=data['device_type'],
        device_id=data['device_id'],
        max_power=float(data['max_power']),
        location=data.get('location', ''),
        description=data.get('description', ''),
        user_id=current_user.id
    )

    db.session.add(device)
    db.session.commit()

    return jsonify({
        'message': 'Device created successfully',
        'device': device.to_dict()
    }), 201

@api_bp.route('/devices/<int:device_id>', methods=['PUT'])
@token_required
def update_device(current_user, device_id):
    """
    Update a specific device

    Args:
        device_id (int): Device ID

    Returns:
        JSON: Updated device details
    """
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Update fields
    if 'name' in data:
        device.name = data['name']

    if 'device_type' in data:
        device.device_type = data['device_type']

    if 'location' in data:
        device.location = data['location']

    if 'description' in data:
        device.description = data['description']

    if 'max_power' in data:
        device.max_power = float(data['max_power'])

    db.session.commit()

    return jsonify({
        'message': 'Device updated successfully',
        'device': device.to_dict()
    })

@api_bp.route('/devices/<int:device_id>', methods=['DELETE'])
@token_required
def delete_device(current_user, device_id):
    """
    Delete a specific device

    Args:
        device_id (int): Device ID

    Returns:
        JSON: Success message
    """
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    db.session.delete(device)
    db.session.commit()

    return jsonify({
        'message': 'Device deleted successfully'
    })

@api_bp.route('/devices/<int:device_id>/control', methods=['POST'])
@token_required
def control_device(current_user, device_id):
    """
    Send control command to a device

    Args:
        device_id (int): Device ID

    Returns:
        JSON: Success or error message
    """
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    data = request.get_json()

    if not data or 'command' not in data:
        return jsonify({'error': 'Command is required'}), 400

    command = data['command']
    value = data.get('value')

    # Send command to device via MQTT
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
        'message': f'Command {command} sent successfully to device'
    })

@api_bp.route('/device-types', methods=['GET'])
@token_required
def get_device_types(current_user):
    """
    Get all device types

    Returns:
        JSON: List of device types
    """
    device_types = DeviceType.query.all()

    return jsonify({
        'device_types': [{
            'id': dt.id,
            'name': dt.name,
            'description': dt.description,
            'typical_power': dt.typical_power,
            'icon': dt.icon
        } for dt in device_types]
    })