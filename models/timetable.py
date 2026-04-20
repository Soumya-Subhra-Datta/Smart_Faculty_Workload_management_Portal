"""
Timetable model — CRUD operations for timetable table.
"""
from models.db import execute_query
from datetime import datetime


def get_faculty_timetable(faculty_id):
    """Get complete timetable for a faculty member."""
    return execute_query(
        """SELECT * FROM timetable WHERE faculty_id = %s 
           ORDER BY FIELD(day_of_week, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'), period""",
        (faculty_id,), fetch_all=True
    )


def get_faculty_schedule_on_day(faculty_id, day_of_week):
    """Get a faculty member's schedule for a specific day."""
    return execute_query(
        "SELECT * FROM timetable WHERE faculty_id = %s AND day_of_week = %s ORDER BY period",
        (faculty_id, day_of_week), fetch_all=True
    )


def check_timetable_clash(faculty_id, day_of_week, start_time, end_time):
    """Check if a faculty member has a timetable clash at a given time."""
    result = execute_query(
        """SELECT COUNT(*) as clash_count FROM timetable 
           WHERE faculty_id = %s AND day_of_week = %s 
           AND ((start_time < %s AND end_time > %s) 
             OR (start_time < %s AND end_time > %s)
             OR (start_time >= %s AND end_time <= %s))""",
        (faculty_id, day_of_week, end_time, start_time, end_time, start_time, start_time, end_time),
        fetch_one=True
    )
    return result['clash_count'] > 0


def check_timetable_clash_on_date(faculty_id, date, start_time, end_time):
    """Check if a faculty member has a timetable clash on a specific date."""
    date_obj = datetime.strptime(str(date), '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A')
    return check_timetable_clash(faculty_id, day_of_week, start_time, end_time)


def get_faculty_classes_at_time(faculty_id, day_of_week, start_time, end_time):
    """Get the specific classes a faculty has at a given time slot."""
    return execute_query(
        """SELECT * FROM timetable 
           WHERE faculty_id = %s AND day_of_week = %s 
           AND ((start_time < %s AND end_time > %s) 
             OR (start_time < %s AND end_time > %s)
             OR (start_time >= %s AND end_time <= %s))""",
        (faculty_id, day_of_week, end_time, start_time, end_time, start_time, start_time, end_time),
        fetch_all=True
    )
