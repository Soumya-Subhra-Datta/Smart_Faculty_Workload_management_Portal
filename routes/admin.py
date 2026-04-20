"""
Admin routes — Faculty management, duty management, substitutions, dashboard.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import user as user_model
from models import event as event_model
from models import substitution as sub_model
from models import notification as notif_model
from models import timetable as timetable_model
from services.substitution_engine import auto_assign_substitute
from services.csv_handler import parse_duty_csv
from services.email_service import send_faculty_email_async
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def admin_required(fn):
    """Decorator to ensure the user is an admin."""
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Dashboard ──

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """Get admin dashboard statistics."""
    stats = event_model.get_dashboard_stats()
    workload = sub_model.get_workload_analytics()
    return jsonify({'stats': stats, 'workload': workload}), 200


# ── Faculty Management ──

@admin_bp.route('/faculty', methods=['GET'])
@admin_required
def get_faculty():
    """Get all faculty members."""
    faculty = user_model.get_all_faculty()
    return jsonify({'faculty': faculty}), 200


@admin_bp.route('/faculty', methods=['POST'])
@admin_required
def add_faculty():
    """Add a new faculty member."""
    data = request.get_json()
    required = ['username', 'full_name', 'email', 'department']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    try:
        faculty_id = user_model.create_faculty(data)
        return jsonify({'message': 'Faculty added successfully', 'id': faculty_id}), 201
    except Exception as e:
        if 'Duplicate' in str(e):
            return jsonify({'error': 'Username or email already exists'}), 409
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/faculty/<int:faculty_id>', methods=['PUT'])
@admin_required
def update_faculty(faculty_id):
    """Update a faculty member."""
    data = request.get_json()
    rows = user_model.update_faculty(faculty_id, data)
    if rows == 0:
        return jsonify({'error': 'Faculty not found'}), 404
    return jsonify({'message': 'Faculty updated successfully'}), 200


@admin_bp.route('/faculty/<int:faculty_id>', methods=['DELETE'])
@admin_required
def delete_faculty(faculty_id):
    """Delete a faculty member."""
    rows = user_model.delete_faculty(faculty_id)
    if rows == 0:
        return jsonify({'error': 'Faculty not found'}), 404
    return jsonify({'message': 'Faculty deleted successfully'}), 200


@admin_bp.route('/faculty/<int:faculty_id>/timetable', methods=['GET'])
@admin_required
def get_faculty_timetable(faculty_id):
    """Get a faculty member's timetable."""
    timetable = timetable_model.get_faculty_timetable(faculty_id)
    return jsonify({'timetable': timetable}), 200


# ── Duty Management ──

