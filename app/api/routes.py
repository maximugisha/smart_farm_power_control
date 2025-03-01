from flask import jsonify, request, current_app
from functools import wraps
import datetime
import logging

from app.api import api_bp
from app.models.user import User
from app import db

logger = logging.getLogger(__name__)

# API authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        # Find user with this API key
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Add user to kwargs
        kwargs['user'] = user
        return f(*args, **kwargs)

    return decorated_function

# Basic JWT token auth decorator (simplified for this example)
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            # In a real app, verify JWT signature and extract user_id
            # This is simplified for the example
            import jwt
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )
            user = User.query.get(data['user_id'])

            if not user:
                return jsonify({'error': 'Invalid token'}), 401

        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401

        # Add user to kwargs
        kwargs['current_user'] = user
        return f(*args, **kwargs)

    return decorated_function

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/login', methods=['POST'])
def login():
    """API login endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Find user
    user = User.query.filter_by(email=email).first()

    if not user or not user.verify_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Generate JWT token
    import jwt
    token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }

    token = jwt.encode(
        token_payload,
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    # Update last login
    user.last_login = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'farm_name': user.farm_name,
            'is_admin': user.is_admin
        }
    })

@api_bp.route('/register', methods=['POST'])
def register():
    """API register endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name', 'phone_number']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        full_name=data['full_name'],
        phone_number=data['phone_number'],
        farm_name=data.get('farm_name', ''),
        password=data['password']  # This is properly hashed in the model
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id
    }), 201

@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/docs', methods=['GET'])
def api_docs():
    """API documentation endpoint"""
    return jsonify({
        'api_version': '1.0.0',
        'endpoints': [
            {
                'path': '/api/health',
                'method': 'GET',
                'description': 'Check API health status',
                'auth_required': False
            },
            {
                'path': '/api/login',
                'method': 'POST',
                'description': 'Authenticate and get token',
                'auth_required': False,
                'request_body': {
                    'email': 'user@example.com',
                    'password': 'password'
                }
            },
            {
                'path': '/api/register',
                'method': 'POST',
                'description': 'Register new user',
                'auth_required': False,
                'request_body': {
                    'username': 'username',
                    'email': 'user@example.com',
                    'password': 'password',
                    'full_name': 'Full Name',
                    'phone_number': '1234567890',
                    'farm_name': 'My Farm'
                }
            },
            {
                'path': '/api/devices',
                'method': 'GET',
                'description': 'Get all devices',
                'auth_required': True
            },
            {
                'path': '/api/power/summary',
                'method': 'GET',
                'description': 'Get power usage summary',
                'auth_required': True,
                'query_params': {
                    'period': 'day|week|month|custom',
                    'start_date': 'YYYY-MM-DD (for custom period)',
                    'end_date': 'YYYY-MM-DD (for custom period)'
                }
            }
        ]
    })