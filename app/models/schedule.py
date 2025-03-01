from datetime import datetime
from app import db

class Schedule(db.Model):
    """Model for device power scheduling"""
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Recurrence
    days_of_week = db.Column(db.String(20))  # '0,1,2,3,4,5,6' for days (0=Monday)
    is_active = db.Column(db.Boolean, default=True)
    is_one_time = db.Column(db.Boolean, default=False)
    one_time_date = db.Column(db.Date)  # Only used if is_one_time is True

    # Action to perform
    action = db.Column(db.String(10), nullable=False)  # 'turn_on', 'turn_off', 'toggle'

    # Conditions
    conditional = db.Column(db.Boolean, default=False)
    condition_type = db.Column(db.String(20))  # 'power_threshold', 'time_of_day', 'weather'
    condition_value = db.Column(db.String(50))  # Threshold or condition value

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Schedule {self.name}: {self.action} at {self.start_time}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'days_of_week': self.days_of_week,
            'is_active': self.is_active,
            'is_one_time': self.is_one_time,
            'one_time_date': self.one_time_date.isoformat() if self.one_time_date else None,
            'action': self.action,
            'conditional': self.conditional,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'device_id': self.device_id,
            'user_id': self.user_id
        }

    def toggle_active(self):
        """Toggle the active state of the schedule"""
        self.is_active = not self.is_active
        db.session.commit()
        return self.is_active

class ScheduleExecution(db.Model):
    """Model for tracking schedule execution history"""
    __tablename__ = 'schedule_executions'

    id = db.Column(db.Integer, primary_key=True)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)  # success, failed, skipped
    result_message = db.Column(db.Text)

    # Foreign Key
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)

    def __repr__(self):
        return f'<ScheduleExecution {self.schedule_id}: {self.status}>'