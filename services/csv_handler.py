"""
CSV Handler
============
Parses uploaded CSV files for bulk duty assignment.
Expected CSV columns: event_name, description, date, start_time, end_time, venue, faculty_username
"""
import csv
import io
from models.db import execute_query


def parse_duty_csv(file_content):
    """
    Parse a CSV file content for bulk duty creation.
    
    Args:
        file_content: String content of the CSV file
    
    Returns:
        dict with 'duties' (list of parsed duty dicts) and 'errors' (validation errors)
    """
    duties = []
    errors = []
    
    reader = csv.DictReader(io.StringIO(file_content))
    
    required_columns = ['event_name', 'date', 'start_time', 'end_time', 'venue', 'faculty_username']
    
    # Check headers
    if reader.fieldnames:
        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            return {'duties': [], 'errors': [f"Missing required columns: {', '.join(missing)}"]}
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 = header)
        row_errors = []
        
        # Validate required fields
        for col in required_columns:
            if not row.get(col, '').strip():
                row_errors.append(f"Row {row_num}: Missing '{col}'")
        
        if row_errors:
            errors.extend(row_errors)
            continue
        
        # Look up faculty by username
        faculty = execute_query(
            "SELECT id, full_name FROM users WHERE username = %s AND role = 'faculty'",
            (row['faculty_username'].strip(),), fetch_one=True
        )
        
        if not faculty:
            errors.append(f"Row {row_num}: Faculty '{row['faculty_username']}' not found")
            continue
        
        duties.append({
            'event_name': row['event_name'].strip(),
            'description': row.get('description', '').strip(),
            'date': row['date'].strip(),
            'start_time': row['start_time'].strip(),
            'end_time': row['end_time'].strip(),
            'venue': row['venue'].strip(),
            'assigned_faculty_id': faculty['id'],
            'faculty_name': faculty['full_name'],
            'faculty_username': row['faculty_username'].strip()
        })
    
    return {'duties': duties, 'errors': errors}
