from datetime import datetime
from app import db

class Device(db.Model):
    """Device model for power-consuming farm equipment"""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='offline')  # online, offline, error
    power_state = db.Column(db.Boolean, default=False)    # on/off
    current_power = db.Column(db.Float, default=0.0)      # current power usage in watts
    max_power = db.Column(db.Float)                      # max power capacity in watts
    device_id = db.Column(db.String(50), unique=True, nullable=False)  # unique identifier for IoT
    firmware_version = db.Column(db.String(20))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    power_readings = db.relationship('PowerReading', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='device', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Device {self.name} ({self.device_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'location': self.location,
            'status': self.status,
            'power_state': self.power_state,
            'current_power': self.current_power,
            'max_power': self.max_power,
            'device_id': self.device_id,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def update_power_state(self, state):
        """Update the power state of the device"""
        self.power_state = state
        self.last_updated = datetime.utcnow()
        db.session.commit()
        return self.power_state

    def update_status(self, status):
        """Update the status of the device"""
        self.status = status
        self.last_updated = datetime.utcnow()
        db.session.commit()
        return self.status

class DeviceType(db.Model):
    """Device type categorization"""
    __tablename__ = 'device_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    typical_power = db.Column(db.Float)  # typical power consumption in watts
    icon = db.Column(db.String(50))      # icon name for UI

    def __repr__(self):
        return f'<DeviceType {self.name}>'