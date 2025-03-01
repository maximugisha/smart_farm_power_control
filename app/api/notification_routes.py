from flask import jsonify, request
from app.api import api_bp
from app.api.routes import token_required
from app.models.notification import Notification
from app import db

import logging
logger = logging.getLogger(__name__)

@api_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    """
    Get user notifications

    Query Parameters:
        unread_only (bool): Filter to only unread notifications
        limit (int): Maximum number of notifications to return
        offset (int): Offset for pagination

    Returns:
        JSON: List of notifications
    """
    # Parse query parameters
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Build query
    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(is_read=False)

    # Get total count before applying pagination
    total_count = query.count()

    # Apply sorting and pagination
    notifications = query.order_by(Notification.timestamp.desc()) \
        .offset(offset) \
        .limit(limit) \
        .all()

    return jsonify({
        'notifications': [notification.to_dict() for notification in notifications],
        'count': len(notifications),
        'total_count': total_count,
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })

@api_bp.route('/notifications/<int:notification_id>', methods=['GET'])
@token_required
def get_notification(current_user, notification_id):
    """
    Get a specific notification

    Args:
        notification_id (int): Notification ID

    Returns:
        JSON: Notification details
    """
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({
        'notification': notification.to_dict()
    })

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@token_required
def mark_notification_read(current_user, notification_id):
    """
    Mark a notification as read

    Args:
        notification_id (int): Notification ID

    Returns:
        JSON: Success message
    """
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    notification.mark_as_read()

    return jsonify({
        'message': 'Notification marked as read',
        'notification_id': notification_id
    })

@api_bp.route('/notifications/read-all', methods=['POST'])
@token_required
def mark_all_notifications_read(current_user):
    """
    Mark all notifications as read

    Returns:
        JSON: Success message and count
    """
    # Get all unread notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    # Mark all as read
    count = 0
    for notification in notifications:
        notification.is_read = True
        count += 1

    db.session.commit()

    return jsonify({
        'message': 'All notifications marked as read',
        'count': count
    })

@api_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@token_required
def delete_notification(current_user, notification_id):
    """
    Delete a notification

    Args:
        notification_id (int): Notification ID

    Returns:
        JSON: Success message
    """
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    db.session.delete(notification)
    db.session.commit()

    return jsonify({
        'message': 'Notification deleted',
        'notification_id': notification_id
    })

@api_bp.route('/notifications/clear-all', methods=['DELETE'])
@token_required
def clear_all_notifications(current_user):
    """
    Delete all notifications for the user

    Returns:
        JSON: Success message and count
    """
    # Get all notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).all()

    # Delete all
    count = 0
    for notification in notifications:
        db.session.delete(notification)
        count += 1

    db.session.commit()

    return jsonify({
        'message': 'All notifications cleared',
        'count': count
    })

@api_bp.route('/notifications/unread-count', methods=['GET'])
@token_required
def get_unread_count(current_user):
    """
    Get count of unread notifications

    Returns:
        JSON: Unread count
    """
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({
        'unread_count': count
    })