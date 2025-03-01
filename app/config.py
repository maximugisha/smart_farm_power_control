import os
from datetime import timedelta

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Africa's Talking API settings
    AT_USERNAME = os.environ.get('AT_USERNAME')
    AT_API_KEY = os.environ.get('AT_API_KEY')

    # MQTT Settings for IoT
    MQTT_BROKER_URL = os.environ.get('MQTT_BROKER_URL', 'localhost')
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', 1883))
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
    MQTT_KEEPALIVE = 60
    MQTT_TLS_ENABLED = False

    # Application settings
    DEVICES_PER_PAGE = 10
    NOTIFICATIONS_PER_PAGE = 20

    # Power thresholds for alerts (in Watts)
    POWER_WARNING_THRESHOLD = float(os.environ.get('POWER_WARNING_THRESHOLD', 800))
    POWER_CRITICAL_THRESHOLD = float(os.environ.get('POWER_CRITICAL_THRESHOLD', 1200))

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL',
                                             'sqlite:///dev-smart-farm.db')

class TestingConfig(Config):
    """Testing config."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL',
                                             'sqlite:///test-smart-farm.db')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production config."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Production security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Enable TLS for MQTT in production
    MQTT_TLS_ENABLED = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}