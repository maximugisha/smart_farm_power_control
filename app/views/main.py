from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Basic validation
        if not name or not email or not message:
            flash('Please fill in all fields', 'danger')
            return render_template('contact.html')

        # In a real app, send email or save to database
        # For this example, just show a confirmation message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.index'))

    return render_template('contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/download')
def download():
    """Download page for IoT firmware and mobile app links"""
    return render_template('download.html')

@main_bp.route('/documentation')
def documentation():
    """Documentation page"""
    return render_template('documentation.html')

# Error handlers
@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500

@main_bp.context_processor
def utility_processor():
    """Add utility functions to templates"""

    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """Format a datetime object"""
        if value is None:
            return ""
        return value.strftime(format)

    def format_watts(watts, precision=1):
        """Format power in watts with proper units"""
        if watts is None:
            return "0 W"

        if watts >= 1000:
            return f"{watts/1000:.{precision}f} kW"
        else:
            return f"{watts:.{precision}f} W"

    return dict(
        format_datetime=format_datetime,
        format_watts=format_watts,
        app_name="Smart Farm Power Control"
    )