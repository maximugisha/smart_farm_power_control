from datetime import datetime
from app import db

class PowerReading(db.Model):
    """Model for power readings from devices"""
    __tablename__ = 'power_readings'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    power_usage = db.Column(db.Float, nullable=False)  # power usage in watts
    voltage = db.Column(db.Float)  # voltage in volts
    current = db.Column(db.Float)  # current in amps
    power_factor = db.Column(db.Float)  # power factor (0-1)
    energy_consumed = db.Column(db.Float)  # cumulative energy in kWh

    # Foreign Key
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)

    def __repr__(self):
        return f'<PowerReading {self.timestamp}: {self.power_usage}W>'

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'power_usage': self.power_usage,
            'voltage': self.voltage,
            'current': self.current,
            'power_factor': self.power_factor,
            'energy_consumed': self.energy_consumed,
            'device_id': self.device_id
        }

class PowerSummary(db.Model):
    """Model for daily, weekly, and monthly power usage summaries"""
    __tablename__ = 'power_summaries'

    id = db.Column(db.Integer, primary_key=True)
    summary_type = db.Column(db.String(10), nullable=False)  # daily, weekly, monthly
    date = db.Column(db.Date, nullable=False)
    total_energy = db.Column(db.Float, nullable=False)  # total energy in kWh
    peak_power = db.Column(db.Float)  # peak power in watts
    average_power = db.Column(db.Float)  # average power in watts
    cost_estimate = db.Column(db.Float)  # cost estimate in local currency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Key - can be null for farm-wide summaries
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    def __repr__(self):
        return f'<PowerSummary {self.summary_type} {self.date}: {self.total_energy}kWh>'

class EnergyRate(db.Model):
    """Model for storing energy rate information for cost calculations"""
    __tablename__ = 'energy_rates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rate_per_kwh = db.Column(db.Float, nullable=False)  # rate per kWh in local currency
    currency = db.Column(db.String(3), default='USD')
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_to = db.Column(db.DateTime)  # null means currently active
    is_time_of_use = db.Column(db.Boolean, default=False)  # if true, uses the time of day pricing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Only used if is_time_of_use is True
    peak_start_time = db.Column(db.Time)
    peak_end_time = db.Column(db.Time)
    peak_rate = db.Column(db.Float)
    off_peak_rate = db.Column(db.Float)

    def __repr__(self):
        return f'<EnergyRate {self.name}: {self.rate_per_kwh}>'