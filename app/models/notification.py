from datetime import datetime
from app import db

class Notification(db.Model):
    """Model for system notifications and alerts"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    notification_type = db.Column(db.String(20), nullable=False)  # alert, warning, info
    is_read = db.Column(db.Boolean, default=False)

    # Delivery methods
    send_sms = db.Column(db.Boolean, default=False)
    send_email = db.Column(db.Boolean, default=False)
    send_push = db.Column(db.Boolean, default=True)

    # SMS/Email delivery status
    sms_sent = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    def __repr__(self):
        return f'<Notification {self.notification_type}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'user_id': self.user_id,
            'device_id': self.device_id
        }

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        db.session.commit()
        return self.is_read

class NotificationSetting(db.Model):
    """Model for user notification preferences"""
    __tablename__ = 'notification_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Threshold settings
    power_threshold_warning = db.Column(db.Float)  # warning threshold in watts
    power_threshold_critical = db.Column(db.Float)  # critical threshold in watts

    # Notification preferences
    alert_on_high_power = db.Column(db.Boolean, default=True)
    alert_on_device_offline = db.Column(db.Boolean, default=True)
    alert_on_schedule_failure = db.Column(db.Boolean, default=True)

    # Delivery preferences
    receive_sms = db.Column(db.Boolean, default=True)
    receive_email = db.Column(db.Boolean, default=True)
    receive_push = db.Column(db.Boolean, default=True)

    # Time restrictions
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)

    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    def __repr__(self):
        return f'<NotificationSetting for user_id: {self.user_id}>'