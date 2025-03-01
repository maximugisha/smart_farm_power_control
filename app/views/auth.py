from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import jwt

from app.models.user import User
from app.models.notification import NotificationSetting
from app.config import Config
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # Check if user already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Validate input
        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('login.html')

        # Find user
        user = User.query.filter_by(email=email).first()

        # Check credentials
        if not user or not user.verify_password(password):
            flash('Invalid email or password', 'danger')
            return render_template('login.html')

        # Log user in
        login_user(user, remember=remember)

        # Update last login time
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()

        # Generate token for API access
        token_payload = {
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }

        token = jwt.encode(
            token_payload,
            Config.SECRET_KEY,
            algorithm="HS256"
        )

        # Check for next URL
        next_url = request.args.get('next')
        if not next_url or not next_url.startswith('/'):
            next_url = url_for('dashboard.index')

        # Add token to session and redirect
        response = redirect(next_url)
        response.set_cookie('api_token', token, httponly=False, max_age=86400)  # 24 hours

        flash('Login successful', 'success')
        return response

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    # Check if user already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        farm_name = request.form.get('farm_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or not email or not full_name or not phone_number or not password:
            flash('Please fill in all required fields', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')

        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            farm_name=farm_name,
            password=password  # Will be hashed in the model
        )

        # Save user to database
        db.session.add(new_user)
        db.session.commit()

        # Create default notification settings
        notification_settings = NotificationSetting(
            user_id=new_user.id,
            power_threshold_warning=Config.POWER_WARNING_THRESHOLD,
            power_threshold_critical=Config.POWER_CRITICAL_THRESHOLD,
            alert_on_high_power=True,
            alert_on_device_offline=True,
            alert_on_schedule_failure=True,
            receive_sms=True,
            receive_email=True,
            receive_push=True
        )
        db.session.add(notification_settings)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')

    # Clear API token cookie
    response = redirect(url_for('main.index'))
    response.delete_cookie('api_token')

    return response

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request page"""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Email is required', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if user:
            # In a real app, send password reset email
            # For this example, just show a confirmation message
            flash('If your email is registered, you will receive a password reset link.', 'info')
        else:
            # Don't reveal that email doesn't exist for security
            flash('If your email is registered, you will receive a password reset link.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset page"""
    # In a real app, verify the token and show reset form
    # For this example, just return a not implemented page
    return render_template('not_implemented.html')