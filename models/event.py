"""
Event (Duty) model — CRUD operations for events table.
"""
from models.db import execute_query


def create_event(data):
    """Create a new duty/event."""
    return execute_query(
        """INSERT INTO events (event_name, description, date, start_time, end_time, venue, assigned_faculty_id, status, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 'upcoming', %s)""",
        (data['event_name'], data.get('description', ''), data['date'],
         data['start_time'], data['end_time'], data['venue'],
         data['assigned_faculty_id'], data.get('created_by')),
        commit=True
    )


def get_all_events():
    """Get all events with faculty details."""
    return execute_query(
        """SELECT e.*, u.full_name as faculty_name, u.department as faculty_department
           FROM events e
           JOIN users u ON e.assigned_faculty_id = u.id
           ORDER BY e.date DESC, e.start_time DESC""",
        fetch_all=True
    )


def get_event_by_id(event_id):
    """Get a single event by ID."""
    return execute_query(
        """SELECT e.*, u.full_name as faculty_name, u.department as faculty_department
           FROM events e
           JOIN users u ON e.assigned_faculty_id = u.id
           WHERE e.id = %s""",
        (event_id,), fetch_one=True
    )


def get_events_by_faculty(faculty_id):
    """Get all events assigned to a faculty member."""
    return execute_query(
        """SELECT * FROM events WHERE assigned_faculty_id = %s
           ORDER BY date DESC, start_time DESC""",
        (faculty_id,), fetch_all=True
    )


def get_active_events_by_faculty(faculty_id):
    """Get upcoming/ongoing events for a faculty member."""
    return execute_query(
        """SELECT * FROM events WHERE assigned_faculty_id = %s AND status IN ('upcoming', 'ongoing')
           ORDER BY date, start_time""",
        (faculty_id,), fetch_all=True
    )


def update_event_status(event_id, status):
    """Update the status of an event."""
    return execute_query(
        "UPDATE events SET status = %s WHERE id = %s",
        (status, event_id)
    )


def cancel_event(event_id):
    """Cancel an event."""
    return execute_query(
        "UPDATE events SET status = 'cancelled' WHERE id = %s",
        (event_id,)
    )


def get_events_to_complete():
    """Get events that should be marked as completed (past end time)."""
    return execute_query(
        """SELECT * FROM events 
           WHERE status IN ('upcoming', 'ongoing')
           AND CONCAT(date, ' ', end_time) <= NOW()""",
        fetch_all=True
    )


def check_duty_clash(faculty_id, date, start_time, end_time, exclude_event_id=None):
    """Check if a faculty member has a duty clash."""
    query = """SELECT COUNT(*) as clash_count FROM events 
               WHERE assigned_faculty_id = %s AND date = %s AND status IN ('upcoming', 'ongoing')
               AND ((start_time < %s AND end_time > %s)
                 OR (start_time < %s AND end_time > %s)
                 OR (start_time >= %s AND end_time <= %s))"""
    params = [faculty_id, date, end_time, start_time, end_time, start_time, start_time, end_time]
    
    if exclude_event_id:
        query += " AND id != %s"
        params.append(exclude_event_id)
    
    result = execute_query(query, tuple(params), fetch_one=True)
    return result['clash_count'] > 0


def get_dashboard_stats():
    """Get statistics for the admin dashboard."""
    stats = {}
    stats['total_faculty'] = execute_query(
        "SELECT COUNT(*) as count FROM users WHERE role = 'faculty'",
        fetch_one=True
    )['count']
    stats['active_duties'] = execute_query(
        "SELECT COUNT(*) as count FROM events WHERE status IN ('upcoming', 'ongoing')",
        fetch_one=True
    )['count']
    stats['completed_duties'] = execute_query(
        "SELECT COUNT(*) as count FROM events WHERE status = 'completed'",
        fetch_one=True
    )['count']
    stats['cancelled_duties'] = execute_query(
        "SELECT COUNT(*) as count FROM events WHERE status = 'cancelled'",
        fetch_one=True
    )['count']
    stats['total_substitutions'] = execute_query(
        "SELECT COUNT(*) as count FROM substitutions WHERE status = 'assigned'",
        fetch_one=True
    )['count']
    stats['departments'] = execute_query(
        "SELECT COUNT(DISTINCT department) as count FROM users WHERE role = 'faculty'",
        fetch_one=True
    )['count']
    return stats


def clear_duty_history():
    """Delete all completed or cancelled duties."""
    return execute_query(
        "DELETE FROM events WHERE status IN ('completed', 'cancelled')"
    )

