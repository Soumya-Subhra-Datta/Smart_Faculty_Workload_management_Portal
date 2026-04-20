"""
User model — CRUD operations for users table.
"""
import json
from models.db import execute_query
from werkzeug.security import check_password_hash, generate_password_hash


def authenticate(username, password):
    """Authenticate a user by username and password."""
    user = execute_query(
        "SELECT * FROM users WHERE username = %s",
        (username,), fetch_one=True
    )
    if user and check_password_hash(user['password_hash'], password):
        user.pop('password_hash', None)
        if isinstance(user.get('subjects'), str):
            user['subjects'] = json.loads(user['subjects'])
        return user
    return None


def get_by_id(user_id):
    """Get a user by ID."""
    user = execute_query(
        "SELECT id, username, full_name, email, department, role, subjects, created_at FROM users WHERE id = %s",
        (user_id,), fetch_one=True
    )
    if user and isinstance(user.get('subjects'), str):
        user['subjects'] = json.loads(user['subjects'])
    return user


def get_all_faculty():
    """Get all faculty members."""
    faculty = execute_query(
        "SELECT id, username, full_name, email, department, role, subjects, created_at FROM users WHERE role = 'faculty' ORDER BY department, full_name",
        fetch_all=True
    )
    for f in faculty:
        if isinstance(f.get('subjects'), str):
            f['subjects'] = json.loads(f['subjects'])
    return faculty


def get_faculty_by_department(department):
    """Get all faculty in a department."""
    faculty = execute_query(
        "SELECT id, username, full_name, email, department, role, subjects FROM users WHERE role = 'faculty' AND department = %s",
        (department,), fetch_all=True
    )
    for f in faculty:
        if isinstance(f.get('subjects'), str):
            f['subjects'] = json.loads(f['subjects'])
    return faculty


def create_faculty(data):
    """Create a new faculty member."""
    password_hash = generate_password_hash(data.get('password', 'faculty123'))
    subjects = json.dumps(data.get('subjects', []))
    return execute_query(
        """INSERT INTO users (username, password_hash, full_name, email, department, role, subjects)
           VALUES (%s, %s, %s, %s, %s, 'faculty', %s)""",
        (data['username'], password_hash, data['full_name'], data['email'],
         data['department'], subjects),
        commit=True
    )


def update_faculty(faculty_id, data):
    """Update a faculty member's details."""
    fields = []
    params = []
    if 'full_name' in data:
        fields.append("full_name = %s")
        params.append(data['full_name'])
    if 'email' in data:
        fields.append("email = %s")
        params.append(data['email'])
    if 'department' in data:
        fields.append("department = %s")
        params.append(data['department'])
    if 'subjects' in data:
        fields.append("subjects = %s")
        params.append(json.dumps(data['subjects']))
    if 'password' in data and data['password']:
        fields.append("password_hash = %s")
        params.append(generate_password_hash(data['password']))

    if not fields:
        return 0

    params.append(faculty_id)
    return execute_query(
        f"UPDATE users SET {', '.join(fields)} WHERE id = %s AND role = 'faculty'",
        tuple(params)
    )


def delete_faculty(faculty_id):
    """Delete a faculty member."""
    return execute_query(
        "DELETE FROM users WHERE id = %s AND role = 'faculty'",
        (faculty_id,)
    )


def get_faculty_with_subject(subject):
    """Get all faculty who can teach a given subject."""
    faculty = execute_query(
        "SELECT id, username, full_name, email, department, subjects FROM users WHERE role = 'faculty'",
        fetch_all=True
    )
    result = []
    for f in faculty:
        subjects = f.get('subjects', '[]')
        if isinstance(subjects, str):
            subjects = json.loads(subjects)
        if subject in subjects:
            f['subjects'] = subjects
            result.append(f)
    return result
