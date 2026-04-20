"""
Notification model — CRUD operations for notifications table.
"""
from models.db import execute_query


def create_notification(user_id, title, message, notif_type='general'):
    """Create a new notification."""
    return execute_query(
        """INSERT INTO notifications (user_id, title, message, type)
           VALUES (%s, %s, %s, %s)""",
        (user_id, title, message, notif_type),
        commit=True
    )


def get_notifications(user_id):
    """Get all notifications for a user, newest first."""
    return execute_query(
        "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,), fetch_all=True
    )


def get_unread_count(user_id):
    """Get count of unread notifications."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE",
        (user_id,), fetch_one=True
    )
    return result['count']


def mark_as_read(notification_id, user_id):
    """Mark a notification as read."""
    return execute_query(
        "UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
        (notification_id, user_id)
    )


def mark_all_as_read(user_id):
    """Mark all notifications as read for a user."""
    return execute_query(
        "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
        (user_id,)
    )


def clear_read_notifications(user_id):
    """Delete all read notifications for a user."""
    return execute_query(
        "DELETE FROM notifications WHERE user_id = %s AND is_read = TRUE",
        (user_id,)
    )
