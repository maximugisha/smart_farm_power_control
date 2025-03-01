from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from app.api import routes, device_routes, power_routes, user_routes, notification_routes