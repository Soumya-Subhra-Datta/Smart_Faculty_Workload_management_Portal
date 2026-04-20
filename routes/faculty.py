"""
Faculty routes — Timetable, duties, notifications.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import user as user_model
from models import timetable as timetable_model
from models import event as event_model
from models import substitution as sub_model
from models import notification as notif_model

faculty_bp = Blueprint('faculty', __name__, url_prefix='/api/faculty')


# ── Timetable ──

@faculty_bp.route('/timetable', methods=['GET'])
@jwt_required()
def get_timetable():
    """Get the current faculty's timetable."""
    user_id = int(get_jwt_identity())
    timetable = timetable_model.get_faculty_timetable(user_id)
    # Convert timedelta objects to strings
    for entry in timetable:
        for key in entry:
            if hasattr(entry[key], 'total_seconds'):
                total = int(entry[key].total_seconds())
                hours, remainder = divmod(total, 3600)
                minutes, seconds = divmod(remainder, 60)
                entry[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return jsonify({'timetable': timetable}), 200


# ── Duties ──

@faculty_bp.route('/duties', methods=['GET'])
@jwt_required()
def get_duties():
    """Get duties assigned to the current faculty."""
    user_id = int(get_jwt_identity())
    events = event_model.get_events_by_faculty(user_id)
    for e in events:
        for key in e:
            if hasattr(e[key], 'isoformat'):
                e[key] = e[key].isoformat()
            elif hasattr(e[key], 'total_seconds'):
                total = int(e[key].total_seconds())
                hours, remainder = divmod(total, 3600)
                minutes, seconds = divmod(remainder, 60)
                e[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return jsonify({'duties': events}), 200


# ── Substitutions ──

@faculty_bp.route('/substitutions', methods=['GET'])
@jwt_required()
def get_substitutions():
    """Get substitutions involving the current faculty (as original or substitute)."""
    user_id = int(get_jwt_identity())
    subs = sub_model.get_substitutions_by_faculty(user_id)
    for s in subs:
        for key in s:
            if hasattr(s[key], 'isoformat'):
                s[key] = s[key].isoformat()
            elif hasattr(s[key], 'total_seconds'):
                total = int(s[key].total_seconds())
                hours, remainder = divmod(total, 3600)
                minutes, seconds = divmod(remainder, 60)
                s[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return jsonify({'substitutions': subs}), 200


# ── Notifications ──

@faculty_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get all notifications for the current faculty."""
    user_id = int(get_jwt_identity())
    notifications = notif_model.get_notifications(user_id)
    unread_count = notif_model.get_unread_count(user_id)
    for n in notifications:
        if hasattr(n.get('created_at'), 'isoformat'):
            n['created_at'] = n['created_at'].isoformat()
    return jsonify({
        'notifications': notifications,
        'unread_count': unread_count
    }), 200


@faculty_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    user_id = int(get_jwt_identity())
    notif_model.mark_as_read(notification_id, user_id)
    return jsonify({'message': 'Notification marked as read'}), 200


@faculty_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read."""
    user_id = int(get_jwt_identity())
    notif_model.mark_all_as_read(user_id)
    return jsonify({'message': 'All notifications marked as read'}), 200


@faculty_bp.route('/notifications/clear', methods=['DELETE'])
@jwt_required()
def clear_notifications():
    """Clear all read notifications (history)."""
    user_id = int(get_jwt_identity())
    deleted = notif_model.clear_read_notifications(user_id)
    return jsonify({'message': f'Cleared {deleted} read notifications'}), 200