@admin_bp.route('/duties', methods=['GET'])
@admin_required
def get_duties():
    """Get all duties/events."""
    events = event_model.get_all_events()
    # Convert timedelta and date objects to strings
    for e in events:
        for key in e:
            if hasattr(e[key], 'isoformat'):
                e[key] = e[key].isoformat() if hasattr(e[key], 'isoformat') else str(e[key])
            elif hasattr(e[key], 'total_seconds'):
                total = int(e[key].total_seconds())
                hours, remainder = divmod(total, 3600)
                minutes, seconds = divmod(remainder, 60)
                e[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return jsonify({'duties': events}), 200


@admin_bp.route('/duties', methods=['POST'])
@admin_required
def create_duty():
    """Create a new duty and auto-assign substitutes."""
    data = request.get_json()
    required = ['event_name', 'date', 'start_time', 'end_time', 'venue', 'assigned_faculty_id']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    admin_id = int(get_jwt_identity())
    data['created_by'] = admin_id

    # Import the time restriction check
    from services.substitution_engine import _is_time_restricted

    # Check if duty time overlaps with break or lunch
    if _is_time_restricted(data['start_time'], data['end_time']):
        return jsonify({'error': 'Duties cannot be assigned during break or lunch periods'}), 400

    # Check for existing duty clash
    has_duty_clash = event_model.check_duty_clash(
        data['assigned_faculty_id'], data['date'], data['start_time'], data['end_time']
    )
    if has_duty_clash:
        return jsonify({'error': 'Faculty has a conflicting duty at this time'}), 409

    # Check for existing substitution clash
    has_sub_clash = sub_model.check_substitution_clash(
        data['assigned_faculty_id'], data['date'], data['start_time'], data['end_time']
    )
    if has_sub_clash:
        return jsonify({'error': 'Faculty has a substitution assigned at this time'}), 409

    try:
        print(f"[DEBUG] Creating duty for faculty {data['assigned_faculty_id']} on {data['date']} {data['start_time']}-{data['end_time']}")

        # Create the event
        event_id = event_model.create_event(data)
        print(f"[DEBUG] Event created with ID {event_id}")

        # Get faculty email
        faculty = user_model.get_by_id(data['assigned_faculty_id'])
        if not faculty:
            return jsonify({'error': 'Faculty not found'}), 404
        to_email = faculty['email']

        # Notify the assigned faculty
        msg = f'You have been assigned to "{data["event_name"]}" on {data["date"]} from {data["start_time"]} to {data["end_time"]} at {data["venue"]}.'
        notif_model.create_notification(
            user_id=data['assigned_faculty_id'],
            title='New Duty Assignment',
            message=msg,
            notif_type='duty_assignment'
        )
        send_faculty_email_async("New Duty Assignment", msg, to_email)

        # Auto-assign substitutes using AI engine
        substitutions = auto_assign_substitute(
            event_id=event_id,
            original_faculty_id=data['assigned_faculty_id'],
            date=data['date'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        print(f"[DEBUG] Created {len(substitutions)} substitutions")

        # Notify substitute faculty
        for sub in substitutions:
            sub_faculty = user_model.get_by_id(sub['substitute_faculty_id'])
            sub_to_email = sub_faculty['email'] if sub_faculty else 'soumyasubhradatta@gmail.com'
            sub_msg = f'You have been assigned as a substitute for {sub["subject"]} in {sub["classroom"]} on {data["date"]} from {sub["start_time"]} to {sub["end_time"]}.'
            notif_model.create_notification(
                user_id=sub['substitute_faculty_id'],
                title='Substitution Assignment',
                message=sub_msg,
                notif_type='substitution'
            )
            send_faculty_email_async("Substitution Assignment", sub_msg, sub_to_email)

        return jsonify({
            'message': 'Duty created successfully',
            'event_id': event_id,
            'substitutions_created': len(substitutions),
            'substitutions': substitutions
        }), 201

    except Exception as e:
        print(f"[ERROR] Duty creation failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/duties/<int:event_id>/cancel', methods=['PUT'])
@admin_required
def cancel_duty(event_id):
    """Cancel a duty and its associated substitutions."""
    event = event_model.get_event_by_id(event_id)
    if not event:
        return jsonify({'error': 'Duty not found'}), 404

    if event['status'] in ('cancelled', 'completed'):
        return jsonify({'error': f'Duty already {event["status"]}'}), 400

    # Cancel the event
    event_model.cancel_event(event_id)

    # Get and cancel substitutions
    subs = sub_model.get_substitutions_by_event(event_id)
    sub_model.cancel_substitutions_by_event(event_id)

    # Notify the assigned faculty
    notif_model.create_notification(
        user_id=event['assigned_faculty_id'],
        title='Duty Cancelled',
        message=f'Your duty "{event["event_name"]}" on {event["date"]} has been cancelled.',
        notif_type='cancellation'
    )

    # Notify substitute faculty
    for sub in subs:
        if sub['status'] == 'assigned':
            notif_model.create_notification(
                user_id=sub['substitute_faculty_id'],
                title='Substitution Cancelled',
                message=f'Your substitution for {sub["subject"]} in {sub["classroom"]} has been cancelled as the duty was cancelled.',
                notif_type='cancellation'
            )

    return jsonify({
        'message': 'Duty cancelled successfully',
        'substitutions_cancelled': len(subs)
    }), 200


@admin_bp.route('/duties/clear', methods=['DELETE'])
@admin_required
def clear_duty_history():
    """Clear history of completed and cancelled duties."""
    try:
        deleted = event_model.clear_duty_history()
        return jsonify({'message': f'Cleared {deleted} completed/cancelled duties'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── CSV Upload ──

@admin_bp.route('/duties/upload-csv', methods=['POST'])
@admin_required
def upload_csv():
    """Upload CSV file for bulk duty creation."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    content = file.read().decode('utf-8')
    result = parse_duty_csv(content)

    if result['errors']:
        return jsonify({'errors': result['errors'], 'parsed': len(result['duties'])}), 400

    admin_id = int(get_jwt_identity())
    created_events = []

    for duty in result['duties']:
        duty['created_by'] = admin_id
        try:
            event_id = event_model.create_event(duty)

            # Notify faculty
            msg = f'You have been assigned to "{duty["event_name"]}" on {duty["date"]} from {duty["start_time"]} to {duty["end_time"]} at {duty["venue"]}.'
            notif_model.create_notification(
                user_id=duty['assigned_faculty_id'],
                title='New Duty Assignment',
                message=msg,
                notif_type='duty_assignment'
            )
            send_faculty_email_async("New Duty Assignment", msg)

            # Auto-assign substitutes
            subs = auto_assign_substitute(
                event_id=event_id,
                original_faculty_id=duty['assigned_faculty_id'],
                date=duty['date'],
                start_time=duty['start_time'],
                end_time=duty['end_time']
            )

            for sub in subs:
                sub_msg = f'You have been assigned as a substitute for {sub["subject"]} in {sub["classroom"]} on {duty["date"]}.'
                notif_model.create_notification(
                    user_id=sub['substitute_faculty_id'],
                    title='Substitution Assignment',
                    message=sub_msg,
                    notif_type='substitution'
                )
                send_faculty_email_async("Substitution Assignment", sub_msg)

            created_events.append({
                'event_id': event_id,
                'event_name': duty['event_name'],
                'faculty': duty['faculty_name'],
                'substitutions': len(subs)
            })
        except Exception as e:
            created_events.append({
                'event_name': duty['event_name'],
                'error': str(e)
            })

    return jsonify({
        'message': f'Processed {len(created_events)} duties from CSV',
        'results': created_events
    }), 201


# ── Substitutions ──

@admin_bp.route('/substitutions', methods=['GET'])
@admin_required
def get_substitutions():
    """Get all substitutions."""
    subs = sub_model.get_all_substitutions()
    for s in subs:
        for key in s:
            if hasattr(s[key], 'isoformat'):
                s[key] = s[key].isoformat() if hasattr(s[key], 'isoformat') else str(s[key])
            elif hasattr(s[key], 'total_seconds'):
                total = int(s[key].total_seconds())
                hours, remainder = divmod(total, 3600)
                minutes, seconds = divmod(remainder, 60)
                s[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return jsonify({'substitutions': subs}), 200
