import json
import paho.mqtt.client as mqtt
from flask import current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global MQTT client
mqtt_client = None

# Topic prefixes
TOPIC_PREFIX = "smart-farm/"
DEVICE_TOPIC = TOPIC_PREFIX + "devices/"
CONTROL_TOPIC = TOPIC_PREFIX + "control/"
TELEMETRY_TOPIC = TOPIC_PREFIX + "telemetry/"

def setup_mqtt_client():
    """Initialize and configure the MQTT client"""
    global mqtt_client

    if mqtt_client:
        # Client already initialized
        return mqtt_client

    # Get configuration from Flask app
    broker_url = current_app.config.get('MQTT_BROKER_URL', 'localhost')
    broker_port = current_app.config.get('MQTT_BROKER_PORT', 1883)
    username = current_app.config.get('MQTT_USERNAME')
    password = current_app.config.get('MQTT_PASSWORD')
    client_id = f"smart-farm-server-{datetime.utcnow().timestamp()}"

    # Initialize the MQTT client
    mqtt_client = mqtt.Client(client_id=client_id, clean_session=True)

    # Set up authentication if provided
    if username and password:
        mqtt_client.username_pw_set(username, password)

    # Set up TLS if enabled
    if current_app.config.get('MQTT_TLS_ENABLED', False):
        mqtt_client.tls_set()

    # Set up callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    # Connect to broker
    try:
        mqtt_client.connect(broker_url, broker_port, keepalive=60)
        mqtt_client.loop_start()
        logger.info(f"MQTT client connected to {broker_url}:{broker_port}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")

    return mqtt_client

