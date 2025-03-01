from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    # Initialize app
    app = Flask(__name__)

    # Load configurations
    from app.config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)

    # Set login view for Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.views.main import main_bp
    app.register_blueprint(main_bp)

    from app.views.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.views.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize MQTT client for IoT devices
    with app.app_context():
        from app.iot.mqtt_client import setup_mqtt_client
        setup_mqtt_client()

    # Register error handlers
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500