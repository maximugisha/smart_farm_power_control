# Smart Farm Power Control System

A comprehensive solution for monitoring and managing power consumption on farms using IoT sensors, real-time analytics, and mobile control.

## Features

- **Real-time Power Monitoring**: Track electricity usage of farm equipment in real-time
- **Remote Device Control**: Turn devices on/off from anywhere via web dashboard or mobile
- **Automated Scheduling**: Create schedules for automatically controlling equipment
- **Power Usage Analytics**: Analyze historical data to optimize energy consumption
- **Alerts & Notifications**: Receive alerts for high power usage, offline devices, or failures
- **SMS & USSD Integration**: Control farm equipment through SMS and USSD codes (via AfricasTalking API)
- **Multi-user Support**: Create accounts for farm workers with different permission levels

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLAlchemy ORM (configurable for SQLite, MySQL, or PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **IoT Communication**: MQTT protocol
- **SMS/USSD**: AfricasTalking API integration
- **API**: RESTful API endpoints with JWT authentication

## System Requirements

- Python 3.8+
- Flask and Flask extensions
- MQTT broker (like Mosquitto, HiveMQ, or AWS IoT)
- AfricasTalking account (for SMS/USSD features)
- SQLite, MySQL, or PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-farm-power-control.git
cd smart-farm-power-control
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## IoT Device Setup

The system is designed to work with ESP8266 or ESP32-based power monitoring devices. The IoT devices should:

1. Connect to the MQTT broker
2. Publish power readings to topic: `smart-farm/telemetry/{device_id}`
3. Subscribe to control commands on topic: `smart-farm/control/{device_id}`

Sample device code is included in the `iot-device-examples` directory.

## Environment Variables

The following environment variables should be set in your `.env` file:

```
# Flask configuration
FLASK_APP=run.py
FLASK_ENV=development  # Change to 'production' for production deployment
SECRET_KEY=your-secret-key-here

# Database URL
DATABASE_URL=sqlite:///smart-farm.db
# For MySQL: mysql://username:password@localhost/db_name
# For PostgreSQL: postgresql://username:password@localhost/db_name

# MQTT Settings
MQTT_BROKER_URL=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# Africa's Talking API
AT_USERNAME=your_africastalking_username
AT_API_KEY=your_africastalking_api_key

# Power thresholds for alerts (in Watts)
POWER_WARNING_THRESHOLD=800
POWER_CRITICAL_THRESHOLD=1200
```

## API Documentation

The system provides a RESTful API for integration with other systems. API documentation can be accessed at `/api/docs` when the application is running.

## AfricasTalking Integration

### SMS Commands

Users can control devices by sending SMS commands to the system. The format is:

```
FARM [COMMAND] [DEVICE_ID]
```

Example: `FARM ON pump1` to turn on the device with ID "pump1"

### USSD Menu

Users can check farm status and control devices through USSD menu:
- Dial the USSD code (e.g., *123#)
- Navigate through menus to view power usage or control devices

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name <your.email@example.com>

## Acknowledgements

- AfricasTalking for providing the SMS/USSD API
- Bootstrap team for the frontend framework
- Flask and SQLAlchemy developers for the excellent Python libraries