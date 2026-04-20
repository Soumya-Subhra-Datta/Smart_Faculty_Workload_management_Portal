"""
Substitution model — CRUD operations for substitutions table.
"""
from models.db import execute_query


def create_substitution(data):
    """Create a new substitution assignment."""
    return execute_query(
        """INSERT INTO substitutions (event_id, original_faculty_id, substitute_faculty_id, 
           subject, classroom, date, start_time, end_time, status, reason)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'assigned', %s)""",
        (data['event_id'], data['original_faculty_id'], data['substitute_faculty_id'],
         data['subject'], data['classroom'], data['date'],
         data['start_time'], data['end_time'], data.get('reason', 'Duty assignment')),
        commit=True
    )


def get_all_substitutions():
    """Get all substitutions with faculty details."""
    return execute_query(
        """SELECT s.*, 
           u1.full_name as original_faculty_name, u1.department as original_department,
           u2.full_name as substitute_faculty_name, u2.department as substitute_department
           FROM substitutions s
           JOIN users u1 ON s.original_faculty_id = u1.id
           JOIN users u2 ON s.substitute_faculty_id = u2.id
           ORDER BY s.date DESC, s.start_time DESC""",
        fetch_all=True
    )


def get_substitutions_by_faculty(faculty_id):
    """Get substitutions where faculty is either original or substitute."""
    return execute_query(
        """SELECT s.*, 
           u1.full_name as original_faculty_name, u1.department as original_department,
           u2.full_name as substitute_faculty_name, u2.department as substitute_department
           FROM substitutions s
           JOIN users u1 ON s.original_faculty_id = u1.id
           JOIN users u2 ON s.substitute_faculty_id = u2.id
           WHERE s.original_faculty_id = %s OR s.substitute_faculty_id = %s
           ORDER BY s.date DESC, s.start_time DESC""",
        (faculty_id, faculty_id), fetch_all=True
    )


def get_substitutions_by_event(event_id):
    """Get all substitutions for a given event."""
    return execute_query(
        """SELECT s.*, 
           u1.full_name as original_faculty_name,
           u2.full_name as substitute_faculty_name
           FROM substitutions s
           JOIN users u1 ON s.original_faculty_id = u1.id
           JOIN users u2 ON s.substitute_faculty_id = u2.id
           WHERE s.event_id = %s""",
        (event_id,), fetch_all=True
    )


def cancel_substitutions_by_event(event_id):
    """Cancel all substitutions for an event."""
    return execute_query(
        "UPDATE substitutions SET status = 'cancelled' WHERE event_id = %s AND status = 'assigned'",
        (event_id,)
    )


def complete_substitutions_by_event(event_id):
    """Mark substitutions as completed for an event."""
    return execute_query(
        "UPDATE substitutions SET status = 'completed' WHERE event_id = %s AND status = 'assigned'",
        (event_id,)
    )


def check_substitution_clash(faculty_id, date, start_time, end_time):
    """Check if a faculty has an existing substitution at the same time."""
    result = execute_query(
        """SELECT COUNT(*) as clash_count FROM substitutions 
           WHERE substitute_faculty_id = %s AND date = %s AND status = 'assigned'
           AND ((start_time < %s AND end_time > %s)
             OR (start_time < %s AND end_time > %s)
             OR (start_time >= %s AND end_time <= %s))""",
        (faculty_id, date, end_time, start_time, end_time, start_time, start_time, end_time),
        fetch_one=True
    )
    return result['clash_count'] > 0


def get_substitution_count(faculty_id):
    """Get the count of active substitutions for a faculty member."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM substitutions WHERE substitute_faculty_id = %s AND status = 'assigned'",
        (faculty_id,), fetch_one=True
    )
    return result['count']


def get_workload_analytics():
    """Get substitution workload analytics per faculty."""
    return execute_query(
        """SELECT u.id, u.full_name, u.department,
           COUNT(CASE WHEN s.status = 'assigned' THEN 1 END) as active_substitutions,
           COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_substitutions,
           COUNT(*) as total_substitutions
           FROM users u
           LEFT JOIN substitutions s ON u.id = s.substitute_faculty_id
           WHERE u.role = 'faculty'
           GROUP BY u.id, u.full_name, u.department
           ORDER BY total_substitutions DESC""",
        fetch_all=True
    )