def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNACK response from the server"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Subscribe to all device topics
        client.subscribe(f"{DEVICE_TOPIC}#")
        client.subscribe(f"{TELEMETRY_TOPIC}#")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the server"""
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
    else:
        logger.info("Disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the server"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        logger.debug(f"Received message on topic {topic}: {payload}")

        # Process message based on topic
        if topic.startswith(DEVICE_TOPIC):
            process_device_message(topic, payload)
        elif topic.startswith(TELEMETRY_TOPIC):
            process_telemetry_message(topic, payload)
    except Exception as e:
        logger.error(f"Error processing MQTT message: {str(e)}")

def process_device_message(topic, payload):
    """Process device status messages"""
    try:
        # Extract device ID from topic
        device_id = topic.replace(DEVICE_TOPIC, "").split("/")[0]
        data = json.loads(payload)

        # Import here to avoid circular imports
        from app.models.device import Device
        from app import db

        # Find the device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            logger.warning(f"Received message for unknown device: {device_id}")
            return

        # Update device status
        if "status" in data:
            device.status = data["status"]

        if "power_state" in data:
            device.power_state = data["power_state"]

        if "firmware_version" in data:
            device.firmware_version = data["firmware_version"]

        device.last_updated = datetime.utcnow()
        db.session.commit()

        logger.info(f"Updated device {device_id} status: {data}")

        # Check if we need to send notifications for this status change
        if "status" in data and data["status"] == "error":
            send_device_error_notification(device)

    except Exception as e:
        logger.error(f"Error processing device message: {str(e)}")

def process_telemetry_message(topic, payload):
    """Process device telemetry/sensor data messages"""
    try:
        # Extract device ID from topic
        device_id = topic.replace(TELEMETRY_TOPIC, "").split("/")[0]
        data = json.loads(payload)

        # Import here to avoid circular imports
        from app.models.device import Device
        from app.models.power_usage import PowerReading
        from app import db

        # Find the device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            logger.warning(f"Received telemetry for unknown device: {device_id}")
            return

        # Update current power in device record
        if "power" in data:
            device.current_power = float(data["power"])
            device.last_updated = datetime.utcnow()
            db.session.commit()

        # Create power reading record
        if all(k in data for k in ["power", "voltage", "current"]):
            power_reading = PowerReading(
                device_id=device.id,
                power_usage=float(data["power"]),
                voltage=float(data["voltage"]),
                current=float(data["current"]),
                power_factor=float(data.get("power_factor", 0.0)),
                energy_consumed=float(data.get("energy", 0.0))
            )
            db.session.add(power_reading)
            db.session.commit()

            logger.debug(f"Recorded power reading for {device_id}: {data['power']}W")

            # Check for power thresholds and send alerts if needed
            check_power_thresholds(device, float(data["power"]))

    except Exception as e:
        logger.error(f"Error processing telemetry message: {str(e)}")

def send_device_control(device_id, command, value=None):
    """
    Send control command to a device

    Args:
        device_id (str): Device ID
        command (str): Command name (e.g., 'power', 'reset')
        value: Command value

    Returns:
        bool: Success or failure
    """
    if not mqtt_client:
        logger.error("MQTT client not initialized")
        return False

    topic = f"{CONTROL_TOPIC}{device_id}"
    payload = {"command": command}

    if value is not None:
        payload["value"] = value

    try:
        mqtt_client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Sent command {command} to device {device_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send command to device: {str(e)}")
        return False

def check_power_thresholds(device, power_usage):
    """Check if power usage exceeds thresholds and send alerts if needed"""
    from app.models.user import User
    from app.models.notification import Notification, NotificationSetting
    from app import db

    # Get warning and critical thresholds
    notification_setting = NotificationSetting.query.filter_by(user_id=device.user_id).first()

    # Use default thresholds if not set
    warning_threshold = notification_setting.power_threshold_warning if notification_setting else current_app.config.get('POWER_WARNING_THRESHOLD')
    critical_threshold = notification_setting.power_threshold_critical if notification_setting else current_app.config.get('POWER_CRITICAL_THRESHOLD')

    # Check if power usage exceeds critical threshold
    if power_usage > critical_threshold:
        # Create critical notification
        notification = Notification(
            title=f"Critical Power Usage: {device.name}",
            message=f"Device '{device.name}' is consuming {power_usage:.2f}W, which exceeds the critical threshold of {critical_threshold:.2f}W.",
            notification_type="alert",
            user_id=device.user_id,
            device_id=device.id,
            send_sms=True if notification_setting and notification_setting.receive_sms else False,
            send_email=True if notification_setting and notification_setting.receive_email else False
        )
        db.session.add(notification)
        db.session.commit()

        # Send SMS if enabled
        if notification.send_sms:
            from app.africastalking.sms import get_sms_service
            user = User.query.get(device.user_id)
            if user:
                sms_service = get_sms_service()
                sms_service.send_power_alert(user.phone_number, device.name, power_usage, critical_threshold)

                # Update notification status
                notification.sms_sent = True
                db.session.commit()

    # Check if power usage exceeds warning threshold but is below critical
    elif power_usage > warning_threshold:
        # Check if we already sent a warning recently (in the last hour)
        from datetime import timedelta
        recent_warning = Notification.query.filter_by(
            device_id=device.id,
            notification_type="warning"
        ).filter(
            Notification.timestamp > datetime.utcnow() - timedelta(hours=1)
        ).first()

        if not recent_warning:
            # Create warning notification
            notification = Notification(
                title=f"High Power Usage: {device.name}",
                message=f"Device '{device.name}' is consuming {power_usage:.2f}W, which exceeds the warning threshold of {warning_threshold:.2f}W.",
                notification_type="warning",
                user_id=device.user_id,
                device_id=device.id,
                send_sms=False,  # Only send SMS for critical alerts
                send_email=True if notification_setting and notification_setting.receive_email else False
            )
            db.session.add(notification)
            db.session.commit()

def send_device_error_notification(device):
    """Send notification for device error"""
    from app.models.user import User
    from app.models.notification import Notification, NotificationSetting
    from app import db

    # Create error notification
    notification = Notification(
        title=f"Device Error: {device.name}",
        message=f"Device '{device.name}' has reported an error status. Please check the device.",
        notification_type="alert",
        user_id=device.user_id,
        device_id=device.id,
        send_sms=True,  # Always send SMS for device errors
        send_email=True
    )
    db.session.add(notification)
    db.session.commit()

    # Send SMS
    from app.africastalking.sms import get_sms_service
    user = User.query.get(device.user_id)
    if user:
        sms_service = get_sms_service()
        sms_service.send_message(
            [user.phone_number],
            f"ALERT: Your device '{device.name}' has reported an error. Please check your system."
        )

        # Update notification status
        notification.sms_sent = True
        db.session.commit()